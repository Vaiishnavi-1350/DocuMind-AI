import json
from pathlib import Path

report_path = (
    Path(__file__).resolve().parent
    / "reports"
    / "retrieval_candidate_experiment.json"
)

with report_path.open("r", encoding="utf-8") as file:
    report = json.load(file)

target_ids = {"ALG003", "RES004", "RES005"}

for limit, experiment in report["results"].items():
    print("\n" + "=" * 60)
    print(f"CANDIDATE LIMIT: {limit}")
    print("=" * 60)

    for question in experiment["per_question_results"]:
        if question["id"] in target_ids:
            print(f"\nQuestion: {question['id']}")
            print(f"Document: {question['document_filename']}")

            print("\nHybrid ranking:")
            for rank, chunk_id in enumerate(
                question["hybrid_ranked_chunks"], start=1
            ):
                print(f"  Rank {rank}: {chunk_id}")

            print("\nReranked ranking:")
            for rank, chunk_id in enumerate(
                question["reranked_chunks"], start=1
            ):
                print(f"  Rank {rank}: {chunk_id}")
