import json
import redis.asyncio as redis

from chatbot.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_chat_history(user_id: str, conversation_id: str) -> list:
    # Use Redis for chat history, keyed by user and conversation
    key = f"chat_history:{user_id}:{conversation_id}"
    history = await redis_client.get(key)
    if history:
        return json.loads(history)
    return []


async def set_chat_history(user_id: str, conversation_id: str, history: list):
    key = f"chat_history:{user_id}:{conversation_id}"
    # 1 day expiry
    await redis_client.set(key, json.dumps(history), ex=60*60*24)


async def get_chat_cache(user_id: str, conversation_id: str, user_message: str) -> str:
    # Use Redis for chat cache, keyed by user and conversation and user_message
    key = f"chat_history:{user_id}:{conversation_id}:{hash(user_message)}"
    return await redis_client.get(key)


async def set_chat_cache(user_id: str, conversation_id: str, user_message: str, answer: str):
    key = f"chat_history:{user_id}:{conversation_id}:{hash(user_message)}"
    # 1h expiry
    await redis_client.set(key, answer, ex=60*60)
