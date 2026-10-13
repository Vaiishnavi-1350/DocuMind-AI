"""
DocuMind AI - Evidence-Aware Ranking Experiment

Compares:
1. Hybrid retrieval
2. Cross-encoder reranking
3. Evidence-aware reranking

Evaluation only. No Gemini calls.
No production code changes.
"""

import json
import re
from pathlib import Path

from app.evaluation.run_evaluation import (
    K,
    DOCUMENT_IDS,
    load_dataset,
    calculate_metrics,
    aggregate_metrics,
)
from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank_documents


BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = BASE_DIR / "app" / "evaluation" / "reports"
OUTPUT_PATH = REPORT_DIR / "evidence_ranking_experiment.json"

CANDIDATE_LIMIT = 5

# Keep the bonus small so lexical matches do not dominate semantic relevance.
EXACT_MATCH_BONUS = 0.15

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can",
    "find", "for", "from", "how", "in", "is", "it", "of",
    "on", "or", "the", "to", "was", "what", "when", "where",
    "which", "who", "with", "would", "given", "mentioned",
}


def normalize(text):
    """Normalize text for simple lexical matching."""
    return re.findall(r"[a-z0-9]+", str(text).lower())


def evidence_bonus(question, document):
    """
    Reward distinctive question terms found in a candidate passage.

    This is a lightweight experiment, not a semantic relevance model.
    """
    question_terms = {
        term for term in normalize(question)
        if term not in STOP_WORDS and len(term) > 1
    }

    if not question_terms:
        return 0.0

    text = document.get("text", "")
    if not text:
        text = document.get("content", "")

    document_terms = set(normalize(text))

    matched = question_terms & document_terms
    return EXACT_MATCH_BONUS * len(matched) / len(question_terms)

def evidence_rerank(question, reranked_documents, top_k):
    """
    Experimental ranking:
    1. Normalize cross-encoder scores.
    2. Add query-term coverage.
    3. Reward matching meaningful adjacent query terms.
    """
    if not reranked_documents:
        return []

    def normalized_text(text):
        text = str(text).lower()
        # Make x^3 and x3 comparable.
        text = re.sub(r"\b([a-z])\s*\^\s*(\d+)\b", r"\1\2", text)
        text = text.replace("³", "3").replace("²", "2")
        return normalize(text)

    question_tokens = [
        token for token in normalized_text(question)
        if token not in STOP_WORDS and len(token) > 1
    ]
    question_terms = set(question_tokens)

    # Adjacent meaningful query terms help preserve short evidence phrases.
    question_pairs = {
        (question_tokens[i], question_tokens[i + 1])
        for i in range(len(question_tokens) - 1)
    }

    raw_scores = [
        float(doc.get("rerank_score", 0.0))
        for doc in reranked_documents
    ]
    low, high = min(raw_scores), max(raw_scores)
    score_range = high - low

    scored = []

    for original_rank, document in enumerate(reranked_documents):
        item = dict(document)
        text = item.get("text") or item.get("content") or ""
        tokens = normalized_text(text)
        token_set = set(tokens)

        # Fraction of distinctive query terms present in the passage.
        coverage = (
            len(question_terms & token_set) / len(question_terms)
            if question_terms else 0.0
        )

        # Reward adjacent query terms that also appear adjacent in the text.
        passage_pairs = set(zip(tokens, tokens[1:]))
        pair_coverage = (
            len(question_pairs & passage_pairs) / len(question_pairs)
            if question_pairs else 0.0
        )

        raw = raw_scores[original_rank]
        normalized_cross = (
            (raw - low) / score_range if score_range > 0 else 1.0
        )

        # Keep semantic relevance dominant; lexical evidence is supplementary.
        final_score = (
            0.75 * normalized_cross
            + 0.20 * coverage
            + 0.05 * pair_coverage
        )

        item["original_cross_encoder_rank"] = original_rank + 1
        item["normalized_cross_score"] = normalized_cross
        item["query_term_coverage"] = coverage
        item["query_pair_coverage"] = pair_coverage
        item["evidence_adjusted_score"] = final_score
        scored.append(item)

    # Stable sort preserves the existing order when scores tie.
    scored.sort(
        key=lambda item: item["evidence_adjusted_score"],
        reverse=True,
    )
    return scored[:top_k]

def run_experiment():
    dataset = load_dataset()

    results = []
    failures = []

    print("=" * 65)
    print("DOCUMIND AI - EVIDENCE-AWARE RANKING EXPERIMENT")
    print("Candidate limit:", CANDIDATE_LIMIT)
    print("Evaluation cutoff K:", K)
    print("Exact-match bonus:", EXACT_MATCH_BONUS)
    print("Gemini generation: DISABLED")
    print("=" * 65)

    for item in dataset:
        question_id = item.get("id", "UNKNOWN")
        question = item.get("question", "").strip()

        filename = item.get(
            "document_filename",
            item.get("document_name", item.get("filename", "")),
        )

        document_id = DOCUMENT_IDS.get(filename)
        relevant_ids = set(item.get("relevant_chunk_ids", []))

        if not question or not document_id or not relevant_ids:
            failures.append({
                "id": question_id,
                "reason": "Missing question, document ID, or relevant chunks",
            })
            continue

        try:
            candidates = hybrid_search(
                query=question,
                document_id=document_id,
                retrieval_limit=CANDIDATE_LIMIT,
            )

            hybrid = candidates[:CANDIDATE_LIMIT]

            reranked = rerank_documents(
                query=question,
                documents=candidates,
                top_k=CANDIDATE_LIMIT,
            )

            evidence_ranked = evidence_rerank(
                question,
                reranked,
                top_k=K,
            )

            hybrid_metrics = calculate_metrics(
                hybrid[:K], relevant_ids, K
            )

            cross_metrics = calculate_metrics(
                reranked[:K], relevant_ids, K
            )

            evidence_metrics = calculate_metrics(
                evidence_ranked, relevant_ids, K
            )

            results.append({
                "id": question_id,
                "document_filename": filename,
                "hybrid_retrieval": hybrid_metrics,
                "cross_encoder": cross_metrics,
                "evidence_aware": evidence_metrics,
                "relevant_chunk_ids": sorted(relevant_ids),
                "hybrid_chunks": [
                    d.get("chunk_id") for d in hybrid
                ],
                "cross_encoder_chunks": [
                    d.get("chunk_id") for d in reranked
                ],
                "evidence_aware_chunks": [
                    {
                        "chunk_id": d.get("chunk_id"),
                        "cross_encoder_rank":
                            d.get("original_cross_encoder_rank"),
                        "evidence_bonus": d.get("evidence_bonus"),
                        "adjusted_score":
                            d.get("evidence_adjusted_score"),
                    }
                    for d in evidence_ranked
                ],
            })

            print(
                f"{question_id}: "
                f"Hybrid RR={hybrid_metrics['reciprocal_rank']:.3f} | "
                f"Cross RR={cross_metrics['reciprocal_rank']:.3f} | "
                f"Evidence RR={evidence_metrics['reciprocal_rank']:.3f}"
            )

        except Exception as exc:
            failures.append({
                "id": question_id,
                "reason": str(exc),
            })
            print(f"ERROR {question_id}: {exc}")

    report = {
        "experiment": "evidence_aware_reranking",
        "candidate_limit": CANDIDATE_LIMIT,
        "cutoff_k": K,
        "exact_match_bonus": EXACT_MATCH_BONUS,
        "gemini_called": False,
        "successfully_evaluated": len(results),
        "failures": failures,
        "aggregate_metrics": {
            "hybrid_retrieval": aggregate_metrics(
                results, "hybrid_retrieval"
            ),
            "cross_encoder": aggregate_metrics(
                results, "cross_encoder"
            ),
            "evidence_aware": aggregate_metrics(
                results, "evidence_aware"
            ),
        },
        "per_question_results": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nAGGREGATE METRICS")
    print(json.dumps(report["aggregate_metrics"], indent=2))
    print("\nQuestions evaluated:", len(results))
    print("Failures:", len(failures))
    print("Gemini called: False")
    print("Report saved to:", OUTPUT_PATH)

    return report


if __name__ == "__main__":
    run_experiment()