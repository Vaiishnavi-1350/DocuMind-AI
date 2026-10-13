# ============================================================
# DOCUMIND AI - QDRANT VECTOR STORE
#
# BGE-M3 Dense + Sparse
# +
# Document-level filtering
# +
# Batch upsert
# ============================================================

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from qdrant_client import QdrantClient

from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    SparseVector,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    QDRANT_UPSERT_BATCH_SIZE,
)

# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_NAME = QDRANT_COLLECTION_NAME
UPSERT_BATCH_SIZE = QDRANT_UPSERT_BATCH_SIZE

# ============================================================
# CLIENT
# ============================================================

client = QdrantClient(url=QDRANT_URL)

# ============================================================
# CREATE COLLECTION
# ============================================================

def create_collection() -> None:
    """
    Create the BGE-M3 Qdrant collection if it does not exist.

    Dense:
        1024 dimensions
        cosine similarity

    Sparse:
        BGE-M3 lexical weights
    """

    if client.collection_exists(
        COLLECTION_NAME
    ):
        return

    client.create_collection(

        collection_name=COLLECTION_NAME,

        vectors_config={

            "dense": VectorParams(

                size=1024,

                distance=Distance.COSINE,
            )
        },

        sparse_vectors_config={

            "sparse": SparseVectorParams(

                index=SparseIndexParams(
                    on_disk=False
                )
            )
        },
    )

    print(
        f"Created Qdrant collection: "
        f"{COLLECTION_NAME}"
    )


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def ensure_collection() -> None:
    """
    Compatibility wrapper used by ingest.py.
    """

    create_collection()


# ============================================================
# DOCUMENT ID
# ============================================================

def generate_document_id(
    text: str,
) -> str:

    if not text:

        raise ValueError(
            "Cannot generate document_id "
            "from empty text."
        )

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# DOCUMENT FILTER
# ============================================================

def build_document_filter(
    document_id: str,
) -> Filter:

    if not document_id:

        raise ValueError(
            "document_id is required."
        )

    return Filter(

        must=[

            FieldCondition(

                key="document_id",

                match=MatchValue(
                    value=document_id
                ),
            )
        ]
    )


# ============================================================
# DELETE DOCUMENT
# ============================================================

def delete_document(
    document_id: str,
) -> None:

    if not document_id:
        return

    if not client.collection_exists(
        COLLECTION_NAME
    ):
        return

    client.delete(

        collection_name=COLLECTION_NAME,

        points_selector=build_document_filter(
            document_id
        ),
    )

    print(
        f"Deleted Qdrant chunks for document: "
        f"{document_id}"
    )


# ============================================================
# UPSERT CHUNKS
# ============================================================

def upsert_chunks(
    embeddings: tuple[
        list[list[float]],
        list[dict[str, Any]],
    ]
    | list[list[float]],

    metadata: list[dict[str, Any]],

    document_id: str | None = None,

    filename: str = "",

    document_type: str = "pdf",

) -> int:
    """
    Store BGE-M3 dense + sparse embeddings in Qdrant.

    Expected embeddings format:

        (
            dense_vectors,
            sparse_vectors
        )

    Example:

        dense_vectors = [
            [1024 floats],
            [1024 floats],
            ...
        ]

        sparse_vectors = [
            {
                "indices": [...],
                "values": [...]
            },
            ...
        ]

    metadata contains one dictionary per chunk.

    The number of dense vectors,
    sparse vectors and metadata entries
    MUST be identical.
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    if not embeddings:

        return 0

    if not metadata:

        raise ValueError(
            "Metadata cannot be empty."
        )

    # ========================================================
    # EXTRACT DENSE + SPARSE
    # ========================================================

    if (
        isinstance(embeddings, tuple)
        and len(embeddings) == 2
    ):

        dense_vectors = embeddings[0]

        sparse_vectors = embeddings[1]

    else:

        raise ValueError(
            "embeddings must contain "
            "(dense_vectors, sparse_vectors)."
        )

    # ========================================================
    # LENGTH CHECK
    # ========================================================

    if len(dense_vectors) != len(
        sparse_vectors
    ):

        raise ValueError(
            "Dense and sparse embeddings "
            "must contain the same number "
            "of items."
        )

    if len(dense_vectors) != len(
        metadata
    ):

        raise ValueError(
            "Dense embeddings and metadata "
            "must contain the same number "
            "of items."
        )

    if len(sparse_vectors) != len(
        metadata
    ):

        raise ValueError(
            "Sparse embeddings and metadata "
            "must contain the same number "
            "of items."
        )

    if not dense_vectors:

        return 0

    # ========================================================
    # CREATE COLLECTION
    # ========================================================

    create_collection()

    # ========================================================
    # DELETE EXISTING DOCUMENT
    #
    # This makes re-uploading the same document_id safe.
    # ========================================================

    resolved_document_id = (
        document_id
    )

    if not resolved_document_id:

        resolved_document_id = (
            metadata[0].get(
                "document_id"
            )
        )

    if resolved_document_id:

        delete_document(
            resolved_document_id
        )

    # ========================================================
    # BUILD POINTS
    # ========================================================

    points: list[PointStruct] = []

    for index in range(
        len(dense_vectors)
    ):

        dense_vector = (
            dense_vectors[index]
        )

        sparse_data = (
            sparse_vectors[index]
        )

        item_metadata = dict(
            metadata[index]
        )

        # ----------------------------------------------------
        # DOCUMENT ID
        # ----------------------------------------------------

        current_document_id = (
            item_metadata.get(
                "document_id"
            )
            or resolved_document_id
        )

        if not current_document_id:

            raise ValueError(
                "document_id is missing "
                f"for chunk {index}."
            )

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        text = str(
            item_metadata.get(
                "text",
                ""
            )
        )

        # ----------------------------------------------------
        # FILENAME
        # ----------------------------------------------------

        current_filename = (
            item_metadata.get(
                "filename"
            )
            or filename
            or ""
        )

        # ----------------------------------------------------
        # DOCUMENT TYPE
        # ----------------------------------------------------

        current_document_type = (
            item_metadata.get(
                "document_type"
            )
            or document_type
        )

        # ----------------------------------------------------
        # CHUNK ID
        # ----------------------------------------------------

        chunk_id = (
            item_metadata.get(
                "chunk_id"
            )
        )

        if chunk_id is None:

            chunk_id = (
                f"{current_document_id}"
                f"_chunk_{index}"
            )

        # ----------------------------------------------------
        # PAGE
        # ----------------------------------------------------

        page = item_metadata.get(
            "page"
        )

        # ----------------------------------------------------
        # PAYLOAD
        # ----------------------------------------------------

        payload = dict(
            item_metadata
        )

        payload.update(

            {
                "text": text,

                "document_id":
                    current_document_id,

                "filename":
                    current_filename,

                "document_type":
                    current_document_type,

                "chunk_id":
                    chunk_id,

                "page":
                    page,
            }
        )

        # ----------------------------------------------------
        # SPARSE VECTOR
        # ----------------------------------------------------

        if not isinstance(
            sparse_data,
            dict
        ):

            raise ValueError(
                "Sparse embedding must be "
                "a dictionary containing "
                "'indices' and 'values'."
            )

        sparse_indices = (
            sparse_data.get(
                "indices",
                []
            )
        )

        sparse_values = (
            sparse_data.get(
                "values",
                []
            )
        )

        if len(sparse_indices) != len(
            sparse_values
        ):

            raise ValueError(
                "Sparse vector indices and "
                "values must have the same "
                "length."
            )

        sparse_vector = SparseVector(

            indices=[
                int(value)
                for value in sparse_indices
            ],

            values=[
                float(value)
                for value in sparse_values
            ],
        )

        # ----------------------------------------------------
        # POINT
        # ----------------------------------------------------

        point = PointStruct(

            id=str(
                uuid.uuid4()
            ),

            vector={

                "dense":
                    dense_vector,

                "sparse":
                    sparse_vector,
            },

            payload=payload,
        )

        points.append(
            point
        )

    # ========================================================
    # BATCH UPSERT
    # ========================================================

    print(
        f"Storing {len(points)} chunks in Qdrant..."
    )

    for start in range(

        0,

        len(points),

        UPSERT_BATCH_SIZE

    ):

        batch = points[
            start:
            start + UPSERT_BATCH_SIZE
        ]

        client.upsert(

            collection_name=
                COLLECTION_NAME,

            points=batch,
        )

        print(
            f"Upserted chunks "
            f"{start + 1}-"
            f"{min(start + len(batch), len(points))}"
        )

    print(
        f"Successfully stored "
        f"{len(points)} chunks in Qdrant."
    )

    return len(points)


# ============================================================
# DENSE SEARCH
# ============================================================

def search_dense(
    query_vector: list[float],
    limit: int = 10,
    document_id: str | None = None,
):

    if not document_id:

        raise ValueError(
            "document_id is required."
        )

    create_collection()

    results = client.query_points(

        collection_name=
            COLLECTION_NAME,

        query=query_vector,

        using="dense",

        query_filter=
            build_document_filter(
                document_id
            ),

        limit=max(
            1,
            int(limit)
        ),

        with_payload=True,
    )

    return results.points


# ============================================================
# SPARSE SEARCH
# ============================================================

def search_sparse(
    query_vector: dict[str, Any],
    limit: int = 10,
    document_id: str | None = None,
):

    if not document_id:

        raise ValueError(
            "document_id is required."
        )

    create_collection()

    # --------------------------------------------------------
    # Convert dictionary into Qdrant SparseVector
    # --------------------------------------------------------

    if isinstance(
        query_vector,
        dict
    ):

        sparse_query = SparseVector(

            indices=[
                int(value)
                for value in query_vector.get(
                    "indices",
                    []
                )
            ],

            values=[
                float(value)
                for value in query_vector.get(
                    "values",
                    []
                )
            ],
        )

    else:

        sparse_query = query_vector

    results = client.query_points(

        collection_name=
            COLLECTION_NAME,

        query=sparse_query,

        using="sparse",

        query_filter=
            build_document_filter(
                document_id
            ),

        limit=max(
            1,
            int(limit)
        ),

        with_payload=True,
    )

    return results.points


# ============================================================
# RESET COLLECTION
# ============================================================

def reset_collection() -> None:

    if client.collection_exists(
        COLLECTION_NAME
    ):

        client.delete_collection(
            COLLECTION_NAME
        )

        print(
            f"Deleted collection: "
            f"{COLLECTION_NAME}"
        )

    create_collection()

    print(
        "Qdrant collection reset successfully."
    )


# ============================================================
# COLLECTION INFO
# ============================================================

def show_collection_info() -> None:

    print(
        "\n" + "=" * 70
    )

    print(
        "QDRANT COLLECTION INFORMATION"
    )

    print(
        "=" * 70
    )

    if not client.collection_exists(
        COLLECTION_NAME
    ):

        print(
            "Collection does not exist."
        )

        return

    info = client.get_collection(
        COLLECTION_NAME
    )

    print(
        "Collection:",
        COLLECTION_NAME
    )

    print(
        "Points:",
        info.points_count
    )

    print(
        "Status:",
        info.status
    )


# ============================================================
# CONNECTION TEST
# ============================================================

def test_qdrant_connection() -> None:

    print(
        "\n" + "=" * 70
    )

    print(
        "QDRANT CONNECTION"
    )

    print(
        "=" * 70
    )

    collections = (
        client.get_collections()
    )

    print(
        "Collections:"
    )

    for collection in (
        collections.collections
    ):

        print(
            f"- {collection.name}"
        )
def debug_document_chunks(document_id: str) -> None:
    print("\n" + "=" * 70)
    print("DEBUG - DOCUMENT CHUNKS")
    print("=" * 70)

    print("Requested document_id:", document_id)

    if not client.collection_exists(COLLECTION_NAME):
        print("Collection does not exist.")
        return

    result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=build_document_filter(document_id),
        limit=10,
        with_payload=True,
        with_vectors=False,
    )

    points, next_page = result

    print("Matching chunks:", len(points))

    for i, point in enumerate(points, start=1):
        payload = point.payload or {}

        print(f"\n--- CHUNK {i} ---")
        print("Point ID:", point.id)
        print("document_id:", payload.get("document_id"))
        print("filename:", payload.get("filename"))
        print("page:", payload.get("page"))
        print("chunk_id:", payload.get("chunk_id"))
        print("text:", str(payload.get("text", ""))[:300])

    print("=" * 70)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    test_qdrant_connection()

    create_collection()

    show_collection_info()