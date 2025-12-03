import json
import os
import redis.asyncio as redis
import httpx
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from dotenv import load_dotenv
import uuid

from chatbot.config import Settings
from chatbot.model import ChatResponse, UpsertDocumentRequest, UpsertDocumentResponse

# Load environment variables from .env
load_dotenv()

# --- Config ---
settings = Settings()

system_prompt = """
You are an AI-powered assistant designed to support patients using a telehealth service called TelehealthChatbot.
You can help users with tasks such as booking appointments, understanding how to use the telehealth platform,
explaining common symptoms or health services (within non-diagnostic boundaries), and answering questions about
insurance, or general healthcare policies.

You do not provide medical diagnoses, treatment plans, or emergency assistance.

If a user asks about topics outside your scope (such as detailed medical advice, personalized health assessments,
or technical issues requiring human help), politely redirect them to human customer support.

Keep your responses clear, professional, and supportive. If no specific data is provided for a request,
let the user know and suggest checking back later or contacting support.
"""

# --- FastAPI app ---
app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Redis client ---
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# --- Qdrant client ---
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


# --- Rate limiting helper ---
async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 60)
    if count > settings.RATE_LIMIT:
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please wait.")


# --- Chat history helpers ---
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


# --- OpenAI wrapper ---
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


# --- OpenAI embedding generation ---
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


# --- Qdrant upsert helper ---
async def upsert_document_to_qdrant(collection: str, doc_id: str, text: str):
    embedding = await get_embedding(text)
    point = PointStruct(id=doc_id, vector=embedding, payload={"text": text})
    qdrant_client.upsert(collection_name=collection, points=[point])


# --- Qdrant search helper ---
async def search_qdrant(collection: str, query: str, top_k: int = 3) -> list:
    search_result = qdrant_client.query(
        collection_name=collection,
        query_text=query,
        limit=top_k
    )
    return [hit.document for hit in search_result]


async def retrieve_context_from_qdrant(query: str, top_k: int = 3) -> str:
    try:
        results = await search_qdrant(settings.VECTOR_COLLECTION, query, top_k=top_k)
        if results:
            return "\n".join(results)
        return ""
    except Exception as e:
        return ""  # Fail gracefully if Qdrant is unavailable


# --- Chat endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, userId: str = Header(..., alias="X-User-ID")):
    data = await request.json()
    user_message = data.get("message")
    if not user_message:
        raise HTTPException(
            status_code=400, detail="Missing message in request body.")
    await check_rate_limit(userId)

    # Retrieve chat history for this conversation
    conversationId = data.get("conversation_id")
    history = await get_chat_history(userId, conversationId)

    # Retrieve context from Qdrant (RAG)
    context = await retrieve_context_from_qdrant(user_message, settings.TOP_K_RETRIEVAL)

    # Compose messages for OpenAI
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    messages.append({"role": "user", "content": user_message})
    if context:
        messages.append(
            {"role": "system", "content": f"Relevant context: {context}"})

    # Query OpenAI
    assistant_reply = await query_openai(messages)

    # Update history
    history.append({"user": user_message, "assistant": assistant_reply})
    await set_chat_history(userId, conversationId, history)

    # Return last 5 turns
    return ChatResponse(response=assistant_reply, history=history[-5:])


@app.post("/upsert-document", response_model=UpsertDocumentResponse)
async def upsert_doc_endpoint(request: UpsertDocumentRequest):
    doc_id = request.doc_id or str(uuid.uuid4())
    await upsert_document_to_qdrant(settings.VECTOR_COLLECTION, doc_id, request.text)
    return UpsertDocumentResponse(success=True, doc_id=doc_id)
