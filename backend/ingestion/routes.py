from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from backend.database.db import get_connection
from backend.guardrails.engine import check_document_safety
from backend.ingestion.extractor import extract_document
from backend.ingestion.cleaner import clean_text
from backend.ingestion.masker import mask_sensitive_data
from backend.ingestion.markdown import prepare_markdown
from backend.ingestion.chunker import chunk_document
from backend.rag.embeddings import embed_texts


router = APIRouter(prefix="/ingestion", tags=["Data Ingestion"])

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def update_document_status(document_id: int, status: str) -> None:
    """Update a document's processing status in PostgreSQL."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE documents
                SET status = %s
                WHERE id = %s
                """,
                (status, document_id),
            )


def process_document(
    file_bytes: bytes,
    filename: str,
    document_id: int,
) -> None:
    """Process an uploaded document in the background."""

    try:
        # 1. Extract document text.
        extracted = extract_document(file_bytes, filename)
        extracted_text = extracted["text"]

        # 2. Clean extracted text.
        cleaned_text = clean_text(extracted_text)

        # 3. Run the existing ingestion safety check.
        safety_result = check_document_safety(cleaned_text)

        if not safety_result.allowed:
            update_document_status(document_id, "rejected")
            print(
                f"Document {document_id} rejected: "
                f"{safety_result.reason}",
                flush=True,
            )
            return

        # 4. Mask sensitive information.
        masking_result = mask_sensitive_data(cleaned_text)
        masked_text = masking_result["masked_text"]

        # 5. Prepare Markdown.
        markdown_text = prepare_markdown(masked_text)

        # 6. Split the document into chunks.
        chunks = chunk_document(markdown_text)

        if not chunks:
            update_document_status(document_id, "failed")
            print(
                f"Document {document_id}: no usable text chunks.",
                flush=True,
            )
            return

        # 7. Generate embeddings.
        chunk_texts = [chunk["chunk_text"] for chunk in chunks]
        embeddings = embed_texts(chunk_texts)

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "The number of embeddings does not match the chunk count."
            )

        # 8. Insert chunks and mark the document completed.
        with get_connection() as connection:
            register_vector(connection)

            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO document_chunks (
                        document_id,
                        chunk_index,
                        chunk_text,
                        embedding,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            document_id,
                            chunk["chunk_index"],
                            chunk["chunk_text"],
                            embedding,
                            Jsonb(
                                {
                                    "word_count": chunk["word_count"],
                                    "masked_categories": (
                                        masking_result[
                                            "detected_categories"
                                        ]
                                    ),
                                }
                            ),
                        )
                        for chunk, embedding in zip(
                            chunks,
                            embeddings,
                            strict=True,
                        )
                    ],
                )

                cursor.execute(
                    """
                    UPDATE documents
                    SET status = 'completed'
                    WHERE id = %s
                    """,
                    (document_id,),
                )

        print(
            f"Document {document_id} processed successfully. "
            f"Chunks: {len(chunks)}",
            flush=True,
        )

    except Exception as error:
        try:
            update_document_status(document_id, "failed")
        except Exception:
            pass

        print(
            f"Document ingestion failed for ID {document_id}: "
            f"{type(error).__name__}: {error}",
            flush=True,
        )


@router.post("/upload", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Accept a PDF or DOCX and process it in the background."""

    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="A valid filename is required.",
        )

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Only PDF and DOCX files are supported.",
        )

    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The maximum permitted file size is 15 MB.",
        )

    file_type = extension.lstrip(".")

    try:
        # Register the document before processing starts.
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        file_name,
                        file_type,
                        file_size,
                        status
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        filename,
                        file_type,
                        len(file_bytes),
                        "processing",
                    ),
                )

                document_id = cursor.fetchone()[0]

    except Exception as error:
        print(
            f"Could not register uploaded document: "
            f"{type(error).__name__}: {error}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail="Could not register the uploaded document.",
        ) from error

    # Process the document after returning the upload response.
    background_tasks.add_task(
        process_document,
        file_bytes,
        filename,
        document_id,
    )

    return {
        "success": True,
        "message": "File uploaded. Document processing has started.",
        "document": {
            "id": document_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": len(file_bytes),
            "status": "processing",
        },
    }