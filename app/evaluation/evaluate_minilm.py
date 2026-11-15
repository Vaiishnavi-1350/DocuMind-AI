
# ============================================================
# DOCUMIND AI - MINILM RETRIEVAL EVALUATION
#
# Positive + Negative Query Evaluation
# No Gemini API calls.
# BGE evaluation remains unchanged.
# ============================================================

import json
from pathlib import Path

from app.rag.retrieval import dense_search_minilm
from app.evaluation.metrics import evaluate_retrieval


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "minilm_dataset.json"
NEGATIVE_DATASET_PATH = BASE_DIR / "minilm_negative_dataset.json"

K = 5
RETRIEVAL_LIMIT = 10

THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40]

MINILM_INGESTION_VERSIONS = {
    "f2dca717-9eee-4c7e-97c8-2c21fed0b7ff":
        "4c660c31-bf2d-434f-8483-3ea759cbf547",

    "5eef3dfe-5876-4953-8688-091ced07d933":
        "8a364888-a162-4257-a1f4-184e6ec2d8ad",
}


# DATASET LOADING

def load_json(path):

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list) or not data:
        raise ValueError(f"Invalid or empty dataset: {path}")

    return data


# COMMON RETRIEVAL

def retrieve_question(question, document_id):

    ingestion_version = MINILM_INGESTION_VERSIONS.get(
        document_id
    )

    if not ingestion_version:
        raise ValueError(
            f"Missing MiniLM ingestion version: {document_id}"
        )

    documents = dense_search_minilm(
        query=question,
        document_id=document_id,
        retrieval_limit=RETRIEVAL_LIMIT,
        ingestion_version=ingestion_version,
    )

    scores = [
        float(document.get("dense_score", 0.0))
        for document in documents
    ]

    return {
        "retrieved_ids": [
            document.get("chunk_id")
            for document in documents
            if document.get("chunk_id")
        ],
        "best_score": max(scores, default=0.0),
    }


# POSITIVE EVALUATION

def evaluate_positive(item):

    relevant_ids = item["relevant_chunk_ids"]

    document_id = relevant_ids[0].rsplit(
        "_chunk_", 1
    )[0]

    retrieved = retrieve_question(
        item["question"], document_id
    )

    metrics = evaluate_retrieval(
        retrieved_ids=retrieved["retrieved_ids"],
        relevant_ids=relevant_ids,
        k=K,
    )

    relevant_rank = next(
        (
            rank
            for rank, chunk_id in enumerate(
                retrieved["retrieved_ids"], start=1
            )
            if chunk_id in relevant_ids
        ),
        None,
    )

    return {
        "id": item["id"],
        "question": item["question"],
        "retrieved_ids": retrieved["retrieved_ids"],
        "relevant_ids": relevant_ids,
        "best_score": retrieved["best_score"],
        "metrics": metrics,
        "relevant_rank": relevant_rank,
    }


# NEGATIVE EVALUATION

def evaluate_negative(item):

    document_id = item["document_id"]

    retrieved = retrieve_question(
        item["question"], document_id
    )

    return {
        "id": item["id"],
        "question": item["question"],
        "document_id": document_id,
        "retrieved_ids": retrieved["retrieved_ids"],
        "best_score": retrieved["best_score"],
    }


# POSITIVE SUMMARY

def calculate_summary(results):

    count = len(results)

    if count == 0:
        raise ValueError("No positive results to summarize.")

    return {
        "precision@5": sum(
            r["metrics"]["precision@5"] for r in results
        ) / count,

        "recall@5": sum(
            r["metrics"]["recall@5"] for r in results
        ) / count,

        "mrr": sum(
            r["metrics"]["reciprocal_rank"] for r in results
        ) / count,

        "hit_rate@5": sum(
            r["relevant_rank"] is not None
            and r["relevant_rank"] <= K
            for r in results
        ) / count,
    }


# THRESHOLD ANALYSIS

def evaluate_thresholds(positive, negative):

    total_positive = len(positive)
    total_negative = len(negative)

    rows = []

    print("\n" + "=" * 105)
    print("MINILM POSITIVE + NEGATIVE THRESHOLD ANALYSIS")
    print("=" * 105)

    print(
        f"{'Threshold':<12}"
        f"{'TP':<8}{'FN':<8}"
        f"{'TN':<8}{'FP':<8}"
        f"{'FPR':<12}{'FNR':<12}"
        f"{'Balanced Acc.':<15}"
    )

    for threshold in THRESHOLDS:

        tp = sum(
            r["best_score"] >= threshold
            for r in positive
        )

        fn = total_positive - tp

        fp = sum(
            r["best_score"] >= threshold
            for r in negative
        )

        tn = total_negative - fp

        tpr = tp / total_positive
        fnr = fn / total_positive
        fpr = fp / total_negative
        tnr = tn / total_negative

        balanced_accuracy = (tpr + tnr) / 2

        row = {
            "threshold": threshold,
            "true_positive": tp,
            "false_negative": fn,
            "true_negative": tn,
            "false_positive": fp,
            "positive_acceptance_rate": tpr,
            "false_rejection_rate": fnr,
            "negative_rejection_rate": tnr,
            "false_acceptance_rate": fpr,
            "balanced_accuracy": balanced_accuracy,
        }

        rows.append(row)

        print(
            f"{threshold:<12.2f}"
            f"{tp:<8}{fn:<8}"
            f"{tn:<8}{fp:<8}"
            f"{fpr:<12.4f}{fnr:<12.4f}"
            f"{balanced_accuracy:<15.4f}"
        )

    return rows


# MAIN

def main():

    print("=" * 70)
    print("DOCUMIND AI - MINILM EVALUATION")
    print("=" * 70)

    positive_dataset = load_json(DATASET_PATH)
    negative_dataset = load_json(NEGATIVE_DATASET_PATH)

    print(f"Positive questions: {len(positive_dataset)}")
    print(f"Negative questions: {len(negative_dataset)}")
    print("Gemini API calls: 0")

    positive_results = []

    for index, item in enumerate(
        positive_dataset, start=1
    ):

        print(
            f"\nPositive [{index}/{len(positive_dataset)}] "
            f"{item['id']}"
        )

        result = evaluate_positive(item)
        positive_results.append(result)

        print(f"Best score: {result['best_score']:.6f}")
        print(f"Relevant rank: {result['relevant_rank']}")

    negative_results = []

    for index, item in enumerate(
        negative_dataset, start=1
    ):

        print(
            f"\nNegative [{index}/{len(negative_dataset)}] "
            f"{item['id']}"
        )

        result = evaluate_negative(item)
        negative_results.append(result)

        print(f"Best score: {result['best_score']:.6f}")

    summary = calculate_summary(positive_results)

    print("\n" + "=" * 70)
    print("MINILM POSITIVE RETRIEVAL METRICS")
    print("=" * 70)

    for name, value in summary.items():
        print(f"{name:<20}: {value:.4f}")

    threshold_results = evaluate_thresholds(
        positive_results,
        negative_results,
    )

    output = {
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "retrieval_method": "dense",
        "gemini_api_calls": 0,
        "positive_question_count": len(positive_results),
        "negative_question_count": len(negative_results),
        "positive_summary": summary,
        "positive_results": positive_results,
        "negative_results": negative_results,
        "threshold_analysis": threshold_results,
    }

    output_path = BASE_DIR / "minilm_threshold_analysis.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=4)

    print("\nCombined analysis saved to:")
    print(output_path)

    print("\nOriginal MiniLM evaluation report was not modified.")
    print("BGE evaluation and production pipeline unchanged.")


if __name__ == "__main__":
    main()
