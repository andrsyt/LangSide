from fastapi import APIRouter, Query

from app.api.deps import Battles, CurrentUser, DbSession, Matchmaking
from app.repository.friendship_repository import FriendshipRepository
from app.schemas.battle import (
    ActiveBattleResponse,
    BattleAnswerResponse,
    BattleProfileResponse,
    BattleRoundAnswerRequest,
    BattleStateResponse,
    LeaderboardResponse,
    MatchmakingJoinRequest,
    MatchmakingStatusResponse,
    QuickBattleStartRequest,
)

router = APIRouter()


@router.get("/active", response_model=ActiveBattleResponse)
async def get_active_battle(battles: Battles) -> ActiveBattleResponse:
    state = await battles.get_active_battle_state()
    if state is None:
        return ActiveBattleResponse(active=False, state=None)
    return ActiveBattleResponse(active=True, state=state)


@router.get("/me", response_model=BattleProfileResponse)
async def battle_profile(battles: Battles) -> BattleProfileResponse:
    return await battles.get_profile()


@router.post("/matchmaking/join", response_model=MatchmakingStatusResponse)
async def matchmaking_join(
    body: MatchmakingJoinRequest,
    matchmaking: Matchmaking,
) -> MatchmakingStatusResponse:
    return await matchmaking.join(body)


@router.get("/matchmaking/{ticket_id}", response_model=MatchmakingStatusResponse)
async def matchmaking_status(
    ticket_id: int,
    matchmaking: Matchmaking,
) -> MatchmakingStatusResponse:
    return await matchmaking.get_status(ticket_id)


@router.post("/matchmaking/{ticket_id}/ai", response_model=MatchmakingStatusResponse)
async def matchmaking_start_ai(
    ticket_id: int,
    matchmaking: Matchmaking,
) -> MatchmakingStatusResponse:
    return await matchmaking.start_ai(ticket_id)


@router.delete("/matchmaking/{ticket_id}")
async def matchmaking_cancel(
    ticket_id: int,
    matchmaking: Matchmaking,
) -> dict:
    await matchmaking.cancel(ticket_id)
    return {"ok": True}


@router.get("/{battle_id}/state", response_model=BattleStateResponse)
async def get_battle_state(
    battle_id: int,
    battles: Battles,
) -> BattleStateResponse:
    return await battles.get_battle_state(battle_id)


@router.post("/quick-start", response_model=BattleStateResponse)
async def quick_start_battle(
    body: QuickBattleStartRequest,
    battles: Battles,
) -> BattleStateResponse:
    return await battles.quick_start(body.mode)


@router.post(
    "/{battle_id}/rounds/{round_index}/answer",
    response_model=BattleAnswerResponse,
)
async def submit_battle_answer(
    battle_id: int,
    round_index: int,
    body: BattleRoundAnswerRequest,
    battles: Battles,
) -> BattleAnswerResponse:
    round_result, state, finish = await battles.submit_round_answer(
        battle_id,
        round_index,
        body,
    )
    return BattleAnswerResponse(round=round_result, state=state, finish=finish)


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def battle_leaderboard(
    battles: Battles,
    current_user: CurrentUser,
    db: DbSession,
    scope: str = Query("global", pattern="^(global|friends|weekly|streak)$"),
) -> LeaderboardResponse:
    friend_ids = None
    if scope == "friends":
        friend_ids = await FriendshipRepository(db).friend_user_ids(current_user.id)
    order_weekly = scope == "weekly"
    streak = scope == "streak"
    if streak:
        return await battles.leaderboard_streak(friend_ids=friend_ids)

    return await battles.leaderboard(
        scope="weekly" if order_weekly else ("friends" if scope == "friends" else "global"),
        friend_ids=friend_ids,
    )
