from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


# Load local .env in development (does not override existing env vars)
load_dotenv(override=False)


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "learn_english_db"
    DATABASE_URL: str
    REDIS_URL: str

    # Auth
    SECRET_KEY: str
    ANON_SALT: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5256000
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 604800

    # AI
    AI_PROVIDER: Literal["huggingface", "ollama", "groq"] = "groq"
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MODEL: str = "microsoft/Phi-3-mini-4k-instruct"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Billing limits
    FREE_TIER_DAILY_LIMIT: int = 50
    FREE_TIER_MONTHLY_LIMIT: int = 1000
    PREMIUM_TIER_DAILY_LIMIT: int = 500
    PREMIUM_TIER_MONTHLY_LIMIT: int = 50000
    FREE_TIER_WORD_LIMIT: int = 3

    # Cache/logging
    CACHE_TTL_SECONDS: int = 3600
    LOG_LEVEL: str = "INFO"

    # Translation APIs
    GOOGLE_TRANSLATION_KEY: str | None = None
    GOOGLE_TRANSLATE_URL: str = "https://translation.googleapis.com/language/translate/v2"
    DEEPL_API_KEY: str | None = None
    DEEPL_TRANSLATE_URL: str = "https://api-free.deepl.com/v2/translate"

    # iOS IAP
    IOS_IAP_MODE: Literal["disabled", "mock", "appstore"] = "disabled"
    IOS_IAP_MOCK_TOKEN: str = ""

    # RevenueCat
    REVENUECAT_WEBHOOK_SECRET: str = ""
    REVENUECAT_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
