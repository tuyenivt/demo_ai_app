from fastapi import FastAPI
from rasa.core.agent import Agent
from rasa.model import get_latest_model
from .models import ChatInput
import logging
import os

app = FastAPI()

agent = None

logging.basicConfig(level=logging.INFO)


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
