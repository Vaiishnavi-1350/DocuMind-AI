import json
from pathlib import Path

from app.evaluation.run_evaluation import DOCUMENT_IDS, load_dataset
from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents

TARGET_IDS = {"ALG003", "RES005"}
LIMIT = 5

dataset = load_dataset()

for item in dataset:
    question_id = item.get("id")
    if question_id not in TARGET_IDS:
        continue

    question = item["question"].strip()
    filename = item.get(
        "document_filename",
        item.get("document_name", item.get("filename", "")),
    )
    document_id = DOCUMENT_IDS.get(filename)
    relevant_ids = set(item.get("relevant_chunk_ids", []))

    candidates = hybrid_search(
        query=question,
        document_id=document_id,
        retrieval_limit=LIMIT,
    )
    reranked = rerank_documents(
        query=question,
        documents=candidates,
        top_k=LIMIT,
    )

    print("\n" + "=" * 75)
    print(f"{question_id}: {question}")
    print("Expected relevant chunk IDs:", sorted(relevant_ids))

    for rank, doc in enumerate(reranked, start=1):
        chunk_id = doc.get("chunk_id")
        text = str(doc.get("text", "")).replace("\n", " ")
        text = text[:350]

        print(f"\nRank: {rank}")
        print("Chunk:", chunk_id)
        print("Relevant:", chunk_id in relevant_ids)
        print("Cross-encoder score:", doc.get("rerank_score"))
        print("Text:", text)

