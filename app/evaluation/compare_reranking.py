"""
Compare hybrid retrieval against cross-encoder reranking.
Read-only evaluation: no Gemini and no production changes.
"""

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
OUTPUT_PATH = REPORT_DIR / "reranking_comparison.json"

CANDIDATE_LIMIT = 5
def run_comparison():
    dataset = load_dataset()
    results = []
    failures = []

    print("=" * 60)
    print("HYBRID VS RERANKED RETRIEVAL")
    print("Candidate limit:", CANDIDATE_LIMIT)
    print("Gemini generation: DISABLED")
    print("=" * 60)

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
            candidates = hybrid_search(
                query=question,
                document_id=document_id,
                retrieval_limit=CANDIDATE_LIMIT,
            )

            hybrid_results = candidates[:K]

            reranked_results = rerank_documents(
                query=question,
                documents=candidates,
                top_k=K,
            )

            hybrid_metrics = calculate_metrics(
                hybrid_results, relevant_ids, K
            )
            reranked_metrics = calculate_metrics(
                reranked_results, relevant_ids, K
            )

            results.append({
                "id": question_id,
                "document_filename": filename,
                "hybrid_retrieval": hybrid_metrics,
                "reranked_retrieval": reranked_metrics,
                "hybrid_chunks": [
                    doc.get("chunk_id") for doc in hybrid_results
                ],
                "reranked_chunks": [
                    doc.get("chunk_id") for doc in reranked_results
                ],
            })

            print(
                f"{question_id}: "
                f"Hybrid RR={hybrid_metrics['reciprocal_rank']:.4f}; "
                f"Reranked RR={reranked_metrics['reciprocal_rank']:.4f}"
            )

        except Exception as exc:
            failures.append({
                "id": question_id,
                "reason": str(exc),
            })
            print(f"ERROR {question_id}: {exc}")

    report = {
        "experiment": "hybrid_vs_cross_encoder",
        "candidate_limit": CANDIDATE_LIMIT,
        "cutoff_k": K,
        "gemini_called": False,
        "successfully_evaluated": len(results),
        "failures": failures,
        "aggregate_metrics": {
            "hybrid_retrieval": aggregate_metrics(
                results, "hybrid_retrieval"
            ),
            "reranked_retrieval": aggregate_metrics(
                results, "reranked_retrieval"
            ),
        },
        "per_question_results": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nAGGREGATE RESULTS")
    print(json.dumps(report["aggregate_metrics"], indent=2))
    print("\nReport saved to:", OUTPUT_PATH)

    return report


if __name__ == "__main__":
    run_comparison()
