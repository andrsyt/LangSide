"""Defaults for today (daily) vocabulary sessions."""

TODAY_SOFT_GOAL = 10
TODAY_STREAK_MIN = 6
TODAY_EXTEND_BATCH = 5
TODAY_GOAL_MIN = 3
TODAY_GOAL_MAX = 30
TODAY_DISCOVERY_DAILY_MAX = 4

SESSION_SOURCE_DUE = "due"
SESSION_SOURCE_LEARNING = "learning"
SESSION_SOURCE_DISCOVERY = "discovery"


def clamp_daily_goal(goal: int) -> int:
    return max(TODAY_GOAL_MIN, min(goal, TODAY_GOAL_MAX))
