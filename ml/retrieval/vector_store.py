import os

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,  # enum: Cosine, Dot, Euclid
    FieldCondition,  # one condition in a filter
    Filter,  # for filtering by metadata
    MatchValue,  # matches a field to an exact value
    PointStruct,  # a single vector + payload to upsert
    VectorParams,  # defines vector dimension + distance_metric
)

from ml.embeddings.embedder import EMBEDDING_DIMENSION

COLLECTION_NAME = "docsense_chunks"

# Module-level client - one connection, reused everywhere
qdrant = AsyncQdrantClient(
    host=os.getenv("QDRANT_HOST", "qdrant"),
    port=int(os.getenv("QDRANT_PORT", "6333")),
)


async def ensure_collection() -> None:
    existing = await qdrant.get_collections()
    names = [c.name for c in existing.collections]
    if COLLECTION_NAME not in names:
        await qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,  # 1536 for text-embedding-3-small
                distance=Distance.COSINE,  # cosine similarity for text
            ),
        )


async def upsert_chunks(
    chunk_ids: list[str],
    embeddings: list[list[float]],
    payloads: list[dict],
) -> None:
    await qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(id=str(i), vector=v, payload=p)
            for i, v, p in zip(chunk_ids, embeddings, payloads)
        ],
    )


async def search_chunks(
    query_embedding: list[float],
    tenant_id: str,
    top_k: int = 5,
) -> list[dict]:
    results = await qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=Filter(must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]),
        limit=top_k,
    )
    # results.points = list of ScoredPoint
    # r.payload = the dict we stored alongside the vector
    # **r.payload unpacks it into the result dict
    return [{"id": r.id, "score": r.score, **r.payload} for r in results.points]
