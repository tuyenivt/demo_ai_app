import httpx
import backoff

from typing import List
from fastapi import HTTPException
from chatbot.config import settings
from openai import AsyncOpenAI


openai_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=30
)


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def query_openai(messages: List) -> str:
    """Send messages to OpenAI's /v1/chat/completions and return the response."""
    try:
        response = await openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            max_tokens=settings.MAX_CONTEXT_TOKENS,
            temperature=0.7,
            stream=False
        )
        if not response.choices:
            raise ValueError("No choices returned in the response.")
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Response content is None.")
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def get_embedding(text: str) -> list:
    """Get embedding vector for a given text using OpenAI's /v1/embeddings endpoint."""
    try:
        response = await openai_client.embeddings.create(
            model=settings.LLM_MODEL,
            input=text
        )
        if not response.data:
            raise ValueError("No data returned in the response.")
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")
