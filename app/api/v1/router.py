from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    words,
    sessions,
    purchases,
    training,
    learning_sessions,
    stats,
    battles,
    friends,
    languages,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(languages.router, prefix="/languages", tags=["languages"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(words.router, prefix="/words", tags=["words"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(learning_sessions.router, prefix="/learning-sessions", tags=["learning-sessions"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(battles.router, prefix="/battles", tags=["battles"])
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])


