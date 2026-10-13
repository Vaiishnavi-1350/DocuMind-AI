# ============================================================
# DOCUMIND AI - CROSS-ENCODER RERANKER
#
# Hybrid retrieval candidates
#          ↓
# Cross Encoder
#          ↓
# Reranked top-k chunks
# ============================================================

from __future__ import annotations

from typing import Any

from sentence_transformers import CrossEncoder


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = (
    "cross-encoder/ms-marco-MiniLM-L-12-v2"
)

RERANKER_MAX_LENGTH = 512


# ============================================================
# MODEL
# ============================================================

_model: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    """
    Load the Cross-Encoder only once.
    """

    global _model

    if _model is None:

        print("\n" + "=" * 70)
        print(
            f"Loading reranker: {MODEL_NAME}"
        )
        print("=" * 70)

        _model = CrossEncoder(
            MODEL_NAME,
            max_length=RERANKER_MAX_LENGTH,
        )

        print(
            "Reranker loaded successfully."
        )

    return _model


# ============================================================
# RERANK DOCUMENTS
# ============================================================

def rerank_documents(
    query: str,
    documents: list[dict[str, Any]],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Rerank hybrid-retrieval candidates.

    Input:

        query
        retrieved documents

    Output:

        top-k documents sorted by
        Cross-Encoder score.
    """

    if not query or not query.strip():
        return []

    if not documents:
        return []

    query = query.strip()

    top_k = max(
        1,
        int(top_k),
    )

    model = get_reranker()

    # --------------------------------------------------------
    # Prepare query-document pairs
    # --------------------------------------------------------

    pairs = []

    valid_documents = []

    for document in documents:

        text = str(
            document.get(
                "text",
                "",
            )
        ).strip()

        if not text:
            continue

        pairs.append(
            [
                query,
                text,
            ]
        )

        valid_documents.append(
            document
        )

    if not pairs:
        return []

    # --------------------------------------------------------
    # Cross-Encoder prediction
    # --------------------------------------------------------

    print(
        f"Reranking {len(pairs)} "
        f"candidate chunks..."
    )

    scores = model.predict(
        pairs,
        show_progress_bar=False,
    )

    # --------------------------------------------------------
    # Attach reranker scores
    # --------------------------------------------------------

    reranked = []

    for document, score in zip(
        valid_documents,
        scores,
    ):

        item = dict(
            document
        )

        try:
            item["rerank_score"] = float(
                score
            )
        except (
            TypeError,
            ValueError,
        ):

            item["rerank_score"] = 0.0

        reranked.append(
            item
        )

    # --------------------------------------------------------
    # Sort highest score first
    # --------------------------------------------------------

    reranked.sort(
        key=lambda item:
            item.get(
                "rerank_score",
                0.0,
            ),
        reverse=True,
    )

    final_results = reranked[
        :top_k
    ]

    print(
        f"Reranking complete. "
        f"Selected {len(final_results)} chunks."
    )

    return final_results