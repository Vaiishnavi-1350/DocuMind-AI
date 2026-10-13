
import json
from pathlib import Path

from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents


# Keep this experiment separate from production settings.
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"
REPORT_PATH = BASE_DIR / "reports" / "context_size_experiment.json"

RETRIEVAL_LIMIT = 12
CONTEXT_SIZES = [3, 5, 8]

DOCUMENT_IDS = {
    "Algebraic Identities.pdf":
        "f2dca717-9eee-4c7e-97c8-2c21fed0b7ff",
    "Resume 1.pdf":
        "5eef3dfe-5876-4953-8688-091ced07d933",
}


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    report = {
        "gemini_called": False,
        "retrieval_limit": RETRIEVAL_LIMIT,
        "context_sizes": CONTEXT_SIZES,
        "total_questions": len(dataset),
        "results": [],
        "summary": {},
    }

    print("=" * 65)
    print("DOCUMIND AI - CONTEXT SIZE EXPERIMENT")
    print("=" * 65)
    print(f"Questions: {len(dataset)}")
    print(f"Retrieval candidates: {RETRIEVAL_LIMIT}")
    print(f"Context sizes: {CONTEXT_SIZES}")
    print("Gemini generation: DISABLED")

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
            print(f"Skipping {question_id}: missing required data.")
            continue

        print(f"\n[{index}/{len(dataset)}] {question_id}")

        try:
            # Retrieve once per question; reuse the same candidates
            # for all context sizes to keep the comparison fair.
            candidates = hybrid_search(
                query=question,
                document_id=document_id,
                retrieval_limit=RETRIEVAL_LIMIT,
            )

            row = {
                "id": question_id,
                "question": question,
                "document_filename": filename,
                "relevant_chunk_ids": sorted(relevant_ids),
                "candidate_count": len(candidates),
                "tests": {},
            }

            for size in CONTEXT_SIZES:
                context = rerank_documents(
                    query=question,
                    documents=candidates,
                    top_k=size,
                )

                ranked_ids = [
                    str(doc.get("chunk_id", ""))
                    for doc in context
                ]

                found = relevant_ids.intersection(ranked_ids)

                first_rank = next(
                    (
                        rank
                        for rank, chunk_id in enumerate(ranked_ids, 1)
                        if chunk_id in relevant_ids
                    ),
                    None,
                )

                row["tests"][str(size)] = {
                    "context_count": len(context),
                    "relevant_chunks_found": len(found),
                    "relevant_chunk_count": len(relevant_ids),
                    "all_relevant_chunks_found":
                        relevant_ids.issubset(set(ranked_ids)),
                    "first_relevant_rank": first_rank,
                    "reciprocal_rank":
                        1.0 / first_rank if first_rank else 0.0,
                    "chunk_ids": ranked_ids,
                }

                print(
                    f"  Top {size}: "
                    f"relevant chunks {len(found)}/{len(relevant_ids)}, "
                    f"first relevant rank={first_rank}"
                )

            report["results"].append(row)

        except Exception as exc:
            print(f"  ERROR: {exc}")
            report["results"].append({
                "id": question_id,
                "error": str(exc),
            })

    successful = [
        row for row in report["results"]
        if "tests" in row
    ]

    for size in CONTEXT_SIZES:
        key = str(size)
        tested = [
            row["tests"][key]
            for row in successful
        ]

        count = len(tested)

        report["summary"][key] = {
            "questions_evaluated": count,
            "questions_with_all_relevant_chunks": sum(
                result["all_relevant_chunks_found"]
                for result in tested
            ),
            "mean_reciprocal_rank": (
                sum(result["reciprocal_rank"] for result in tested)
                / count
                if count else None
            ),
        }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print("EXPERIMENT SUMMARY")
    print("=" * 65)

    for size in CONTEXT_SIZES:
        summary = report["summary"][str(size)]
        print(
            f"Top {size}: "
            f"all relevant chunks found="
            f"{summary['questions_with_all_relevant_chunks']}/"
            f"{summary['questions_evaluated']}, "
            f"MRR={summary['mean_reciprocal_rank']}"
        )

    print(f"\nReport saved to: {REPORT_PATH}")
    print("Gemini called: False")


if __name__ == "__main__":
    main()
