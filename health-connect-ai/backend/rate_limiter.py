import os
import time
from fastapi import Request, HTTPException, status
from collections import defaultdict
from typing import Callable

# Simple in-memory rate limiter (for production, use Redis or similar)
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 10))  # requests per minute per IP
rate_limit_store = defaultdict(list)

async def limiter(request: Request, call_next: Callable):
    ip = request.client.host
    now = time.time()
    window = 60  # seconds
    requests = rate_limit_store[ip]
    # Remove old requests
    rate_limit_store[ip] = [t for t in requests if now - t < window]
    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    rate_limit_store[ip].append(now)
    response = await call_next(request)
    return response

async def check_rate_limit(request: Request):
    ip = request.client.host
    now = time.time()
    window = 60
    requests = rate_limit_store[ip]
    rate_limit_store[ip] = [t for t in requests if now - t < window]
    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    rate_limit_store[ip].append(now)
