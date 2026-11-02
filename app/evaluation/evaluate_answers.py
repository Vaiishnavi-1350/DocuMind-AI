
"""
DocuMind AI - Phase 9.1
Offline evaluation using saved JSON history and SQLite chat history.

No Gemini calls.
No production RAG pipeline changes.
Unmatched benchmark questions remain pending.
"""

import json
import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EVALUATION_DIR = BASE_DIR / "app" / "evaluation"
DATASET_PATH = EVALUATION_DIR / "dataset.json"
HISTORY_PATH = EVALUATION_DIR / "documind_saved_history.json"

DATABASE_PATH = BASE_DIR / "data" / "documind.db"

REPORT_DIR = EVALUATION_DIR / "reports"
OUTPUT_PATH = REPORT_DIR / "answer_evaluation_report.json"


# Manually reviewed mappings based on genuine saved database answers.
# These are semantic matches, not exact question matches.
MANUAL_MAPPINGS = {
    "RES001": 47,  # Programming languages
    "RES002": 47,  # AI project experience
    "RES003": 47,  # University
    "RES004": 59,  # Tools and platforms
    "RES005": 47,  # Hackathon experience
}


def normalize_text(text):
    """Normalize text for exact question matching."""
    text = str(text or "").lower().strip()

    # Normalize Unicode mathematical superscripts.
    text = (
        text.replace("²", "^2")
            .replace("³", "^3")
            .replace("¹", "^1")
            .replace("⁰", "^0")
    )

    # Normalize multiplication symbols.
    text = text.replace("×", "*")

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    # Normalize spacing around mathematical operators.
    text = re.sub(r"\s*([=+*])\s*", r"\1", text)

    # Remove trailing punctuation.
    text = re.sub(r"[.,;:!?]+$", "", text)

    return text


def load_json_answers():
    """Load answers from the existing JSON history export."""
    answers = {}

    if not HISTORY_PATH.exists():
        print("JSON history export not found. Skipping JSON source.")
        return answers

    with HISTORY_PATH.open("r", encoding="utf-8") as file:
        exported = json.load(file)

    for document in exported.get("documents", []):
        if not document.get("ok"):
            continue

        history_data = document.get("history", {})
        messages = history_data.get("history", [])

        for message in messages:
            question = message.get("question", "")
            answer = message.get("answer", "")

            if question and answer:
                answers[normalize_text(question)] = {
                    "answer": answer,
                    "source": "saved_json_history",
                    "source_record_id": None,
                }

    return answers


def load_database_answers():
    """Read saved chat answers from SQLite without modifying the database."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    answers = {}

    connection = sqlite3.connect(
        f"{DATABASE_PATH.resolve().as_uri()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute("""
            SELECT id, document_id, question, answer, created_at
            FROM chat_messages
            ORDER BY created_at ASC
        """).fetchall()

        for row in rows:
            question = row["question"]
            answer = row["answer"]

            if question and answer:
                # Later records replace earlier duplicates.
                answers[normalize_text(question)] = {
                    "answer": answer,
                    "source": "sqlite_chat_history",
                    "source_record_id": row["id"],
                }

    finally:
        connection.close()

    return answers


def load_manual_answer(connection, message_id):
    """Load one manually reviewed saved answer by database message ID."""
    row = connection.execute("""
        SELECT
            c.id,
            c.question,
            c.answer,
            d.filename
        FROM chat_messages c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE c.id = ?
    """, (message_id,)).fetchone()

    if row is None:
        raise ValueError(
            f"Manual mapping message ID {message_id} was not found."
        )

    if row["filename"] != "Resume 1.pdf":
        raise ValueError(
            f"Message {message_id} does not belong to Resume 1.pdf."
        )

    if not row["answer"]:
        raise ValueError(
            f"Message {message_id} has no saved answer."
        )

    return {
        "answer": row["answer"],
        "source": "sqlite_chat_history",
        "source_record_id": row["id"],
        "original_question": row["question"],
    }


def main():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    json_answers = load_json_answers()
    database_answers = load_database_answers()

    # Database exact matches take priority over JSON history.
    exact_answers = {**json_answers, **database_answers}

    connection = sqlite3.connect(
        f"{DATABASE_PATH.resolve().as_uri()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row

    results = []

    exact_evaluated = 0
    manual_evaluated = 0
    expected_found_count = 0

    try:
        for item in dataset:
            question_id = item["id"]
            question = item["question"]
            expected = item.get("expected_answer", "")

            saved = exact_answers.get(normalize_text(question))
            match_type = None

            # First preference: exact normalized question match.
            if saved:
                match_type = "exact_question_match"

            # Second preference: manually reviewed Resume mapping.
            elif question_id in MANUAL_MAPPINGS:
                saved = load_manual_answer(
                    connection,
                    MANUAL_MAPPINGS[question_id],
                )
                match_type = "manual_semantic_match"

            has_prediction = bool(
                saved and saved["answer"].strip()
            )

            if has_prediction:
                predicted = saved["answer"]

                if match_type == "exact_question_match":
                    exact_evaluated += 1

                    expected_found = (
                        normalize_text(expected)
                        in normalize_text(predicted)
                        if expected else None
                    )

                    if expected_found is True:
                        expected_found_count += 1

                else:
                    manual_evaluated += 1

                    # Manual semantic matches are not automatically
                    # scored using substring containment.
                    expected_found = None

            else:
                predicted = None
                expected_found = None

            results.append({
                "id": question_id,
                "document_name": item.get("document_name"),
                "question": question,
                "expected_answer": expected,
                "predicted_answer": predicted,
                "prediction_source": (
                    saved["source"] if has_prediction else None
                ),
                "source_record_id": (
                    saved.get("source_record_id")
                    if has_prediction else None
                ),
                "original_saved_question": (
                    saved.get("original_question")
                    if has_prediction and match_type == "manual_semantic_match"
                    else None
                ),
                "match_type": match_type,
                "evaluated": has_prediction,
                "expected_answer_found_in_response": expected_found,
                "relevant_chunk_ids": item.get(
                    "relevant_chunk_ids", []
                ),
            })

    finally:
        connection.close()

    evaluated = exact_evaluated + manual_evaluated
    pending = len(dataset) - evaluated

    report = {
        "evaluation": "offline_saved_answer_check",
        "gemini_called": False,
        "production_pipeline_changed": False,

        "total_questions": len(dataset),
        "evaluated_questions": evaluated,
        "pending_questions": pending,

        "exact_question_matches": exact_evaluated,
        "manually_verified_semantic_matches": manual_evaluated,

        "expected_answer_found_count": expected_found_count,
        "expected_answer_found_rate": (
            expected_found_count / exact_evaluated
            if exact_evaluated else None
        ),

        "results": results,

        "limitations": [
            "Only genuine saved JSON and SQLite answers are used.",
            "Exact matches use normalized question text.",
            "Resume semantic mappings were manually reviewed.",
            "Expected-answer containment is a simple check, not "
            "a semantic correctness metric.",
            "Manual semantic matches are not included in the "
            "automatic expected-answer containment rate.",
            "Unmatched questions remain pending, not incorrect.",
            "This script does not modify the production RAG pipeline.",
            "No Gemini API calls are made.",
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 55)
    print("DOCUMIND AI - OFFLINE ANSWER EVALUATION")
    print("=" * 55)

    print("Total questions:", report["total_questions"])
    print("Evaluated:", report["evaluated_questions"])
    print("Pending:", report["pending_questions"])
    print("Exact matches:", report["exact_question_matches"])
    print(
        "Manual semantic matches:",
        report["manually_verified_semantic_matches"],
    )
    print(
        "Expected answer found:",
        report["expected_answer_found_count"],
    )
    print("Gemini called:", report["gemini_called"])
    print("Pipeline changed:", report["production_pipeline_changed"])
    print("Report saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()

