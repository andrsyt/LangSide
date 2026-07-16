from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kyiv",
    enable_utc=True,
)


def _register_task_modules() -> None:
    import app.tasks.ai_tasks  # noqa: F401
    import app.tasks.word_tasks  # noqa: F401


_register_task_modules()