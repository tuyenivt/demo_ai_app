import json
import redis.asyncio as redis

from fastapi import HTTPException

from chatbot.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 60)
    if count > settings.RATE_LIMIT:
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please wait.")


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
