"""
DocuMind AI - Isolated Retrieval Candidate Experiment

Compares candidate limits of 5, 10, and 12.
Does not call Gemini.
Does not modify the production RAG pipeline.
Saves results separately from the baseline report.
"""

import json
from datetime import datetime
from pathlib import Path

from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents
from app.evaluation.run_evaluation import (
    DATASET_PATH,
    DOCUMENT_IDS,
    K,
    load_dataset,
    calculate_metrics,
    aggregate_metrics,
)

# Test different numbers of candidates before reranking.
CANDIDATE_LIMITS = [5, 10, 12]

BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = BASE_DIR / "app" / "evaluation" / "reports"
OUTPUT_PATH = REPORT_DIR / "retrieval_candidate_experiment.json"

def run_experiment():
    dataset = load_dataset()
    experiment_results = {}
    print("=" * 65)
    print("DOCUMIND AI - RETRIEVAL CANDIDATE EXPERIMENT")
    print("=" * 65)
    print(f"Questions: {len(dataset)}")
    print(f"Candidate limits: {CANDIDATE_LIMITS}")
    print(f"Evaluation cutoff: {K}")
    print("Gemini generation: DISABLED")

    for candidate_limit in CANDIDATE_LIMITS:
        print(f"\nTesting candidate limit: {candidate_limit}")

        question_results = []
        failures = []

        for index, item in enumerate(dataset, start=1):
            question_id = item.get("id", f"QUESTION_{index}")
            question = item.get("question", "").strip()

            filename = item.get(
                "document_filename",
                item.get("document_name", item.get("filename", "")),
            )

            relevant_ids = set(item.get("relevant_chunk_ids", []))
            document_id = DOCUMENT_IDS.get(filename)

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
                    retrieval_limit=candidate_limit,
                )

                hybrid_metrics = calculate_metrics(
                    candidates[:K], relevant_ids, K
                )

                reranked = rerank_documents(
                    query=question,
                    documents=candidates,
                    top_k=K,
                )

                reranked_metrics = calculate_metrics(reranked, relevant_ids, K)

                question_results.append({
                    "id": question_id,
                    "document_filename": filename,
                    "hybrid_retrieval": hybrid_metrics,
                    "reranked_retrieval": reranked_metrics,
                    "candidate_count": len(candidates),
                    "hybrid_ranked_chunks": [
                        result.get("chunk_id")
                        for result in candidates[:K]
                    ],
                    "reranked_chunks": [
                        result.get("chunk_id")
                        for result in reranked
                    ],
                })

                print(
                    f"  {question_id}: "
                    f"Hybrid MRR="
                    f"{hybrid_metrics['reciprocal_rank']:.4f}, "
                    f"Reranked MRR="
                    f"{reranked_metrics['reciprocal_rank']:.4f}"
                )

            except Exception as exc:
                failures.append({
                    "id": question_id,
                    "reason": str(exc),
                })
                print(f"  ERROR {question_id}: {exc}")

        experiment_results[str(candidate_limit)] = {
            "candidate_limit": candidate_limit,
            "successfully_evaluated": len(question_results),
            "failed_questions": failures,
            "aggregate_metrics": {
                "hybrid_retrieval": aggregate_metrics(
                    question_results, "hybrid_retrieval"
                ),
                "reranked_retrieval": aggregate_metrics(
                    question_results, "reranked_retrieval"
                ),
            },
            "per_question_results": question_results,
        }

        print(
            "  Successfully evaluated:",
            f"{len(question_results)}/{len(dataset)}",
        )

    report = {
        "project": "DocuMind AI",
        "experiment": "retrieval_candidate_limit_comparison",
        "generated_at": datetime.now().astimezone().isoformat(),
        "dataset_path": str(DATASET_PATH),
        "cutoff_k": K,
        "candidate_limits": CANDIDATE_LIMITS,
        "gemini_called": False,
        "results": experiment_results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print("EXPERIMENT SUMMARY")
    print("=" * 65)

    for limit, result in experiment_results.items():
        metrics = result["aggregate_metrics"]

        print(f"\nCandidate limit: {limit}")
        print("Hybrid:", json.dumps(
            metrics["hybrid_retrieval"], indent=2
        ))
        print("Reranked:", json.dumps(
            metrics["reranked_retrieval"], indent=2
        ))

    print(f"\nExperiment report saved to:\n{OUTPUT_PATH}")

    return report


if __name__ == "__main__":
    run_experiment()
