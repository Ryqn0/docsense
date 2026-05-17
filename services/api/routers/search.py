from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ml.embeddings.embedder import embed_single
from ml.retrieval.generator import generate_answer
from ml.retrieval.vector_store import search_chunks

from ..database import get_db

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    # Pydantic model - defines and validates the request body
    # FastAPI reads JSON body and validates it against this model automatically
    query: str
    top_k: int = 5  # default: retrieve 5 chunks


@router.post("/")
async def search(
    request: SearchRequest,
    x_tenant_id: str = Header(...),
    x_user_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1 - embed the query into the same vector space as the chunks
    query_embedding = await embed_single(request.query)

    # Step 2 - find top_k nearest chunks in Qdrant, filtered by tenant
    chunks = await search_chunks(
        query_embedding=query_embedding,
        tenant_id=x_tenant_id,
        top_k=request.top_k,
    )

    # Step 3 - generate a cited answer using the retrieved chunks
    result = await generate_answer(request.query, chunks)

    # Step 4 - attach metadata for the client
    return {
        **result,
        "query": request.query,
        "chunks_retrieved": len(chunks),
    }
