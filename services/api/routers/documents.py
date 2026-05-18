import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ml.embeddings.embedder import embed_batch
from ml.retrieval.chunker import Chunk as TextChunk
from ml.retrieval.chunker import chunk_text, extract_text
from ml.retrieval.vector_store import upsert_chunks
from services.api.metrics import CHUNKS_CREATED, DOCUMENTS_UPLOADED

from ..database import get_db
from ..models import Chunk as DBChunk  # ORM model
from ..models import Document

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/docsense_uploads")
# Local disk for now - Phase 9 replaces this with Google Cloud Storage
# /tmp is fine for development; it's cleared on container restart

ALLOWED_MIME_TYPES = {"application/pdf", "text/plain"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    # UploadFile = FastAPI's streaming file upload type
    # File(...) = required parameter (... means no default)
    x_tenant_id: str = Header(...),
    x_user_id: str = Header(...),
    # Using headers for tenant/user ID - placeholder until auth phase
    # Real auth (JWT tokens) comes in a later phase
    # Header(...) reads the X-Tenant-Id and X-User-Id HTTP headers
    db: AsyncSession = Depends(get_db),
    # Depends(get_db) = FastAPI injects a DB session automatically
    # et_db opens a session, yields it, closes it after the request
):
    # TODO 1: validate mime_type is in ALLOWED_MIME_TYPES
    # hint: file.content_type gives you the MIME type string
    # raise HTTPException(status_code=415, detail="...") if not allowed
    # 415 = Unsupported Media Type

    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported Media Type, mime_type not in ALLOWED_MIME_TYPES",
        )

        # TODO 2: read the file content into memory
        # hint: content = await file.read()
        # then check len(content) against MAX_FILE_SIZE
        # raise HTTPException(status_code=413, detail="...") if too large
        # 413 = Content Too Large

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Content Too Large, MAX_FILE_SIZE exceeded")

        # TODO 3: save the file to disk
        # - generate a unique filename: f"{uuid.uuid4()}_{file.filename}"
        # - create UPLOAD_DIR if it doesn't exist (os.makedirs, exist_ok=True)
        # - use aiofiles.open() to write — async file I/O, non-blocking
        # hint:
    # async with aiofiles.open(file_path, "wb") as f:
    #     await f.write(content)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # TODO 4: create a Document record in the database
    # - create a Document() object with all the fields
    # - db.add(document) to stage it
    # - await db.flush() to get the generated ID without committing
    # hint: status should be "pending" (worker will process it)

    document = Document(
        tenant_id=uuid.UUID(x_tenant_id),
        user_id=uuid.UUID(x_user_id),
        filename=str(file.filename),
        file_path=str(file_path),
        mime_type=str(mime_type),
        file_size=int(len(content)),
    )
    try:
        db.add(document)
        await db.flush()

    except IntegrityError:
        raise HTTPException(
            status_code=422,
            detail="Invalid tenant_id or user_id - ensure both exist before uploading",
        )

    try:
        # extract text from saved file
        text = extract_text(file_path, mime_type)

        # Cunk the text
        text_chunks: list[TextChunk] = chunk_text(text)

        # Build DB Chunk records
        db_chunks = [
            DBChunk(
                document_id=document.id,
                tenant_id=uuid.UUID(x_tenant_id),
                content=tc.content,
                chunk_index=tc.chunk_index,
                token_count=tc.token_count,
                metadata_=tc.metadata,
            )
            for tc in text_chunks
        ]

        # Bulk insert - one round trip to DB instead of N inserts
        db.add_all(db_chunks)
        await db.flush()
        # Flush first so db_chunks have their UUIDs generated

        # Embed all chunks in one API call
        embeddings = await embed_batch([tc.content for tc in text_chunks])

        # Build payloads - what Qdrant stores alongside each vector
        payloads = [
            {
                "chunk_id": str(db_chunk.id),
                "document_id": str(document.id),
                "tenant_id": x_tenant_id,
                "content": tc.content,
                "chunk_index": tc.chunk_index,
                "filename": file.filename,
            }
            for db_chunk, tc in zip(db_chunks, text_chunks)
        ]

        # Upsert into Qdrant
        await upsert_chunks(
            chunk_ids=[str(c.id) for c in db_chunks],
            embeddings=embeddings,
            payloads=payloads,
        )

        # Update embedding_id on each DB bunk (Qdrant ID = chunk UUID)
        for db_chunk in db_chunks:
            db_chunk.embedding_id = str(db_chunk.id)

            # Update document status to ready
            document.status = "ready"

            DOCUMENTS_UPLOADED.inc()
            CHUNKS_CREATED.inc(len(db_chunks))

    except Exception as e:
        document.status = "failed"
        await db.flush()
        raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")

    # TODO 5: return a response dict with:
    # {"id": str(document.id), "filename": file.filename, "status": "pending"}
    # New return

    return {
        "id": str(document.id),
        "filename": file.filename,
        "status": document.status,
        "chunks": len(db_chunks),  # Show how many chunks created
    }
