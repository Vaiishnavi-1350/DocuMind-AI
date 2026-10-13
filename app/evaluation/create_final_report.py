
"""
DocuMind AI - Phase 9.2
Consolidate existing evaluation reports.

No Gemini calls.
No production pipeline changes.
Does not modify existing experiment reports.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"

SOURCE_FILES = {
    "retrieval_baseline": "retrieval_evaluation_baseline.json",
    "retrieval_report": "retrieval_evaluation_report.json",
    "reranking_comparison": "reranking_comparison.json",
    "context_evaluation": "context_evaluation_report.json",
    "context_size_experiment": "context_size_experiment.json",
    "answer_evaluation": "answer_evaluation_report.json",
}


def load_report(filename):
    path = REPORTS_DIR / filename

    if not path.exists():
        return {
            "available": False,
            "error": f"Report not found: {filename}",
        }

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return {
            "available": True,
            "data": data,
        }

    except (json.JSONDecodeError, OSError) as exc:
        return {
            "available": False,
            "error": str(exc),
        }


def main():
    sources = {
        name: load_report(filename)
        for name, filename in SOURCE_FILES.items()
    }

    def get_data(name):
        source = sources[name]
        if source["available"]:
            return source["data"]
        return {}

    retrieval = get_data("retrieval_baseline")
    reranking = get_data("reranking_comparison")
    context = get_data("context_evaluation")
    context_size = get_data("context_size_experiment")
    answers = get_data("answer_evaluation")

    retrieval_summary = retrieval.get("summary", {})
    context_summary = context.get("summary", {})
    answer_summary = answers.get("summary", {})

    # Some existing reports store their metrics under different keys.
    # Preserve each full source report's data below rather than guessing
    # missing values or silently replacing one experiment with another.
    report = {
        "project": "DocuMind AI",
        "phase": "9.2",
        "report_type": "consolidated_evaluation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "constraints": {
            "gemini_called_by_report_generator": False,
            "production_pipeline_changed": False,
            "existing_reports_modified": False,
        },
        "evaluation_summary": {
            "benchmark_questions": 10,
            "retrieval_baseline": {
                "source": SOURCE_FILES["retrieval_baseline"],
                "data": retrieval_summary,
            },
            "reranking_comparison": {
                "source": SOURCE_FILES["reranking_comparison"],
                "data": reranking.get("summary", {}),
            },
            "context_evaluation": {
                "source": SOURCE_FILES["context_evaluation"],
                "data": context_summary,
            },
            "context_size_experiment": {
                "source": SOURCE_FILES["context_size_experiment"],
                "data": context_size.get("summary", {}),
            },
            "offline_answer_evaluation": {
                "source": SOURCE_FILES["answer_evaluation"],
                "data": answer_summary,
            },
        },
        "source_reports": sources,
        "interpretation": [
            (
                "Retrieval and answer generation are evaluated separately."
            ),
            (
                "Unmatched saved answers are pending, not incorrect."
            ),
            (
                "Expected-answer containment is a simple check, "
                "not a semantic correctness metric."
            ),
            (
                "Results from different experiment configurations "
                "must not be treated as a single experiment."
            ),
            (
                "Context-size results describe retrieval evidence coverage; "
                "they do not prove answer-generation accuracy."
            ),
        ],
    }

    output_path = REPORTS_DIR / "final_evaluation_report.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("Final evaluation report created successfully.")
    print(f"Location: {output_path}")
    print(f"Source reports checked: {len(sources)}")

    missing = [
        name
        for name, result in sources.items()
        if not result["available"]
    ]

    if missing:
        print("WARNING: Some source reports were unavailable:")
        for name in missing:
            print(f" - {name}: {sources[name].get('error')}")

    print("Gemini called: No")
    print("Production pipeline changed: No")


if __name__ == "__main__":
    main()
