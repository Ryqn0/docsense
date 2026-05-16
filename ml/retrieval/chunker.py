from dataclasses import dataclass

import tiktoken

TOKENIZER = tiktoken.get_encoding("cl100k_base")
# cl100k_base = the tokenizer used by GPT-4 and text-embedding-ada-002
# We use it as a standard - actual token counts may differ per model
# but this gives a good approximation for chunk sizing


@dataclass
class Chunk:
    content: str  # the actual text
    chunk_index: int  # position within the document
    token_count: int  # number of tokens in this chunk
    metadata: dict  # page number, char offset, etc...


def count_tokens(text: str) -> int:
    """Count tokens in a string using cl100k_base tokenizer."""
    return len(TOKENIZER.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = 512,  # max tokens per chunk
    chunk_overlap: int = 64,  # tokens of overlap between chunks
) -> list[Chunk]:
    """
    Split text into overlapping fixed-size chunks by token count.

    Args:
    text: the full document text
    chunk_size: maximum tokens per chunk
    chunk_overlap: tokens shared between consecutive chunks

    Returns:
    list of Chunk dataclasses in order
    """
    # TODO 1: encode the full text into tokens using TOKENIZER.encode(text)
    # tokens is now a list of integers (token IDs)

    token_ids = TOKENIZER.encode(text)

    # TODO 2: slide a window over the tokens to create chunks
    # start at index 0
    # each chunk: tokens[start : start + chunk_size]
    # next start: start + (chunk_size - chunk_overlap)
    # stop when start >= len(tokens)
    # hint: use a while loop, append to a list

    # TODO 3: for each token slice, decode back to text
    # hint: TOKENIZER.decode(token_slice) → string

    # TODO 4: build a Chunk dataclass for each slice
    # chunk_index = position in the list (0, 1, 2...)
    # token_count = len(token_slice)
    # metadata = {"char_offset": approximate character position}

    # TODO 5: return the list of Chunk objects

    chunks = []
    start = 0
    while start < len(token_ids):
        token_slice = token_ids[start : start + chunk_size]
        chunks.append(
            Chunk(
                content=TOKENIZER.decode(token_slice),
                chunk_index=len(chunks),
                token_count=len(token_slice),
                metadata={"char_offset": start},  # token offset, close enough
            )
        )
        start += chunk_size - chunk_overlap
    return chunks


def extract_text_from_txt(file_path: str) -> str:
    """Read plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pypdf"""
    from pypdf import PdfReader

    # TODO: open the PDF with PdfReader(file_path)
    # loop over reader.pages
    # extract text from each page with page.extract_text() or ""
    # join all pages with "\n\n" between them
    # return the full text string
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def extract_text(file_path: str, mime_type: str) -> str:
    """Route to the correct extractor based on mime type."""
    if mime_type == "text/plain":
        return extract_text_from_txt(file_path)
    elif mime_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported mime type: {mime_type}")
