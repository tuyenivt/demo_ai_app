# Chatbot

## Overview

- This is full stack of chatbot application.

## Quick Start

### ### 0. Using dependencies (poetry)

```shell
poetry add fastapi[standard-no-fastapi-cloud-cli] openai
poetry add --group dev httpx black ruff pipdeptree pytest pytest-asyncio pytest-cov
```

### 1. Prepare services with docker (or local installation)

```shell
docker network create devnet
docker run -d --network devnet --name chatbot-local-ai -p 8080:8080 localai/localai:latest
```

Go to `http://localhost:8080/browse/`, search and install `llama-doctor-3.2-3b-instruct`.

### 2. Running Locally

Start the app with cli:

```shell
fastapi dev src/chatbot/main.py
```
Server started at `http://localhost:8000`.

Interactive API docs (Swagger UI): `http://localhost:8000/docs`.
