from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now


from fastapi import HTTPException

from app.helpers.training_helpers import (
    TrainingContextHelper,
    TrainingDistractorHelper,
    TrainingOptionHelper,
    TrainingStateHelper,
    default_anchor_prompts,
    fetch_anchor_prompts_from_groq,
    fetch_context_distractors_from_groq,
)
from app.models.semantic_anchor_session import SemanticAnchorSession
from app.schemas.training import (
    SemanticAnchorExercise,
    SemanticAnchorSubmitRequest,
    SemanticAnchorSubmitResult,
)
from app.services.training.base import TrainingBaseService


class SemanticAnchorTrainingService(TrainingBaseService):
    """Use cases for semantic anchor training."""

    async def get_semantic_anchor_exercise(self, word_id: int) -> SemanticAnchorExercise:
        word = await self.get_word(word_id)
        word_info = await self.build_word_intro_info(word_id)

        explanation_short = (word_info.explanation or "").strip()
        if not explanation_short:
            explanation_short = "Understand the core meaning of the word in context."

        example = word_info.examples[0].strip() if word_info.examples else ""
        if not example:
            example = "Choose the context where this word sounds natural."

        lang = await self.get_user_language()
        translation_gloss = (word_info.translation or "").strip()
        anchor_variants = await fetch_anchor_prompts_from_groq(
            word_text=word.word_text,
            explanation=explanation_short,
            translation_gloss=translation_gloss,
            learner_language=lang,
        )
        anchor_personalized = anchor_variants is not None
        if not anchor_variants:
            anchor_variants = default_anchor_prompts(
                word.word_text,
                translation_gloss,
                lang,
            )

        learning_words = await self.get_learning_words_except(word_id)
        ai_pair = await fetch_context_distractors_from_groq(example, word.word_text)
        if ai_pair is not None:
            distractor_one, distractor_two = ai_pair
        else:
            if len(learning_words) < 2:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Not enough words to generate exercise "
                        "(need more learning words when AI distractors are unavailable)"
                    ),
                )
            try:
                distractor_one, distractor_two = (
                    TrainingDistractorHelper.pick_two_distractor_words(
                        learning_words,
                        word.word_text,
                    )
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Not enough distractor candidates after filtering",
                ) from None

        context_variants, _ = TrainingContextHelper.build_three_similar_sentences(
            word.word_text,
            example,
            distractor_one,
            distractor_two,
        )
        shuffled_contexts, correct_context_index = (
            TrainingOptionHelper.shuffle_context_variants(context_variants)
        )

        session = await self.access.create_semantic_anchor_session(
            SemanticAnchorSession(
                user_id=self.user_id,
                word_id=word_id,
                explanation=explanation_short,
                example=example,
                anchor_variants=anchor_variants,
                context_variants=shuffled_contexts,
                correct_context_index=correct_context_index,
            )
        )
        await self.db.commit()
        await self.db.refresh(session)

        return SemanticAnchorExercise(
            exercise_id=session.id,
            explanation=explanation_short,
            example=example,
            anchor_variants=anchor_variants,
            anchor_prompts_personalized=anchor_personalized,
            context_variants=shuffled_contexts,
        )

    async def submit_semantic_anchor_answer_for_word(
        self,
        word_id: int,
        body: SemanticAnchorSubmitRequest,
    ) -> SemanticAnchorSubmitResult:
        session = await self.access.get_semantic_anchor_session_or_404(
            body.exercise_id,
            word_id,
        )
        if session.used_at is not None:
            raise HTTPException(status_code=410, detail="Exercise already used")
        if body.chosen_anchor_id < 0 or body.chosen_anchor_id >= len(session.anchor_variants):
            raise HTTPException(status_code=400, detail="Invalid chosen_anchor_id")

        contexts = list(session.context_variants or [])
        if body.context_choice_index >= len(contexts):
            raise HTTPException(status_code=400, detail="Invalid context_choice_index")

        selected_context_index = body.context_choice_index
        is_context_correct = selected_context_index == session.correct_context_index
        custom_anchor = body.custom_anchor_text.strip()
        accepted_anchor_text = custom_anchor
        correct_sentence = contexts[session.correct_context_index]
        selected_sentence = contexts[selected_context_index]
        if is_context_correct:
            feedback_message = "Correct — this sentence matches how the word is used."
        else:
            feedback_message = (
                "Not quite. The sentence that fits this word best is shown below."
            )

        training = await self.access.get_or_create_training(word_id)
        training.semantic_anchor_data = {
            "exercise_id": session.id,
            "accepted_anchor_text": accepted_anchor_text,
            "anchor_template": session.anchor_variants[body.chosen_anchor_id],
            "is_context_correct": is_context_correct,
            "context_choice_index": selected_context_index,
            "correct_context_index": session.correct_context_index,
            "example": session.example,
        }
        training.example_sentence = session.example
        training.last_training_at = utc_naive_now()
        TrainingStateHelper.append_completed_quest_type(training, "semantic_anchor")

        session.used_at = utc_naive_now()
        await self.db.commit()
        return SemanticAnchorSubmitResult(
            is_context_correct=is_context_correct,
            accepted_anchor_text=accepted_anchor_text,
            correct_context_sentence=correct_sentence,
            selected_context_sentence=selected_sentence,
            feedback_message=feedback_message,
        )
