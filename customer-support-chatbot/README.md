# Customer Support Chatbot

## Overview
This is a demo AI-powered customer support chatbot designed to assist users with inquiries about a telehealth platform. 

## Features
- Integration with **Ollama**, utilizing the **LLaMA 3.1** language model.
- Predefined system prompts to guide chatbot behavior and maintain consistent tone.
- **Redis** ensures persistent chat history for multi-turn conversations and supports rate limiting to prevent abuse.
- **Qdrant** serves as the vector store for semantic search, enabling context-aware responses via Retrieval-Augmented Generation (RAG).

## Start Ollama
```shell
docker run -d --network devnet --name ai-ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama:0.7.1
```
Environment Variable:
- `OLLAMA_BASE_URL=http://ai-ollama:11434`
- `OLLAMA_MODEL=llama3.1`

## Start Vector DB
```shell
docker run -d --network devnet --name ai-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.14.1
```
Environment Variable:
- `QDRANT_HOST=ai-qdrant`
- `QDRANT_PORT=6334`

## Start Redis
```shell
docker run -d --network devnet --name ai-redis -p 6379:6379 redis:8.0-alpine
```
Environment Variable:
- `REDIS_URL=redis://ai-redis:6379`

## Start FastAPI Backend
```shell
uvicorn main:app --reload
```

## Test via REST API
```shell
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"conversation_id": "test_conversation", "message": "What are insurance supported?"}'
```

## Test Chat Memory via REST API
```shell
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"conversation_id": "test_conversation", "message": "My name is ABC"}'
```

```shell
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test_user" \
     -d '{"conversation_id": "test_conversation", "message": "Do you remember my name?"}'
```
