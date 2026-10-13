# ============================================================
# DOCUMIND AI - HYBRID RETRIEVAL
#
# BGE-M3 Dense + Sparse
# +
# Qdrant document filtering
# +
# Reciprocal Rank Fusion (RRF)
# ============================================================

from __future__ import annotations

from typing import Any

from .embeddings import (
    embed_query,
)

from .qdrant import (
    search_dense,
    search_sparse,
)


# ============================================================
# QDRANT POINT → DOCUMENT
# ============================================================

def _point_to_document(
    point: Any,
) -> dict:

    payload = (
        point.payload
        or {}
    )

    return {
        "text": payload.get(
            "text",
            "",
        ),

        "document_id": payload.get(
            "document_id"
        ),

        "filename": payload.get(
            "filename",
            "",
        ),

        "page": payload.get(
            "page"
        ),

        "chunk_id": payload.get(
            "chunk_id"
        ),

        "score": float(
            point.score
            or 0.0
        ),

        "metadata": payload,
    }


# ============================================================
# RECIPROCAL RANK FUSION
# ============================================================

def _rrf_merge(
    dense_results: list[Any],
    sparse_results: list[Any],
    top_k: int = 10,
    rrf_k: int = 60,
) -> list[dict]:
    """
    Combine dense and sparse retrieval results
    using Reciprocal Rank Fusion.

    RRF score:

        1 / (k + rank)
    """

    merged: dict[str, dict] = {}

    # --------------------------------------------------------
    # Create stable chunk key
    # --------------------------------------------------------

    def get_key(
        point: Any,
    ) -> str:

        payload = (
            point.payload
            or {}
        )

        chunk_id = payload.get(
            "chunk_id"
        )

        if chunk_id is not None:
            return str(
                chunk_id
            )

        text = payload.get(
            "text",
            "",
        )

        return text[:500]

    # --------------------------------------------------------
    # Dense results
    # --------------------------------------------------------

    for rank, point in enumerate(
        dense_results,
        start=1,
    ):

        key = get_key(
            point
        )

        if key not in merged:

            merged[key] = (
                _point_to_document(
                    point
                )
            )

            merged[key][
                "dense_score"
            ] = float(
                point.score
                or 0.0
            )

            merged[key][
                "sparse_score"
            ] = 0.0

            merged[key][
                "rrf_score"
            ] = 0.0

        merged[key][
            "rrf_score"
        ] += (
            1.0
            / (
                rrf_k
                + rank
            )
        )

    # --------------------------------------------------------
    # Sparse results
    # --------------------------------------------------------

    for rank, point in enumerate(
        sparse_results,
        start=1,
    ):

        key = get_key(
            point
        )

        if key not in merged:

            merged[key] = (
                _point_to_document(
                    point
                )
            )

            merged[key][
                "dense_score"
            ] = 0.0

            merged[key][
                "sparse_score"
            ] = float(
                point.score
                or 0.0
            )

            merged[key][
                "rrf_score"
            ] = 0.0

        else:

            merged[key][
                "sparse_score"
            ] = float(
                point.score
                or 0.0
            )

        merged[key][
            "rrf_score"
        ] += (
            1.0
            / (
                rrf_k
                + rank
            )
        )

    # --------------------------------------------------------
    # Sort by RRF
    # --------------------------------------------------------

    results = list(
        merged.values()
    )

    results.sort(
        key=lambda item:
            item[
                "rrf_score"
            ],
        reverse=True,
    )

    return results[
        :top_k
    ]


# ============================================================
# HYBRID SEARCH
# ============================================================

def hybrid_search(
    query: str,
    document_id: str,
    retrieval_limit: int = 10,
) -> list[dict]:
    """
    Hybrid document retrieval.

    Flow:

        User question
              ↓
        BGE-M3
              ↓
       ┌──────┴──────┐
       ↓             ↓
     Dense         Sparse
       ↓             ↓
       └──────┬──────┘
              ↓
           Qdrant
              ↓
       document_id filter
              ↓
             RRF
              ↓
       top candidates
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query or not query.strip():
        return []

    if not document_id:
        raise ValueError(
            "document_id is required "
            "for retrieval."
        )

    query = query.strip()

    # --------------------------------------------------------
    # Generate both BGE-M3 query vectors
    # --------------------------------------------------------

    print(
        "\nGenerating BGE-M3 query embeddings..."
    )

    dense_vector, sparse_vector = (
        embed_query(
            query
        )
    )

    # --------------------------------------------------------
    # Dense retrieval
    # --------------------------------------------------------

    print(
        "Running dense retrieval..."
    )

    dense_results = search_dense(
        query_vector=dense_vector,
        document_id=document_id,
        limit=retrieval_limit,
    )

    print(
        f"Dense results: "
        f"{len(dense_results)}"
    )

    # --------------------------------------------------------
    # Sparse retrieval
    # --------------------------------------------------------

    print(
        "Running sparse retrieval..."
    )

    sparse_results = search_sparse(
        query_vector=sparse_vector,
        document_id=document_id,
        limit=retrieval_limit,
    )

    print(
        f"Sparse results: "
        f"{len(sparse_results)}"
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    results = _rrf_merge(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=retrieval_limit,
    )

    print(
        f"Hybrid results after RRF: "
        f"{len(results)}"
    )

    return results