from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.battle import (
    MATCHMAKING_AI_SECONDS,
    enum_value,
    matchmaking_search_message,
    public_display_name,
)
from app.helpers.battle.matchmaking_rules import matchmaking_rating_window
from app.helpers.datetime_utils import elapsed_seconds_since, utc_naive_now
from app.models.battle_matchmaking import MatchmakingStatus
from app.repository.matchmaking_repository import MatchmakingRepository
from app.schemas.battle import (
    BattleModeRequest,
    MatchmakingJoinRequest,
    MatchmakingOpponentPreview,
    MatchmakingStatusResponse,
)
from app.services.battle.battle_service import BattleService
from app.services.users.user_service import UserQueryService


class MatchmakingService:
    """Queue management and PvP / AI battle pairing."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.tickets = MatchmakingRepository(db)
        self.users = UserQueryService(db)
        self.battles = BattleService(db, user_id)

    async def join(self, body: MatchmakingJoinRequest) -> MatchmakingStatusResponse:
        if body.mode == BattleModeRequest.voice:
            raise HTTPException(status_code=501, detail="Voice duels coming soon")

        battle_svc = self.battles
        await battle_svc.cleanup_stale_for_user()

        if body.mode == BattleModeRequest.ai:
            await self.tickets.cancel_searching_for_user(self.user_id)
            stats = await battle_svc.get_or_create_stats()
            ticket = await self.tickets.create_ticket(
                self.user_id,
                body.mode.value,
                stats.rating,
            )
            await self.db.commit()
            return await self.start_ai(ticket.id)

        stats = await battle_svc.get_or_create_stats()
        mode_value = body.mode.value
        await self.tickets.cancel_searching_for_user(self.user_id)

        opponent_ticket = await self.tickets.find_opponent_ticket(
            self.user_id,
            mode_value,
            stats.rating,
            rating_window=matchmaking_rating_window(body.mode),
        )

        if opponent_ticket is not None:
            return await self._complete_match(
                await self._create_matched_ticket(
                    mode_value,
                    stats.rating,
                    opponent_ticket,
                    body.mode,
                ),
                opponent_ticket,
                body.mode,
                battle_svc,
            )

        ticket = await self.tickets.create_ticket(self.user_id, mode_value, stats.rating)
        await self.db.commit()
        return await self.get_status(ticket.id)

    async def get_status(self, ticket_id: int) -> MatchmakingStatusResponse:
        ticket = await self.tickets.get_ticket(ticket_id, self.user_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Matchmaking ticket not found")

        elapsed = elapsed_seconds_since(ticket.created_at)
        battle_svc = self.battles

        if ticket.status == MatchmakingStatus.MATCHED and ticket.battle_id:
            return await self._matched_status_response(ticket, elapsed, battle_svc)

        if ticket.status == MatchmakingStatus.SEARCHING:
            opponent_ticket = await self.tickets.find_opponent_ticket(
                self.user_id,
                ticket.mode,
                ticket.rating,
                rating_window=matchmaking_rating_window(ticket.mode),
            )
            if opponent_ticket is not None:
                return await self._complete_match(
                    ticket,
                    opponent_ticket,
                    BattleModeRequest(ticket.mode),
                )

            return MatchmakingStatusResponse(
                ticket_id=ticket.id,
                status="searching",
                elapsed_seconds=elapsed,
                can_play_ai=elapsed >= MATCHMAKING_AI_SECONDS,
                search_message=matchmaking_search_message(elapsed),
            )

        if ticket.status == MatchmakingStatus.AI_STARTED:
            battle_state = None
            if ticket.battle_id:
                battle_state = await battle_svc.get_battle_state(ticket.battle_id)
            return MatchmakingStatusResponse(
                ticket_id=ticket.id,
                status="ai_ready",
                elapsed_seconds=elapsed,
                can_play_ai=True,
                opponent=self._ai_opponent_preview(ticket.rating),
                battle=battle_state,
            )

        return MatchmakingStatusResponse(
            ticket_id=ticket.id,
            status="cancelled",
            elapsed_seconds=elapsed,
            can_play_ai=False,
        )

    async def start_ai(self, ticket_id: int) -> MatchmakingStatusResponse:
        ticket = await self.tickets.get_ticket(ticket_id, self.user_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if ticket.status != MatchmakingStatus.SEARCHING:
            raise HTTPException(status_code=400, detail="Not searching")

        ticket.status = MatchmakingStatus.AI_STARTED
        battle_state = await self.battles.start_ai_battle(BattleModeRequest.ai)
        ticket.battle_id = battle_state.battle_id
        await self.db.commit()
        return MatchmakingStatusResponse(
            ticket_id=ticket.id,
            status="ai_ready",
            elapsed_seconds=elapsed_seconds_since(ticket.created_at),
            can_play_ai=True,
            opponent=self._ai_opponent_preview(ticket.rating),
            battle=battle_state,
        )

    async def cancel(self, ticket_id: int) -> None:
        ticket = await self.tickets.get_ticket(ticket_id, self.user_id)
        if ticket and ticket.status == MatchmakingStatus.SEARCHING:
            ticket.status = MatchmakingStatus.CANCELLED
            await self.db.commit()

    async def _create_matched_ticket(
        self,
        mode_value: str,
        rating: int,
        opponent_ticket,
        mode: BattleModeRequest,
    ):
        battle_state = await self.battles.create_pvp_battle(
            self.user_id,
            opponent_ticket.user_id,
            mode,
        )
        now = utc_naive_now()
        my_ticket = await self.tickets.create_ticket(self.user_id, mode_value, rating)
        my_ticket.status = MatchmakingStatus.MATCHED
        my_ticket.opponent_user_id = opponent_ticket.user_id
        my_ticket.battle_id = battle_state.battle_id
        my_ticket.matched_at = now

        opponent_ticket.status = MatchmakingStatus.MATCHED
        opponent_ticket.opponent_user_id = self.user_id
        opponent_ticket.battle_id = battle_state.battle_id
        opponent_ticket.matched_at = now
        return my_ticket

    async def _complete_match(
        self,
        my_ticket,
        opponent_ticket,
        mode: BattleModeRequest,
        battle_svc: BattleService | None = None,
    ) -> MatchmakingStatusResponse:
        battle_svc = battle_svc or self.battles
        if my_ticket.battle_id is None:
            battle_state = await battle_svc.create_pvp_battle(
                self.user_id,
                opponent_ticket.user_id,
                mode,
            )
            now = utc_naive_now()
            my_ticket.status = MatchmakingStatus.MATCHED
            my_ticket.opponent_user_id = opponent_ticket.user_id
            my_ticket.battle_id = battle_state.battle_id
            my_ticket.matched_at = now
            opponent_ticket.status = MatchmakingStatus.MATCHED
            opponent_ticket.opponent_user_id = self.user_id
            opponent_ticket.battle_id = battle_state.battle_id
            opponent_ticket.matched_at = now
        else:
            battle_state = await battle_svc.get_battle_state(my_ticket.battle_id)

        await self.db.commit()
        opp_user = await self.users.get_user_by_id(opponent_ticket.user_id)
        opp_stats = await battle_svc.battles.get_stats(opponent_ticket.user_id)
        return MatchmakingStatusResponse(
            ticket_id=my_ticket.id,
            status="matched",
            elapsed_seconds=0,
            can_play_ai=False,
            opponent=MatchmakingOpponentPreview(
                user_id=opponent_ticket.user_id,
                username=public_display_name(opp_user),
                rating=opp_stats.rating if opp_stats else 1000,
                league=enum_value(opp_stats.league) if opp_stats else "bronze",
                is_bot=False,
            ),
            battle=battle_state,
        )

    async def _matched_status_response(self, ticket, elapsed: float, battle_svc: BattleService):
        opponent = None
        if ticket.opponent_user_id:
            opp_user = await self.users.get_user_by_id(ticket.opponent_user_id)
            opp_stats = await battle_svc.battles.get_stats(ticket.opponent_user_id)
            opponent = MatchmakingOpponentPreview(
                user_id=ticket.opponent_user_id,
                username=public_display_name(opp_user),
                rating=opp_stats.rating if opp_stats else 1000,
                league=enum_value(opp_stats.league) if opp_stats else "bronze",
                is_bot=False,
            )
        battle_state = await battle_svc.get_battle_state(ticket.battle_id)
        return MatchmakingStatusResponse(
            ticket_id=ticket.id,
            status="matched",
            elapsed_seconds=elapsed,
            can_play_ai=False,
            opponent=opponent,
            battle=battle_state,
        )

    @staticmethod
    def _ai_opponent_preview(rating: int) -> MatchmakingOpponentPreview:
        return MatchmakingOpponentPreview(
            user_id=0,
            username="AI Coach",
            rating=rating,
            league="ai",
            is_bot=True,
        )
