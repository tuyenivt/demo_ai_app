# Chatbot

## Overview
This is a demo AI-powered chatbot designed to assist users with inquiries about a telehealth platform. 

## Features
- Integration with **LocalAI**, utilizing the **llama-doctor-3.2-3b-instruct** language model.
- Predefined system prompts to guide chatbot behavior and maintain consistent tone.
- **Redis** ensures persistent chat history for multi-turn conversations and supports rate limiting to prevent abuse.
- **Qdrant** serves as the vector store for semantic search, enabling context-aware responses via Retrieval-Augmented Generation (RAG).

## Using Dependencies (poetry)

```shell
poetry new chatbot
poetry add fastapi[standard] redis[hiredis] langchain-community langchain-text-splitters slowapi openai qdrant-client unstructured markdown pybreaker
poetry add --group dev httpx black ruff pytest-asyncio pytest-cov
```

## Start LocalAI
```shell
docker network create devnet
docker run -d --network devnet --name chatbot-local-ai -p 8080:8080 localai/localai:v3.8.0
```

Go to `http://localhost:8080/browse/`, search and install `llama-doctor-3.2-3b-instruct`.

Environment Variable:
- `OPENAI_API_KEY=NOT_REQUIRED_FOR_DEV`
- `OPENAI_BASE_URL=http://chatbot-local-ai:8080/v1`
- `OPENAI_MODEL=llama-doctor-3.2-3b-instruct`

## Start Vector DB
```shell
docker run -d --network devnet --name chatbot-qdrant -p 6333:6333 qdrant/qdrant:v1.16
```
Environment Variable:
- `QDRANT_URL=http://chatbot-qdrant:6333`

Go to Qdrant Collections page `http://localhost:6333/dashboard#/collections`, create sample collection:
- Name your collection: `telehealth_chatbot_docs`
- What's your use case?: `Global search`
- What to use for search?: `Simple Single embedding`
- Vector configuration:
  - Choose dimensions: `384` (`sentence-transformers/all-MiniLM-L6-v2`) or `1536` (`openai-ai/text-embedding-3-small`)
  - Choose metric: `Cosine`

## Start Redis
```shell
docker run -d --network devnet --name chatbot-redis -p 6379:6379 redis:8.4-alpine
```
Environment Variable:
- `REDIS_URL=redis://chatbot-redis:6379`

## Start FastAPI Backend
```shell
fastapi dev src/chatbot/main.py
```
For production: `fastapi run src/chatbot/main.py`

## Test content upsertion
```shell
curl -X POST http://localhost:8000/upsert-text \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"text": "Our telehealth app allows video consultations with licensed doctors."}'

curl -X POST http://localhost:8000/upsert-text \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"text": "To schedule an appointment, tap the calendar icon and select a time slot."}'

curl -X POST http://localhost:8000/upsert-file -F "file=@sample_upsert_1.pdf"

curl -X POST http://localhost:8000/upsert-file -F "file=@sample_upsert_2.md"
```

## Test Chat Memory via REST API
```shell
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"conversation_id": "test_conversation", "message": "My name is ABC"}'

curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"conversation_id": "test_conversation", "message": "Do you remember my name?"}'

curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"conversation_id": "test_conversation", "message": "What are insurance supported?"}'
```
