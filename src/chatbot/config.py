import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = 'Telehealth Chatbot'
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL: str = os.getenv(
        'OPENAI_BASE_URL', 'http://chatbot-local-ai:8080/v1')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'llama-doctor-3.2-3b-instruct')
    VECTOR_COLLECTION: str = os.getenv(
        'VECTOR_COLLECTION', 'telehealth_chatbot_docs')
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    MAX_CONTEXT_TOKENS: int = 1800
    TOP_K_RETRIEVAL: int = 6
    REINDEX_CRON: str = '0 3 * * *'  # daily 03:00
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://ai-redis:6379')
    RATE_LIMIT: int = int(os.getenv('RATE_LIMIT', '60'))  # per minute
    QDRANT_URL: str = os.getenv('QDRANT_URL', 'chatbot-qdrant:6334')
    QDRANT_API_KEY: str = os.getenv('QDRANT_API_KEY', '')


class Config:
    env_file = '.env'
