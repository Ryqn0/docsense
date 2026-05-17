import json
import os

import numpy as np
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Result: 1.0 = identical direction, 0.0 = perpendicular, -1.0 = opposite
    """
    a = np.array(vec_a)
    b = np.array(vec_b)
    # TODO 1: implement cosine similarity
    # formula: dot(a, b) / (norm(a) * norm(b))
    # numpy functions: np.dot(), np.linalg.norm()
    # handle edge case: if either norm is 0, return 0.0

    norm = np.linalg.norm(a) * np.linalg.norm(b)

    if norm == 0:
        return 0.0

    return np.dot(a, b) / norm


async def compute_answer_similarity(
    generated_answer: str,
    ground_truth: str,
    embedder,  # the embed_single function - passed in to avoid circular import
) -> float:
    """
    Semantic similarity between generated answer and ground truth.
    Uses embeddings - captures meaning, not just keyword overlap.
    Score: 0.0 (completely different) → 1.0 (identical meaning)
    """
    # TODO 2: embed both strings using embedder(text)
    # compute cosine_similarity between the two embeddings
    # return the score

    emb_ans = await embedder(generated_answer)
    emb_tru = await embedder(ground_truth)

    return cosine_similarity(emb_ans, emb_tru)


async def compute_faithfulness(
    answer: str,
    chunks: list[dict],
) -> float:
    """
    LLM-as-judge: does the answer make claims not supported by the chunks?
    Score: 1.0 = fully grounded, 0.0 = fully hallucinated
    """
    if not answer or not chunks:
        return 1.0  # no answer = no claims = no hallucinations

    chunks_text = "\n\n".join(f"[{c['chunk_index']}] {c['content']}" for c in chunks)

    judge_prompt = f"""You are evaluating whether an AI answer is faithful to source documents.

SOURCE CHUNKS:
{chunks_text}

ANSWER TO EVALUATE:
{answer}

Task: Identify each factual claim in the answer.
For each claim, determine if it is SUPPORTED or NOT SUPPORTED by the source chunks.

Respond with ONLY a JSON object:
{{"supported": <count>, "total": <count>, "score": <float 0.0-1.0>}}

The score = supported / total. If the answer makes no claims; score = 1.0."""

    # TODO 3: call client.chat.completions.create()
    # model="gpt-4o-mini", temperature=0.0 (fully deterministic for judging)
    # messages: just a user message with judge_prompt (no system prompt needed)
    # parse the JSON from response.choices[0].message.content
    # return the "score" field as a float
    # hint: use Python's json.loads() to parse the response
    # wrap in try/except — LLM sometimes returns malformed JSON
    # return 0.5 as fallback if parsing fails

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[{"role": "user", "content": judge_prompt}],
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return float(data["score"])

    except (json.JSONDecodeError, KeyError, ValueError):
        return 0.5  # fallbacks as to not creash eval run


async def compute_context_precision(
    question: str,
    chunks: list[dict],
) -> float:
    """
    What fraction of retrieved chunks were actually relevant to the question?
    Score: 1.0 = all chunks relevant, 0.0 = no chunks relevant
    """
    if not chunks:
        return 0.0

    relevant_count = 0
    chunks_text = "\n\n".join(f"CHUNK {i}: {c['content']}" for i, c in enumerate(chunks))
    judge_prompt = f"""For each chunk below, answer YES if it is relevant to the question, NO if not.

QUESTION: {question}

{chunks_text}

Respond with ONLY a comma-separated list of YES/NO in order, e.g.: YES,NO,YES,YES,NO"""

    # TODO 4: call the LLM for the whole chunks
    # model="gpt-4o-mini", temperature=0.0
    # check if "YES" in response (case-insensitive)
    # increment relevant_count if yes

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[{"role": "user", "content": judge_prompt}],
    )

    try:
        raw = response.choices[0].message.content.strip().upper()
        answers = [a.strip() for a in raw.split(",")]
        relevant_count = sum(1 for a in answers if "YES" in a)
        return relevant_count / len(chunks)
    except Exception:
        return 0.5
