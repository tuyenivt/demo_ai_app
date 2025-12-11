import backoff

from typing import List
from fastapi import HTTPException
from httpx import HTTPStatusError
from openai import AsyncOpenAI

from chatbot.config import settings
from chatbot.util import should_retry_http


openai_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=30
)


@backoff.on_exception(
    backoff.expo,
    HTTPStatusError,
    max_tries=5,
    max_time=20,
    giveup=lambda e: not should_retry_http(e),
    on_backoff=lambda details: print(
        f"openai.query_openai retried {details['tries']} times"
    )
)
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


@backoff.on_exception(
    backoff.expo,
    HTTPStatusError,
    max_tries=5,
    max_time=20,
    giveup=lambda e: not should_retry_http(e),
    on_backoff=lambda details: print(
        f"openai.get_embedding retried {details['tries']} times"
    )
)
async def get_embedding(text: str) -> list:
    """Get embedding vector for a given text using OpenAI's /v1/embeddings endpoint."""
    try:
        response = await openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        if not response.data:
            raise ValueError("No data returned in the response.")
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")
