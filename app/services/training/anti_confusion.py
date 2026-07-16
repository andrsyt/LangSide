from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now

import random

from fastapi import HTTPException

from app.helpers.training_helpers import TrainingContentHelper, TrainingStateHelper
from app.helpers.translation_helper import translate_word
from app.models.anti_confusion_session import AntiConfusionSession
from app.models.word import Word
from app.schemas.training import (
    AntiConfusionExercise,
    AntiConfusionSubmitRequest,
    AntiConfusionSubmitResult,
)
from app.services.training.base import TrainingBaseService
from app.services.words.user_word_confusion_service import (
    bump_user_word_confusion,
    get_top_neighbor_word_id,
)


class AntiConfusionTrainingService(TrainingBaseService):
    """Use cases for anti-confusion training."""

    async def get_anti_confusion_exercise(self, word_id: int) -> AntiConfusionExercise:
        word = await self.get_word(word_id)
        learning_words = await self.get_learning_words_except(word_id)
        if len(learning_words) < 2:
            raise HTTPException(
                status_code=400,
                detail="Not enough words to generate exercise",
            )

        learning_ids = {learning_word.id for learning_word in learning_words}
        learning_by_id = {learning_word.id: learning_word for learning_word in learning_words}
        prioritized_id = await get_top_neighbor_word_id(
            self.db,
            self.user_id,
            word.id,
            learning_ids,
        )
        confusion_focus = prioritized_id is not None

        distractors: list[Word] = []
        if prioritized_id is not None and prioritized_id in learning_by_id:
            distractors.append(learning_by_id[prioritized_id])

        pool = [
            learning_word
            for learning_word in learning_words
            if learning_word.id != prioritized_id
        ]
        need_more = 2 - len(distractors)
        if need_more > 0:
            if len(pool) < need_more:
                raise HTTPException(
                    status_code=400,
                    detail="Not enough words to generate exercise",
                )
            distractors.extend(random.sample(pool, need_more))

        if len(distractors) != 2:
            raise HTTPException(
                status_code=500,
                detail="Failed to pick distractor words",
            )

        distractor_one, distractor_two = distractors
        triples = [
            (word.word_text.strip(), word.id),
            (distractor_one.word_text.strip(), distractor_one.id),
            (distractor_two.word_text.strip(), distractor_two.id),
        ]
        random.shuffle(triples)
        options = [triple[0] for triple in triples]
        option_word_ids = [triple[1] for triple in triples]
        correct_index = next(
            index for index, triple in enumerate(triples) if triple[1] == word.id
        )

        parsed_examples = TrainingContentHelper.parse_examples(word.examples)
        context_sentence = parsed_examples[0] if parsed_examples else (word.examples or "")

        session = await self.access.create_anti_confusion_session(
            AntiConfusionSession(
                user_id=self.user_id,
                word_id=word.id,
                options=options,
                option_word_ids=option_word_ids,
                correct_index=correct_index,
            )
        )
        await self.db.commit()
        await self.db.refresh(session)

        partner_word: str | None = None
        if confusion_focus and prioritized_id is not None:
            partner = learning_by_id.get(prioritized_id)
            if partner is not None:
                partner_word = partner.word_text.strip()

        return AntiConfusionExercise(
            exercise_id=session.id,
            word_id=word.id,
            question="Choose the word that fits this context best.",
            context_sentence=context_sentence,
            options=options,
            confusion_pair_focus=confusion_focus,
            confusion_partner_word=partner_word,
        )

    async def check_anti_confusion_answer_for_word(
        self,
        word_id: int,
        body: AntiConfusionSubmitRequest,
    ) -> AntiConfusionSubmitResult:
        session = await self.access.get_anti_confusion_session_or_404(
            body.exercise_id,
            word_id,
        )
        if session.used_at is not None:
            raise HTTPException(status_code=410, detail="Exercise already used")

        word = await self.get_word(word_id)
        if body.selected_index < 0 or body.selected_index >= len(session.options):
            raise HTTPException(status_code=400, detail="Invalid selected index")

        is_correct = body.selected_index == session.correct_index
        neighbor_word_id: int | None = None
        if not is_correct:
            if session.option_word_ids and len(session.option_word_ids) == len(session.options):
                raw_neighbor_id = session.option_word_ids[body.selected_index]
                if raw_neighbor_id is not None and raw_neighbor_id != word.id:
                    neighbor_word_id = int(raw_neighbor_id)
            if neighbor_word_id is None:
                wrong_text = (session.options[body.selected_index] or "").strip().lower()
                for learning_word in await self.get_learning_words_except(word_id):
                    if (learning_word.word_text or "").strip().lower() == wrong_text:
                        neighbor_word_id = learning_word.id
                        break
            await bump_user_word_confusion(
                self.db,
                self.user_id,
                word_id,
                neighbor_word_id,
            )

        pair_hint = None
        if not is_correct and neighbor_word_id is not None:
            pair_hint = await self.build_anti_confusion_pair_hint(word, neighbor_word_id)

        session.used_at = utc_naive_now()
        training = await self.access.get_or_create_training(word_id)
        training.last_training_at = utc_naive_now()
        TrainingStateHelper.append_completed_quest_type(training, "anti_confusion")
        await self.db.commit()

        return AntiConfusionSubmitResult(
            is_correct=is_correct,
            selected_option=session.options[body.selected_index],
            correct_option=session.options[session.correct_index],
            explanation=word.explanation
            or "Pick the option that matches the context best.",
            pair_hint=pair_hint,
            suggest_retry=not is_correct,
        )

    async def build_anti_confusion_pair_hint(
        self,
        word: Word,
        neighbor_word_id: int,
    ) -> str | None:
        try:
            neighbor = await self.get_word(neighbor_word_id)
        except HTTPException:
            return None

        lang = await self.get_user_language()
        target_translation = await translate_word(word.word_text, lang)
        neighbor_translation = await translate_word(neighbor.word_text, lang)
        return (
            f"Don't confuse «{word.word_text}» ({(target_translation or '').strip()}) "
            f"with «{neighbor.word_text}» ({(neighbor_translation or '').strip()})."
        ).strip()
