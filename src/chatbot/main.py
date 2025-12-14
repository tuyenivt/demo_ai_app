import logging
import os
import tempfile
import uuid

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from chatbot.cache import get_chat_cache, set_chat_cache, get_chat_history, set_chat_history
from chatbot.config import settings
from chatbot.model import ChatResponse, UpsertResponse, UpsertFileResponse
from chatbot.openai import query_openai
from chatbot.qdrant_client import retrieve_context_from_qdrant, upsert_text_to_qdrant, upsert_langchain_docs_to_qdrant


# --- System prompt ---
system_prompt = """
You are an AI-powered assistant designed to support patients using a telehealth service called Telehealth Virtual Care Assistant.
You can help users with tasks such as booking appointments, understanding how to use the telehealth platform,
explaining common symptoms or health services (within non-diagnostic boundaries), and answering questions about
insurance, or general healthcare policies.

You do not provide medical diagnoses, treatment plans, or emergency assistance.

If a user asks about topics outside your scope (such as detailed medical advice, personalized health assessments,
or technical issues requiring human help), politely redirect them to human customer support.

Keep your responses clear, professional, and supportive. If no specific data is provided for a request,
let the user know and suggest checking back later or contacting support.
"""


# Initialize slowapi Limiter
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)


# Initialize app, CORS, and rate limiter
app = FastAPI(title=settings.APP_NAME)


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Setup logging
logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT)
async def chat_endpoint(request: Request, userId: str = Header(..., alias="X-User-ID")):
    data = await request.json()
    user_message = data.get("message")
    if not user_message:
        raise HTTPException(
            status_code=400, detail="Missing message in request body.")
    conversation_id = data.get("conversation_id")

    # Retrieve chat history for this conversation
    history = await get_chat_history(userId, conversation_id)

    # Check Redis cache
    cached_answer = await get_chat_cache(userId, conversation_id, user_message)
    if cached_answer:
        logger.info("Cache hit for query.")
        return ChatResponse(response=cached_answer, history=history[-10:])

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

    # Update cache
    await set_chat_cache(userId, conversation_id, user_message, assistant_reply)

    # Update history
    history.append({"user": user_message, "assistant": assistant_reply})
    await set_chat_history(userId, conversation_id, history)

    # Return last 10 turns
    return ChatResponse(response=assistant_reply, history=history[-10:])


@app.post("/upsert-text", response_model=UpsertResponse)
@limiter.limit(settings.RATE_LIMIT)
async def upsert_text_endpoint(request: Request):
    data = await request.json()
    doc_id = data.get("doc_id") or str(uuid.uuid4())
    await upsert_text_to_qdrant(settings.VECTOR_COLLECTION, doc_id, data.get("text"))
    return UpsertResponse(success=True, doc_id=doc_id)


@app.post("/upsert-file")
@limiter.limit(settings.RATE_LIMIT)
async def upsert_file_endpoint(request: Request, file: UploadFile = File(None)):
    try:
        # Get file content from upload
        if file is not None and file.filename is not None:
            content = await file.read()
            file_ext = file.filename.split(".")[-1].lower()
        else:
            raise HTTPException(
                status_code=400, detail="No file provided.")

        # Save to temporary file and load
        if file_ext == "pdf":
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            tmp.write(content)
            tmp.flush()
            tmp.close()
            loader = PyPDFLoader(tmp.name)
        elif file_ext == "md":
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            tmp.write(content)
            tmp.flush()
            tmp.close()
            loader = UnstructuredMarkdownLoader(tmp.name)
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported file type.")

        # Chunk document into 1024-token pieces
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, chunk_overlap=200)
        docs = splitter.split_documents(documents)

        doc_ids = await upsert_langchain_docs_to_qdrant(settings.VECTOR_COLLECTION, docs)
        return UpsertFileResponse(success=True, doc_ids=doc_ids)
    except Exception as e:
        logger.error(f"upsertion error: {e}")
        raise HTTPException(
            status_code=500, detail="Document upsertion failed.")
