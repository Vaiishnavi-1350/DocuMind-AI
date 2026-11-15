import json
import numpy as np

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.embeddings import (
    embed_documents_minilm,
    embed_query_minilm,
)


BASE_DIR = Path(__file__).resolve().parent

PDF_PATH = (
    BASE_DIR.parent
    / "tests"
    / "sample_documents"
    / "Algebraic Identities.pdf"
)

DATASET_PATH = BASE_DIR / "minilm_dataset.json"

CONFIGURATIONS = [
    (700, 200),
    (400, 100),
    (500, 100),
]

TOP_K = 5


def load_questions():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    return [
        item for item in dataset
        if item["id"].startswith("ALG")
    ]


def create_chunks(pages, chunk_size, overlap):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    return splitter.split_documents(pages)


def run_experiment():

    print("\nLoading Algebra PDF...")

    pages = PyPDFLoader(str(PDF_PATH)).load()
    questions = load_questions()

    print(f"Pages loaded: {len(pages)}")
    print(f"Questions: {len(questions)}")

    for chunk_size, overlap in CONFIGURATIONS:

        print("\n" + "=" * 90)
        print(f"CHUNK SIZE: {chunk_size} | OVERLAP: {overlap}")
        print("=" * 90)

        chunks = create_chunks(
            pages,
            chunk_size,
            overlap,
        )

        texts = [
            chunk.page_content
            for chunk in chunks
        ]

        print(f"Total chunks: {len(chunks)}")
        print("Generating document embeddings...")

        document_vectors = np.asarray(
            embed_documents_minilm(texts)
        )

        for question in questions:

            query_vector = np.asarray(
                embed_query_minilm(question["question"])
            )

            scores = document_vectors @ query_vector

            ranked_indices = np.argsort(scores)[::-1][:TOP_K]

            print("\n" + "-" * 80)
            print(f"{question['id']}: {question['question']}")
            print(f"Expected answer: {question['expected_answer']}")
            print("-" * 80)

            for rank, index in enumerate(ranked_indices, start=1):

                chunk = chunks[int(index)]

                print(
                    f"\nRank: {rank}"
                    f" | Chunk: {index}"
                    f" | Score: {scores[index]:.6f}"
                    f" | Page: {chunk.metadata.get('page', 'N/A')}"
                )

                print(chunk.page_content[:700])


if __name__ == "__main__":
    run_experiment()
