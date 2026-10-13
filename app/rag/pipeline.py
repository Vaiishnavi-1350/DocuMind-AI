# ============================================================
# DOCUMIND AI - UNIFIED RAG PIPELINE
#
# Question
#    ↓
# Hybrid BGE-M3 Retrieval
#    ↓
# RRF
#    ↓
# Cross-Encoder Reranking
#    ↓
# Relevant Context
#    ↓
# Gemini
#    ↓
# Answer + Relevant Sources
# ============================================================

from __future__ import annotations

from typing import Any

from .retrieval import hybrid_search
from .reranker import rerank_documents
from .gemini import generate_answer


# ============================================================
# CONFIGURATION
# ============================================================

# Number of candidates retrieved from Qdrant
RETRIEVAL_LIMIT = 12

# Number of chunks available for Gemini
FINAL_TOP_K = 8

# ------------------------------------------------------------
# SOURCE FILTER
# ------------------------------------------------------------
# Sources are displayed only when their reranker score is
# sufficiently close to the best matching chunk.
#
# Example:
# Best score = 2.37
# Second score = 1.15
#
# With margin = 1.0:
# 2.37 - 1.0 = 1.37
#
# Therefore only the best chunk is shown as a source.
# ------------------------------------------------------------

SOURCE_SCORE_MARGIN = 1.0

# Maximum number of source chips shown in UI
MAX_DISPLAY_SOURCES = 5


# ============================================================
# EMPTY ANSWER
# ============================================================

NOT_FOUND_MESSAGE = (
    "The information was not found in "
    "the uploaded document."
)


# ============================================================
# SELECT RELEVANT SOURCES
# ============================================================

def _select_relevant_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Select only the most relevant documents for displaying
    as sources in the frontend.

    IMPORTANT:
    This does NOT remove context from Gemini.

    Gemini can still receive multiple chunks, while the UI
    displays only the strongest source chunks.
    """

    if not documents:
        return []

    # --------------------------------------------------------
    # Get reranker scores safely
    # --------------------------------------------------------

    scored_documents: list[tuple[float, dict[str, Any]]] = []

    for document in documents:

        try:
            score = float(
                document.get(
                    "rerank_score",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            score = 0.0

        scored_documents.append(
            (
                score,
                document,
            )
        )

    # --------------------------------------------------------
    # Sort by reranker score
    # --------------------------------------------------------

    scored_documents.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score = scored_documents[0][0]

    # --------------------------------------------------------
    # Keep documents close to the best score
    # --------------------------------------------------------

    minimum_score = (
        best_score
        - SOURCE_SCORE_MARGIN
    )

    selected: list[dict[str, Any]] = []

    seen_sources: set[tuple[Any, Any]] = set()

    for score, document in scored_documents:

        if score < minimum_score:
            continue

        filename = document.get(
            "filename",
            "",
        )

        page = document.get(
            "page",
        )

        source_key = (
            filename,
            page,
        )

        # ----------------------------------------------------
        # Avoid showing the same page multiple times
        # ----------------------------------------------------

        if source_key in seen_sources:
            continue

        seen_sources.add(
            source_key
        )

        selected.append(
            document
        )

        if len(selected) >= MAX_DISPLAY_SOURCES:
            break

    # --------------------------------------------------------
    # Always return at least the best source
    # --------------------------------------------------------

    if not selected:
        selected.append(
            scored_documents[0][1]
        )

    return selected


# ============================================================
# BUILD SOURCES
# ============================================================

def _build_sources(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert selected relevant documents into the source
    format returned to the frontend.
    """

    # --------------------------------------------------------
    # Filter sources first
    # --------------------------------------------------------

    relevant_documents = (
        _select_relevant_sources(
            documents
        )
    )

    sources: list[dict[str, Any]] = []

    for rank, document in enumerate(
        relevant_documents,
        start=1,
    ):

        sources.append(
            {
                "rank": rank,

                "filename": document.get(
                    "filename",
                    "",
                ),

                "page": document.get(
                    "page",
                ),

                "chunk_id": document.get(
                    "chunk_id",
                ),

                "rerank_score": document.get(
                    "rerank_score",
                    0.0,
                ),

                "retrieval_score": document.get(
                    "rrf_score",
                    0.0,
                ),

                "dense_score": document.get(
                    "dense_score",
                    0.0,
                ),

                "sparse_score": document.get(
                    "sparse_score",
                    0.0,
                ),

                "text": document.get(
                    "text",
                    "",
                ),
            }
        )

    return sources


# ============================================================
# MAIN RAG FUNCTION
# ============================================================

def ask_question(
    question: str,
    document_id: str,
    retrieval_limit: int = RETRIEVAL_LIMIT,
    final_top_k: int = FINAL_TOP_K,
) -> dict[str, Any]:
    """
    Complete DocuMind AI RAG pipeline.

    Architecture:

        Question
            ↓
        BGE-M3
            ↓
        Dense + Sparse Qdrant retrieval
            ↓
        Reciprocal Rank Fusion
            ↓
        Cross-Encoder reranking
            ↓
        Relevant context
            ↓
        Gemini
            ↓
        Answer + relevant sources
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    if not question or not question.strip():

        raise ValueError(
            "Question cannot be empty."
        )

    if not document_id or not document_id.strip():

        raise ValueError(
            "document_id is required."
        )

    question = question.strip()

    document_id = document_id.strip()

    retrieval_limit = max(
        1,
        int(retrieval_limit),
    )

    final_top_k = max(
        1,
        int(final_top_k),
    )

    # ========================================================
    # LOGGING
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "DOCUMIND AI - UNIFIED RAG PIPELINE"
    )

    print("=" * 70)

    print(
        f"Document ID : {document_id}"
    )

    print(
        f"Question    : {question}"
    )

    print(
        f"Retrieval   : top {retrieval_limit}"
    )

    print(
        f"Final       : top {final_top_k}"
    )

    # ========================================================
    # STEP 1 - HYBRID RETRIEVAL
    # ========================================================

    print(
        "\n[1/4] Hybrid BGE-M3 retrieval..."
    )

    retrieved_documents = hybrid_search(
        query=question,

        document_id=document_id,

        retrieval_limit=retrieval_limit,
    )

    print(
        f"Retrieved candidates: "
        f"{len(retrieved_documents)}"
    )

    # --------------------------------------------------------
    # No retrieval results
    # --------------------------------------------------------

    if not retrieved_documents:

        print(
            "No document chunks were retrieved."
        )

        return {
            "answer": NOT_FOUND_MESSAGE,

            "sources": [],

            "document_id": document_id,

            "retrieved_count": 0,

            "context_count": 0,
        }

    # ========================================================
    # STEP 2 - CROSS-ENCODER RERANKING
    # ========================================================

    print(
        "\n[2/4] Cross-Encoder reranking..."
    )

    reranked_documents = rerank_documents(
        query=question,

        documents=retrieved_documents,

        top_k=final_top_k,
    )

    # ========================================================
    # DEBUG - RERANKED DOCUMENTS
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "DEBUG - RERANKED DOCUMENTS"
    )

    print("=" * 70)

    for i, doc in enumerate(
        reranked_documents,
        start=1,
    ):

        print(
            f"\n--- DOCUMENT {i} ---"
        )

        print(
            "Filename:",
            doc.get(
                "filename"
            ),
        )

        print(
            "Page:",
            doc.get(
                "page"
            ),
        )

        print(
            "Chunk:",
            doc.get(
                "chunk_id"
            ),
        )

        print(
            "RRF score:",
            doc.get(
                "rrf_score"
            ),
        )

        print(
            "Rerank score:",
            doc.get(
                "rerank_score"
            ),
        )

        print(
            "TEXT:"
        )

        print(
            doc.get(
                "text",
                "",
            )
        )

        print(
            "-" * 70
        )

    print(
        f"\nFinal context chunks: "
        f"{len(reranked_documents)}"
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not reranked_documents:

        print(
            "Reranker returned no usable chunks."
        )

        return {
            "answer": NOT_FOUND_MESSAGE,

            "sources": [],

            "document_id": document_id,

            "retrieved_count": len(
                retrieved_documents
            ),

            "context_count": 0,
        }

    # ========================================================
    # DEBUG CONTEXT
    # ========================================================

    print(
        "\n" + "-" * 70
    )

    print(
        "FINAL RERANKED CONTEXT"
    )

    print(
        "-" * 70
    )

    for index, document in enumerate(
        reranked_documents,
        start=1,
    ):

        print(
            f"\nRank {index}"
        )

        print(
            "Filename:",
            document.get(
                "filename",
                "",
            ),
        )

        print(
            "Page:",
            document.get(
                "page",
            ),
        )

        print(
            "Chunk:",
            document.get(
                "chunk_id",
            ),
        )

        try:

            rrf_score = float(
                document.get(
                    "rrf_score",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            rrf_score = 0.0

        try:

            rerank_score = float(
                document.get(
                    "rerank_score",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            rerank_score = 0.0

        print(
            "RRF score:",
            round(
                rrf_score,
                6,
            ),
        )

        print(
            "Rerank score:",
            round(
                rerank_score,
                6,
            ),
        )

        text = str(
            document.get(
                "text",
                "",
            )
        )

        print(
            "Text:",
            text[:500],
        )

    # ========================================================
    # STEP 3 - GEMINI
    # ========================================================

    print(
        "\n[3/4] Generating grounded Gemini answer..."
    )

    answer = generate_answer(
    question=question,
    documents=reranked_documents,
    )

    # ========================================================
    # SAFETY CHECK - GEMINI ANSWER
    # ========================================================

    if answer is None:
        raise RuntimeError(
            "Gemini returned no answer."
        )

    answer = str(answer).strip()

    if not answer:
        raise RuntimeError(
            "Gemini returned an empty answer."
        )

    # ========================================================
    # NO-SOURCE CASE
    # ========================================================
    # If Gemini determines that the answer is not present
    # in the uploaded document, do not display unrelated
    # retrieved pages as sources.
    # ========================================================

    if answer.lower().strip().rstrip(".") == (
        NOT_FOUND_MESSAGE.lower().strip().rstrip(".")
    ):

        print(
            "\nAnswer is NOT grounded in the uploaded document."
        )

        print(
            "Hiding retrieved sources from the UI."
        )

        return {
            "answer": answer,
            "sources": [],
            "document_id": document_id,
            "retrieved_count": len(
                retrieved_documents
            ),
            "context_count": len(
                reranked_documents
            ),
        }

    # ========================================================
    # STEP 4 - SOURCES
    # ========================================================

    print( "\n[4/4] Preparing relevant sources..." )
    sources = _build_sources(reranked_documents)
    print("Displayed sources:")

    for source in sources:

        print(
            f"  Page {source.get('page')} "
            f"| score={source.get('rerank_score')}"
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    result = {
        "answer": answer,

        "sources": sources,

        "document_id": document_id,

        "retrieved_count": len(retrieved_documents),

        "context_count": len( reranked_documents),
    }
    print("\n" + "=" * 70)
    print("RAG PIPELINE COMPLETE")
    print("=" * 70)

    return result