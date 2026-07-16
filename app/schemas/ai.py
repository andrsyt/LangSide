from pydantic import BaseModel

class WordAnalysisRequest(BaseModel):
    word: str
    difficulty_level: str | None = None

class WordAnalysisResponse(BaseModel):
    word: str
    translation: str
    explanation: str
    examples: list[str]
    difficulty: str | None = None