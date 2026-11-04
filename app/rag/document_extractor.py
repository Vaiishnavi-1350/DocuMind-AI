from pathlib import Path
import csv
import json


# ============================================================
# SUPPORTED DOCUMENT FORMATS
# ============================================================

SUPPORTED_FORMATS = {
    ".pdf",
    ".txt",
    ".json",
    ".docx",
    ".csv",
    ".sql",
    ".jpg",
    ".jpeg",
    ".png",
}


# ============================================================
# TEXT FILE READER
# ============================================================

def read_text_file(file_path: Path) -> str:
    """Read text using UTF-8, with a Windows encoding fallback."""

    try:
        return file_path.read_text(encoding="utf-8-sig")

    except UnicodeDecodeError:
        return file_path.read_text(encoding="cp1252")


# ============================================================
# TXT EXTRACTION
# ============================================================

def extract_txt(file_path: Path) -> str:

    text = read_text_file(file_path).strip()

    if not text:
        raise ValueError("The TXT file contains no readable text.")

    return text


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(file_path: Path) -> str:

    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)

    except UnicodeDecodeError:
        with open(file_path, "r", encoding="cp1252") as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON file: {error}")

    text = json.dumps(
        data,
        indent=2,
        ensure_ascii=False
    )

    if not text.strip():
        raise ValueError("The JSON file contains no readable data.")

    return text


# ============================================================
# DOCX EXTRACTION
# ============================================================

def extract_docx(file_path: Path) -> str:

    try:
        from docx import Document as WordDocument

    except ImportError:
        raise ImportError(
            "DOCX support requires python-docx. "
            "Install it using: pip install python-docx"
        )

    document = WordDocument(str(file_path))
    extracted_content = []

    # Extract paragraphs
    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:
            extracted_content.append(text)

    # Extract tables
    for table_index, table in enumerate(document.tables, start=1):

        extracted_content.append(
            f"\nTable {table_index}:"
        )

        for row in table.rows:

            cells = [
                cell.text.strip().replace("\n", " ")
                for cell in row.cells
            ]

            extracted_content.append(" | ".join(cells))

    text = "\n".join(extracted_content).strip()

    if not text:
        raise ValueError("The DOCX file contains no readable text.")

    return text


# ============================================================
# CSV EXTRACTION
# ============================================================

def extract_csv(file_path: Path) -> str:

    try:
        content = read_text_file(file_path)

    except Exception as error:
        raise ValueError(f"Unable to read CSV file: {error}")

    if not content.strip():
        raise ValueError("The CSV file is empty.")

    try:
        dialect = csv.Sniffer().sniff(content[:8192])
    except csv.Error:
        dialect = csv.excel

    rows = list(csv.reader(content.splitlines(), dialect))

    if not rows:
        raise ValueError("The CSV file contains no rows.")

    headers = rows[0]
    extracted_content = []

    for row_number, row in enumerate(rows[1:], start=1):

        row_data = []

        for index, value in enumerate(row):

            if index < len(headers):
                column_name = headers[index].strip()
            else:
                column_name = f"Column_{index + 1}"

            row_data.append(f"{column_name}: {value.strip()}")

        if row_data:
            extracted_content.append(
                f"Row {row_number}: " + "; ".join(row_data)
            )

    if not extracted_content:
        extracted_content.append(
            "Columns: " + ", ".join(headers)
        )

    return "\n".join(extracted_content)


# ============================================================
# SQL EXTRACTION
# ============================================================

def extract_sql(file_path: Path) -> str:
    """
    Read SQL scripts as plain text.
    Uploaded SQL is NEVER executed.
    """

    text = read_text_file(file_path).strip()

    if not text:
        raise ValueError("The SQL file contains no readable text.")

    return text


# ============================================================
# IMAGE OCR EXTRACTION
# ============================================================
def extract_image(file_path: Path) -> str:

    try:
        from PIL import Image
        import pytesseract

    except ImportError:
        raise ImportError(
            "Image OCR requires Pillow and pytesseract."
        )

    # Configure the installed Tesseract executable
    tesseract_path = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    if not Path(tesseract_path).exists():
        raise FileNotFoundError(
            "Tesseract OCR executable was not found."
        )

    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    try:

        with Image.open(file_path) as image:

            image.verify()

        with Image.open(file_path) as image:

            image = image.convert("RGB")

            text = pytesseract.image_to_string(
                image,
                lang="eng"
            ).strip()

    except Exception as error:

        raise ValueError(
            f"Image OCR failed: {error}"
        )

    if not text:

        raise ValueError(
            "No readable text was detected in the image."
        )

    return text


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf(file_path: Path) -> tuple[str, int]:

    from langchain_community.document_loaders import PyPDFLoader

    documents = PyPDFLoader(str(file_path)).load()

    if not documents:
        raise ValueError("The PDF file contains no readable pages.")

    page_texts = []

    for document in documents:

        text = document.page_content.strip()

        if text:
            page_number = document.metadata.get("page", 0) + 1

            page_texts.append(
                f"[Page {page_number}]\n{text}"
            )

    extracted_text = "\n\n".join(page_texts)

    if not extracted_text:
        raise ValueError("The PDF file contains no readable text.")

    return extracted_text, len(documents)


# ============================================================
# MAIN DOCUMENT EXTRACTION FUNCTION
# ============================================================

def extract_document(file_path: Path) -> dict:
    """
    Automatically identifies the document format
    and extracts its text.

    Returns:
        {
            "text": extracted text,
            "document_type": file format,
            "pages": page count
        }
    """

    file_path = Path(file_path)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    document_type = extension.lstrip(".")
    pages = 1

    # PDF
    if extension == ".pdf":

        text, pages = extract_pdf(file_path)

    # TXT
    elif extension == ".txt":

        text = extract_txt(file_path)

    # JSON
    elif extension == ".json":

        text = extract_json(file_path)

    # DOCX
    elif extension == ".docx":

        text = extract_docx(file_path)

    # CSV
    elif extension == ".csv":

        text = extract_csv(file_path)

    # SQL
    elif extension == ".sql":

        text = extract_sql(file_path)

    # JPG, JPEG, PNG
    elif extension in {".jpg", ".jpeg", ".png"}:

        text = extract_image(file_path)

    else:
        raise ValueError("Unsupported document format.")

    return {
        "text": text,
        "document_type": document_type,
        "pages": pages
    }