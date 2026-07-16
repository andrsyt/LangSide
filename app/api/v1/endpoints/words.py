import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.api.deps import (
    AIAnalysis,
    Billing,
    LanguageResolver,
    Repeats,
    WordAI,
    WordCommands,
    WordQueries,
)
from app.models.word import DifficultyLevel
from app.schemas.word import (
    WordCreate,
    WordDifficultyUpdate,
    WordResponse,
    WordUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=WordResponse)
async def create_word_endpoint(
    word_data: WordCreate,
    word_commands: WordCommands,
    word_ai: WordAI,
    language_resolver: LanguageResolver,
    billing: Billing,
    ai_analysis: AIAnalysis,
) -> WordResponse:
    new_word = await word_commands.create_word(word_data)
    can_make_request = await billing.check_rate_limits()

    if not can_make_request:
        return WordResponse.model_validate(new_word)

    try:
        user_language = await language_resolver.get_user_target_language()
        logger.info(f"Using language for word '{word_data.word_text}': {user_language}")

        analysis_result = await ai_analysis.analyze_word(
            word=word_data.word_text,
            difficulty_level=None,
            target_language=user_language,
        )
    except Exception:
        return WordResponse.model_validate(new_word)

    updated_word = await word_ai.update_word_with_ai_analysis(new_word.id, analysis_result)

    await billing.record_api_usage()

    return WordResponse.model_validate(updated_word)


@router.get("/", response_model=list[WordResponse])
async def get_words_endpoint(
    word_queries: WordQueries,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[WordResponse]:
    difficulty_level: Optional[DifficultyLevel] = None
    if difficulty:
        try:
            difficulty_level = DifficultyLevel(difficulty.upper())
        except ValueError:
            difficulty_level = None

    date_from_datetime: Optional[datetime] = None
    if date_from:
        date_from_datetime = datetime.combine(date_from, datetime.min.time())

    date_to_datetime: Optional[datetime] = None
    if date_to:
        date_to_datetime = datetime.combine(date_to, datetime.max.time())

    words = await word_queries.get_user_words(
        search,
        difficulty_level,
        date_from_datetime,
        date_to_datetime,
    )

    return [WordResponse.model_validate(word) for word in words]


@router.get("/review", response_model=list[WordResponse])
async def get_words_to_repeat_endpoint(
    repeats: Repeats,
    limit: int = 20,
) -> list[WordResponse]:
    words = await repeats.get_words_to_repeat(limit)
    return [WordResponse.model_validate(word) for word in words]


@router.get("/{word_id}", response_model=WordResponse)
async def get_word_endpoint(
    word_id: int,
    word_queries: WordQueries,
) -> WordResponse:
    word = await word_queries.get_word_by_id(word_id)
    return WordResponse.model_validate(word)


@router.patch("/{word_id}/difficulty", response_model=WordResponse)
async def update_word_difficulty_endpoint(
    word_id: int,
    payload: WordDifficultyUpdate,
    word_commands: WordCommands,
) -> WordResponse:
    updated_word = await word_commands.update_word(
        word_id,
        WordUpdate(difficulty=payload.difficulty),
    )
    return WordResponse.model_validate(updated_word)


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word_endpoint(
    word_id: int,
    word_commands: WordCommands,
) -> None:
    await word_commands.delete_word(word_id)


@router.post("/{word_id}/analyze", response_model=WordResponse)
async def analyze_word_endpoint(
    word_id: int,
    word_queries: WordQueries,
    word_ai: WordAI,
    language_resolver: LanguageResolver,
    billing: Billing,
    ai_analysis: AIAnalysis,
) -> WordResponse:
    word = await word_queries.get_word_by_id(word_id)

    can_make_request = await billing.check_rate_limits()
    if not can_make_request:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    try:
        user_language = await language_resolver.get_user_target_language()
        analysis_result = await ai_analysis.analyze_word(
            word=word.word_text,
            difficulty_level=None,
            target_language=user_language,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing word: {str(e)}")

    updated_word = await word_ai.update_word_with_ai_analysis(word_id, analysis_result)
    await billing.record_api_usage()
    return WordResponse.model_validate(updated_word)


@router.post("/{word_id}/reset-progress", response_model=WordResponse)
async def reset_word_progress_endpoint(
    word_id: int,
    repeats: Repeats,
) -> WordResponse:
    updated_word = await repeats.reset_word_progress(word_id)
    return WordResponse.model_validate(updated_word)


@router.post("/{word_id}/mark-mastered", response_model=WordResponse)
async def mark_word_mastered_endpoint(
    word_id: int,
    repeats: Repeats,
) -> WordResponse:
    updated_word = await repeats.mark_word_mastered(word_id)
    return WordResponse.model_validate(updated_word)
