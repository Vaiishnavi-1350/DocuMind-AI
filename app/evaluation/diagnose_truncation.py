from app.evaluation.run_evaluation import DOCUMENT_IDS, load_dataset
from app.rag.retrieval import hybrid_search
from app.rag.reranker import get_reranker, RERANKER_MAX_LENGTH

TARGETS = {
    "ALG003": ["x + y = 12", "xy = 27", "x3 + y3"],
    "RES005": ["hackathon", "hackathon participant", "real-world AI solutions"],
}

LIMIT = 5

dataset = load_dataset()
model = get_reranker()
tokenizer = model.tokenizer

for item in dataset:
    question_id = item.get("id")
    if question_id not in TARGETS:
        continue

    question = item["question"].strip()
    filename = item.get(
        "document_filename",
        item.get("document_name", item.get("filename", "")),
    )
    document_id = DOCUMENT_IDS.get(filename)

    if not document_id:
        print(f"\n{question_id}: Could not resolve document ID for {filename!r}")
        continue

    candidates = hybrid_search(
        query=question,
        document_id=document_id,
        retrieval_limit=LIMIT,
    )

    print("\n" + "=" * 80)
    print(f"{question_id}: {question}")
    print(f"Reranker maximum length: {RERANKER_MAX_LENGTH}")

    for doc in candidates:
        chunk_id = doc.get("chunk_id", "unknown")
        text = str(doc.get("text", "")).strip()

        # Count tokens before truncation.
        full_pair = tokenizer(
            question,
            text,
            add_special_tokens=True,
            truncation=False,
        )
        full_token_count = len(full_pair["input_ids"])

        # Reproduce the configured truncation behavior.
        truncated_pair = tokenizer(
            question,
            text,
            add_special_tokens=True,
            truncation=True,
            max_length=RERANKER_MAX_LENGTH,
        )
        truncated_ids = truncated_pair["input_ids"]
        truncated_text = tokenizer.decode(
            truncated_ids,
            skip_special_tokens=True,
        ).lower()

        print(f"\nChunk: {chunk_id}")
        print(f"Original pair tokens: {full_token_count}")
        print(f"Tokens after truncation: {len(truncated_ids)}")
        print(f"Would exceed limit: {full_token_count > RERANKER_MAX_LENGTH}")

        for phrase in TARGETS[question_id]:
            found_in_original = phrase.lower() in text.lower()
            found_after_truncation = phrase.lower() in truncated_text

            print(
                f"Evidence {phrase!r}: "
                f"in original={found_in_original}, "
                f"visible after truncation={found_after_truncation}"
            )

        if chunk_id in set(item.get("relevant_chunk_ids", [])):
            print("Relevant chunk text preview:")
            print(text[:700].replace("\n", " "))

