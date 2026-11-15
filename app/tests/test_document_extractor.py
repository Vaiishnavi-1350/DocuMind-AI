
from pathlib import Path
import json
import csv
import sys

from docx import Document
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

from app.rag.document_extractor import extract_document


# ============================================================
# TEST DIRECTORY
# ============================================================

TEST_DIR = Path("app/tests/sample_documents")
TEST_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CREATE SAMPLE DOCUMENTS
# ============================================================

def create_sample_documents():

    # TXT
    (TEST_DIR / "sample.txt").write_text(
        "DocuMind AI is an AI-powered document intelligence platform. "
        "It uses BGE-M3 embeddings and Qdrant for document retrieval.",
        encoding="utf-8"
    )

    # JSON
    (TEST_DIR / "sample.json").write_text(
        json.dumps({
            "project": "DocuMind AI",
            "technology": ["Python", "FastAPI", "Qdrant"],
            "status": "development"
        }, indent=2),
        encoding="utf-8"
    )

    # DOCX
    document = Document()
    document.add_paragraph("DocuMind AI document extraction test.")
    document.add_paragraph("This document contains sample paragraphs.")
    document.save(TEST_DIR / "sample.docx")

    # CSV
    with open(TEST_DIR / "sample.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Technology", "Status"])
        writer.writerow(["DocuMind AI", "Python", "Development"])
        writer.writerow(["EmotionSenseAI", "TensorFlow", "Training"])

    # SQL
    (TEST_DIR / "sample.sql").write_text(
        """
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            filename VARCHAR(255),
            document_type VARCHAR(50)
        );

        SELECT * FROM documents;
        """,
        encoding="utf-8"
    )

    # PDF
    pdf = canvas.Canvas(str(TEST_DIR / "sample.pdf"))
    pdf.drawString(100, 750, "DocuMind AI PDF extraction test.")
    pdf.drawString(100, 720, "PDF text extraction is working.")
    pdf.save()

    # PNG, JPG, JPEG
    image = Image.new("RGB", (900, 250), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()

    draw.text(
        (30, 80),
        "DocuMind AI OCR Test",
        fill="black",
        font=font
    )

    image.save(TEST_DIR / "sample.png", format="PNG")
    image.save(TEST_DIR / "sample.jpg", format="JPEG")
    image.save(TEST_DIR / "sample.jpeg", format="JPEG")


# ============================================================
# TEST ALL NINE FORMATS
# ============================================================

def test_document_extraction():

    expected_formats = {
        ".pdf",
        ".txt",
        ".json",
        ".docx",
        ".csv",
        ".sql",
        ".jpg",
        ".jpeg",
        ".png"
    }

    print("\n" + "=" * 60)
    print("DOCUMIND AI - MULTI-FORMAT EXTRACTION TEST")
    print("=" * 60)

    create_sample_documents()

    sample_files = [
        path for path in TEST_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in expected_formats
    ]

    found_formats = {path.suffix.lower() for path in sample_files}

    missing_formats = expected_formats - found_formats

    if missing_formats:
        raise AssertionError(
            f"Missing sample formats: {missing_formats}"
        )

    passed = 0
    failed = 0

    for file_path in sorted(sample_files):

        try:
            result = extract_document(file_path)

            assert isinstance(result, dict), "Result must be a dictionary"

            assert result.get("text", "").strip(), (
                "Extracted text is empty"
            )

            assert result.get("document_type"), (
                "Document type is missing"
            )

            assert isinstance(result.get("pages"), int), (
                "Page count must be an integer"
            )

            assert result["pages"] > 0, (
                "Page count must be greater than zero"
            )

            print(f"\nFile: {file_path.name}")
            print(f"Type: {result['document_type']}")
            print(f"Pages: {result['pages']}")
            print(f"Extracted text: {result['text'][:200]}")
            print("Status: SUCCESS")

            passed += 1

        except Exception as error:

            print(f"\nFile: {file_path.name}")
            print("Status: FAILED")
            print(f"Error: {error}")

            failed += 1

    print("\n" + "=" * 60)
    print(f"TOTAL: {passed + failed}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 60)

    if failed > 0 or passed == 0:
        raise AssertionError(
            f"Document extraction tests failed: "
            f"{failed} failures out of 9 formats."
        )

    print("ALL DOCUMENT EXTRACTION TESTS PASSED!")
# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    try:
        test_document_extraction()
    except Exception as error:
        print(f"\nTEST SUITE FAILED: {error}")
        sys.exit(1)
