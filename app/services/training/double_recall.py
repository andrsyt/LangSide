from __future__ import annotations

import asyncio

from localization.get_synonyms import get_synonyms_with_auto_fill

from app.core.exceptions.http import BadRequestError, InternalServerError
from app.helpers.datetime_utils import utc_naive_now
from app.helpers.training.double_recall_guard import (
    STEP_EN_RECALL,
    STEP_EXAMPLE,
    STEP_GLOSS_RECALL,
    STEP_OWN_SENTENCE,
    STEP_SYNONYMS,
    TOTAL_STEPS,
    DoubleRecallStepGuard,
)
from app.helpers.training_helpers import (
    TrainingAnswerHelper,
    TrainingContentHelper,
    TrainingContextHelper,
    TrainingDistractorHelper,
    TrainingOptionHelper,
    TrainingStateHelper,
    fetch_context_distractors_from_groq,
)
from app.helpers.translation_helper import translate_word
from app.models.double_recall_session import DoubleRecallSession
from app.schemas.training import (
    DoubleRecallExampleResult,
    DoubleRecallExercise,
    DoubleRecallExampleSubmitRequest,
    DoubleRecallFinishResult,
    DoubleRecallGlossResult,
    DoubleRecallGlossSubmitRequest,
    DoubleRecallOwnSentenceSubmitRequest,
    DoubleRecallSynonymsResult,
    DoubleRecallSynonymsSubmitRequest,
    DoubleRecallTranslationResult,
    DoubleRecallTranslationSubmitRequest,
)
from app.services.training.base import TrainingBaseService
from app.services.words.user_word_confusion_service import bump_user_word_confusion


class DoubleRecallTrainingService(TrainingBaseService):
    """Use cases for double recall training."""

    async def get_double_recall_exercise(self, word_id: int) -> DoubleRecallExercise:
        await self.ensure_word_analyzed(word_id)
        word = await self.get_word(word_id)
        lang = await self.get_user_language()
        translation_prompt = (await translate_word(word.word_text, lang)) or ""

        examples = TrainingContentHelper.parse_examples(word.examples)
        base_sentence = examples[0].strip() if examples else ""
        if not base_sentence:
            base_sentence = "Choose the sentence where this word fits naturally."

        learning_words = await self.get_learning_words_except(word_id)
        ai_pair = await fetch_context_distractors_from_groq(base_sentence, word.word_text)
        if ai_pair is not None:
            distractor_one, distractor_two = ai_pair
        else:
            if len(learning_words) < 2:
                raise BadRequestError(
                    "Not enough words to generate exercise "
                    "(need more learning words when AI distractors are unavailable)",
                    error_code="NOT_ENOUGH_DISTRACTORS",
                )
            try:
                distractor_one, distractor_two = (
                    TrainingDistractorHelper.pick_two_distractor_words(
                        learning_words,
                        word.word_text,
                    )
                )
            except ValueError:
                raise BadRequestError(
                    "Not enough distractor candidates after filtering",
                    error_code="NOT_ENOUGH_DISTRACTORS",
                ) from None

        neighbor_id_one, neighbor_id_two = TrainingOptionHelper.neighbor_word_ids_from_texts(
            distractor_one,
            distractor_two,
            learning_words,
        )

        three_sentences, _ = TrainingContextHelper.build_three_similar_sentences(
            word.word_text,
            base_sentence,
            distractor_one,
            distractor_two,
        )
        if len(three_sentences) != 3:
            raise InternalServerError(
                "Failed to build example sentences",
                error_code="EXAMPLE_BUILD_FAILED",
            )

        example_sentences, example_neighbor_word_ids, correct_example_index = (
            TrainingOptionHelper.shuffle_sentence_neighbor_aligned(
                three_sentences,
                [None, neighbor_id_one, neighbor_id_two],
            )
        )
        min_synonyms = 1

        session = await self.access.create_double_recall_session(
            DoubleRecallSession(
                user_id=self.user_id,
                word_id=word.id,
                example_sentences=example_sentences,
                example_neighbor_word_ids=example_neighbor_word_ids,
                correct_example_index=correct_example_index,
                min_synonyms=min_synonyms,
                translation_prompt=translation_prompt,
            )
        )
        await self.db.commit()
        await self.db.refresh(session)

        return DoubleRecallExercise(
            exercise_id=session.id,
            word_id=word.id,
            word_text=word.word_text,
            translation_prompt=translation_prompt,
            min_synonyms=min_synonyms,
            example_sentences=example_sentences,
            total_steps=TOTAL_STEPS,
            current_step=session.current_step,
        )

    async def check_double_recall_translation_step(
        self,
        word_id: int,
        body: DoubleRecallTranslationSubmitRequest,
    ) -> DoubleRecallTranslationResult:
        session = await self.access.get_double_recall_session_or_404(
            body.exercise_id,
            word_id,
        )
        DoubleRecallStepGuard.ensure_active(session)
        DoubleRecallStepGuard.ensure_step(session, STEP_EN_RECALL)

        word = await self.get_word(word_id)
        en_ok = TrainingAnswerHelper.check_english_word_answer_relaxed(
            body.translation_answer,
            word.word_text,
        )
        if en_ok:
            session.translation_passed = True
            session.current_step = STEP_GLOSS_RECALL
            await self.db.commit()

        return DoubleRecallTranslationResult(
            correct=en_ok,
            current_step=session.current_step,
        )

    async def check_double_recall_gloss_step(
        self,
        word_id: int,
        body: DoubleRecallGlossSubmitRequest,
    ) -> DoubleRecallGlossResult:
        session = await self.access.get_double_recall_session_or_404(
            body.exercise_id,
            word_id,
        )
        DoubleRecallStepGuard.ensure_active(session)
        DoubleRecallStepGuard.ensure_step(session, STEP_GLOSS_RECALL)

        word = await self.get_word(word_id)
        gloss_ok = TrainingAnswerHelper.check_translation_relaxed(
            body.gloss_answer,
            word.word_text,
            session.translation_prompt,
        )
        if gloss_ok:
            session.gloss_recall_passed = True
            session.current_step = STEP_SYNONYMS
            await self.db.commit()

        return DoubleRecallGlossResult(
            correct=gloss_ok,
            current_step=session.current_step,
        )

    async def check_double_recall_synonyms_step(
        self,
        word_id: int,
        body: DoubleRecallSynonymsSubmitRequest,
    ) -> DoubleRecallSynonymsResult:
        session = await self.access.get_double_recall_session_or_404(
            body.exercise_id,
            word_id,
        )
        DoubleRecallStepGuard.ensure_active(session)
        DoubleRecallStepGuard.ensure_step(session, STEP_SYNONYMS)

        if body.skip:
            session.synonyms_submitted = []
            session.synonyms_passed = False
            session.current_step = STEP_EXAMPLE
            await self.db.commit()
            return DoubleRecallSynonymsResult(
                correct=False,
                current_step=session.current_step,
            )

        word = await self.get_word(word_id)
        expected_synonyms = await asyncio.to_thread(
            get_synonyms_with_auto_fill,
            word.word_text,
        )
        synonyms_result = TrainingAnswerHelper.check_synonyms_recall_answer(
            body.synonyms_answer,
            expected_synonyms,
            session.min_synonyms,
        )
        if synonyms_result.correct:
            session.synonyms_submitted = list(body.synonyms_answer)
            session.synonyms_passed = True
            session.current_step = STEP_EXAMPLE
            await self.db.commit()

        return DoubleRecallSynonymsResult(
            correct=synonyms_result.correct,
            current_step=session.current_step,
        )

    async def check_double_recall_example_step(
        self,
        word_id: int,
        body: DoubleRecallExampleSubmitRequest,
    ) -> DoubleRecallExampleResult:
        session = await self.access.get_double_recall_session_or_404(
            body.exercise_id,
            word_id,
        )
        DoubleRecallStepGuard.ensure_active(session)
        DoubleRecallStepGuard.ensure_step(session, STEP_EXAMPLE)

        if session.synonyms_submitted is None:
            raise BadRequestError(
                "Synonyms step not completed; finish or skip synonyms first",
                error_code="SYNONYMS_STEP_REQUIRED",
            )
        if body.selected_example_index < 0 or body.selected_example_index >= len(
            session.example_sentences
        ):
            raise BadRequestError(
                "Invalid selected_example_index",
                error_code="INVALID_EXAMPLE_INDEX",
            )

        example_ok = body.selected_example_index == session.correct_example_index
        if not example_ok:
            neighbor_word_id = None
            if (
                session.example_neighbor_word_ids
                and 0 <= body.selected_example_index < len(session.example_neighbor_word_ids)
            ):
                raw_neighbor_id = session.example_neighbor_word_ids[
                    body.selected_example_index
                ]
                if raw_neighbor_id is not None:
                    neighbor_word_id = int(raw_neighbor_id)
            if neighbor_word_id is not None:
                await bump_user_word_confusion(
                    self.db,
                    self.user_id,
                    word_id,
                    neighbor_word_id,
                )

        session.example_passed = example_ok
        session.current_step = STEP_OWN_SENTENCE
        await self.db.commit()

        return DoubleRecallExampleResult(
            correct=example_ok,
            current_step=session.current_step,
        )

    async def check_double_recall_own_sentence_step(
        self,
        word_id: int,
        body: DoubleRecallOwnSentenceSubmitRequest,
    ) -> DoubleRecallFinishResult:
        session = await self.access.get_double_recall_session_or_404(
            body.exercise_id,
            word_id,
        )
        DoubleRecallStepGuard.ensure_active(session)
        DoubleRecallStepGuard.ensure_step(session, STEP_OWN_SENTENCE)

        if session.synonyms_submitted is None:
            raise BadRequestError(
                "Complete earlier steps before own sentence",
                error_code="EARLIER_STEPS_REQUIRED",
            )

        word = await self.get_word(word_id)
        sentence_ok = TrainingAnswerHelper.sentence_contains_word(
            body.sentence,
            word.word_text,
        )
        session.own_sentence_text = body.sentence.strip()
        session.own_sentence_passed = sentence_ok
        session.used_at = utc_naive_now()
        await self.db.commit()

        return await self._build_finish_result(session, word)

    async def _build_finish_result(
        self,
        session: DoubleRecallSession,
        word,
    ) -> DoubleRecallFinishResult:
        submitted_synonyms = list(session.synonyms_submitted or [])
        expected_synonyms = await asyncio.to_thread(
            get_synonyms_with_auto_fill,
            word.word_text,
        )
        synonyms_result = TrainingAnswerHelper.check_synonyms_recall_answer(
            submitted_synonyms,
            expected_synonyms,
            session.min_synonyms,
        )
        synonyms_skipped = len(submitted_synonyms) == 0

        translation_correct = bool(session.translation_passed)
        gloss_recall_correct = bool(session.gloss_recall_passed)
        if session.synonyms_passed is None:
            synonyms_correct = (
                synonyms_result.correct if not synonyms_skipped else False
            )
        else:
            synonyms_correct = bool(session.synonyms_passed)
        if session.example_passed is None:
            example_correct = session.current_step > STEP_EXAMPLE
        else:
            example_correct = bool(session.example_passed)
        own_sentence_correct = bool(session.own_sentence_passed)

        overall_correct = (
            translation_correct
            and gloss_recall_correct
            and synonyms_correct
            and example_correct
            and own_sentence_correct
        )

        training = await self.access.get_or_create_training(word.id)
        training.synonyms_shown = list(expected_synonyms)
        training.synonyms_user = submitted_synonyms
        if session.own_sentence_text:
            training.example_sentence = session.own_sentence_text
        training.last_training_at = utc_naive_now()
        TrainingStateHelper.append_completed_quest_type(training, "double_recall")
        await self.db.commit()

        return DoubleRecallFinishResult(
            translation_correct=translation_correct,
            gloss_recall_correct=gloss_recall_correct,
            synonyms_correct=synonyms_correct,
            synonyms_skipped=synonyms_skipped,
            example_correct=example_correct,
            own_sentence_correct=own_sentence_correct,
            overall_correct=overall_correct,
            correct_word=word.word_text,
            matched_synonyms=synonyms_result.correct_synonyms,
            missed_synonyms=synonyms_result.incorrect_synonyms,
        )
