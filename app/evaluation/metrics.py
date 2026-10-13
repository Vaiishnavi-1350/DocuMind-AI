
# ============================================================
# DOCUMIND AI - RETRIEVAL EVALUATION METRICS
#
# Metrics:
#   1. Precision@K
#   2. Recall@K
#   3. Reciprocal Rank
#   4. Mean Reciprocal Rank (MRR)
#
# No Gemini API calls required.
# ============================================================

from __future__ import annotations

from typing import Any, Iterable


def _normalize_ids(
    chunk_ids: Iterable[Any],
) -> list[str]:
    """Convert chunk IDs to clean strings."""

    if isinstance(chunk_ids, str):
        chunk_ids = [chunk_ids]

    normalized = []

    for chunk_id in chunk_ids:
        if chunk_id is None:
            continue

        value = str(chunk_id).strip()

        if value and value not in normalized:
            normalized.append(value)

    return normalized


def precision_at_k(
    retrieved_ids: Iterable[Any],
    relevant_ids: Iterable[Any],
    k: int = 5,
) -> float:
    """
    Precision@K = relevant retrieved chunks in top K / K.

    The denominator is K, even if fewer than K chunks
    were returned.
    """

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    retrieved = _normalize_ids(retrieved_ids)[:k]
    relevant = set(_normalize_ids(relevant_ids))

    if not relevant:
        raise ValueError(
            "relevant_ids cannot be empty for Precision@K."
        )

    relevant_retrieved = sum(
        1 for chunk_id in retrieved
        if chunk_id in relevant
    )

    return relevant_retrieved / k


def recall_at_k(
    retrieved_ids: Iterable[Any],
    relevant_ids: Iterable[Any],
    k: int = 5,
) -> float:
    """
    Recall@K = relevant chunks retrieved in top K /
               all known relevant chunks.
    """

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    retrieved = _normalize_ids(retrieved_ids)[:k]
    relevant = set(_normalize_ids(relevant_ids))

    if not relevant:
        raise ValueError(
            "relevant_ids cannot be empty for Recall@K."
        )

    relevant_retrieved = sum(
        1 for chunk_id in retrieved
        if chunk_id in relevant
    )

    return relevant_retrieved / len(relevant)


def reciprocal_rank(
    retrieved_ids: Iterable[Any],
    relevant_ids: Iterable[Any],
) -> float:
    """
    Reciprocal rank = 1 / rank of the first relevant chunk.

    Returns 0.0 when no relevant chunk is retrieved.
    Ranking positions start at 1.
    """

    retrieved = _normalize_ids(retrieved_ids)
    relevant = set(_normalize_ids(relevant_ids))

    if not relevant:
        raise ValueError(
            "relevant_ids cannot be empty for reciprocal rank."
        )

    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
    query_results: Iterable[dict[str, Any]],
) -> float:
    """
    MRR = mean reciprocal rank across benchmark questions.

    Each result must contain:
        retrieved_ids
        relevant_ids
    """

    results = list(query_results)

    if not results:
        raise ValueError(
            "query_results cannot be empty."
        )

    reciprocal_ranks = []

    for index, result in enumerate(results, start=1):
        if "retrieved_ids" not in result:
            raise ValueError(
                f"Result {index} is missing 'retrieved_ids'."
            )

        if "relevant_ids" not in result:
            raise ValueError(
                f"Result {index} is missing 'relevant_ids'."
            )

        reciprocal_ranks.append(
            reciprocal_rank(
                retrieved_ids=result["retrieved_ids"],
                relevant_ids=result["relevant_ids"],
            )
        )

    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def evaluate_retrieval(
    retrieved_ids: Iterable[Any],
    relevant_ids: Iterable[Any],
    k: int = 5,
) -> dict[str, float]:
    """Calculate retrieval metrics for one question."""

    retrieved = _normalize_ids(retrieved_ids)
    relevant = _normalize_ids(relevant_ids)

    return {
        f"precision@{k}": precision_at_k(
            retrieved, relevant, k
        ),
        f"recall@{k}": recall_at_k(
            retrieved, relevant, k
        ),
        "reciprocal_rank": reciprocal_rank(
            retrieved, relevant
        ),
    }