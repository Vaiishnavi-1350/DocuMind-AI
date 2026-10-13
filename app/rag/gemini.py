# ============================================================
# DOCUMIND AI - GEMINI GENERATION
#
# Hybrid RAG
#     ↓
# Reranked document chunks
#     ↓
# Grounded Gemini
#     ↓
# Answer
# ============================================================

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)

TEMPERATURE = float(
    os.getenv(
        "GEMINI_TEMPERATURE",
        "0.1",
    )
)

MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "GEMINI_MAX_OUTPUT_TOKENS",
        "1024",
    )
)


# ============================================================
# API KEY
# ============================================================

def _get_api_key() -> str:
    """
    Get Gemini API key from .env.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file."
        )

    return api_key


# ============================================================
# CREATE GEMINI MODEL
# ============================================================

def get_gemini_model() -> ChatGoogleGenerativeAI:
    """
    Create the configured Gemini model.
    """

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,

        google_api_key=_get_api_key(),

        temperature=TEMPERATURE,

        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are DocuMind AI, a document question-answering assistant.

Your task is to answer questions using the uploaded document
context supplied below.

GROUNDING RULES:

1. The uploaded document context is the primary source.

2. Use the retrieved document context to answer the question.

3. Do not invent facts, numbers, equations, names, or document
   content.

4. Information does NOT need to appear as an exact sentence in
   the document. If the retrieved context contains the relevant
   mathematical identity, formula, question, values, or
   intermediate information needed to solve the user's question,
   you may derive the answer from that information.

5. For mathematical questions:
   - Identify the relevant identity or formula from the document.
   - Use the values given by the user when they correspond to the
     mathematical problem.
   - Show the calculation step by step.
   - Give the final answer clearly.

6. If the document contains an answer key, use it to verify the
   result when applicable.

7. Do not use unrelated outside facts.

8. If the retrieved context genuinely does not contain enough
   relevant information to answer the question, respond exactly:

   "The information was not found in the uploaded document."

9. Do not reject a question merely because the exact wording of
   the question is not present in the retrieved context.

10. Preserve mathematical notation, numbers, equations, and
    terminology accurately.

11. Keep answers concise but useful.

12. Do not mention Qdrant, embeddings, retrieval, reranking,
    vector databases, or internal implementation details unless
    explicitly asked.

IMPORTANT:

If the document provides the mathematical identity needed to
solve a question, you may apply that identity to the values given
in the user's question.

The goal is grounded document-based reasoning, not exact-text
matching.
"""
# ============================================================
# BUILD CONTEXT
# ============================================================
def _build_context(
    documents: list[dict[str, Any]],
) -> str:
    """
    Build a clean grounded context from retrieved chunks.
    Every retrieved chunk is preserved in the context.
    """

    context_parts: list[str] = []

    MAX_CONTEXT_CHARS = 14000
    MAX_CHUNK_CHARS = 4000

    total_chars = 0

    for index, document in enumerate(documents, start=1):

        text = str(
            document.get("text", "")
        ).strip()

        if not text:
            continue

        if len(text) > MAX_CHUNK_CHARS:
            text = (
                text[:MAX_CHUNK_CHARS]
                .rstrip()
                + "..."
            )

        filename = str(
            document.get("filename", "")
        ).strip()

        page = document.get("page")

        if filename:
            source = filename
        else:
            source = "Uploaded document"

        if page is not None:
            source = f"{source}, page {page}"

        source_text = (
            f"[DOCUMENT CONTEXT {index}]\n"
            f"Source: {source}\n"
            f"{text}"
        )

        remaining = (
            MAX_CONTEXT_CHARS - total_chars
        )

        if remaining <= 0:
            break

        if len(source_text) > remaining:
            source_text = (
                source_text[:remaining]
                .rstrip()
                + "..."
            )

        context_parts.append(source_text)

        total_chars += len(source_text)

    return "\n\n".join(context_parts)
# ============================================================
# BUILD PROMPT
# ============================================================
def _build_prompt(
    question: str,
    documents: list[dict[str, Any]],
) -> str:

    context = _build_context(documents)

    if not context:
        context = (
            "No usable document context was retrieved."
        )

    return f"""
{SYSTEM_INSTRUCTION}

============================================================
UPLOADED DOCUMENT CONTEXT
============================================================

{context}

============================================================
USER QUESTION
============================================================

{question}

============================================================
HOW TO ANSWER
============================================================

First examine ALL supplied document context.

If the document contains the relevant formula, identity,
question, values, or answer-key information needed to solve
the question:

1. Identify the relevant information.
2. Apply the appropriate identity/formula.
3. Show the calculation.
4. Give the final answer.

The exact wording of the user's question does not have to
appear verbatim in the document.

However, do NOT introduce unrelated facts that are not
supported by the document.

If the supplied context truly contains insufficient relevant
information, respond exactly:

"The information was not found in the uploaded document."

============================================================
FINAL ANSWER
============================================================
"""
# ============================================================
# EXTRACT RESPONSE TEXT
# ============================================================

def _extract_response_text(
    response: Any,
) -> str:
    """
    Safely extract text from a LangChain Gemini response.

    Gemini may return:
        AIMessage(content="text")

    or:

        AIMessage(
            content=[
                {
                    "type": "text",
                    "text": "..."
                }
            ]
        )
    """

    if response is None:
        return ""

    # --------------------------------------------------------
    # Get content from AIMessage
    # --------------------------------------------------------

    content = getattr(
        response,
        "content",
        response,
    )

    if content is None:
        return ""

    # --------------------------------------------------------
    # Normal string response
    # --------------------------------------------------------

    if isinstance(content, str):

        return content.strip()

    # --------------------------------------------------------
    # Gemini structured content
    # --------------------------------------------------------

    if isinstance(content, list):

        parts: list[str] = []

        for item in content:

            # ----------------------------------------------
            # Plain string
            # ----------------------------------------------

            if isinstance(item, str):

                text = item.strip()

                if text:
                    parts.append(text)

                continue

            # ----------------------------------------------
            # Dictionary content block
            # ----------------------------------------------

            if isinstance(item, dict):

                text = item.get("text")

                if text is not None:

                    text = str(text).strip()

                    if text:
                        parts.append(text)

                continue

            # ----------------------------------------------
            # Object with .text
            # ----------------------------------------------

            text = getattr(
                item,
                "text",
                None,
            )

            if text is not None:

                text = str(text).strip()

                if text:
                    parts.append(text)

        return "\n".join(parts).strip()

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return str(content).strip()

# ============================================================
# GEMINI REQUEST
# ============================================================

def _invoke_gemini(
    prompt: str,
) -> str:
    """
    Send the grounded prompt to Gemini and safely
    extract the generated answer.
    """

    model = get_gemini_model()

    response = model.invoke(
        prompt
    )

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DEBUG - RAW GEMINI RESPONSE")
    print("=" * 70)

    print(
        "Response type:",
        type(response),
    )

    print(
        "Response metadata:",
        getattr(
            response,
            "response_metadata",
            None,
        ),
    )

    print(
        "Raw content:",
        getattr(
            response,
            "content",
            None,
        ),
    )

    print("=" * 70)

    # --------------------------------------------------------
    # EXTRACT ANSWER
    # --------------------------------------------------------

    answer = _extract_response_text(
        response
    )

    print(
        "Extracted answer:",
        repr(answer),
    )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if not answer:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return answer
# ============================================================
# PUBLIC FUNCTION
# ============================================================

def generate_answer(
    question: str,
    documents: list[dict[str, Any]],
) -> str:
    """
    Generate an answer from retrieved document chunks.

    Flow:

        question
             ↓
        retrieved chunks
             ↓
        grounded prompt
             ↓
        Gemini
             ↓
        answer
    """

    if not question or not question.strip():

        raise ValueError(
            "Question cannot be empty."
        )

    if not documents:

        return (
            "The information was not found "
            "in the uploaded document."
        )

    question = question.strip()

    prompt = _build_prompt(
        question=question,
        documents=documents,
    )

        # --------------------------------------------------------
    # ROBUST GEMINI RETRY HANDLING
    # --------------------------------------------------------
    #
    # Gemini can temporarily return:
    #
    #   429 RESOURCE_EXHAUSTED
    #   500 INTERNAL
    #   502 BAD_GATEWAY
    #   503 UNAVAILABLE
    #   504 DEADLINE_EXCEEDED
    #
    # These are generally transient errors.
    #
    # We use exponential backoff:
    #
    # Attempt 1
    #     ↓
    #   error
    #     ↓
    #   wait 2 sec
    #
    # Attempt 2
    #     ↓
    #   error
    #     ↓
    #   wait 4 sec
    #
    # Attempt 3
    #     ↓
    #   error
    #     ↓
    #   wait 8 sec
    #
    # Attempt 4
    #     ↓
    #   error
    #     ↓
    #   wait 16 sec
    #
    # Attempt 5
    #
    # --------------------------------------------------------

    max_attempts = 5

    last_error: Exception | None = None

    for attempt in range(
        max_attempts
    ):

        try:

            print(
                "\n" + "=" * 70
            )

            print(
                "GEMINI REQUEST"
            )

            print(
                "=" * 70
            )

            print(
                f"Attempt       : "
                f"{attempt + 1}/{max_attempts}"
            )

            print(
                f"Model         : "
                f"{GEMINI_MODEL}"
            )

            answer = _invoke_gemini(
                prompt
            )

            print(
                "Gemini generation successful."
            )

            print(
                "=" * 70
            )

            return answer

        except Exception as exc:

            last_error = exc

            error_text = str(
                exc
            ).lower()

            print(
                "\nGemini error:"
            )

            print(
                str(exc)
            )

            # ------------------------------------------------
            # MODEL CONFIGURATION ERRORS
            # ------------------------------------------------
            #
            # Do NOT retry these.
            # ------------------------------------------------

            model_error = any(
                phrase in error_text
                for phrase in [
                    "not found",
                    "not_found",
                    "does not exist",
                    "invalid model",
                    "model not available",
                    "unsupported model",
                ]
            )

            if model_error:

                raise RuntimeError(
                    f"Gemini model "
                    f"'{GEMINI_MODEL}' "
                    f"is not available.\n\n"
                    f"Check GEMINI_MODEL in "
                    f"your .env file.\n\n"
                    f"Original error: {exc}"
                ) from exc

            # ------------------------------------------------
            # AUTHENTICATION ERRORS
            # ------------------------------------------------
            #
            # Do NOT retry an invalid API key.
            # ------------------------------------------------

            authentication_error = any(
                phrase in error_text
                for phrase in [
                    "api key",
                    "api_key",
                    "authentication",
                    "unauthenticated",
                    "permission denied",
                    "invalid argument",
                ]
            )

            if authentication_error:

                raise RuntimeError(
                    "Gemini authentication/configuration "
                    "failed.\n\n"
                    "Please check GEMINI_API_KEY "
                    "in your .env file.\n\n"
                    f"Original error: {exc}"
                ) from exc

            # ------------------------------------------------
            # RETRYABLE TRANSIENT ERRORS
            # ------------------------------------------------

            retryable = any(
                phrase in error_text
                for phrase in [
                    "429",
                    "500",
                    "502",
                    "503",
                    "504",
                    "unavailable",
                    "temporarily",
                    "timeout",
                    "timed out",
                    "deadline exceeded",
                    "resource exhausted",
                    "internal server error",
                    "service unavailable",
                    "overloaded",
                    "high demand",
                ]
            )

            # ------------------------------------------------
            # LAST ATTEMPT
            # ------------------------------------------------

            if (
                not retryable
                or attempt >= max_attempts - 1
            ):

                break

            # ------------------------------------------------
            # EXPONENTIAL BACKOFF
            # ------------------------------------------------
            #
            # 2, 4, 8, 16 seconds
            # ------------------------------------------------

            wait_time = min(
                2 ** (attempt + 1),
                30
            )

            print(
                "\nGemini returned a "
                "temporary error."
            )

            print(
                f"Retrying in "
                f"{wait_time} seconds..."
            )

            print(
                f"Remaining attempts: "
                f"{max_attempts - attempt - 1}"
            )

            time.sleep(
                wait_time
            )

    # --------------------------------------------------------
    # ALL RETRIES FAILED
    # --------------------------------------------------------

    raise RuntimeError(
        "Gemini generation failed after "
        f"{max_attempts} attempts.\n\n"
        f"Model: {GEMINI_MODEL}\n\n"
        f"Last error: {last_error}"
    ) from last_error