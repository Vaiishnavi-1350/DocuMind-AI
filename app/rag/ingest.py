# ============================================================
# DOCUMIND AI - PDF INGESTION
#
# PDF
#  ↓
# PyPDFLoader
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

from langchain_community.document_loaders import (
    PyPDFLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from .embeddings import embed_documents

from .qdrant import (
    ensure_collection,
    delete_document,
    upsert_chunks,
)


# ============================================================
# CHUNKING CONFIGURATION
# ============================================================

CHUNK_SIZE = 700
CHUNK_OVERLAP = 200

# ============================================================
# PDF INGESTION
# ============================================================

def ingest_pdf(
    pdf_path: str | Path,
    document_id: str,
    filename: str | None = None,
) -> dict[str, Any]:
    """
    Ingest one PDF into the new unified BGE-M3 + Qdrant RAG.

    Flow:

        PDF
         ↓
        PyPDFLoader
         ↓
        text extraction
         ↓
        chunking
         ↓
        BGE-M3
         ↓
        dense + sparse embeddings
         ↓
        Qdrant
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    pdf_path = Path(
        pdf_path
    )

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
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
        or pdf_path.name
    )

    # ========================================================
    # START LOGGING
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "DOCUMIND AI - PDF INGESTION"
    )

    print("=" * 70)

    print(
        f"File        : {display_filename}"
    )

    print(
        f"Document ID : {document_id}"
    )

    # ========================================================
    # STEP 1 - LOAD PDF
    # ========================================================

    print(
        "\n[1/4] Loading PDF..."
    )

    loader = PyPDFLoader(
        str(pdf_path)
    )

    documents = loader.load()

    if not documents:

        raise ValueError(
            "No text could be extracted "
            "from the PDF."
        )

    print(
        f"Pages extracted: "
        f"{len(documents)}"
    )

    # ========================================================
    # STEP 2 - SPLIT PDF
    # ========================================================

    print(
        "\n[2/4] Splitting document..."
    )

    splitter = (
        RecursiveCharacterTextSplitter(
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
    )

    chunks = (
        splitter.split_documents(
            documents
        )
    )

    if not chunks:

        raise ValueError(
            "No text chunks were created."
        )

    print(
        f"Chunks created: "
        f"{len(chunks)}"
    )

    # ========================================================
    # STEP 3 - PREPARE TEXT + METADATA
    # ========================================================

    print(
        "\n[3/4] Preparing BGE-M3 embeddings..."
    )

    texts: list[str] = []

    metadata: list[
        dict[str, Any]
    ] = []

    for index, chunk in enumerate(
        chunks
    ):

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
        # PyPDFLoader page index:
        #     0, 1, 2, ...
        #
        # UI page number:
        #     1, 2, 3, ...
        # ----------------------------------------------------

        page_number = (
            chunk.metadata.get(
                "page"
            )
        )

        if page_number is not None:

            page_number = (
                int(page_number)
                + 1
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
                "document_id":
                    document_id,

                "filename":
                    display_filename,

                "page":
                    page_number,

                "chunk_id":
                    chunk_id,

                "text":
                    text,
            }
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not texts:

        raise ValueError(
            "The PDF contains no "
            "usable text."
        )

    print(
        f"Usable chunks: "
        f"{len(texts)}"
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

    dense_vectors, sparse_vectors = (
        embeddings
    )

    print(
        f"Dense vectors : "
        f"{len(dense_vectors)}"
    )

    print(
        f"Sparse vectors: "
        f"{len(sparse_vectors)}"
    )

    # ========================================================
    # QDRANT
    # ========================================================

    print(
        "\nStoring chunks in Qdrant..."
    )

    ensure_collection()

    # --------------------------------------------------------
    # Remove existing chunks belonging to this document ID.
    #
    # This prevents duplicate chunks when the same PDF is
    # uploaded again with the same document_id.
    # --------------------------------------------------------

    delete_document(
        document_id
    )

    # --------------------------------------------------------
    # Insert new chunks
    # --------------------------------------------------------
    inserted_count = upsert_chunks(
    embeddings=(
        dense_vectors,
        sparse_vectors,
    ),

    metadata=metadata,

    document_id=document_id,

    filename=display_filename,

    document_type="pdf",
)
    
    # ========================================================
    # COMPLETE
    # ========================================================

    print(
        f"\nStored chunks in Qdrant: "
        f"{inserted_count}"
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "PDF INGESTION COMPLETE"
    )

    print("=" * 70)

    return {
        "document_id":
            document_id,

        "filename":
            display_filename,

        "pages":
            len(documents),

        "chunks":
            inserted_count,
    }