"""Run async service code from sync Celery workers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Run one async coroutine (new event loop per task invocation)."""
    return asyncio.run(coro)
