import json
from pathlib import Path

from app.evaluation.run_evaluation import DOCUMENT_IDS, load_dataset
from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents

BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    BASE_DIR
    / "app"
    / "evaluation"
    / "reports"
    / "reranking_diagnosis.json"
)

TARGET_IDS = {"ALG003", "RES004", "RES005"}
CANDIDATE_LIMIT = 5
def main():
    dataset = load_dataset()
    report = []

    for item in dataset:
        question_id = item.get("id")

        if question_id not in TARGET_IDS:
            continue

        question = item["question"]
        filename = item.get(
            "document_filename",
            item.get("document_name", ""),
        )
        relevant_ids = set(item.get("relevant_chunk_ids", []))
        document_id = DOCUMENT_IDS.get(filename)

        if not document_id:
            print(f"Skipping {question_id}: document ID not found")
            continue

        candidates = hybrid_search(
            query=question,
            document_id=document_id,
            retrieval_limit=CANDIDATE_LIMIT,
        )

        reranked = rerank_documents(
            query=question,
            documents=candidates,
            top_k=CANDIDATE_LIMIT,
        )

        print("\n" + "=" * 75)
        print(f"{question_id}: {question}")
        print("Relevant chunk IDs:", sorted(relevant_ids))

        print("\nHYBRID RANKING")
        for rank, doc in enumerate(candidates, start=1):
            chunk_id = doc.get("chunk_id")
            print(
                f"\nRank {rank} | Relevant: {chunk_id in relevant_ids}"
                f"\nChunk: {chunk_id}"
                f"\nText: {doc.get('text', '')[:700]}"
            )

        print("\nRERANKED RANKING")
        for rank, doc in enumerate(reranked, start=1):
            chunk_id = doc.get("chunk_id")
            print(
                f"\nRank {rank} | Relevant: {chunk_id in relevant_ids}"
                f"\nChunk: {chunk_id}"
                f"\nReranker score: {doc.get('rerank_score')}"
                f"\nText: {doc.get('text', '')[:700]}"
            )

        report.append({
            "id": question_id,
            "question": question,
            "relevant_chunk_ids": sorted(relevant_ids),
            "hybrid": [
                {
                    "chunk_id": d.get("chunk_id"),
                    "text": d.get("text", ""),
                }
                for d in candidates
            ],
            "reranked": [
                {
                    "chunk_id": d.get("chunk_id"),
                    "rerank_score": d.get("rerank_score"),
                    "text": d.get("text", ""),
                }
                for d in reranked
            ],
        })

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\nDiagnostic report saved to:", REPORT_PATH)


if __name__ == "__main__":
    main()
