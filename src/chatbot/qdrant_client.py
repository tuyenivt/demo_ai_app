import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

from chatbot.config import settings
from chatbot.openai import get_embedding


qdrant_client = QdrantClient(
    url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


async def upsert_text_to_qdrant(collection: str, doc_id: str, text: str):
    embedding = await get_embedding(text)
    point = PointStruct(id=doc_id, vector=embedding, payload={"text": text})
    qdrant_client.upsert(collection_name=collection, points=[point])


async def search_qdrant(collection: str, query: str, top_k: int = 3) -> list:
    search_result = qdrant_client.query(
        collection_name=collection,
        query_text=query,
        limit=top_k
    )
    return [hit.document for hit in search_result]


async def retrieve_context_from_qdrant(query: str, top_k: int = 3) -> str:
    try:
        results = await search_qdrant(settings.VECTOR_COLLECTION, query, top_k=top_k)
        if results:
            return "\n".join(results)
        return ""
    except Exception as e:
        logging.error(f"Qdrant retrieval error: {e}")
        return ""  # Fail gracefully if Qdrant is unavailable
