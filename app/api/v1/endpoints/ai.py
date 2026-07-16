"""
AI endpoints. Standalone POST /ai/analyze was removed: analysis runs on word create
(POST /words/) and on re-analyze (POST /words/{word_id}/analyze).
"""
from fastapi import APIRouter

router = APIRouter()
