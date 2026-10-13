
from app.database.database import SessionLocal, Document
from app.rag.qdrant import client, COLLECTION_NAME

print("\n========== SQLITE DOCUMENTS ==========")

db = SessionLocal()

try:
    documents = db.query(Document).all()

    if not documents:
        print("No documents found in SQLite.")

    for doc in documents:
        print(f"\nFilename: {doc.filename}")
        print(f"Document ID: {doc.id}")
        print(f"Status: {doc.status}")
        print(f"Chunks: {doc.chunks}")

finally:
    db.close()


print("\n========== QDRANT DOCUMENTS ==========")

if not client.collection_exists(COLLECTION_NAME):
    print("Qdrant collection does not exist.")
else:
    offset = None
    seen = set()

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
            document_id = payload.get("document_id")
            filename = payload.get("filename")
            chunk_id = payload.get("chunk_id")

            key = (document_id, filename)

            if key not in seen:
                seen.add(key)
                print(f"\nFilename: {filename}")
                print(f"Document ID: {document_id}")
                print(f"Example chunk ID: {chunk_id}")

        if next_offset is None:
            break

        offset = next_offset

print("\n========== FINISHED ==========")