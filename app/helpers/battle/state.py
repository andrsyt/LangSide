from __future__ import annotations

from app.core.language_codes import default_language_code
from app.helpers.battle.constants import DEFAULT_RATING
from app.helpers.battle.league import enum_value
from app.helpers.battle.prompts import battle_prompt_for_word
from app.helpers.battle.round_answer import BattleRoundAnswerHelper
from app.models.battle import Battle, BattleMode, BattleParticipant
from app.schemas.battle import (
    BattleOpponentView,
    BattleRoundView,
    BattleStateResponse,
)


class BattleStateMapper:
    """Maps ORM battle entities to API state responses."""

    @staticmethod
    def participants_for_user(
        battle: Battle,
        user_id: int,
    ) -> tuple[BattleParticipant, BattleParticipant]:
        me = next(participant for participant in battle.participants if participant.user_id == user_id)
        opponent = next(participant for participant in battle.participants if participant.id != me.id)
        return me, opponent

    @classmethod
    def to_state(
        cls,
        battle: Battle,
        user_id: int,
        *,
        prompt_language: str | None = None,
        waiting_for_opponent: bool = False,
    ) -> BattleStateResponse:
        language = prompt_language or default_language_code()
        me, opponent = cls.participants_for_user(battle, user_id)
        my_slot = me.slot
        rounds_sorted = sorted(battle.rounds, key=lambda row: row.round_index)

        current_idx = next(
            (
                row.round_index
                for row in rounds_sorted
                if not BattleRoundAnswerHelper.slot_answered(row, my_slot)
            ),
            battle.round_count,
        )

        round_views: list[BattleRoundView] = []
        for row in rounds_sorted:
            my_answered = BattleRoundAnswerHelper.slot_answered(row, my_slot)
            opponent_answered = BattleRoundAnswerHelper.slot_answered(row, opponent.slot)
            prompt = battle_prompt_for_word(row.correct_answer, language)
            round_views.append(
                BattleRoundView(
                    round_index=row.round_index,
                    prompt_text=prompt,
                    choices=BattleRoundAnswerHelper.parse_choices(row)
                    if not my_answered and row.round_index == current_idx
                    else [],
                    answered=my_answered,
                    player_correct=BattleRoundAnswerHelper.slot_correct(row, my_slot)
                    if my_answered
                    else None,
                    opponent_correct=BattleRoundAnswerHelper.slot_correct(row, opponent.slot)
                    if opponent_answered
                    else None,
                )
            )

        current_round = round_views[current_idx] if current_idx < len(round_views) else None

        return BattleStateResponse(
            battle_id=battle.id,
            mode=enum_value(battle.mode),
            status=enum_value(battle.status),
            is_ranked=battle.is_ranked,
            round_count=battle.round_count,
            round_seconds=battle.round_seconds,
            current_round_index=current_idx,
            you=BattleOpponentView(
                display_name=me.display_name,
                is_bot=False,
                rating=me.rating_before or DEFAULT_RATING,
                score=me.score,
            ),
            opponent=BattleOpponentView(
                display_name=opponent.display_name,
                is_bot=opponent.is_bot,
                rating=opponent.rating_before or DEFAULT_RATING,
                score=opponent.score,
            ),
            current_round=current_round,
            rounds=round_views,
            waiting_for_opponent=waiting_for_opponent,
            is_ai_battle=opponent.is_bot and battle.mode == BattleMode.AI,
        )
