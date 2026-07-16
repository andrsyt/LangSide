from pydantic import BaseModel, Field


class HomeStatsResponse(BaseModel):
    current_streak: int = 0
    best_streak: int = 0
    study_days_total: int = 0

    total_words: int = 0
    learning_words: int = 0
    mastered_words: int = 0
    words_due_today: int = 0
    words_due_later_this_week: int = 0
    mastery_percent: int = Field(0, ge=0, le=100)

    exercises_today: int = 0
    reviews_today: int = 0
    practice_today: int = 0
    words_added_today: int = 0
    session_cards_done_today: int = 0
