
from pathlib import Path
import json
import csv

from docx import Document

from app.rag.document_extractor import extract_document


# ============================================================
# TEST DIRECTORY
# ============================================================

TEST_DIR = Path("tests/sample_documents")

TEST_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CREATE SAMPLE TXT
# ============================================================

txt_file = TEST_DIR / "sample.txt"

txt_file.write_text(
    """
    DocuMind AI is an AI-powered document intelligence platform.
    It uses BGE-M3 embeddings and Qdrant for document retrieval.
    """,
    encoding="utf-8"
)
# ============================================================
# CREATE SAMPLE JSON
# ============================================================

json_file = TEST_DIR / "sample.json"

json_file.write_text(
    json.dumps(
        {
            "project": "DocuMind AI",
            "technology": ["Python", "FastAPI", "Qdrant"],
            "status": "development"
        },
        indent=2
    ),
    encoding="utf-8"
)

# ============================================================
# CREATE SAMPLE DOCX
# ============================================================

docx_file = TEST_DIR / "sample.docx"

document = Document()

document.add_paragraph(
    "DocuMind AI document extraction test."
)

document.add_paragraph(
    "This document contains sample paragraphs."
)

document.save(docx_file)


# ============================================================
# CREATE SAMPLE CSV
# ============================================================

csv_file = TEST_DIR / "sample.csv"

with open(csv_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    writer.writerow(["Name", "Technology", "Status"])

    writer.writerow(
        ["DocuMind AI", "Python", "Development"]
    )

    writer.writerow(
        ["EmotionSenseAI", "TensorFlow", "Training"]
    )


# ============================================================
# CREATE SAMPLE SQL
# ============================================================

sql_file = TEST_DIR / "sample.sql"

sql_file.write_text(
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


# ============================================================
# CREATE SAMPLE PDF
# ============================================================

pdf_file = TEST_DIR / "sample.pdf"

try:

    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(pdf_file))

    pdf.drawString(
        100,
        750,
        "DocuMind AI PDF extraction test."
    )

    pdf.drawString(
        100,
        720,
        "PDF text extraction is working."
    )

    pdf.save()

except ImportError:

    print("PDF sample creation skipped: reportlab is not installed.")

# ============================================================
# CREATE SAMPLE IMAGE - PNG, JPG, JPEG
# ============================================================

try:

    from PIL import Image, ImageDraw, ImageFont

    image = Image.new(
        "RGB",
        (900, 250),
        "white"
    )

    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(
            "arial.ttf",
            32
        )
    except OSError:
        font = ImageFont.load_default()

    draw.text(
        (30, 80),
        "DocuMind AI OCR Test",
        fill="black",
        font=font
    )

    # PNG
    png_file = TEST_DIR / "sample.png"
    image.save(png_file, format="PNG")

    # JPG
    jpg_file = TEST_DIR / "sample.jpg"
    image.save(jpg_file, format="JPEG")

    # JPEG
    jpeg_file = TEST_DIR / "sample.jpeg"
    image.save(jpeg_file, format="JPEG")

    print("PNG, JPG, and JPEG samples created successfully.")

except Exception as error:

    print("Image sample creation failed:", error)


# ============================================================
# TEST ALL FORMATS
# ============================================================

print("\n" + "=" * 60)

print("DOCUMIND AI - MULTI-FORMAT EXTRACTION TEST")

print("=" * 60)


for file_path in TEST_DIR.iterdir():

    if not file_path.is_file():
        continue

    try:

        result = extract_document(file_path)

        print("\nFile:", file_path.name)

        print("Type:", result["document_type"])

        print("Pages:", result["pages"])

        print("Extracted text:")

        print(result["text"][:300])

        print("\nStatus: SUCCESS")

    except Exception as error:

        print("\nFile:", file_path.name)

        print("Status: FAILED")

        print("Error:", error)


print("\n" + "=" * 60)

print("MULTI-FORMAT TEST COMPLETED")

print("=" * 60)
