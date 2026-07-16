"""
Mini-training endpoints for a single word.
Flow: intro → semantic-anchor → double-recall (5 steps) → associations → complete.
"""

from fastapi import APIRouter

from app.api.deps import Training, WordQueries
from app.schemas.training import (
    AntiConfusionExercise,
    AntiConfusionSubmitRequest,
    AntiConfusionSubmitResult,
    AssociationRecallExercise,
    AssociationRecallResult,
    AssociationRecallSubmitRequest,
    AssociationsSubmitRequest,
    DoubleRecallExampleResult,
    DoubleRecallExampleSubmitRequest,
    DoubleRecallExercise,
    DoubleRecallFinishResult,
    DoubleRecallGlossResult,
    DoubleRecallGlossSubmitRequest,
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
from app.schemas.word import WordCardBase

router = APIRouter()


@router.get("/word/{word_id}/intro", response_model=WordIntroInfo)
async def get_training_intro(
    word_id: int,
    training: Training,
) -> WordIntroInfo:
    """Data for the word-intro screen: translation, examples, synonyms, explanation."""
    return await training.show_info_about_word(word_id)


@router.get("/word/{word_id}/exercise/semantic-anchor", response_model=SemanticAnchorExercise)
async def get_semantic_anchor(
    word_id: int,
    training: Training,
) -> SemanticAnchorExercise:
    """Exercise: pick the correct semantic anchor from options."""
    return await training.get_semantic_anchor_exercise(word_id)


@router.post("/word/{word_id}/exercise/semantic-anchor", response_model=SemanticAnchorSubmitResult)
async def check_semantic_anchor(
    word_id: int,
    body: SemanticAnchorSubmitRequest,
    training: Training,
) -> SemanticAnchorSubmitResult:
    """Check answer for the semantic-anchor exercise."""
    return await training.submit_semantic_anchor_answer_for_word(word_id, body)


@router.get("/word/{word_id}/exercise/double-recall", response_model=DoubleRecallExercise)
async def get_double_recall(
    word_id: int,
    training: Training,
) -> DoubleRecallExercise:
    """Double recall: GET creates the session and exercise_id."""
    return await training.get_double_recall_exercise(word_id)


@router.post(
    "/word/{word_id}/exercise/double-recall/translation",
    response_model=DoubleRecallTranslationResult,
)
async def submit_double_recall_translation(
    word_id: int,
    body: DoubleRecallTranslationSubmitRequest,
    training: Training,
) -> DoubleRecallTranslationResult:
    """Step 0: recall the English word from the translation."""
    return await training.check_double_recall_translation_step(word_id, body)


@router.post("/word/{word_id}/exercise/double-recall/gloss", response_model=DoubleRecallGlossResult)
async def submit_double_recall_gloss(
    word_id: int,
    body: DoubleRecallGlossSubmitRequest,
    training: Training,
) -> DoubleRecallGlossResult:
    """Step 1: recall the translation/meaning from the English word."""
    return await training.check_double_recall_gloss_step(word_id, body)


@router.post(
    "/word/{word_id}/exercise/double-recall/synonyms",
    response_model=DoubleRecallSynonymsResult,
)
async def submit_double_recall_synonyms(
    word_id: int,
    body: DoubleRecallSynonymsSubmitRequest,
    training: Training,
) -> DoubleRecallSynonymsResult:
    """Step 2: synonyms."""
    return await training.check_double_recall_synonyms_step(word_id, body)


@router.post(
    "/word/{word_id}/exercise/double-recall/example",
    response_model=DoubleRecallExampleResult,
)
async def submit_double_recall_example(
    word_id: int,
    body: DoubleRecallExampleSubmitRequest,
    training: Training,
) -> DoubleRecallExampleResult:
    """Step 3: pick the correct context from three sentences."""
    return await training.check_double_recall_example_step(word_id, body)


@router.post(
    "/word/{word_id}/exercise/double-recall/sentence",
    response_model=DoubleRecallFinishResult,
)
async def submit_double_recall_own_sentence(
    word_id: int,
    body: DoubleRecallOwnSentenceSubmitRequest,
    training: Training,
) -> DoubleRecallFinishResult:
    """Step 4: own sentence with the word; full summary."""
    return await training.check_double_recall_own_sentence_step(word_id, body)


@router.post("/word/{word_id}/associations")
async def submit_associations(
    word_id: int,
    body: AssociationsSubmitRequest,
    training: Training,
):
    """Accept and store user associations or sentences for the word."""
    await training.save_user_association(
        word_id,
        body.associations,
        association_v2=body.association_v2,
    )
    return {"status": "ok"}


@router.post("/word/{word_id}/complete", response_model=WordCardBase)
async def complete_training(
    word_id: int,
    training: Training,
    word_queries: WordQueries,
) -> WordCardBase:
    """Finish mini-training: create a word card (intro + associations) for the profile."""
    card = await training.create_word_card_after_training(word_id)
    word = await word_queries.get_word_by_id(word_id)
    return WordCardBase(
        id=card.id,
        word_id=card.word_id,
        word_text=word.word_text,
        translation=card.translation or "",
        explanation=card.explanation or None,
        examples=card.examples if isinstance(card.examples, list) else [],
        synonyms=card.synonyms if isinstance(card.synonyms, list) else [],
        associations=card.associations if isinstance(card.associations, list) else [],
        created_at=card.created_at,
    )


@router.get("/word/{word_id}/exercise/anti-confusion", response_model=AntiConfusionExercise)
async def anti_confusion(
    word_id: int,
    training: Training,
) -> AntiConfusionExercise:
    """Exercise: pick the word that best fits the context."""
    return await training.get_anti_confusion_exercise(word_id)


@router.post("/word/{word_id}/exercise/anti-confusion", response_model=AntiConfusionSubmitResult)
async def check_antonym_answer(
    word_id: int,
    body: AntiConfusionSubmitRequest,
    training: Training,
) -> AntiConfusionSubmitResult:
    """Check answer for the anti-confusion exercise."""
    return await training.check_anti_confusion_answer_for_word(word_id, body)


@router.get(
    "/word/{word_id}/exercise/association-recall",
    response_model=AssociationRecallExercise,
)
async def get_association_recall(
    word_id: int,
    training: Training,
) -> AssociationRecallExercise:
    """Association 2.0 cue for recalling the word."""
    return await training.get_association_recall_exercise(word_id)


@router.post(
    "/word/{word_id}/exercise/association-recall",
    response_model=AssociationRecallResult,
)
async def submit_association_recall(
    word_id: int,
    body: AssociationRecallSubmitRequest,
    training: Training,
) -> AssociationRecallResult:
    """Check word recall from an Association 2.0 partial cue."""
    return await training.check_association_recall_answer(word_id, body)
