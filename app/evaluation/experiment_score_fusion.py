import json
from pathlib import Path

from app.evaluation.run_evaluation import (
    K,
    DOCUMENT_IDS,
    load_dataset,
    calculate_metrics,
    aggregate_metrics,
)
from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents

BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = BASE_DIR / "app" / "evaluation" / "reports"
OUTPUT_PATH = REPORT_DIR / "score_fusion_experiment.json"

CANDIDATE_LIMIT = 5

# Test a small contribution from hybrid rank while preserving
# the cross-encoder's real scores as the primary ranking signal.
HYBRID_WEIGHT = 0.10


def normalize_scores(documents):
    """Min-max normalize cross-encoder scores to [0, 1]."""
    scores = [float(d.get("rerank_score", 0.0)) for d in documents]

    if not scores:
        return {}

    low = min(scores)
    high = max(scores)

    if high == low:
        return {d.get("chunk_id"): 1.0 for d in documents}

    return {
        d.get("chunk_id"): (score - low) / (high - low)
        for d, score in zip(documents, scores)
    }


def score_fusion(hybrid, reranked, top_k):
    """Combine normalized cross-encoder scores and hybrid rank."""
    hybrid_ranks = {
        d.get("chunk_id"): rank
        for rank, d in enumerate(hybrid, start=1)
        if d.get("chunk_id")
    }

    normalized = normalize_scores(reranked)
    max_rank = max(len(hybrid), 1)
    combined = []

    for doc in reranked:
        chunk_id = doc.get("chunk_id")
        if not chunk_id:
            continue

        hybrid_rank = hybrid_ranks.get(chunk_id, max_rank + 1)
        hybrid_score = 1.0 - ((hybrid_rank - 1) / max(max_rank - 1, 1))
        cross_score = normalized.get(chunk_id, 0.0)

        final_score = (
            (1.0 - HYBRID_WEIGHT) * cross_score
            + HYBRID_WEIGHT * hybrid_score
        )

        item = dict(doc)
        item["hybrid_rank"] = hybrid_ranks.get(chunk_id)
        item["normalized_cross_encoder_score"] = cross_score
        item["hybrid_rank_score"] = hybrid_score
        item["combined_score"] = final_score
        combined.append(item)

    combined.sort(
        key=lambda d: d["combined_score"],
        reverse=True,
    )

    return combined[:top_k]


def run_experiment():
    dataset = load_dataset()
    results = []
    failures = []

    print("=" * 65)
    print("DOCUMIND AI - CROSS-ENCODER SCORE + HYBRID RANK EXPERIMENT")
    print("Candidate limit:", CANDIDATE_LIMIT)
    print("Hybrid weight:", HYBRID_WEIGHT)
    print("Gemini: DISABLED")
    print("=" * 65)

    for item in dataset:
        question_id = item.get("id", "UNKNOWN")
        question = item.get("question", "").strip()
        filename = item.get(
            "document_filename",
            item.get("document_name", item.get("filename", "")),
        )
        document_id = DOCUMENT_IDS.get(filename)
        relevant_ids = set(item.get("relevant_chunk_ids", []))

        if not question or not document_id or not relevant_ids:
            failures.append({
                "id": question_id,
                "reason": "Missing question, document ID, or relevant chunks",
            })
            continue

        try:
            hybrid = hybrid_search(
                query=question,
                document_id=document_id,
                retrieval_limit=CANDIDATE_LIMIT,
            )[:CANDIDATE_LIMIT]

            reranked = rerank_documents(
                query=question,
                documents=hybrid,
                top_k=CANDIDATE_LIMIT,
            )

            fused = score_fusion(hybrid, reranked, K)

            hybrid_metrics = calculate_metrics(hybrid[:K], relevant_ids, K)
            cross_metrics = calculate_metrics(reranked[:K], relevant_ids, K)
            fusion_metrics = calculate_metrics(fused, relevant_ids, K)

            results.append({
                "id": question_id,
                "document_filename": filename,
                "hybrid_retrieval": hybrid_metrics,
                "cross_encoder": cross_metrics,
                "score_fusion": fusion_metrics,
                "relevant_chunk_ids": sorted(relevant_ids),
                "score_fusion_chunks": [
                    {
                        "chunk_id": d.get("chunk_id"),
                        "hybrid_rank": d.get("hybrid_rank"),
                        "rerank_score": d.get("rerank_score"),
                        "combined_score": d.get("combined_score"),
                    }
                    for d in fused
                ],
            })

            print(
                f"{question_id}: "
                f"Hybrid RR={hybrid_metrics['reciprocal_rank']:.3f} | "
                f"Cross RR={cross_metrics['reciprocal_rank']:.3f} | "
                f"Score Fusion RR={fusion_metrics['reciprocal_rank']:.3f}"
            )

        except Exception as exc:
            failures.append({"id": question_id, "reason": str(exc)})
            print(f"ERROR {question_id}: {exc}")

    report = {
        "experiment": "cross_encoder_score_hybrid_rank_fusion",
        "candidate_limit": CANDIDATE_LIMIT,
        "cutoff_k": K,
        "hybrid_weight": HYBRID_WEIGHT,
        "gemini_called": False,
        "successfully_evaluated": len(results),
        "failures": failures,
        "aggregate_metrics": {
            "hybrid_retrieval": aggregate_metrics(results, "hybrid_retrieval"),
            "cross_encoder": aggregate_metrics(results, "cross_encoder"),
            "score_fusion": aggregate_metrics(results, "score_fusion"),
        },
        "per_question_results": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nAGGREGATE METRICS")
    print(json.dumps(report["aggregate_metrics"], indent=2))
    print("\nQuestions evaluated:", len(results))
    print("Failures:", len(failures))
    print("Gemini called: False")
    print("Report saved to:", OUTPUT_PATH)

    return report


if __name__ == "__main__":
    run_experiment()
