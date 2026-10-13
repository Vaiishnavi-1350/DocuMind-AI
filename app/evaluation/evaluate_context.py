
import json
from pathlib import Path

from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "dataset.json"

REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = REPORT_DIR / "context_evaluation_report.json"

RETRIEVAL_LIMIT = 12
FINAL_TOP_K = 8

DOCUMENT_IDS = {
    "Algebraic Identities.pdf":
        "f2dca717-9eee-4c7e-97c8-2c21fed0b7ff",

    "Resume 1.pdf":
        "5eef3dfe-5876-4953-8688-091ced07d933",
}


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("dataset.json must contain a JSON list.")

    return data


def evaluate_ranked_context(documents, relevant_ids):
    """
    Evaluate the presence and ranking of labelled relevant chunks.
    This is a chunk-label metric, not a semantic answer-accuracy metric.
    """
    ranked_ids = [
        str(doc.get("chunk_id", ""))
        for doc in documents
    ]

    relevant_ids = set(relevant_ids)

    hits = [
        chunk_id for chunk_id in ranked_ids
        if chunk_id in relevant_ids
    ]

    first_relevant_rank = next(
        (
            rank
            for rank, chunk_id in enumerate(ranked_ids, start=1)
            if chunk_id in relevant_ids
        ),
        None,
    )

    return {
        "context_count": len(documents),
        "relevant_chunk_ids": sorted(relevant_ids),
        "retrieved_chunk_ids": ranked_ids,
        "relevant_chunks_found": len(set(hits)),
        "relevant_chunk_count": len(relevant_ids),
        "all_relevant_chunks_found": relevant_ids.issubset(
            set(ranked_ids)
        ),
        "first_relevant_rank": first_relevant_rank,
        "reciprocal_rank": (
            1.0 / first_relevant_rank
            if first_relevant_rank is not None
            else 0.0
        ),
        "context": [
            {
                "rank": rank,
                "chunk_id": doc.get("chunk_id"),
                "filename": doc.get("filename"),
                "page": doc.get("page"),
                "rrf_score": doc.get("rrf_score"),
                "rerank_score": doc.get("rerank_score"),
                "text": str(doc.get("text", "")),
            }
            for rank, doc in enumerate(documents, start=1)
        ],
    }


def main():
    dataset = load_dataset()

    results = []
    skipped = []
    errors = []

    print("=" * 68)
    print("DOCUMIND AI - CONTEXT EVALUATION")
    print("=" * 68)
    print(f"Questions: {len(dataset)}")
    print(f"Retrieval candidates: {RETRIEVAL_LIMIT}")
    print(f"Final context chunks: {FINAL_TOP_K}")
    print("Gemini generation: DISABLED")

    for index, item in enumerate(dataset, start=1):
        question_id = item.get("id", f"QUESTION_{index}")
        question = item.get("question", "").strip()

        filename = item.get(
            "document_filename",
            item.get("document_name", item.get("filename", "")),
        )

        relevant_ids = item.get("relevant_chunk_ids", [])
        document_id = DOCUMENT_IDS.get(filename)

        if not question or not document_id or not relevant_ids:
            skipped.append({
                "id": question_id,
                "filename": filename,
                "reason": "Missing question, document ID, or relevant chunk labels.",
            })
            continue

        print(f"\n[{index}/{len(dataset)}] {question_id}")
        print(f"Document: {filename}")
        print(f"Question: {question}")

        try:
            candidates = hybrid_search(
                query=question,
                document_id=document_id,
                retrieval_limit=RETRIEVAL_LIMIT,
            )

            context = rerank_documents(
                query=question,
                documents=candidates,
                top_k=FINAL_TOP_K,
            )

            evaluation = evaluate_ranked_context(
                context,
                relevant_ids,
            )

            row = {
                "id": question_id,
                "question": question,
                "document_filename": filename,
                "document_id": document_id,
                "expected_answer": item.get("expected_answer"),
                "hybrid_candidate_count": len(candidates),
                "retrieval_limit": RETRIEVAL_LIMIT,
                "final_top_k": FINAL_TOP_K,
                "context_evaluation": evaluation,
            }

            results.append(row)

            print(
                "Relevant chunks found:",
                f"{evaluation['relevant_chunks_found']}/"
                f"{evaluation['relevant_chunk_count']}",
            )
            print(
                "All labelled chunks in context:",
                evaluation["all_relevant_chunks_found"],
            )
            print(
                "First relevant rank:",
                evaluation["first_relevant_rank"],
            )

        except Exception as exc:
            errors.append({
                "id": question_id,
                "filename": filename,
                "error": str(exc),
            })
            print(f"ERROR: {exc}")

    evaluated = len(results)

    summary = {
        "total_questions": len(dataset),
        "evaluated_questions": evaluated,
        "skipped_questions": len(skipped),
        "failed_questions": len(errors),
        "retrieval_limit": RETRIEVAL_LIMIT,
        "final_top_k": FINAL_TOP_K,
        "gemini_called": False,
        "questions_with_all_relevant_chunks": sum(
            row["context_evaluation"]["all_relevant_chunks_found"]
            for row in results
        ),
        "mean_reciprocal_rank": (
            sum(
                row["context_evaluation"]["reciprocal_rank"]
                for row in results
            ) / evaluated
            if evaluated else None
        ),
    }

    report = {
        "summary": summary,
        "results": results,
        "skipped": skipped,
        "errors": errors,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n" + "=" * 68)
    print("CONTEXT EVALUATION SUMMARY")
    print("=" * 68)
    print(json.dumps(summary, indent=2))
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
