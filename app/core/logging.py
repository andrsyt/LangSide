import logging
import sys
from app.core.config import settings



def setup_logging():
    logging.basicConfig(
        level = getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # ✅ asctime,
        handlers = [logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


