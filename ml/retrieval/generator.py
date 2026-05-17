import os

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are a helpful assistant that answers questions \
based strictly on the provided document chunks.

Rules:
- Only use information from the provided chunks
- If the answer is not in the chunks, say "I cannot find this in the documents"
- Cite your sources using [chunk_index] notation
- Be concise and precise"""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build the user prompt by inserting retrieved chunks.
    The LLM sees the chunks as context, then the question.
    """
    # TODO 1: format each chunk as a readable block
    # Use this format for each chunk:
    # [chunk_index] Source: {filename} (chunk {chunk_index})
    # {content}
    # hint: use enumerate() or chunk["chunk_index"] and chunk["filename"]

    chunks_blocks = []
    for chunk in chunks:
        chunks_blocks.append(
            f"[{chunk['chunk_index']}] Source: {chunk['filename']} "
            f"(chunk {chunk['chunk_index']})\n{chunk['content']}"
        )

    # TODO 2: join all formatted chunks with "\n\n---\n\n" as separator

    chunks_text = "\n\n---\n\n".join(chunks_blocks)

    # TODO 3: return a string in this format:
    # "DOCUMENT CHUNKS:\n\n{chunks_text}\n\nQUESTION: {query}"

    return f"DOCUMENT CHUNKS:\n\n{chunks_text}\n\nQUESTION: {query}"


async def generate_answer(query: str, chunks: list[dict]) -> dict:
    """
    Call the LLM with the query and retrieved chunks.
    Returns the answer and the sources used.
    """
    if not chunks:
        return {"answer": "No relevant documents found for your query.", "sources": []}

    prompt = build_prompt(query, chunks)

    # TODO 4: call client.chat.completions.create()
    # parameters:
    #   model=LLM_MODEL
    #   messages=[
    #       {"role": "system", "content": SYSTEM_PROMPT},
    #       {"role": "user", "content": prompt}
    #   ]
    #   temperature=0.1
    #   (low temperature = more factual, less creative — right for Q&A)

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    # TODO 5: extract the answer text
    # response.choices[0].message.content

    answer_text = response.choices[0].message.content

    # TODO 6: return a dict:
    # {
    #     "answer": answer_text,
    #     "sources": [
    #         {"chunk_index": c["chunk_index"], "filename": c["filename"], "score": c["score"]}
    #         for c in chunks
    #     ]
    # }

    return {
        "answer": answer_text,
        "sources": [
            {
                "chunk_index": c["chunk_index"],
                "filename": c["filename"],
                "score": c["score"],
            }
            for c in chunks
        ],
    }
