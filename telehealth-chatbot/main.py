import os
import logging
import tempfile
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import urllib.parse
import redis
import backoff
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai


# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT = os.getenv("RATE_LIMIT", "60/minute")
MAX_TOKEN_LIMIT = int(os.getenv("MAX_TOKEN_LIMIT", 4096))
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


# Initialize app, CORS, and rate limiter
app = FastAPI(title="Telehealth Support Chatbot API")
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_methods=["*"], allow_headers=["*"])
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Setup logging
logger = logging.getLogger("uvicorn.access")
logger.setLevel(logging.INFO)


# Connect to Redis for caching
redis_url = urllib.parse.urlparse(REDIS_URL)
redis = redis.Redis(host=redis_url.hostname,
                    port=redis_url.port or 6379, db=0, protocol=3)


# Configure OpenAI client
openai.api_key = OPENAI_API_KEY


# Global FAISS store (in-memory for this service)
vector_store = None


# --- Document Ingestion Endpoint ---
@app.post("/ingest")
@limiter.limit(RATE_LIMIT)
async def ingest_document(
    request: Request,
    file: UploadFile = File(None)
):
    """
    Ingest a PDF or Markdown document (via upload).
    Splits into chunks, embeds, and stores in FAISS.
    """
    try:
        # Get file content from upload
        if file is not None:
            content = await file.read()
            file_ext = os.path.splitext(file.filename)[1].lower()
        else:
            raise HTTPException(
                status_code=400, detail="No file provided.")

        # Save to temporary file and load
        if file_ext == ".pdf":
            # Save PDF content to temp file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            tmp.write(content)
            tmp.flush()
            tmp.close()
            loader = PyPDFLoader(tmp.name)
        elif file_ext == ".md":
            # Save Markdown content to temp file
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

        # Embed and store in FAISS
        embeddings = OpenAIEmbeddings()
        global vector_store
        if vector_store:
            vector_store.add_documents(docs, embeddings)
        else:
            vector_store = FAISS.from_documents(docs, embeddings)

        return {"detail": f"Ingested {len(docs)} document chunks."}
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(
            status_code=500, detail="Document ingestion failed.")


def sanitize_query(query: str) -> str:
    # Remove dangerous tokens (e.g. code fences)
    return query.replace("```", "").strip()


def get_cache_key(query: str) -> str:
    return f"chatbot:cache:{hash(query)}"


@app.post("/chat")
@limiter.limit(RATE_LIMIT)
async def chat_endpoint(request: Request, body: dict = Body(...)):
    try:
        # Input validation
        query = body.get("query", "").strip()
        if not query or len(query) < 3 or len(query) > 1000:
            raise HTTPException(
                status_code=400, detail="Query must be 3-1000 characters.")

        sanitized_query = sanitize_query(query)
        cache_key = get_cache_key(sanitized_query)

        # Check Redis cache
        cached_answer = redis.get(cache_key)
        if cached_answer:
            logger.info(f"Cache hit for query.")
            return {"answer": cached_answer.decode(), "cached": True}

        # Vector store retrieval
        global vector_store
        if not vector_store:
            logger.error("Vector store not initialized.")
            raise HTTPException(
                status_code=503, detail="Knowledge base not loaded.")
        docs_and_scores = vector_store.similarity_search_with_score(
            sanitized_query, k=5)
        filtered_docs = [doc for doc,
                         score in docs_and_scores if score > 0.2][:5]
        context = "\n---\n".join(doc.page_content for doc in filtered_docs)

        # Compose prompt
        system_prompt = (
            "You are a medical customer support assistant in a telehealth application. "
            "Use the following context from the knowledge base to answer the question. "
            "If not found, say you don't have enough information."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {sanitized_query}"}
        ]
        # Token management
        max_tokens = min(1024, MAX_TOKEN_LIMIT - len(context) // 4)

        # Call OpenAI with backoff
        try:
            answer = await call_openai_chat(messages, max_tokens)
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            raise HTTPException(
                status_code=503, detail="LLM service unavailable.")

        # Cache answer
        redis.set(cache_key, answer, ex=3600)
        logger.info(f"Answered query (not cached).")
        return {"answer": answer, "cached": False}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Chat failed.")


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def call_openai_chat(messages: list, max_tokens: int):
    response = await openai.ChatCompletion.acreate(
        model="gpt-4.1-nano",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return response.choices[0].message["content"]
