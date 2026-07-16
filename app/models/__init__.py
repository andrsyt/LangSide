"""
Import all models so Alembic can discover them.
"""
from app.models.user import User, UserTier
from app.models.user_public_id import UserPublicIdCounter
from app.models.word import Word, DifficultyLevel
from app.models.usage import Usage
from app.models.session import Session, SessionItem, SessionStatus
from app.models.quest import Quest, QuestType
from app.models.common_word import CommonWord
from app.models.test_session import TestSession, TestSessionStatus
from app.models.word_card import WordCard
from app.models.training import Training
from app.models.refresh_token import RefreshToken
from app.models.anti_confusion_session import AntiConfusionSession
from app.models.double_recall_session import DoubleRecallSession
from app.models.semantic_anchor_session import SemanticAnchorSession
from app.models.learning_session import LearningSession, LearningSessionItem, LearningSessionStatus, LearningQuestType
from app.models.user_word_confusion import UserWordConfusion
from app.models.user_daily_activity import UserDailyActivity
from app.models.battle import (
    Battle,
    BattleLeague,
    BattleMode,
    BattleParticipant,
    BattleRound,
    BattleStatus,
    UserBattleStats,
)
from app.models.friendship import FriendInviteCode, Friendship, FriendshipStatus
from app.models.battle_matchmaking import BattleMatchmakingTicket, MatchmakingStatus

__all__ = ["User", "UserTier", "UserPublicIdCounter", "Word", "DifficultyLevel", "Usage",
 "Session", "SessionItem", "SessionStatus", "Quest", "QuestType", "CommonWord",
 "TestSession", "TestSessionStatus", "WordCard", "Training", "RefreshToken", 
 "AntiConfusionSession", "DoubleRecallSession", "SemanticAnchorSession",
 "LearningSession", "LearningSessionItem", "LearningSessionStatus", "LearningQuestType",
 "UserWordConfusion", "UserDailyActivity",
 "Battle", "BattleLeague", "BattleMode", "BattleParticipant", "BattleRound", "BattleStatus", "UserBattleStats",
 "FriendInviteCode", "Friendship", "FriendshipStatus",
 "BattleMatchmakingTicket", "MatchmakingStatus"]
