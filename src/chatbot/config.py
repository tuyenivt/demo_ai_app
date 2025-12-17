import os

from enum import Enum
from pydantic_settings import BaseSettings


class AppEnv(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    APP_ENV: AppEnv = AppEnv.development
    APP_NAME: str = 'Telehealth Chatbot'
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL: str = os.getenv(
        'OPENAI_BASE_URL', 'http://chatbot-local-ai:8080/v1')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'llama-doctor-3.2-3b-instruct')
    EMBEDDING_MODEL: str = os.getenv(
        'EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    QDRANT_URL: str = os.getenv('QDRANT_URL', 'http://chatbot-qdrant:6333')
    QDRANT_API_KEY: str = os.getenv('QDRANT_API_KEY', '')
    VECTOR_COLLECTION: str = os.getenv(
        'VECTOR_COLLECTION', 'telehealth_chatbot_docs')
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    MAX_CONTEXT_TOKENS: int = 1800
    TOP_K_RETRIEVAL: int = 6
    REINDEX_CRON: str = '0 3 * * *'  # daily 03:00
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://ai-redis:6379')
    RATE_LIMIT: str = os.getenv('RATE_LIMIT', '60/minute')
    CORS_ALLOW_ORIGINS: str = os.getenv('CORS_ALLOW_ORIGINS', '*')
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL', 'postgres://username:password@chatbot-postgres:5432/chatbotdb')

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
