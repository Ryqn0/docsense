import asyncio
import json
from pathlib import Path

from ml.embeddings.embedder import embed_single
from ml.evaluation.metrics import (
    compute_answer_similarity,
    compute_context_precision,
    compute_faithfulness,
)
from ml.retrieval.generator import generate_answer
from ml.retrieval.vector_store import search_chunks


async def run_single(
    item: dict,
    tenant_id: str,
    top_k: int = 5,
) -> dict:
    """
    Run the full RAG pipeline on one eval item and compute all metrics.
    Returns a result dict with scores and metadata.
    """
    question = item["question"]
    ground_truth = item["ground_truth"]

    # Step 1 - run the RAG pipeline (same as the search endpoint)
    query_embedding = await embed_single(question)
    chunks = await search_chunks(query_embedding, tenant_id, top_k)
    rag_result = await generate_answer(question, chunks)
    generated_answer = rag_result["answer"]

    # Step 2 - compute metrics (all three at the same time)
    faithfulness, answer_sim, context_prec = await asyncio.gather(
        compute_faithfulness(generated_answer, chunks),
        compute_answer_similarity(generated_answer, ground_truth, embed_single),
        compute_context_precision(question, chunks),
    )
    # asyncio.gather() runs all three coroutines CONCURRENTLY
    # instead of sequentially - 3 MM% calls in parallel, not one after another
    # Wall time = max(t1, t2, t3) instead of t1 + t2 + t3

    return {
        "id": item["id"],
        "question": question,
        "ground_truth": ground_truth,
        "generated_answer": generated_answer,
        "metrics": {
            "faithfulness": round(faithfulness, 3),
            "answer_similarity": round(answer_sim, 3),
            "context_precision": round(context_prec, 3),
        },
        "chunkd_retrieved": len(chunks),
        "sources": [s["filename"] for s in rag_result["sources"]],
    }


async def run_evaluation(
    eval_set_path: str,
    tenant_id: str,
    top_k: int = 5,
) -> dict:
    """
    Run evaluation on the full golden set.
    Returns aggregated report with per-question results and averages.
    """
    path = Path(eval_set_path)
    if not path.exists():
        raise FileNotFoundError(f"Eval set not found: {eval_set_path}")

    with open(path) as f:
        eval_set = json.load(f)

    # Run questions sequentially to avoid hammering the API
    # (parallel would be faster but risks rate limits)
    results = []
    for item in eval_set:
        result = await run_single(item, tenant_id, top_k)
        results.append(result)

    # Aggregate metrics
    def avg(metric: str) -> float:
        scores = [r["metrics"][metric] for r in results]
        return round(sum(scores) / len(scores), 3)

    report = {
        "summary": {
            "total_questions": len(results),
            "avg_faithfulness": avg("faithfulness"),
            "avg_answer_similarity": avg("answer_similarity"),
            "avg_context_precision": avg("context_precision"),
        },
        "results": results,
    }

    return report
