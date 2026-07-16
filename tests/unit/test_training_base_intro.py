import pytest
from unittest.mock import AsyncMock

from app.core.exceptions.http import UnprocessableEntityError
from app.models.word import Word
from app.services.training.base import TrainingBaseService


@pytest.mark.asyncio
@pytest.mark.parametrize("explanation", [None, "", " "])
async def test_build_word_intro_info_raises_when_explanation_empty(
    explanation: str | None,
) -> None:
    db = AsyncMock()
    service = TrainingBaseService(db, user_id=1)
    service.ensure_word_analyzed = AsyncMock()
    service.get_word = AsyncMock(
        return_value=Word(id=1, user_id=1, word_text="run", explanation=explanation)
    )

    with pytest.raises(UnprocessableEntityError) as exc:
        await service.build_word_intro_info(1)

    assert exc.value.status_code == 422
    assert exc.value.message == "Word is still being prepared"
