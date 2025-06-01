from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from rasa.core.agent import Agent
from rasa.model import get_latest_model
import os
import logging

from .models import ChatInput
from .rate_limiter import limiter
from .logging_config import configure_logging

# Load environment variables
load_dotenv()

# Configure logging
configure_logging()

app = FastAPI()

agent = None


# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    response = await limiter(request, call_next)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )


async def load_rasa_agent():
    global agent
    models_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'rasa', 'models'))
    rasa_model_path = get_latest_model(models_dir)
    agent = Agent.load(model_path=rasa_model_path)


async def chat_endpoint(sender_id: str, message: str):
    if agent is None:
        await load_rasa_agent()  # Load agent if not already loaded

    # Process the message with Rasa, maintaining session via sender_id
    responses = await agent.handle_text(message, sender_id=sender_id)
    return {"responses": responses}


@app.post("/chat/")
async def chat(chat_input: ChatInput):
    response = await chat_endpoint(chat_input.sender_id, chat_input.message)
    return response
