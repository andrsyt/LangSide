from __future__ import annotations

from app.helpers.datetime_utils import utc_naive_now


from fastapi import HTTPException

from app.helpers.training.answers import TrainingAnswerHelper
from app.helpers.training_helpers import (
    TrainingAssociationHelper,
    TrainingContentHelper,
    TrainingStateHelper,
)
from app.models.training import Training
from app.models.word_card import WordCard
from app.schemas.training import (
    AssociationRecallExercise,
    AssociationRecallResult,
    AssociationRecallSubmitRequest,
    AssociationV2Input,
)
from app.services.training.base import TrainingBaseService


class TrainingAssociationService(TrainingBaseService):
    """Use cases for association-building and recall training."""

    async def save_user_association(
        self,
        word_id: int,
        user_answer: list[str] | None,
        association_v2: AssociationV2Input | None = None,
    ) -> Training:
        training = await self.access.get_or_create_training(word_id)
        freeform_associations = TrainingAssociationHelper.normalize_freeform_associations(
            user_answer
        )
        if freeform_associations:
            training.freeform_associations = freeform_associations
            training.user_association = (
                TrainingAssociationHelper.merge_legacy_system_with_user(
                    list(training.user_association or []),
                    freeform_associations,
                )
            )

        if association_v2 is not None:
            payload = association_v2.model_dump()
            training.association_v2_data = payload
            training.association_recall_cue = (
                TrainingAssociationHelper.build_association_recall_cue(payload)
            )
            TrainingStateHelper.append_completed_quest_type(
                training,
                "association_build",
            )

        if not freeform_associations and association_v2 is None:
            raise HTTPException(status_code=400, detail="Association payload is empty")

        training.last_training_at = utc_naive_now()
        await self.db.commit()
        await self.db.refresh(training)
        return training

    async def create_word_card_after_training(self, word_id: int) -> WordCard:
        word_info = await self.build_word_intro_info(word_id)
        training = await self.access.get_training(word_id)
        if not TrainingContentHelper.can_complete_training(training):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Complete requires: semantic anchor with correct context, "
                    "saved associations, and association recall if you used Association 2.0"
                ),
            )

        associations = TrainingContentHelper.collect_display_associations(training)
        word_card = await self.access.get_word_card(word_id)
        if word_card is None:
            word_card = WordCard(
                user_id=self.user_id,
                word_id=word_id,
                translation=word_info.translation or "",
                explanation=word_info.explanation or "",
                examples=word_info.examples,
                synonyms=word_info.synonyms,
                associations=associations,
                semantic_anchor_data=training.semantic_anchor_data if training else None,
                association_v2_data=training.association_v2_data if training else None,
            )
            await self.access.add_word_card(word_card)
        else:
            word_card.translation = word_info.translation or ""
            word_card.explanation = word_info.explanation or ""
            word_card.examples = word_info.examples
            word_card.synonyms = word_info.synonyms
            word_card.associations = associations
            word_card.semantic_anchor_data = (
                training.semantic_anchor_data if training else None
            )
            word_card.association_v2_data = (
                training.association_v2_data if training else None
            )

        await self.db.commit()
        await self.db.refresh(word_card)
        return word_card

    async def get_association_recall_exercise(
        self,
        word_id: int,
    ) -> AssociationRecallExercise:
        training = await self.access.get_or_create_training(word_id)
        cue_text = (training.association_recall_cue or "").strip()
        if not cue_text:
            raise HTTPException(
                status_code=400,
                detail="Association 2.0 cue is not available for this word yet",
            )
        anchor_text = ""
        if training.semantic_anchor_data:
            anchor_text = (
                training.semantic_anchor_data.get("accepted_anchor_text") or ""
            ).strip()
        if anchor_text:
            cue_text = f"Your anchor: {anchor_text} — {cue_text}"
        return AssociationRecallExercise(word_id=word_id, cue_text=cue_text)

    async def check_association_recall_answer(
        self,
        word_id: int,
        body: AssociationRecallSubmitRequest,
    ) -> AssociationRecallResult:
        training = await self.access.get_or_create_training(word_id)
        cue_text = (training.association_recall_cue or "").strip()
        if not cue_text:
            raise HTTPException(
                status_code=400,
                detail="Association 2.0 cue is not available for this word yet",
            )

        word = await self.get_word(word_id)
        correct = TrainingAnswerHelper.check_english_word_answer_relaxed(
            body.answer,
            word.word_text,
        )
        training.last_training_at = utc_naive_now()
        TrainingStateHelper.append_completed_quest_type(training, "association_recall")
        await self.db.commit()
        return AssociationRecallResult(
            correct=correct,
            correct_word=word.word_text,
            cue_text=cue_text,
        )
