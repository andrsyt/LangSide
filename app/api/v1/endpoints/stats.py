from fastapi import APIRouter

from app.api.deps import UserStats
from app.schemas.stats import HomeStatsResponse

router = APIRouter()


@router.get("/home", response_model=HomeStatsResponse)
async def get_home_stats_endpoint(stats: UserStats) -> HomeStatsResponse:
    return await stats.get_home_stats()
