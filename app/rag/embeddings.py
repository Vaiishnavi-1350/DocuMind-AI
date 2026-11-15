# ============================================================
# DOCUMIND AI - BGE-M3 EMBEDDINGS
#
# BAAI/bge-m3
#
# Generates:
#   1. Dense embeddings
#   2. Sparse embeddings
#
# Compatible with:
#   app/rag/ingest.py
#   app/rag/qdrant.py
#   app/rag/retrieval.py
# ============================================================

from __future__ import annotations

from typing import Any

from FlagEmbedding import BGEM3FlagModel
from sentence_transformers import SentenceTransformer
from app.config import (
    BGE_M3_MODEL,
    MINILM_MODEL,
    MINILM_VECTOR_SIZE,
)

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = BGE_M3_MODEL

USE_FP16 = False

BATCH_SIZE = 8

MAX_LENGTH = 8192

# ============================================================
# GLOBAL MODEL
# ============================================================

_model: BGEM3FlagModel | None = None
# ============================================================
# MINILM CONFIGURATION
# ============================================================

MINILM_BATCH_SIZE = 16

MINILM_MAX_LENGTH = 256

_minilm_model: SentenceTransformer | None = None


# ============================================================
# LOAD MINILM MODEL
# ============================================================

def get_minilm_model() -> SentenceTransformer:
    """
    Load MiniLM only once.

    Uses CPU and lazy loading to avoid
    loading the model during application startup.
    """

    global _minilm_model

    if _minilm_model is None:

        print("\n" + "=" * 70)
        print("DOCUMIND AI - LOADING MINILM")
        print("=" * 70)

        print(f"Model: {MINILM_MODEL}")

        _minilm_model = SentenceTransformer(
            MINILM_MODEL,
            device="cpu",
        )

        _minilm_model.max_seq_length = MINILM_MAX_LENGTH

        print("MiniLM loaded successfully.")

    return _minilm_model

# ============================================================
# LOAD MODEL
# ============================================================

def get_bge_model() -> BGEM3FlagModel:
    """
    Load BGE-M3 only once.

    The model is kept in memory after the first load.
    """

    global _model

    if _model is None:

        print("\n" + "=" * 70)
        print("DOCUMIND AI - LOADING BGE-M3")
        print("=" * 70)

        print(
            f"Model: {MODEL_NAME}"
        )

        print(
            "Loading model..."
        )

        _model = BGEM3FlagModel(
            MODEL_NAME,
            use_fp16=USE_FP16,
        )

        print(
            "BGE-M3 loaded successfully."
        )

    return _model
# ============================================================
# MINILM DOCUMENT EMBEDDINGS
# ============================================================

def embed_documents_minilm(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate dense-only MiniLM embeddings.

    Returns:
        list[list[float]]

    Vector dimension:
        384
    """

    if not texts:
        return []

    cleaned_texts = [
        str(text).strip() if text is not None else ""
        for text in texts
    ]

    model = get_minilm_model()

    print(
        f"Generating MiniLM embeddings "
        f"for {len(cleaned_texts)} chunks..."
    )

    embeddings = model.encode(
        cleaned_texts,
        batch_size=MINILM_BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    vectors = embeddings.tolist()

    if len(vectors) != len(cleaned_texts):
        raise RuntimeError(
            "MiniLM embedding count does not match text count."
        )

    for vector in vectors:
        if len(vector) != MINILM_VECTOR_SIZE:
            raise RuntimeError(
                f"Expected {MINILM_VECTOR_SIZE} dimensions, "
                f"received {len(vector)}."
            )

    print(
        f"MiniLM embeddings generated: {len(vectors)}"
    )

    print(
        f"Vector dimension: {len(vectors[0])}"
    )

    return vectors


# ============================================================
# MINILM QUERY EMBEDDING
# ============================================================

def embed_query_minilm(
    query: str,
) -> list[float]:
    """
    Generate one dense-only MiniLM query embedding.

    Returns:
        list[float]

    Vector dimension:
        384
    """

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    model = get_minilm_model()

    print("Generating MiniLM query embedding...")

    embeddings = model.encode(
        [query.strip()],
        batch_size=1,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    vector = embeddings[0].tolist()

    if len(vector) != MINILM_VECTOR_SIZE:
        raise RuntimeError(
            f"Expected {MINILM_VECTOR_SIZE} dimensions, "
            f"received {len(vector)}."
        )

    print(
        f"MiniLM query dimension: {len(vector)}"
    )

    return vector

# ============================================================
# DOCUMENT EMBEDDINGS
# ============================================================

def embed_documents(
    texts: list[str],
) -> tuple[list[list[float]], list[dict[str, Any]]]:
    """
    Generate BGE-M3 dense + sparse embeddings
    for document chunks.

    Returns EXACTLY TWO VALUES:

        dense_vectors
        sparse_vectors

    dense_vectors:
        list[list[float]]

    sparse_vectors:
        list[dict]

    This matches ingest.py:

        dense_vectors, sparse_vectors = embed_documents(texts)
    """

    if not texts:

        return [], []

    # --------------------------------------------------------
    # Validate texts
    # --------------------------------------------------------

    cleaned_texts = []

    for text in texts:

        if text is None:
            cleaned_texts.append("")

        else:
            cleaned_texts.append(
                str(text).strip()
            )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = get_bge_model()

    print(
        f"Generating BGE-M3 embeddings "
        f"for {len(cleaned_texts)} chunks..."
    )

    # --------------------------------------------------------
    # BGE-M3 encoding
    # --------------------------------------------------------

    output = model.encode(

        cleaned_texts,

        batch_size=BATCH_SIZE,

        max_length=MAX_LENGTH,

        return_dense=True,

        return_sparse=True,

        return_colbert_vecs=False,

    )

    # ========================================================
    # DENSE VECTORS
    # ========================================================

    dense_embeddings = output.get(
        "dense_vecs"
    )

    if dense_embeddings is None:

        raise RuntimeError(
            "BGE-M3 did not return dense vectors."
        )

    dense_vectors = (
        dense_embeddings.tolist()
        if hasattr(
            dense_embeddings,
            "tolist"
        )
        else list(
            dense_embeddings
        )
    )

    # ========================================================
    # SPARSE VECTORS
    # ========================================================

    sparse_embeddings = output.get(
        "lexical_weights"
    )

    if sparse_embeddings is None:

        raise RuntimeError(
            "BGE-M3 did not return sparse vectors."
        )

    sparse_vectors = []

    for sparse_embedding in sparse_embeddings:

        # ----------------------------------------------------
        # BGE-M3 lexical_weights is usually:
        #
        # {
        #     token_id: weight,
        #     token_id: weight,
        #     ...
        # }
        #
        # Qdrant expects:
        #
        # {
        #     "indices": [...],
        #     "values": [...]
        # }
        # ----------------------------------------------------

        if hasattr(
            sparse_embedding,
            "items"
        ):

            items = list(
                sparse_embedding.items()
            )

        else:

            items = list(
                sparse_embedding
            )

        indices = []
        values = []

        for token_id, weight in items:

            indices.append(
                int(token_id)
            )

            values.append(
                float(weight)
            )

        sparse_vectors.append(
            {
                "indices": indices,
                "values": values,
            }
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    if len(dense_vectors) != len(
        cleaned_texts
    ):

        raise RuntimeError(
            "Number of dense embeddings "
            "does not match number of texts."
        )

    if len(sparse_vectors) != len(
        cleaned_texts
    ):

        raise RuntimeError(
            "Number of sparse embeddings "
            "does not match number of texts."
        )

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        f"BGE-M3 embeddings generated: "
        f"{len(dense_vectors)}"
    )

    if dense_vectors:

        print(
            "Dense dimension: "
            f"{len(dense_vectors[0])}"
        )

    if sparse_vectors:

        print(
            "Sparse vectors generated: "
            f"{len(sparse_vectors)}"
        )

    return (
        dense_vectors,
        sparse_vectors,
    )


# ============================================================
# QUERY EMBEDDINGS
# ============================================================

def embed_query(
    query: str,
) -> tuple[list[float], dict[str, Any]]:
    """
    Generate BGE-M3 dense + sparse embeddings
    for ONE query.

    Returns EXACTLY TWO VALUES:

        dense_vector
        sparse_vector

    This matches retrieval.py:

        dense_vector, sparse_vector = embed_query(query)
    """

    if not query or not query.strip():

        raise ValueError(
            "Query cannot be empty."
        )

    query = query.strip()

    model = get_bge_model()

    print(
        "Generating BGE-M3 query embedding..."
    )

    output = model.encode(

        [query],

        batch_size=1,

        max_length=MAX_LENGTH,

        return_dense=True,

        return_sparse=True,

        return_colbert_vecs=False,

    )

    # ========================================================
    # DENSE
    # ========================================================

    dense_embeddings = output.get(
        "dense_vecs"
    )

    if dense_embeddings is None:

        raise RuntimeError(
            "BGE-M3 did not return "
            "a dense query vector."
        )

    dense_vector = dense_embeddings[0]

    if hasattr(
        dense_vector,
        "tolist"
    ):

        dense_vector = (
            dense_vector.tolist()
        )

    else:

        dense_vector = list(
            dense_vector
        )

    # ========================================================
    # SPARSE
    # ========================================================

    sparse_embeddings = output.get(
        "lexical_weights"
    )

    if sparse_embeddings is None:

        raise RuntimeError(
            "BGE-M3 did not return "
            "a sparse query vector."
        )

    sparse_embedding = (
        sparse_embeddings[0]
    )

    if hasattr(
        sparse_embedding,
        "items"
    ):

        items = list(
            sparse_embedding.items()
        )

    else:

        items = list(
            sparse_embedding
        )

    indices = []
    values = []

    for token_id, weight in items:

        indices.append(
            int(token_id)
        )

        values.append(
            float(weight)
        )

    sparse_vector = {

        "indices":
            indices,

        "values":
            values,

    }

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "Query embeddings generated."
    )

    print(
        f"Dense dimension: "
        f"{len(dense_vector)}"
    )

    print(
        f"Sparse dimensions: "
        f"{len(indices)}"
    )

    return (
        dense_vector,
        sparse_vector,
    )


# ============================================================
# OPTIONAL COMPATIBILITY FUNCTIONS
# ============================================================

def embed_query_dense(
    query: str,
) -> list[float]:
    """
    Convenience function for dense-only retrieval.
    """

    dense_vector, _ = embed_query(
        query
    )

    return dense_vector


def embed_query_sparse(
    query: str,
) -> dict[str, Any]:
    """
    Convenience function for sparse-only retrieval.
    """

    _, sparse_vector = embed_query(
        query
    )

    return sparse_vector


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\nTesting BGE-M3 embeddings...")

    test_texts = [
        "An algebraic identity is an equality "
        "that holds for all values of the variables.",
        "The square of a sum is given by "
        "(a + b)^2 = a^2 + 2ab + b^2.",
    ]

    dense_vectors, sparse_vectors = (
        embed_documents(
            test_texts
        )
    )

    print(
        "\nDocument embedding test:"
    )

    print(
        f"Texts: {len(test_texts)}"
    )

    print(
        f"Dense vectors: "
        f"{len(dense_vectors)}"
    )

    print(
        f"Sparse vectors: "
        f"{len(sparse_vectors)}"
    )

    query_dense, query_sparse = (
        embed_query(
            "What is the square of a sum?"
        )
    )

    print(
        "\nQuery embedding test:"
    )

    print(
        f"Dense dimension: "
        f"{len(query_dense)}"
    )

    print(
        f"Sparse entries: "
        f"{len(query_sparse['indices'])}"
    )

    print(
        "\nBGE-M3 embedding test completed."
    )