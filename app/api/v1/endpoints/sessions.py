"""Today session HTTP endpoints."""

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.today_session_config import (
    TODAY_EXTEND_BATCH,
    TODAY_SOFT_GOAL,
    TODAY_STREAK_MIN,
)
from app.db.session import get_db
from app.helpers.datetime_utils import utc_naive_now
from app.models.user import User
from app.repository.session_item_repository import SessionItemRepository
from app.schemas.session import (
    SessionCardResponse,
    SessionExtendResponse,
    SessionStartResponse,
    SessionSummaryResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.schemas.word import WordResponse
from app.services.sessions.session_service import SessionCommandService, SessionQueryService


router = APIRouter()


def _word_responses_with_sources(words: list, source_by_word_id: dict[int, str | None]) -> list[WordResponse]:
    responses: list[WordResponse] = []
    for word in words:
        payload = WordResponse.model_validate(word).model_dump()
        payload["session_source"] = source_by_word_id.get(word.id)
        responses.append(WordResponse(**payload))
    return responses


async def _source_map_for_session(db: AsyncSession, session_id: int) -> dict[int, str | None]:
    items = await SessionItemRepository(db).list_for_session(session_id)
    return {item.word_id: item.source for item in items}


def _build_session_message(words: list, skipped_count: int) -> str | None:
    if words:
        return None
    if skipped_count:
        return "Could not build session — try again"
    return "Add at least one learning word"


async def _build_start_response(
    db: AsyncSession,
    user_id: int,
    session,
    words: list,
    skipped_count: int = 0,
) -> SessionStartResponse:
    query = SessionQueryService(db, user_id)
    done, total = await query.get_session_progress(session.id)
    meta = SessionQueryService.session_progress_meta(session, done, total)
    sources = await _source_map_for_session(db, session.id)
    breakdown = dict(Counter(source for source in sources.values() if source))
    return SessionStartResponse(
        session_id=session.id,
        session_date=session.session_date,
        goal=session.goal,
        words=_word_responses_with_sources(words, sources),
        sources_breakdown=breakdown,
        words_ready=bool(words),
        skipped_count=skipped_count,
        message=_build_session_message(words, skipped_count),
        **meta,
    )


@router.post("/today/start", response_model=SessionStartResponse)
async def start_today_session_endpoint(
    daily_goal: int = TODAY_SOFT_GOAL,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionStartResponse:
    session, words, skipped_count = await SessionCommandService(
        db,
        current_user.id,
    ).start_today_session(daily_goal)
    return await _build_start_response(
        db,
        current_user.id,
        session,
        words,
        skipped_count=skipped_count,
    )


@router.get("/today", response_model=SessionStartResponse)
async def get_today_session_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionStartResponse:
    result = await SessionQueryService(db, current_user.id).get_today_session()
    if not result:
        return SessionStartResponse(
            session_id=0,
            session_date=utc_naive_now().date(),
            goal=0,
            words=[],
            recommended_goal=TODAY_SOFT_GOAL,
            streak_threshold=TODAY_STREAK_MIN,
            can_extend=False,
            done=0,
            total=0,
            soft_goal_met=False,
        )

    session, words = result
    return await _build_start_response(db, current_user.id, session, words)


@router.post("/{session_id}/extend", response_model=SessionExtendResponse)
async def extend_session_endpoint(
    session_id: int,
    count: int = TODAY_EXTEND_BATCH,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionExtendResponse:
    command = SessionCommandService(db, current_user.id)
    query = SessionQueryService(db, current_user.id)
    session, added_words, added_count = await command.extend_session(session_id, count)
    done, total = await query.get_session_progress(session.id)
    meta = SessionQueryService.session_progress_meta(session, done, total)
    sources = await _source_map_for_session(db, session.id)
    return SessionExtendResponse(
        session_id=session.id,
        added=added_count,
        total=total,
        done=done,
        goal=session.goal,
        words=_word_responses_with_sources(added_words, sources),
        **meta,
    )


@router.get("/{session_id}/next", response_model=SessionCardResponse)
async def get_next_card_endpoint(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionCardResponse:
    nxt = await SessionQueryService(db, current_user.id).get_next_session_card(session_id)
    if not nxt:
        raise HTTPException(status_code=404, detail="No next card")

    item, word, total = nxt
    return SessionCardResponse(
        session_id=session_id,
        item_id=item.id,
        position=item.position,
        total=total,
        word=WordResponse.model_validate(word),
    )


@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer_endpoint(
    session_id: int,
    payload: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmitAnswerResponse:
    command_service = SessionCommandService(db, current_user.id)
    query_service = SessionQueryService(db, current_user.id)

    word = await command_service.submit_session_answer(
        session_id=session_id,
        word_id=payload.word_id,
        is_correct=payload.is_correct,
        grade=payload.grade,
    )

    session = await query_service.session_access.get_session_or_404(session_id)
    done, total = await query_service.get_session_progress(session_id)
    meta = SessionQueryService.session_progress_meta(session, done, total)

    return SubmitAnswerResponse(
        word=WordResponse.model_validate(word),
        is_correct=payload.is_correct,
        next_review_at=word.next_review_at.isoformat() if word.next_review_at else None,
        done=done,
        total=total,
        recommended_goal=meta["recommended_goal"],
        streak_threshold=meta["streak_threshold"],
        soft_goal_met=meta["soft_goal_met"],
    )


@router.post("/{session_id}/finish", response_model=SessionSummaryResponse)
async def finish_session_endpoint(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionSummaryResponse:
    summary = await SessionCommandService(db, current_user.id).finish_session(session_id)
    return SessionSummaryResponse(**summary)


@router.get("/profile/stats")
async def get_profile_stats_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Быстрый эндпоинт для Home/Profile.
    Можно позже перенести в /users/me/stats — сейчас так проще.
    """
    return await SessionQueryService(db, current_user.id).get_profile_stats()
