import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models import Feedback


async def get_chunk_feedback_scores(
    chunk_ids: list[str],
    tenant_id: str,
    db: AsyncSession,
) -> dict[str, float]:
    """
    For each chunk ID, compute its average feedback score.
    Returns: {chunk_id: avg_rating} where avg_rating between -1.0 and 1.0
    1.0 = always upvoted, -1.0 = always downvoted, 0.0 = no feedback
    """
    if not chunk_ids:
        return {}

    # Query feedback table for chunks that appear in retrieved_chunk_ids
    # PostgreSQL ARRAY contains operator: ANY(array_column) = value
    result = await db.execute(
        select(Feedback).where(
            Feedback.tenant_id == uuid.UUID(tenant_id),
        )
    )
    all_feedback = result.scalars().all()

    # Build per-chunk score feedback history
    chunk_ratings: dict[str, list[int]] = {cid: [] for cid in chunk_ids}

    for feedback_item in all_feedback:
        if feedback_item.retrieved_chunk_ids:
            for chunk_uuid in feedback_item.retrieved_chunk_ids:
                cid = str(chunk_uuid)
                if cid in chunk_ratings:
                    chunk_ratings[cid].append(feedback_item.rating)

    # Average the ratings - chunks with no feedback get 0.0
    return {
        cid: (sum(ratings) / len(ratings)) if ratings else 0.0 for cid, ratings in chunk_ratings.items()
    }


def rerank_chunks(
    chunks: list[dict],
    feedback_scores: dict[str, float],
    alpha: float = 0.1,
) -> list[dict]:
    """
    Adjust chunk scores using feedback history and re-sort.

    Args:
        chunks: list of chunk dicts from Qdrant (each has "score" and "chunk_id")
        feedback_scores: {chunk_id: avg_rating} from get_chunk_feedback_scores()
        alpha: how much weight to five feedback vs retrieval score
                0.0 = ignore feedback, 1.0 = only use feedback
                0.1 = 10% feedback influence (conservative start)

    Returns:
        re-sorted list of chunks, highest adjusted score first
    """

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        feedback_score = feedback_scores.get(chunk_id, 0.0)

        # adjusted = original_qdrant_score + alpha * feedback_signal
        # feedback_score between -1 and 1, alpha=0.1 -> max adjustment = +-0.1
        # keeps feedback from completely overriding semantic similarity
        chunk["adjusted_score"] = chunk["score"] + alpha * feedback_score
        chunk["feedback_score"] = round(feedback_score, 3)

    return sorted(chunks, key=lambda c: c["adjusted_score"], reverse=True)
