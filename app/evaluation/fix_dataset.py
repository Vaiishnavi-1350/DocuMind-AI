
import json
from pathlib import Path

DATASET_PATH = Path("app/evaluation/dataset.json")

ALGEBRA_ID = "f2dca717-9eee-4c7e-97c8-2c21fed0b7ff"
RESUME_ID = "5eef3dfe-5876-4953-8688-091ced07d933"

# Correct document names and ground-truth chunk IDs.
ground_truth = {
    "ALG001": ( "Algebraic Identities.pdf", f"{ALGEBRA_ID}_chunk_0"),
    "ALG002": ( "Algebraic Identities.pdf", f"{ALGEBRA_ID}_chunk_3"),
    "ALG003": ( "Algebraic Identities.pdf", f"{ALGEBRA_ID}_chunk_4"),
    "ALG004": ( "Algebraic Identities.pdf", f"{ALGEBRA_ID}_chunk_5"),
    "ALG005": ( "Algebraic Identities.pdf", f"{ALGEBRA_ID}_chunk_6"),
    "RES001": ( "Resume 1.pdf", f"{RESUME_ID}_chunk_1"),
    "RES002": ( "Resume 1.pdf", f"{RESUME_ID}_chunk_0"),
    "RES003": ( "Resume 1.pdf", f"{RESUME_ID}_chunk_1"),
    "RES004": ( "Resume 1.pdf", f"{RESUME_ID}_chunk_1"),
    "RES005": ( "Resume 1.pdf", f"{RESUME_ID}_chunk_1"),
}

with DATASET_PATH.open("r", encoding="utf-8") as file:
    raw_data = json.load(file)

if isinstance(raw_data, list):
    questions = raw_data
elif isinstance(raw_data, dict) and isinstance(raw_data.get("questions"), list):
    questions = raw_data["questions"]
else:
    raise ValueError(
        "Unexpected dataset format. Expected a list or a 'questions' list."
    )

# Keep one entry per ID. The last ALG005 entry is the product question.
by_id = {}
for item in questions:
    if item.get("id"):
        by_id[item["id"]] = item

# Keep the ten intended questions in a predictable order.
required_ids = [
    "ALG001", "ALG002", "ALG003", "ALG004", "ALG005",
    "RES001", "RES002", "RES003", "RES004", "RES005",
]

fixed_questions = []

for question_id in required_ids:
    if question_id not in by_id and question_id != "RES005":
        raise ValueError(
            f"Missing question {question_id}. Check dataset.json."
        )

    if question_id == "RES005" and question_id not in by_id:
        # Add the missing hackathon question.
        item = {
            "id": "RES005",
            "question": "What hackathon experience is mentioned in the resume?",
            "expected_answer": "The resume mentions hackathon experience. Verify the exact event name against the resume.",
        }
    else:
        item = by_id[question_id]

    # Replace the duplicate ALG005 question with the verified product question.
    if question_id == "ALG005":
        item["question"] = (
            "Simplify the product (x^3 + 1)(x^6 - x^3 + 1)."
        )
        item["expected_answer"] = "x^9 + 1"

    filename, relevant_chunk_id = ground_truth[question_id]
    item["document_name"] = filename
    item["document_filename"] = filename
    item["relevant_chunk_ids"] = [relevant_chunk_id]

    fixed_questions.append(item)

# Preserve the dataset's original outer structure.
if isinstance(raw_data, list):
    output_data = fixed_questions
else:
    raw_data["questions"] = fixed_questions
    output_data = raw_data

with DATASET_PATH.open("w", encoding="utf-8") as file:
    json.dump(output_data, file, indent=2, ensure_ascii=False)

print("Dataset corrected successfully.")
print(f"Total questions: {len(fixed_questions)}")
for item in fixed_questions:
    print(
        item["id"],
        "|",
        item["document_filename"],
        "|",
        item["relevant_chunk_ids"][0],
    )
