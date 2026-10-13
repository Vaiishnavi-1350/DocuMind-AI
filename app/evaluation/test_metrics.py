
from metrics import evaluate_retrieval, mean_reciprocal_rank


# Simulated example only — these are not real project results.
retrieved = [
    "doc1_chunk_4",
    "doc1_chunk_2",
    "doc1_chunk_8",
    "doc1_chunk_1",
    "doc1_chunk_5",
]

relevant = [
    "doc1_chunk_2",
    "doc1_chunk_8",
]

metrics = evaluate_retrieval(
    retrieved_ids=retrieved,
    relevant_ids=relevant,
    k=5,
)

print("Retrieval metrics:")
for name, value in metrics.items():
    print(f"{name}: {value:.4f}")


# Two-question example for MRR
benchmark_results = [
    {
        "retrieved_ids": [
            "doc1_chunk_4",
            "doc1_chunk_2",
        ],
        "relevant_ids": ["doc1_chunk_2"],
    },
    {
        "retrieved_ids": [
            "doc1_chunk_8",
            "doc1_chunk_3",
        ],
        "relevant_ids": ["doc1_chunk_8"],
    },
]

print(
    "MRR:",
    round(mean_reciprocal_rank(benchmark_results), 4),
)