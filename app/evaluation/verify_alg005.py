
from app.rag.qdrant import client, COLLECTION_NAME

DOCUMENT_ID = "f2dca717-9eee-4c7e-97c8-2c21fed0b7ff"

print("\n========== VERIFY ALG005 ==========")
print(f"Document ID: {DOCUMENT_ID}")

if not client.collection_exists(COLLECTION_NAME):
    print("ERROR: Qdrant collection does not exist.")
    raise SystemExit(1)

offset = None
found_chunks = {}

while True:
    points, next_offset = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )

    for point in points:
        payload = point.payload or {}

        if str(payload.get("document_id")) != DOCUMENT_ID:
            continue

        chunk_id = payload.get("chunk_id")
        text = payload.get("text", "")

        if chunk_id:
            found_chunks[str(chunk_id)] = text

    if next_offset is None:
        break

    offset = next_offset

if not found_chunks:
    print("ERROR: No chunks found for this document.")
    raise SystemExit(1)

print(f"\nTotal chunks found: {len(found_chunks)}")

# Print chunks 4 through 10 for context.
for chunk_number in range(4, 11):
    chunk_id = f"{DOCUMENT_ID}_chunk_{chunk_number}"

    if chunk_id not in found_chunks:
        continue

    print(f"\n{'=' * 60}")
    print(f"CHUNK: {chunk_id}")
    print("=" * 60)
    print(found_chunks[chunk_id])

    text = found_chunks[chunk_id].lower()

    if (
        "difference of cubes" in text
        or "a^3 - b^3" in text
        or "a³ - b³" in text
        or "a3 - b3" in text
        or "a^3-b^3" in text
        or "a³−b³" in text
    ):
        print("\n*** POSSIBLE ALG005 SUPPORT FOUND ***")

print("\n========== VERIFICATION COMPLETE ==========")
