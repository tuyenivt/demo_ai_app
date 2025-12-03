import httpx

from typing import List
from fastapi import HTTPException
from chatbot.config import settings


async def query_openai(messages: List[dict]) -> str:
    """Send messages to OpenAI and return the response."""
    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")


async def get_embedding(text: str) -> list:
    """Get embedding vector for a given text using OpenAI's /v1/embeddings endpoint."""
    payload = {
        "model": settings.LLM_MODEL,
        "input": text
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/v1/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            return data['data'][0]['embedding']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")
