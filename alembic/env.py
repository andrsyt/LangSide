"""
Alembic environment configuration для миграций БД.
"""
import os
import re
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from sqlalchemy.engine import Connection
from dotenv import load_dotenv

from alembic import context

# Загружаем переменные окружения
load_dotenv()

# Получаем DATABASE_URL из переменных окружения
database_url_raw = os.environ.get("DATABASE_URL", "")

# Если не найден, пробуем прочитать из .env файла напрямую
if not database_url_raw:
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == 'DATABASE_URL':
                            database_url_raw = value.strip().strip('"').strip("'")
                            break
    except Exception:
        pass

if not database_url_raw:
    raise ValueError("DATABASE_URL не найден в переменных окружения")

# Очищаем от проблемных символов, оставляя только ASCII
database_url_raw = database_url_raw.encode('ascii', errors='ignore').decode('ascii')

# Импортируем модели
from app.db.base import Base
from app.models import *  # Импортируем все модели

# this is the Alembic Config object
config = context.config

# Убираем +asyncpg и заменяем на postgresql:// для синхронного драйвера
database_url = database_url_raw.replace("+asyncpg", "").replace("postgresql+asyncpg://", "postgresql://")

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

