from __future__ import annotations

import random
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.http import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    NotImplementedAPIError,
)
from app.core.language_codes import default_language_code, resolve_canonical_language_code
from app.helpers.battle import (
    AI_OPPONENT_NAME,
    BATTLE_STALE_HOURS,
    BattleFinishHelper,
    BattleLeaderboardHelper,
    BattleRoundAnswerHelper,
    BattleRoundPoolBuilder,
    BattleSetupHelper,
    BattleStateMapper,
    BattleTimeoutHelper,
    MATCHMAKING_SEARCH_MAX_AGE_SECONDS,
    enum_value,
    public_display_name,
    season_week,
)
from app.helpers.datetime_utils import utc_naive_now
from app.repository.matchmaking_repository import MatchmakingRepository
from app.models.battle import (
    Battle,
    BattleMode,
    BattleParticipant,
    BattleRound,
    BattleStatus,
    UserBattleStats,
)
from app.repository.battle_repository import BattleRepository
from app.schemas.battle import (
    BattleFinishResponse,
    BattleModeRequest,
    BattleProfileResponse,
    BattleRoundAnswerRequest,
    BattleRoundResultView,
    BattleStateResponse,
    LeaderboardResponse,
)
from app.services.users.user_service import UserQueryService


class BattleService:
    """Battle use cases: profile, match play, leaderboards."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.battles = BattleRepository(db)
        self.users = UserQueryService(db)
        self._rounds = BattleRoundPoolBuilder(db)
        self.matchmaking = MatchmakingRepository(db)

    async def ensure_can_start_battle(self, user_id: int | None = None) -> None:
        uid = user_id if user_id is not None else self.user_id
        active = await self.battles.get_active_battle_for_user(uid)
        if active is not None:
            raise ConflictError(
                f"Active battle {active.id} is still in progress",
                error_code="ACTIVE_BATTLE_EXISTS",
            )

    async def cleanup_stale_for_user(self) -> None:
        cutoff_battle = utc_naive_now() - timedelta(hours=BATTLE_STALE_HOURS)
        cutoff_ticket = utc_naive_now() - timedelta(
            seconds=MATCHMAKING_SEARCH_MAX_AGE_SECONDS
        )
        await self.battles.cancel_stale_active_battles(
            self.user_id,
            older_than=cutoff_battle,
        )
        await self.matchmaking.expire_stale_searching_tickets(
            older_than=cutoff_ticket
        )

    async def get_active_battle_state(self) -> BattleStateResponse | None:
        await self.cleanup_stale_for_user()
        battle = await self.battles.get_active_battle_for_user(self.user_id)
        if battle is None:
            return None
        state = await self._sync_and_state(battle)
        if state.status != BattleStatus.ACTIVE.value:
            return None
        return state

    async def get_or_create_stats(self) -> UserBattleStats:
        stats = await self.battles.get_stats(self.user_id)
        if stats is None:
            stats = await self.battles.create_stats(self.user_id)
        week = season_week()
        if stats.season_week != week:
            stats.season_week = week
            stats.weekly_xp = 0
        return stats

    async def get_profile(self) -> BattleProfileResponse:
        stats = await self.get_or_create_stats()
        await self.db.commit()
        total = stats.wins + stats.losses + stats.draws
        win_rate = round(100 * stats.wins / total, 1) if total > 0 else 0.0
        rank = (await self.battles.count_rank_above_rating(stats.rating)) + 1
        return BattleProfileResponse(
            rating=stats.rating,
            xp=stats.xp,
            wins=stats.wins,
            losses=stats.losses,
            win_rate=win_rate,
            win_streak=stats.win_streak,
            best_win_streak=stats.best_win_streak,
            league=enum_value(stats.league),
            battles_played=stats.battles_played,
            weekly_xp=stats.weekly_xp,
            global_rank=rank,
        )

    async def quick_start(self, mode: BattleModeRequest) -> BattleStateResponse:
        """Legacy instant start — prefer matchmaking + start_ai_battle."""
        await self.cleanup_stale_for_user()
        if mode == BattleModeRequest.ai:
            return await self.start_ai_battle(mode)
        return await self.start_ai_battle(
            BattleModeRequest.ai if mode == BattleModeRequest.quick else mode
        )

    async def start_ai_battle(self, mode: BattleModeRequest) -> BattleStateResponse:
        await self.ensure_can_start_battle()
        if mode == BattleModeRequest.voice:
            raise NotImplementedAPIError(
                "Voice duels coming soon",
                error_code="VOICE_DUELS_NOT_IMPLEMENTED",
            )

        stats = await self.get_or_create_stats()
        user = await self.users.get_user_by_id(self.user_id)
        display = public_display_name(user, fallback="You")
        battle_mode = BattleMode.AI if mode == BattleModeRequest.ai else BattleMode(mode.value)
        is_ranked = mode == BattleModeRequest.ranked
        bot_rating = max(800, stats.rating + random.randint(-80, 80))

        round_count = BattleRoundPoolBuilder.pick_round_count()
        battle = await BattleSetupHelper.create_shell(self.battles, battle_mode, is_ranked, round_count)
        await self.battles.add_participant(
            BattleParticipant(
                battle_id=battle.id,
                user_id=self.user_id,
                slot=0,
                display_name=display[:64],
                is_bot=False,
                rating_before=stats.rating,
                score=0,
            )
        )
        await self.battles.add_participant(
            BattleParticipant(
                battle_id=battle.id,
                user_id=None,
                slot=1,
                display_name=AI_OPPONENT_NAME,
                is_bot=True,
                rating_before=bot_rating,
                score=0,
            )
        )
        rounds_data = await self._rounds.build_rounds(round_count)
        await BattleSetupHelper.attach_rounds(self.battles, battle.id, rounds_data)
        BattleTimeoutHelper.start_next_round_deadline(battle)
        await self.db.commit()
        battle = await self.battles.get_battle_for_user(battle.id, self.user_id)
        return await self._battle_state(battle)

    async def create_pvp_battle(
        self,
        user_a_id: int,
        user_b_id: int,
        mode: BattleModeRequest,
    ) -> BattleStateResponse:
        await self.ensure_can_start_battle(user_a_id)
        await self.ensure_can_start_battle(user_b_id)
        low_id, high_id = sorted((user_a_id, user_b_id))
        stats_a = await self._stats_for_user(low_id)
        stats_b = await self._stats_for_user(high_id)
        user_low = await self.users.get_user_by_id(low_id)
        user_high = await self.users.get_user_by_id(high_id)

        battle_mode = BattleMode(mode.value)
        is_ranked = mode == BattleModeRequest.ranked
        round_count = BattleRoundPoolBuilder.pick_round_count()
        battle = await BattleSetupHelper.create_shell(self.battles, battle_mode, is_ranked, round_count)

        await self.battles.add_participant(
            BattleParticipant(
                battle_id=battle.id,
                user_id=low_id,
                slot=0,
                display_name=public_display_name(user_low),
                is_bot=False,
                rating_before=stats_a.rating,
                score=0,
            )
        )
        await self.battles.add_participant(
            BattleParticipant(
                battle_id=battle.id,
                user_id=high_id,
                slot=1,
                display_name=public_display_name(user_high),
                is_bot=False,
                rating_before=stats_b.rating,
                score=0,
            )
        )
        rounds_data = await self._rounds.build_rounds(round_count)
        await BattleSetupHelper.attach_rounds(self.battles, battle.id, rounds_data)
        BattleTimeoutHelper.start_next_round_deadline(battle)
        await self.db.commit()
        battle = await self.battles.get_battle_for_user(battle.id, self.user_id)
        return await self._battle_state(battle)

    async def get_battle_state(self, battle_id: int) -> BattleStateResponse:
        battle = await self.battles.get_battle_for_user(battle_id, self.user_id)
        if battle is None:
            raise NotFoundError("Battle not found", error_code="BATTLE_NOT_FOUND")
        return await self._sync_and_state(battle)

    async def _sync_and_state(
        self,
        battle: Battle,
        *,
        waiting_for_opponent: bool = False,
    ) -> BattleStateResponse:
        me, opponent = BattleStateMapper.participants_for_user(battle, self.user_id)
        stats = await self.get_or_create_stats()
        timeout_result = BattleTimeoutHelper.resolve(battle, me, opponent, stats)
        if timeout_result.changed or timeout_result.finished:
            await self.db.commit()
            battle = await self.battles.get_battle_for_user(battle.id, self.user_id)
            if battle is None:
                raise NotFoundError("Battle not found", error_code="BATTLE_NOT_FOUND")
            me, opponent = BattleStateMapper.participants_for_user(battle, self.user_id)

        if battle.status == BattleStatus.ACTIVE and not waiting_for_opponent:
            round_row = BattleTimeoutHelper.current_round(battle.rounds)
            if round_row is not None and BattleRoundAnswerHelper.slot_answered(
                round_row, me.slot
            ) and not BattleRoundAnswerHelper.slot_answered(round_row, opponent.slot):
                if not opponent.is_bot:
                    waiting_for_opponent = True

        return await self._battle_state(
            battle,
            waiting_for_opponent=waiting_for_opponent,
        )

    async def submit_round_answer(
        self,
        battle_id: int,
        round_index: int,
        body: BattleRoundAnswerRequest,
    ) -> tuple[BattleRoundResultView, BattleStateResponse | None, BattleFinishResponse | None]:
        battle = await self.battles.get_battle_for_user(battle_id, self.user_id)
        if battle is None:
            raise NotFoundError("Battle not found", error_code="BATTLE_NOT_FOUND")
        if battle.status != BattleStatus.ACTIVE:
            raise BadRequestError("Battle already finished", error_code="BATTLE_FINISHED")

        me, opponent = BattleStateMapper.participants_for_user(battle, self.user_id)
        stats = await self.get_or_create_stats()
        timeout_result = BattleTimeoutHelper.resolve(battle, me, opponent, stats)
        if timeout_result.finished:
            await self.db.commit()
            battle = await self.battles.get_battle_for_user(battle_id, self.user_id)
            if battle is None:
                raise NotFoundError("Battle not found", error_code="BATTLE_NOT_FOUND")
            me, opponent = BattleStateMapper.participants_for_user(battle, self.user_id)
            round_row = next(
                (row for row in battle.rounds if row.round_index == round_index),
                None,
            )
            if round_row is None:
                raise NotFoundError("Round not found", error_code="ROUND_NOT_FOUND")
            return self._round_result_view(
                round_row, round_index, me, opponent, waiting=False
            ), None, timeout_result.finished

        round_row = next((row for row in battle.rounds if row.round_index == round_index), None)
        if round_row is None:
            raise NotFoundError("Round not found", error_code="ROUND_NOT_FOUND")

        my_slot = me.slot

        if BattleRoundAnswerHelper.slot_answered(round_row, my_slot):
            await self.db.commit()
            round_result = self._round_result_view(
                round_row,
                round_index,
                me,
                opponent,
                waiting=not opponent.is_bot
                and not BattleRoundAnswerHelper.slot_answered(round_row, opponent.slot),
            )
            if battle.status == BattleStatus.FINISHED:
                return round_result, None, None
            state = await self._sync_and_state(battle)
            return round_result, state, None

        my_correct = BattleRoundAnswerHelper.choice_is_correct(body.answer, round_row)
        BattleRoundAnswerHelper.write_slot_answer(
            round_row, my_slot, body.answer, my_correct, body.time_ms
        )

        waiting = False
        opponent_correct: bool | None = None

        if opponent.is_bot:
            opponent_correct = random.random() < BattleRoundAnswerHelper.bot_accuracy(battle.mode)
            bot_pick = BattleRoundAnswerHelper.bot_choice(round_row, opponent_correct)
            BattleRoundAnswerHelper.write_slot_answer(
                round_row,
                1 - my_slot,
                bot_pick,
                opponent_correct,
                BattleRoundAnswerHelper.bot_time_ms(),
            )
        elif not BattleRoundAnswerHelper.slot_answered(round_row, opponent.slot):
            waiting = True
        else:
            opponent_correct = BattleRoundAnswerHelper.slot_correct(round_row, opponent.slot)

        if not waiting:
            if my_correct:
                me.score += 1
            if opponent_correct:
                opponent.score += 1

        round_result = BattleRoundResultView(
            round_index=round_index,
            player_correct=my_correct,
            opponent_correct=opponent_correct,
            correct_answer=round_row.correct_answer,
            player_score=me.score,
            opponent_score=opponent.score,
            waiting_for_opponent=waiting,
        )

        finish: BattleFinishResponse | None = None
        state: BattleStateResponse | None = None

        if not waiting:
            if BattleRoundAnswerHelper.all_rounds_answered(battle.rounds):
                finish = BattleFinishHelper.apply(battle, me, opponent, stats)
            else:
                BattleTimeoutHelper.start_next_round_deadline(battle)
                state = await self._battle_state(battle)
        else:
            state = await self._battle_state(battle, waiting_for_opponent=True)

        await self.db.commit()
        return round_result, state, finish

    @staticmethod
    def _round_result_view(
        round_row: BattleRound,
        round_index: int,
        me: BattleParticipant,
        opponent: BattleParticipant,
        *,
        waiting: bool,
    ) -> BattleRoundResultView:
        my_slot = me.slot
        opponent_correct: bool | None = None
        if BattleRoundAnswerHelper.slot_answered(round_row, opponent.slot):
            opponent_correct = BattleRoundAnswerHelper.slot_correct(
                round_row, opponent.slot
            )
        return BattleRoundResultView(
            round_index=round_index,
            player_correct=bool(BattleRoundAnswerHelper.slot_correct(round_row, my_slot)),
            opponent_correct=opponent_correct,
            correct_answer=round_row.correct_answer,
            player_score=me.score,
            opponent_score=opponent.score,
            waiting_for_opponent=waiting,
        )

    async def leaderboard_streak(
        self,
        friend_ids: list[int] | None = None,
    ) -> LeaderboardResponse:
        rows = await self.battles.leaderboard(
            limit=100,
            user_ids=friend_ids,
            order_by_weekly=False,
        )
        rows = sorted(rows, key=lambda row: row[0].win_streak, reverse=True)[:50]
        entries = BattleLeaderboardHelper.build_entries(
            rows,
            current_user_id=self.user_id,
            xp_field="win_streak",
        )
        return BattleLeaderboardHelper.response(
            scope="streak",
            entries=entries,
            your_rank=BattleLeaderboardHelper.find_your_rank(entries),
        )

    async def leaderboard(
        self,
        scope: str = "global",
        friend_ids: list[int] | None = None,
    ) -> LeaderboardResponse:
        stats = await self.get_or_create_stats()
        order_weekly = scope == "weekly"
        user_ids = friend_ids if scope == "friends" else None
        rows = await self.battles.leaderboard(
            limit=50,
            user_ids=user_ids,
            order_by_weekly=order_weekly,
        )
        entries = BattleLeaderboardHelper.build_entries(
            rows,
            current_user_id=self.user_id,
            xp_field="weekly_xp" if order_weekly else "xp",
        )
        your_rank = BattleLeaderboardHelper.find_your_rank(entries)
        if your_rank is None and scope == "global":
            your_rank = (await self.battles.count_rank_above_rating(stats.rating)) + 1

        return BattleLeaderboardHelper.response(
            scope=scope,
            entries=entries,
            your_rank=your_rank,
            order_weekly=order_weekly,
        )

    async def _prompt_language(self) -> str:
        user = await self.users.get_user_by_id(self.user_id)
        if user is None or not user.preferred_language:
            return default_language_code()
        return resolve_canonical_language_code(user.preferred_language) or default_language_code()

    async def _battle_state(
        self,
        battle: Battle,
        *,
        waiting_for_opponent: bool = False,
    ) -> BattleStateResponse:
        return BattleStateMapper.to_state(
            battle,
            self.user_id,
            prompt_language=await self._prompt_language(),
            waiting_for_opponent=waiting_for_opponent,
        )

    async def _stats_for_user(self, user_id: int) -> UserBattleStats:
        stats = await self.battles.get_stats(user_id)
        if stats is None:
            stats = await self.battles.create_stats(user_id)
        return stats
