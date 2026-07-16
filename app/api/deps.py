"""FastAPI dependency providers for DB, auth, and application services.

Prefer these in endpoints instead of constructing services inline:
``WordQueryService(db, current_user.id)``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.helpers.word_helpers import UserLanguageResolver
from app.models.user import User
from app.services.battle.battle_service import BattleService
from app.services.battle.matchmaking_service import MatchmakingService
from app.services.billing.billing_service import BillingService
from app.services.billing.purchase_service import SubscriptionService
from app.services.sessions.learning_session_service import (
    LearningSessionCommandService,
    LearningSessionQueryService,
)
from app.services.sessions.repeat_service import RepeatService
from app.services.sessions.session_service import (
    SessionCommandService,
    SessionQueryService,
)
from app.services.sessions.user_stats_service import UserStatsService
from app.services.training.facade import TrainingService
from app.services.users.friend_service import FriendService
from app.services.users.refresh_token_service import RefreshTokenService
from app.services.users.user_identity_service import UserIdentityService
from app.services.users.user_service import (
    UserCommandService,
    UserQueryService,
    UserRegistrationService,
)
from app.services.words.ai_service import AIAnalysisService
from app.services.words.word_service import (
    WordAIAnalysisService,
    WordCommandService,
    WordQueryService,
)

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_word_query_service(
    db: DbSession,
    current_user: CurrentUser,
) -> WordQueryService:
    return WordQueryService(db, current_user.id)


def get_word_command_service(
    db: DbSession,
    current_user: CurrentUser,
) -> WordCommandService:
    return WordCommandService(db, current_user.id)


def get_word_ai_analysis_service(
    db: DbSession,
    current_user: CurrentUser,
) -> WordAIAnalysisService:
    return WordAIAnalysisService(db, current_user.id)


def get_repeat_service(
    db: DbSession,
    current_user: CurrentUser,
) -> RepeatService:
    return RepeatService(db, current_user.id)


def get_billing_service(
    db: DbSession,
    current_user: CurrentUser,
) -> BillingService:
    return BillingService(db, current_user.id)


def get_ai_analysis_service(db: DbSession) -> AIAnalysisService:
    return AIAnalysisService(db)


def get_user_language_resolver(
    db: DbSession,
    current_user: CurrentUser,
) -> UserLanguageResolver:
    return UserLanguageResolver(db, current_user.id)


def get_session_query_service(
    db: DbSession,
    current_user: CurrentUser,
) -> SessionQueryService:
    return SessionQueryService(db, current_user.id)


def get_session_command_service(
    db: DbSession,
    current_user: CurrentUser,
) -> SessionCommandService:
    return SessionCommandService(db, current_user.id)


def get_training_service(
    db: DbSession,
    current_user: CurrentUser,
) -> TrainingService:
    return TrainingService(db, current_user.id)


def get_learning_session_query_service(
    db: DbSession,
    current_user: CurrentUser,
) -> LearningSessionQueryService:
    return LearningSessionQueryService(db, current_user.id)


def get_learning_session_command_service(
    db: DbSession,
    current_user: CurrentUser,
) -> LearningSessionCommandService:
    return LearningSessionCommandService(db, current_user.id)


def get_friend_service(
    db: DbSession,
    current_user: CurrentUser,
) -> FriendService:
    return FriendService(db, current_user.id)


def get_user_command_service(db: DbSession) -> UserCommandService:
    return UserCommandService(db)


def get_user_query_service(db: DbSession) -> UserQueryService:
    return UserQueryService(db)


def get_user_registration_service(db: DbSession) -> UserRegistrationService:
    return UserRegistrationService(db)


def get_user_identity_service(db: DbSession) -> UserIdentityService:
    return UserIdentityService(db)


def get_refresh_token_service(db: DbSession) -> RefreshTokenService:
    return RefreshTokenService(db)


def get_battle_service(
    db: DbSession,
    current_user: CurrentUser,
) -> BattleService:
    return BattleService(db, current_user.id)


def get_matchmaking_service(
    db: DbSession,
    current_user: CurrentUser,
) -> MatchmakingService:
    return MatchmakingService(db, current_user.id)


def get_user_stats_service(
    db: DbSession,
    current_user: CurrentUser,
) -> UserStatsService:
    return UserStatsService(db, current_user.id)


def get_subscription_service(
    db: DbSession,
    current_user: CurrentUser,
) -> SubscriptionService:
    return SubscriptionService(db, current_user.id)


WordQueries = Annotated[WordQueryService, Depends(get_word_query_service)]
WordCommands = Annotated[WordCommandService, Depends(get_word_command_service)]
WordAI = Annotated[WordAIAnalysisService, Depends(get_word_ai_analysis_service)]
Repeats = Annotated[RepeatService, Depends(get_repeat_service)]
Billing = Annotated[BillingService, Depends(get_billing_service)]
AIAnalysis = Annotated[AIAnalysisService, Depends(get_ai_analysis_service)]
LanguageResolver = Annotated[UserLanguageResolver, Depends(get_user_language_resolver)]
SessionQueries = Annotated[SessionQueryService, Depends(get_session_query_service)]
SessionCommands = Annotated[SessionCommandService, Depends(get_session_command_service)]
Training = Annotated[TrainingService, Depends(get_training_service)]
LearningSessionQueries = Annotated[
    LearningSessionQueryService,
    Depends(get_learning_session_query_service),
]
LearningSessionCommands = Annotated[
    LearningSessionCommandService,
    Depends(get_learning_session_command_service),
]
Friends = Annotated[FriendService, Depends(get_friend_service)]
UserCommands = Annotated[UserCommandService, Depends(get_user_command_service)]
UserQueries = Annotated[UserQueryService, Depends(get_user_query_service)]
UserRegistration = Annotated[
    UserRegistrationService,
    Depends(get_user_registration_service),
]
UserIdentity = Annotated[UserIdentityService, Depends(get_user_identity_service)]
RefreshTokens = Annotated[RefreshTokenService, Depends(get_refresh_token_service)]
Battles = Annotated[BattleService, Depends(get_battle_service)]
Matchmaking = Annotated[MatchmakingService, Depends(get_matchmaking_service)]
UserStats = Annotated[UserStatsService, Depends(get_user_stats_service)]
Subscriptions = Annotated[SubscriptionService, Depends(get_subscription_service)]
