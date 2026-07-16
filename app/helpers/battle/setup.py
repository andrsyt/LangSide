"""Battle shell and round attachment helpers."""

from __future__ import annotations

import json

from app.helpers.battle.constants import ROUND_SECONDS
from app.helpers.battle.league import season_week
from app.models.battle import Battle, BattleMode, BattleRound, BattleStatus
from app.repository.battle_repository import BattleRepository


class BattleSetupHelper:
    """Creates battle rows and attaches generated rounds (no commit)."""

    @staticmethod
    async def create_shell(
        battles: BattleRepository,
        mode: BattleMode,
        is_ranked: bool,
        round_count: int,
    ) -> Battle:
        battle = Battle(
            mode=mode,
            status=BattleStatus.ACTIVE,
            is_ranked=is_ranked,
            round_count=round_count,
            round_seconds=ROUND_SECONDS,
            season_week=season_week(),
        )
        return await battles.create_battle(battle)

    @staticmethod
    async def attach_rounds(
        battles: BattleRepository,
        battle_id: int,
        prompts: list[dict],
    ) -> None:
        rounds = [
            BattleRound(
                battle_id=battle_id,
                round_index=index,
                prompt_text=prompt["prompt"],
                correct_answer=prompt["answer"],
                choices_json=json.dumps(prompt["choices"]),
            )
            for index, prompt in enumerate(prompts)
        ]
        await battles.add_rounds(rounds)
