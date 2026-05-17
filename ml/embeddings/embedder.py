import os

from openai import AsyncOpenAI

# Module-level client - created once, reused across all requests
# AsyncOpenAI auomatically reads OPENAI_API_KEY from environment
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
# 1536 = the output dimension of text-embedding-3-small
# This number MUST match Qdrant collection dimension we create later
# Changing the model later requires re-embedding ALL chunks


async def embed_single(text: str) -> list[float]:
    """Embed one text string. Returns a list of 1536 floats."""
    # TODO 1: call client.embeddings.create()
    # parameters: input=text, model=EMBEDDING_MODEL
    # the response structure is:
    #   response.data = list of embedding objects
    #   response.data[0].embedding = the list of floats for the first input
    # return the embedding for the first (only) input

    response = await client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts in one API call.
    More efficient than calling embed_single() in a loop.

    Returns a list of embeddings in the same order as input texts.
    """
    # TODO 2: call client.embeddings.create() with input=texts (the whole list)
    # The API embeds all texts in one HTTP request
    # response.data is a list of embedding objects, one per input text
    # return [item.embedding for item in response.data]

    response = await client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in response.data]
