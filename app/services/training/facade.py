from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import Training
from app.models.word_card import WordCard
from app.schemas.training import (
    AntiConfusionExercise,
    AntiConfusionSubmitRequest,
    AntiConfusionSubmitResult,
    AssociationRecallExercise,
    AssociationRecallResult,
    AssociationRecallSubmitRequest,
    AssociationV2Input,
    DoubleRecallExercise,
    DoubleRecallExampleSubmitRequest,
    DoubleRecallExampleResult,
    DoubleRecallFinishResult,
    DoubleRecallGlossSubmitRequest,
    DoubleRecallGlossResult,
    DoubleRecallOwnSentenceSubmitRequest,
    DoubleRecallSynonymsResult,
    DoubleRecallSynonymsSubmitRequest,
    DoubleRecallTranslationResult,
    DoubleRecallTranslationSubmitRequest,
    SemanticAnchorExercise,
    SemanticAnchorSubmitRequest,
    SemanticAnchorSubmitResult,
    WordIntroInfo,
)
from app.services.training.anti_confusion import AntiConfusionTrainingService
from app.services.training.association import TrainingAssociationService
from app.services.training.double_recall import DoubleRecallTrainingService
from app.services.training.info import TrainingInfoQueryService
from app.services.training.semantic_anchor import SemanticAnchorTrainingService


class TrainingService:
    """Facade over all training use cases."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.info = TrainingInfoQueryService(db, user_id)
        self.semantic_anchor = SemanticAnchorTrainingService(db, user_id)
        self.association = TrainingAssociationService(db, user_id)
        self.double_recall = DoubleRecallTrainingService(db, user_id)
        self.anti_confusion = AntiConfusionTrainingService(db, user_id)

    async def get_synonyms_for_word(self, word_id: int) -> list[str]:
        return await self.info.get_synonyms_for_word(word_id)

    async def show_info_about_word(self, word_id: int) -> WordIntroInfo:
        return await self.info.show_info_about_word(word_id)

    async def save_user_association(
        self,
        word_id: int,
        user_answer: list[str] | None,
        association_v2: AssociationV2Input | None = None,
    ) -> Training:
        return await self.association.save_user_association(
            word_id,
            user_answer,
            association_v2=association_v2,
        )

    async def create_word_card_after_training(self, word_id: int) -> WordCard:
        return await self.association.create_word_card_after_training(word_id)

    async def get_semantic_anchor_exercise(self, word_id: int) -> SemanticAnchorExercise:
        return await self.semantic_anchor.get_semantic_anchor_exercise(word_id)

    async def submit_semantic_anchor_answer_for_word(
        self,
        word_id: int,
        body: SemanticAnchorSubmitRequest,
    ) -> SemanticAnchorSubmitResult:
        return await self.semantic_anchor.submit_semantic_anchor_answer_for_word(
            word_id,
            body,
        )

    async def get_association_recall_exercise(
        self,
        word_id: int,
    ) -> AssociationRecallExercise:
        return await self.association.get_association_recall_exercise(word_id)

    async def check_association_recall_answer(
        self,
        word_id: int,
        body: AssociationRecallSubmitRequest,
    ) -> AssociationRecallResult:
        return await self.association.check_association_recall_answer(word_id, body)

    async def get_double_recall_exercise(self, word_id: int) -> DoubleRecallExercise:
        return await self.double_recall.get_double_recall_exercise(word_id)

    async def check_double_recall_translation_step(
        self,
        word_id: int,
        body: DoubleRecallTranslationSubmitRequest,
    ) -> DoubleRecallTranslationResult:
        return await self.double_recall.check_double_recall_translation_step(
            word_id,
            body,
        )

    async def check_double_recall_gloss_step(
        self,
        word_id: int,
        body: DoubleRecallGlossSubmitRequest,
    ) -> DoubleRecallGlossResult:
        return await self.double_recall.check_double_recall_gloss_step(word_id, body)

    async def check_double_recall_synonyms_step(
        self,
        word_id: int,
        body: DoubleRecallSynonymsSubmitRequest,
    ) -> DoubleRecallSynonymsResult:
        return await self.double_recall.check_double_recall_synonyms_step(
            word_id,
            body,
        )

    async def check_double_recall_example_step(
        self,
        word_id: int,
        body: DoubleRecallExampleSubmitRequest,
    ) -> DoubleRecallExampleResult:
        return await self.double_recall.check_double_recall_example_step(word_id, body)

    async def check_double_recall_own_sentence_step(
        self,
        word_id: int,
        body: DoubleRecallOwnSentenceSubmitRequest,
    ) -> DoubleRecallFinishResult:
        return await self.double_recall.check_double_recall_own_sentence_step(
            word_id,
            body,
        )

    async def get_anti_confusion_exercise(self, word_id: int) -> AntiConfusionExercise:
        return await self.anti_confusion.get_anti_confusion_exercise(word_id)

    async def check_anti_confusion_answer_for_word(
        self,
        word_id: int,
        body: AntiConfusionSubmitRequest,
    ) -> AntiConfusionSubmitResult:
        return await self.anti_confusion.check_anti_confusion_answer_for_word(
            word_id,
            body,
        )
