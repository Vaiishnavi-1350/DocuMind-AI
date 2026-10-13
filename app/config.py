# ============================================================
# DOCUMIND AI - CENTRAL CONFIGURATION
# ============================================================

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

# Project root:
# documind-ai/
#     app/
#     .env
#
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)

# ============================================================
# APPLICATION
# ============================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "DocuMind AI"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "2.0.0"
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/documind.db"
)


# ============================================================
# JWT / AUTHENTICATION
# ============================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not configured. "
        "Please add JWT_SECRET_KEY to your .env file."
    )


JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)


# ============================================================
# QDRANT
# ============================================================

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333"
)

QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "documind_bge_m3"
)
QDRANT_UPSERT_BATCH_SIZE = int(
    os.getenv(
        "QDRANT_UPSERT_BATCH_SIZE",
        "64"
    )
)

# ============================================================
# EMBEDDING MODEL
# ============================================================

BGE_M3_MODEL = os.getenv(
    "BGE_M3_MODEL",
    "BAAI/bge-m3"
)


# ============================================================
# RERANKER
# ============================================================

RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "cross-encoder/ms-marco-MiniLM-L-12-v2"
)

RERANKER_MAX_LENGTH = int(
    os.getenv(
        "RERANKER_MAX_LENGTH",
        "512"
    )
)


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL"
)

GEMINI_TEMPERATURE = float(
    os.getenv(
        "GEMINI_TEMPERATURE",
        "0.2"
    )
)

GEMINI_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "GEMINI_MAX_OUTPUT_TOKENS",
        "2048"
    )
)


# ============================================================
# RAG CONFIGURATION
# ============================================================

RETRIEVAL_LIMIT = int(
    os.getenv(
        "RETRIEVAL_LIMIT",
        "12"
    )
)

FINAL_TOP_K = int(
    os.getenv(
        "FINAL_TOP_K",
        "8"
    )
)

SOURCE_SCORE_MARGIN = float(
    os.getenv(
        "SOURCE_SCORE_MARGIN",
        "1.0"
    )
)

MAX_DISPLAY_SOURCES = int(
    os.getenv(
        "MAX_DISPLAY_SOURCES",
        "5"
    )
)


# ============================================================
# CHUNKING
# ============================================================

CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "700"
    )
)

CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "200"
    )
)


# ============================================================
# STORAGE
# ============================================================

UPLOAD_DIR_NAME = os.getenv(
    "UPLOAD_DIR",
    "data/uploads"
)

UPLOAD_DIR = (
    BASE_DIR /
    UPLOAD_DIR_NAME
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CORS
# ============================================================

CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]


# ============================================================
# DEBUG / ENVIRONMENT
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)

DEBUG = (
    os.getenv(
        "DEBUG",
        "false"
    ).lower()
    == "true"
)

# ============================================================
# PRODUCTION SAFETY
# ============================================================

if ENVIRONMENT == "production" and DEBUG:

    raise RuntimeError(
        "DEBUG must be false in production."
    )

# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

def show_config() -> None:

    print("\n" + "=" * 70)
    print("DOCUMIND AI - CONFIGURATION")
    print("=" * 70)

    print("Application :", APP_NAME)
    print("Version     :", APP_VERSION)

    print(
        "Environment :",
        ENVIRONMENT
    )

    print(
        "Database    :",
        DATABASE_URL
    )

    print(
        "Qdrant      :",
        QDRANT_URL
    )

    print(
        "Collection  :",
        QDRANT_COLLECTION_NAME
    )
    print(
    "Upsert Batch :",
    QDRANT_UPSERT_BATCH_SIZE
    )

    print(
        "Embedding   :",
        BGE_M3_MODEL
    )

    print(
        "Reranker    :",
        RERANKER_MODEL
    )

    print(
        "Retrieval   :",
        RETRIEVAL_LIMIT
    )

    print(
        "Final Top-K :",
        FINAL_TOP_K
    )

    print(
        "Chunk Size  :",
        CHUNK_SIZE
    )

    print(
        "Overlap     :",
        CHUNK_OVERLAP
    )

    print(
        "Upload Dir  :",
        UPLOAD_DIR
    )

    print(
        "CORS Origins:",
        CORS_ALLOW_ORIGINS
    )
    print(
    "JWT Secret  :",
    "configured"
    if JWT_SECRET_KEY
    else "missing"
    )
    print(
        "Gemini Key  :",
        "configured"
        if GEMINI_API_KEY
        else "missing"
    )
    print("=" * 70)


# ============================================================
# OPTIONAL TEST
# ============================================================

if __name__ == "__main__":

    show_config()