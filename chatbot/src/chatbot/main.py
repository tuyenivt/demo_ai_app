import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # load environment variables from .env

openai = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

response = openai.chat.completions.create(
    model=str(os.getenv("OPENAI_MODEL")),
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how to treat a cough?"}
    ],
    temperature=0.7,
    max_tokens=10000,
    stream=False
)

print(response)
