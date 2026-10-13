
import json
from pathlib import Path

from app.rag.qdrant import (
    client,
    COLLECTION_NAME,
    build_document_filter,
)

DATASET_PATH = Path("app/evaluation/dataset.json")


def load_dataset():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("questions", "data", "examples"):
            if isinstance(data.get(key), list):
                return data[key]

    raise ValueError("Could not find questions in dataset.json.")


def split_ground_truth_id(value):
    """Convert UUID_chunk_N into (document UUID, chunk_N)."""
    if not isinstance(value, str) or "_chunk_" not in value:
        return None, None

    document_id, number = value.rsplit("_chunk_", 1)

    if not document_id or not number.isdigit():
        return None, None

    return document_id, f"chunk_{number}"


def fetch_all_document_chunks(document_id):
    """Read document chunks from Qdrant without modifying them."""
    chunks = {}
    offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=build_document_filter(document_id),
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            raw_chunk_id = payload.get("chunk_id", "")

            if not raw_chunk_id:
                continue

            # Support either "chunk_0" or a full UUID_chunk_0 ID.
            if raw_chunk_id.startswith(document_id + "_chunk_"):
                full_chunk_id = raw_chunk_id
            elif raw_chunk_id.startswith("chunk_"):
                full_chunk_id = f"{document_id}_{raw_chunk_id}"
            else:
                full_chunk_id = f"{document_id}_{raw_chunk_id}"

            chunks[full_chunk_id] = {
                "raw_chunk_id": raw_chunk_id,
                "filename": payload.get("filename", ""),
                "page": payload.get("page"),
                "text": payload.get("text", ""),
            }

        if next_offset is None:
            break

        offset = next_offset

    return chunks


def main():
    if not client.collection_exists(COLLECTION_NAME):
        print(f"Qdrant collection not found: {COLLECTION_NAME}")
        return

    questions = load_dataset()

    document_ids = set()
    invalid_ids = []

    for item in questions:
        for chunk_id in item.get("relevant_chunk_ids", []):
            document_id, _ = split_ground_truth_id(chunk_id)

            if document_id:
                document_ids.add(document_id)
            else:
                invalid_ids.append((item.get("id", "UNKNOWN"), chunk_id))

    if not document_ids:
        print("No document IDs could be extracted from relevant_chunk_ids.")
        print("Check the chunk ID format in dataset.json.")
        return

    print("=" * 90)
    print("DOCUMIND AI - GROUND-TRUTH VALIDATION")
    print("READ-ONLY: dataset, Qdrant, and reports will not be modified.")
    print("=" * 90)

    all_chunks = {}

    for document_id in sorted(document_ids):
        chunks = fetch_all_document_chunks(document_id)
        all_chunks[document_id] = chunks

        names = sorted({
            item.get("document_filename", item.get("document_name", ""))
            for item in questions
            if any(
                split_ground_truth_id(cid)[0] == document_id
                for cid in item.get("relevant_chunk_ids", [])
            )
        })

        print(f"\n\nDOCUMENT: {', '.join(names)}")
        print(f"Document ID: {document_id}")
        print(f"Stored chunks found: {len(chunks)}")

        for full_chunk_id, chunk in sorted(chunks.items()):
            print("\n" + "-" * 90)
            print(f"Chunk ID: {full_chunk_id}")
            print(f"Raw payload chunk ID: {chunk['raw_chunk_id']}")
            print(f"Page: {chunk['page']}")
            print("FULL CHUNK TEXT:")
            print(chunk["text"] or "[EMPTY TEXT]")

        if not chunks:
            print("WARNING: No chunks found for this document ID.")

    print("\n\n" + "=" * 90)
    print("QUESTION-TO-GROUND-TRUTH MAPPING")
    print("=" * 90)

    for item in questions:
        print(f"\n{item.get('id', 'UNKNOWN')}: {item.get('question', '')}")
        print(f"Expected answer: {item.get('expected_answer', '[MISSING]')}")

        for expected_id in item.get("relevant_chunk_ids", []):
            document_id, _ = split_ground_truth_id(expected_id)

            if not document_id:
                print(f"  INVALID ID FORMAT: {expected_id}")
                continue

            stored = all_chunks.get(document_id, {})

            if expected_id in stored:
                print(f"  FOUND: {expected_id}")
            else:
                print(f"  NOT FOUND: {expected_id}")

    if invalid_ids:
        print("\nIDs that could not be parsed:")
        for question_id, chunk_id in invalid_ids:
            print(f"  {question_id}: {chunk_id}")

    print("\nValidation inspection complete.")
    print("No dataset entries, vectors, or reports were changed.")


if __name__ == "__main__":
    main()
