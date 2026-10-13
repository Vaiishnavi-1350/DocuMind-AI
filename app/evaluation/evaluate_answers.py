
"""
DocuMind AI - Phase 9.1
Offline evaluation using saved chat history.

No Gemini calls.
No production pipeline changes.
Unmatched benchmark questions remain pending.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
EVALUATION_DIR = BASE_DIR / "app" / "evaluation"
DATASET_PATH = EVALUATION_DIR / "dataset.json"
HISTORY_PATH = EVALUATION_DIR / "documind_saved_history.json"
REPORT_DIR = EVALUATION_DIR / "reports"
OUTPUT_PATH = REPORT_DIR / "answer_evaluation_report.json"


def normalize_text(text):
    """Normalize text for question matching and answer checks."""
    text = str(text or "").lower().strip()
    text = text.replace("²", "^2").replace("³", "^3")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.,;:!?]+$", "", text)
    return text


def load_saved_answers():
    """Load only answers present in the saved history export."""
    if not HISTORY_PATH.exists():
        raise FileNotFoundError(
            f"Saved history export not found: {HISTORY_PATH}\n"
            "Copy documind_saved_history.json into app/evaluation first."
        )

    with HISTORY_PATH.open("r", encoding="utf-8") as file:
        exported = json.load(file)

    answers_by_question = {}

    for document in exported.get("documents", []):
        if not document.get("ok"):
            continue

        history_data = document.get("history", {})
        messages = history_data.get("history", [])

        for message in messages:
            question = message.get("question", "")
            answer = message.get("answer", "")

            if question and answer:
                key = normalize_text(question)
                # Preserve the most recently encountered saved response.
                answers_by_question[key] = answer

    return answers_by_question


def main():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    saved_answers = load_saved_answers()

    results = []
    evaluated = 0
    expected_answer_found_count = 0

    for item in dataset:
        question_id = item["id"]
        question = item["question"]
        expected = item.get("expected_answer", "")

        # Only an exact normalized question match can supply a prediction.
        predicted = saved_answers.get(normalize_text(question), "")
        has_prediction = bool(predicted.strip())

        expected_found = (
            normalize_text(expected) in normalize_text(predicted)
            if has_prediction and expected
            else None
        )

        if has_prediction:
            evaluated += 1
            expected_answer_found_count += int(expected_found)

        results.append({
            "id": question_id,
            "document_name": item.get("document_name"),
            "question": question,
            "expected_answer": expected,
            "predicted_answer": predicted if has_prediction else None,
            "prediction_source": (
                "saved_chat_history" if has_prediction else None
            ),
            "evaluated": has_prediction,
            "expected_answer_found_in_response": expected_found,
            "relevant_chunk_ids": item.get("relevant_chunk_ids", []),
        })

    report = {
        "evaluation": "offline_saved_answer_check",
        "gemini_called": False,
        "production_pipeline_changed": False,
        "total_questions": len(dataset),
        "evaluated_questions": evaluated,
        "pending_questions": len(dataset) - evaluated,
        "expected_answer_found_count": expected_answer_found_count,
        "expected_answer_found_rate": (
            expected_answer_found_count / evaluated
            if evaluated else None
        ),
        "results": results,
        "limitations": [
            "Only questions found in the saved history export are evaluated.",
            "Questions must match after basic text normalization.",
            "Expected-answer containment is a simple check, not a semantic "
            "correctness metric.",
            "Unmatched questions are pending, not incorrect.",
            "This script does not call Gemini or the production RAG pipeline."
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 55)
    print("DOCUMIND AI - OFFLINE SAVED ANSWER EVALUATION")
    print("=" * 55)
    print("Total questions:", report["total_questions"])
    print("Evaluated:", report["evaluated_questions"])
    print("Pending:", report["pending_questions"])
    print("Expected answer found:", expected_answer_found_count)
    print("Gemini called:", report["gemini_called"])
    print("Report saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
