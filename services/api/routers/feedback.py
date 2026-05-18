import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.metrics import FEEDBACK_SUBMITTED

from ..database import get_db
from ..models import Feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    query: str  # the question that was asked
    answer: str  # the generated answer
    retrieved_chunk_ids: list[str]  # chunk UUIDs returned by search
    rating: int  # +1 (thumbs up) or -1 (thumbs down)


@router.post("/", status_code=201)
async def submit_feedback(
    request: FeedbackRequest,
    x_tenant_id: str = Header(...),
    x_user_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    # TODO 1: validate rating — must be +1 or -1
    # raise HTTPException(status_code=422) if not

    if request.rating not in [-1, 1]:
        raise HTTPException(status_code=422)

    # TODO 2: create a Feedback ORM object
    # tenant_id=uuid.UUID(x_tenant_id)
    # user_id=uuid.UUID(x_user_id)
    # query=request.query
    # answer=request.answer
    # retrieved_chunk_ids=[uuid.UUID(cid) for cid in request.retrieved_chunk_ids]
    # rating=request.rating

    feedback = Feedback(
        tenant_id=uuid.UUID(x_tenant_id),
        user_id=uuid.UUID(x_user_id),
        query=request.query,
        answer=request.answer,
        retrieved_chunk_ids=[uuid.UUID(cid) for cid in request.retrieved_chunk_ids],
        rating=request.rating,
    )

    # TODO 3: db.add(feedback), await db.flush()
    # return {"id": str(feedback.id), "rating": request.rating}

    db.add(feedback)
    await db.flush()
    FEEDBACK_SUBMITTED.labels(rating=str(request.rating)).inc()
    return {"id": str(feedback.id), "rating": request.rating}


@router.get("/stats")
async def get_feedback_stats(
    x_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns feedback statistics per chunk:
    which chunks consistently get positive or negative ratings.
    """
    # Query feedback for this tenant
    result = await db.execute(
        select(Feedback)
        .where(Feedback.tenant_id == uuid.UUID(x_tenant_id))
        .order_by(Feedback.created_at.desc())
        .limit(100)  # last 100 feedback items
    )
    feedbacks = result.scalars().all()

    if not feedbacks:
        return {"total": 0, "positive": 0, "negative": 0, "items": []}

    positive = sum(1 for f in feedbacks if f.rating == 1)
    negative = sum(1 for f in feedbacks if f.rating == -1)

    return {
        "total": len(feedbacks),
        "positive": positive,
        "negative": negative,
        "positive_rate": round(positive / len(feedbacks), 3),
        "items": [
            {
                "id": str(f.id),
                "query": f.query,
                "rating": f.rating,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ],
    }
