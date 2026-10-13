
"""
DocuMind AI - Standalone Retrieval Evaluation

Evaluates:
1. Hybrid retrieval (Dense + Sparse + RRF)
2. Cross-encoder reranking
3. Precision@5, Recall@5, Reciprocal Rank and MRR

Does not call Gemini or modify the production RAG pipeline.
"""

import json
from datetime import datetime
from pathlib import Path

from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "app" / "evaluation" / "dataset.json"
REPORT_DIR = BASE_DIR / "app" / "evaluation" / "reports"

K = 5
RETRIEVAL_LIMIT = 10

DOCUMENT_IDS = {
    "Algebraic Identities.pdf":
        "f2dca717-9eee-4c7e-97c8-2c21fed0b7ff",
    "Resume 1.pdf":
        "5eef3dfe-5876-4953-8688-091ced07d933",
}


# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------

def precision_at_k(results, relevant_ids, k=5):
    """Fraction of the top-k results that are relevant."""
    if k <= 0:
        return 0.0

    retrieved = [
        item.get("chunk_id")
        for item in results[:k]
        if item.get("chunk_id") is not None
    ]

    hits = sum(
        1 for chunk_id in retrieved
        if chunk_id in relevant_ids
    )

    # Standard Precision@K uses K as the denominator,
    # even when fewer than K results are returned.
    return hits / k


def recall_at_k(results, relevant_ids, k=5):
    """Fraction of known relevant chunks retrieved in top-k."""
    if not relevant_ids:
        return 0.0

    retrieved_ids = {
        item.get("chunk_id")
        for item in results[:k]
        if item.get("chunk_id") is not None
    }

    hits = len(retrieved_ids.intersection(relevant_ids))
    return hits / len(relevant_ids)


def reciprocal_rank(results, relevant_ids):
    """Reciprocal rank of the first relevant result."""
    for rank, item in enumerate(results, start=1):
        if item.get("chunk_id") in relevant_ids:
            return 1.0 / rank

    return 0.0


def calculate_metrics(results, relevant_ids, k=5):
    return {
        f"precision@{k}": round(
            precision_at_k(results, relevant_ids, k), 4
        ),
        f"recall@{k}": round(
            recall_at_k(results, relevant_ids, k), 4
        ),
        "reciprocal_rank": round(
            reciprocal_rank(results, relevant_ids), 4
        ),
    }


def aggregate_metrics(question_results, stage):
    """Calculate mean metrics across benchmark questions."""
    if not question_results:
        return {}

    metric_names = [
        f"precision@{K}",
        f"recall@{K}",
        "reciprocal_rank",
    ]

    summary = {}

    for metric in metric_names:
        values = [
            row[stage][metric]
            for row in question_results
        ]

        summary[metric] = round(
            sum(values) / len(values), 4
        )

    summary["mrr"] = summary.pop("reciprocal_rank")
    summary["evaluated_questions"] = len(question_results)

    return summary


# ---------------------------------------------------------
# DATASET
# ---------------------------------------------------------

def load_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    # Support either a JSON list or {"questions": [...]}.
    if isinstance(dataset, dict):
        dataset = dataset.get("questions", [])

    if not isinstance(dataset, list) or not dataset:
        raise ValueError(
            "dataset.json must contain a non-empty list of questions."
        )

    return dataset


# ---------------------------------------------------------
# RESULT FORMATTING
# ---------------------------------------------------------

def describe_results(results):
    """Keep the actual ranking and scores in the report."""
    described = []

    for rank, item in enumerate(results, start=1):
        described.append({
            "rank": rank,
            "chunk_id": item.get("chunk_id"),
            "document_id": item.get("document_id"),
            "filename": item.get("filename"),
            "page": item.get("page"),
            "score": item.get("score"),
            "rrf_score": item.get("rrf_score"),
            "rerank_score": item.get("rerank_score"),
            "text_preview": str(item.get("text", ""))[:300],
        })

    return described


# ---------------------------------------------------------
# EVALUATION
# ---------------------------------------------------------

def run_evaluation():
    dataset = load_dataset()
    question_results = []
    skipped_questions = []

    print("\n" + "=" * 72)
    print("DOCUMIND AI - RETRIEVAL EVALUATION")
    print("=" * 72)
    print(f"Dataset: {DATASET_PATH}")
    print(f"Questions loaded: {len(dataset)}")
    print(f"Retrieval candidates: {RETRIEVAL_LIMIT}")
    print(f"Evaluation cutoff: {K}")
    print("Gemini generation: DISABLED")

    for index, item in enumerate(dataset, start=1):
        question_id = item.get("id", f"QUESTION_{index}")
        question = item.get("question", "").strip()
        filename = item.get(
        "document_filename",
        item.get("document_name", item.get("filename", ""))
        )
        relevant_list = item.get("relevant_chunk_ids", [])

        document_id = DOCUMENT_IDS.get(filename)

        if not question or not document_id or not relevant_list:
            reason = (
                "Missing question, unknown document filename, "
                "or empty relevant_chunk_ids."
            )
            skipped_questions.append({
                "id": question_id,
                "reason": reason,
                "filename": filename,
            })
            print(f"\n[{question_id}] SKIPPED: {reason}")
            continue

        relevant_ids = set(relevant_list)

        print(f"\n[{index}/{len(dataset)}] {question_id}")
        print(f"Document: {filename}")
        print(f"Question: {question}")

        try:
            # Stage 1: Existing hybrid retrieval.
            candidates = hybrid_search(
                query=question,
                document_id=document_id,
                retrieval_limit=RETRIEVAL_LIMIT,
            )

            if not candidates:
                print("WARNING: Hybrid retrieval returned no results.")

            # Evaluate the top K of the hybrid ranking.
            hybrid_top_k = candidates[:K]

            hybrid_metrics = calculate_metrics(
                hybrid_top_k, relevant_ids, K
            )

            # Stage 2: Rerank the same candidate set.
            reranked = rerank_documents(
                query=question,
                documents=candidates,
                top_k=K,
            )

            reranked_metrics = calculate_metrics(
                reranked, relevant_ids, K
            )

            row = {
                "id": question_id,
                "question": question,
                "document_filename": filename,
                "document_id": document_id,
                "relevant_chunk_ids": sorted(relevant_ids),
                "hybrid_retrieval": {
                    **hybrid_metrics,
                    "results": describe_results(hybrid_top_k),
                },
                "reranked_retrieval": {
                    **reranked_metrics,
                    "results": describe_results(reranked),
                },
            }

            question_results.append(row)

            print(
                f"Hybrid:   P@{K}={hybrid_metrics[f'precision@{K}']:.4f} "
                f"R@{K}={hybrid_metrics[f'recall@{K}']:.4f} "
                f"RR={hybrid_metrics['reciprocal_rank']:.4f}"
            )
            print(
                f"Reranked: P@{K}={reranked_metrics[f'precision@{K}']:.4f} "
                f"R@{K}={reranked_metrics[f'recall@{K}']:.4f} "
                f"RR={reranked_metrics['reciprocal_rank']:.4f}"
            )

        except Exception as exc:
            # Continue with other questions, but report failures.
            print(f"ERROR evaluating {question_id}: {exc}")
            skipped_questions.append({
                "id": question_id,
                "reason": str(exc),
                "filename": filename,
            })

    # -----------------------------------------------------
    # AGGREGATE AND SAVE
    # -----------------------------------------------------

    report = {
        "project": "DocuMind AI",
        "evaluation_type": "retrieval_only",
        "generated_at": datetime.now().astimezone().isoformat(),
        "dataset_path": str(DATASET_PATH),
        "cutoff_k": K,
        "retrieval_candidate_limit": RETRIEVAL_LIMIT,
        "gemini_called": False,
        "total_dataset_questions": len(dataset),
        "successfully_evaluated": len(question_results),
        "skipped_or_failed": skipped_questions,
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

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "retrieval_evaluation_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n" + "=" * 72)
    print("EVALUATION SUMMARY")
    print("=" * 72)

    print(json.dumps(report["aggregate_metrics"], indent=2))
    print(f"\nSuccessfully evaluated: {len(question_results)}/{len(dataset)}")
    print(f"Skipped or failed: {len(skipped_questions)}")
    print(f"Report saved to: {report_path}")

    if skipped_questions:
        print("\nQuestions requiring attention:")
        for skipped in skipped_questions:
            print(f"- {skipped['id']}: {skipped['reason']}")

    return report


if __name__ == "__main__":
    run_evaluation()
