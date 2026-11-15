
# ============================================================
# DOCUMIND AI - MULTI-FORMAT DOCUMENT INGESTION
#
# Supported:
# PDF, TXT, JSON, DOCX, CSV, SQL, JPG, JPEG, PNG
#
# Document
#  ↓
# Text extraction
#  ↓
# Chunking
#  ↓
# BGE-M3 dense + sparse embeddings
#  ↓
# Qdrant
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Any
import uuid

from langchain_core.documents import Document

from langchain_community.document_loaders import (
    PyPDFLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from .document_extractor import extract_document

from .embeddings import (
    embed_documents,
    embed_documents_minilm,
)

from .qdrant import (
    ensure_collection,
    upsert_chunks,
    upsert_chunks_minilm,
)

# ============================================================
# CHUNKING CONFIGURATION
# ============================================================

CHUNK_SIZE = 700
CHUNK_OVERLAP = 200


# ============================================================
# MULTI-FORMAT DOCUMENT INGESTION
# ============================================================

def ingest_document(
    file_path: str | Path,
    document_id: str,
    filename: str | None = None,
) -> dict[str, Any]:

    # ========================================================
    # VALIDATION
    # ========================================================

    file_path = Path(file_path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"Document file not found: {file_path}"
        )

    if not document_id:

        raise ValueError(
            "document_id is required."
        )

    document_id = str(
        document_id
    ).strip()

    display_filename = (
        filename
        or file_path.name
    )

    document_type = (
        file_path.suffix.lower().replace(".", "")
    )

    # ========================================================
    # INGESTION VERSION
    # ========================================================

    ingestion_version = str(
        uuid.uuid4()
    )

    # ========================================================
    # START LOGGING
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "DOCUMIND AI - DOCUMENT INGESTION"
    )

    print("=" * 70)

    print(
        f"File        : {display_filename}"
    )

    print(
        f"Document ID : {document_id}"
    )

    print(
        f"File type  : {document_type}"
    )

    # ========================================================
    # STEP 1 - EXTRACT DOCUMENT TEXT
    # ========================================================

    print(
        "\n[1/4] Extracting document text..."
    )

    # --------------------------------------------------------
    # PDF
    #
    # Keep PyPDFLoader for PDFs because it preserves
    # page-level metadata.
    # --------------------------------------------------------

    if document_type == "pdf":

        loader = PyPDFLoader(
            str(file_path)
        )

        documents = loader.load()

        if not documents:

            raise ValueError(
                "No text could be extracted from the PDF."
            )

        pages = len(documents)

    # --------------------------------------------------------
    # Other supported formats
    # --------------------------------------------------------

    else:

        extracted = extract_document(
            file_path
        )

        extracted_text = str(
            extracted.get("text")
            or ""
        ).strip()

        if not extracted_text:

            raise ValueError(
                "No text could be extracted from the document."
            )

        pages = int(
            extracted.get("pages")
            or 0
        )

        documents = [
            Document(
                page_content=extracted_text,
                metadata={
                    "source": str(file_path),
                    "document_type": document_type,
                },
            )
        ]

    print(
        f"Pages extracted: {pages}"
    )

    # ========================================================
    # STEP 2 - SPLIT DOCUMENT
    # ========================================================

    print(
        "\n[2/4] Splitting document..."
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_documents(
        documents
    )

    if not chunks:

        raise ValueError(
            "No text chunks were created."
        )

    print(
        f"Chunks created: {len(chunks)}"
    )

    # ========================================================
    # STEP 3 - PREPARE TEXT + METADATA
    # ========================================================

    print(
        "\n[3/4] Preparing BGE-M3 embeddings..."
    )

    texts: list[str] = []

    metadata: list[dict[str, Any]] = []

    for index, chunk in enumerate(chunks):

        text = str(
            chunk.page_content
            or ""
        ).strip()

        # ----------------------------------------------------
        # Skip empty chunks
        # ----------------------------------------------------

        if not text:

            continue

        # ----------------------------------------------------
        # Page number
        #
        # PDF page index:
        #     0, 1, 2, ...
        #
        # UI page number:
        #     1, 2, 3, ...
        #
        # Non-PDF formats:
        #     None
        # ----------------------------------------------------

        page_number = chunk.metadata.get(
            "page"
        )

        if page_number is not None:

            page_number = (
                int(page_number) + 1
            )

        # ----------------------------------------------------
        # Unique chunk ID
        # ----------------------------------------------------

        chunk_id = (
            f"{document_id}"
            f"_chunk_{index}"
        )

        # ----------------------------------------------------
        # Text
        # ----------------------------------------------------

        texts.append(
            text
        )

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        metadata.append(
            {
                "document_id": document_id,

                "filename": display_filename,

                "page": page_number,

                "chunk_id": chunk_id,

                "text": text,
            }
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not texts:

        raise ValueError(
            "The document contains no usable text."
        )

    print(
        f"Usable chunks: {len(texts)}"
    )

    # ========================================================
    # STEP 4 - EMBEDDINGS
    # ========================================================

    print(
        "\n[4/4] Generating BGE-M3 "
        "dense + sparse embeddings..."
    )

    embeddings = embed_documents(
        texts
    )

    dense_vectors, sparse_vectors = embeddings

    print(
        f"Dense vectors : {len(dense_vectors)}"
    )

    print(
        f"Sparse vectors: {len(sparse_vectors)}"
    )

    # ========================================================
    # QDRANT
    # ========================================================

    print("\nStoring chunks in Qdrant...")

    ensure_collection()

    # --------------------------------------------------------
    # Insert versioned chunks
    # --------------------------------------------------------

    inserted_count = upsert_chunks(
        embeddings=(
            dense_vectors,
            sparse_vectors,
        ),

        metadata=metadata,

        document_id=document_id,

        filename=display_filename,

        document_type=document_type,

        ingestion_version=ingestion_version,
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print(
        f"\nStored chunks in Qdrant: {inserted_count}"
    )

    print(
        f"Ingestion version: {ingestion_version}"
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "DOCUMENT INGESTION COMPLETE"
    )

    print("=" * 70)

    return {
        "document_id": document_id,

        "filename": display_filename,

        "pages": pages,

        "chunks": inserted_count,

        "ingestion_version": ingestion_version,
    }

# ============================================================
# PDF INGESTION - BACKWARD COMPATIBILITY
# ============================================================

def ingest_pdf(
    pdf_path: str | Path,
    document_id: str,
    filename: str | None = None,
) -> dict[str, Any]:

    return ingest_document(
        file_path=pdf_path,
        document_id=document_id,
        filename=filename,
    )

# ============================================================
# MINILM DOCUMENT INGESTION
# ============================================================

def ingest_document_minilm(
    file_path: str,
    document_id: str,
    filename: str | None = None,
) -> dict[str, Any]:
    """
    Ingest documents using MiniLM dense embeddings.

    Supported formats:
        PDF, TXT, JSON, DOCX, CSV, SQL,
        JPG, JPEG, PNG

    Stores vectors exclusively in:
        documind_minilm_384
    """

    import os
    import uuid

    from pathlib import Path

    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not file_path:
        raise ValueError("file_path is required.")

    if not document_id:
        raise ValueError("document_id is required.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    path = Path(file_path)

    document_type = path.suffix.lower().lstrip(".")

    supported_formats = {
        "pdf", "txt", "json", "docx",
        "csv", "sql", "jpg", "jpeg", "png",
    }

    if document_type not in supported_formats:
        raise ValueError(
            f"Unsupported document format: {document_type}"
        )

    resolved_filename = filename or path.name

    ingestion_version = str(uuid.uuid4())

    print("=" * 70)
    print("DOCUMIND AI - MINILM INGESTION")
    print("=" * 70)
    print("Filename:", resolved_filename)
    print("Document ID:", document_id)
    print("Document type:", document_type)
    print("Ingestion version:", ingestion_version)

    # --------------------------------------------------------
    # DOCUMENT EXTRACTION
    # --------------------------------------------------------

    if document_type == "pdf":

        from langchain_community.document_loaders import PyPDFLoader

        documents = PyPDFLoader(
            str(path)
        ).load()

    else:

        from app.rag.document_extractor import extract_document

        extraction_result = extract_document(str(path))

        if not isinstance(extraction_result, dict):
            raise TypeError(
                "Document extractor must return a dictionary."
            )

        extracted_text = extraction_result.get("text", "")

        if not isinstance(extracted_text, str):
            raise TypeError(
                "Extracted document text must be a string."
            )

        if not extracted_text.strip():
            raise ValueError(
                "No text could be extracted from the document."
            )

        documents = [
            Document(
                page_content=extracted_text,
                metadata={
                    "source": resolved_filename,
                    "page": 1,
                },
            )
        ]

    if not documents:
        raise ValueError(
            "Document extraction returned no content."
        )

    # --------------------------------------------------------
    # CHUNKING
    # --------------------------------------------------------

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = text_splitter.split_documents(
        documents
    )

    if not chunks:
        raise ValueError(
            "No document chunks were generated."
        )

    texts = []
    metadata = []

    for index, chunk in enumerate(chunks):

        text = chunk.page_content.strip()

        if not text:
            continue

        texts.append(text)

        item_metadata = dict(
            chunk.metadata
        )

        item_metadata.update({
            "document_id": document_id,
            "filename": resolved_filename,
            "document_type": document_type,
            "chunk_id": f"{document_id}_chunk_{index}",
            "page": item_metadata.get("page", 1),
            "text": text,
        })

        metadata.append(item_metadata)

    if not texts:
        raise ValueError(
            "No non-empty chunks available for embedding."
        )

    # --------------------------------------------------------
    # MINILM EMBEDDINGS
    # --------------------------------------------------------

    print(
        f"Generating MiniLM embeddings for {len(texts)} chunks..."
    )

    embeddings = embed_documents_minilm(
        texts
    )

    # --------------------------------------------------------
    # QDRANT UPSERT
    # --------------------------------------------------------

    stored_chunks = upsert_chunks_minilm(
        embeddings=embeddings,
        metadata=metadata,
        document_id=document_id,
        filename=resolved_filename,
        document_type=document_type,
        ingestion_version=ingestion_version,
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {
        "document_id": document_id,
        "filename": resolved_filename,
        "document_type": document_type,
        "pages": len(documents),
        "chunks": stored_chunks,
        "ingestion_version": ingestion_version,
        "embedding_model": "MiniLM",
        "vector_dimension": 384,
        "collection": "documind_minilm_384",
    }

    print("=" * 70)
    print("MINILM INGESTION COMPLETED")
    print("Pages:", result["pages"])
    print("Chunks:", result["chunks"])
    print("Vector dimension:", result["vector_dimension"])
    print("=" * 70)

    return result
