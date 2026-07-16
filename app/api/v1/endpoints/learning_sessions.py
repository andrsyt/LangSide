from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import LearningSessionCommands, LearningSessionQueries
from app.schemas.learning_session import (
    LearningSessionCompleteItemRequest,
    LearningSessionCompleteItemResponse,
    LearningSessionResponse,
    LearningSessionStartRequest,
    LearningSessionSummaryResponse,
)

router = APIRouter()


@router.post("/start", response_model=LearningSessionResponse)
async def start_learning_session_endpoint(
    body: LearningSessionStartRequest,
    learning_commands: LearningSessionCommands,
) -> LearningSessionResponse:
    return await learning_commands.start_learning_session(
        goal=body.goal,
        semantic_anchor_target=body.semantic_anchor_target,
        double_recall_target=body.double_recall_target,
        anti_confusion_target=body.anti_confusion_target,
        association_recall_target=body.association_recall_target,
    )


@router.get("/current", response_model=LearningSessionResponse)
async def get_current_learning_session_endpoint(
    learning_queries: LearningSessionQueries,
) -> LearningSessionResponse:
    learning_session = await learning_queries.get_current_learning_session()
    if learning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active learning session",
        )
    return learning_session


@router.get("/{session_id}", response_model=LearningSessionResponse)
async def get_learning_session_endpoint(
    session_id: int,
    learning_queries: LearningSessionQueries,
) -> LearningSessionResponse:
    return await learning_queries.get_learning_session(session_id)


@router.post(
    "/{session_id}/items/{item_id}/complete",
    response_model=LearningSessionCompleteItemResponse,
)
async def complete_learning_item_endpoint(
    session_id: int,
    item_id: int,
    body: LearningSessionCompleteItemRequest,
    learning_commands: LearningSessionCommands,
) -> LearningSessionCompleteItemResponse:
    item, word, remaining = await learning_commands.complete_learning_session_item(
        session_id=session_id,
        item_id=item_id,
        payload=body,
    )
    return LearningSessionCompleteItemResponse(
        item_id=item.id,
        is_done=item.is_done,
        is_correct=item.is_correct,
        next_review_at=word.next_review_at,
        remaining=remaining,
    )


@router.post("/{session_id}/finish", response_model=LearningSessionSummaryResponse)
async def finish_learning_session_endpoint(
    session_id: int,
    learning_commands: LearningSessionCommands,
) -> LearningSessionSummaryResponse:
    summary = await learning_commands.finish_learning_session(session_id)
    return LearningSessionSummaryResponse(**summary)
