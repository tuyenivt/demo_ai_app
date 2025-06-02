# Telehealth Chatbot Service

## Overview
- This backend service provides a customer support chatbot using GPT-4 with Retrieval-Augmented Generation (RAG).
- It ingests documents, indexes them in FAISS, and answers user queries via a `/chat` endpoint.

## Features
- **Document Ingestion:** Upload PDF/Markdown (via `/ingest`) or specify an S3 key. Documents are chunked, embedded, and stored in a FAISS vector index for semantic search.
- **Chat API (`/chat`):** Handles user queries, retrieves relevant context chunks, and uses GPT-4 (via LangChain) to generate answers. Includes input sanitization and prompt injection mitigation.
- **Asynchronous & Scalable:** Uses async FastAPI endpoints to support 100+ concurrent users with <2s latency. Rate limiting and Redis caching improve performance under load.
- **Logging & Monitoring:** Requests, responses, and errors are logged (without PII). Retry/backoff logic handles transient OpenAI API failures gracefully.

## Setup
1. **Environment:** Copy `.env.example` to `.env` and fill in your credentials (OpenAI key, AWS S3, Redis URL, etc.).
2. **Python Dependencies:** Ensure Python 3.13 is installed. Install packages:
```shell
pip install -r requirements.txt
```
3. **Redis:** Run a Redis instance (locally or via URL in `.env`).

## Running Locally
Start the FastAPI app with Uvicorn:
```shell
uvicorn main:app --reload
```
The service will listen on `http://localhost:8000`. You can send:
- `POST /ingest` with a PDF/Markdown file or S3 key (admin only) to index documents.
- `POST /chat` with JSON `{"query": "Your question here"}` to get an answer.

## Docker Deployment
Build and run with Docker:
```shell
docker build -t telehealth-chatbot .
docker run -p 8000:8000 --env-file .env telehealth-chatbot
```
For AWS EKS or similar, use the provided multi-stage `Dockerfile` (based on `python:3.13-slim`) to build a production image.

## Notes
- **Performance:** We use in-memory FAISS (persist to disk in prod). The app is stateless aside from FAISS; you may scale via Kubernetes and manage the FAISS store as needed.
- **Security:** Sensitive data is only in environment variables (12-factor practice):contentReference[oaicite:10]{index=10}. No user data is logged. RBAC stubs allow future JWT/role integration.
- **Further Improvements:** Implement document re-ranker (LLM or MMR), enhance prompt templates, and integrate structured logging/metrics.
