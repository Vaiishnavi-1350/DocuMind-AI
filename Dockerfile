
FROM python:3.10-slim

WORKDIR /app

# System dependencies for OCR and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch dependencies from PyPI
RUN pip install --no-cache-dir \
    filelock \
    fsspec \
    jinja2 \
    networkx \
    setuptools \
    sympy \
    typing-extensions

# Install CPU-only PyTorch without resolving dependencies again
RUN pip install --no-cache-dir \
    torch==2.14.0 \
    --no-deps \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY .env.example ./.env.example

# Create runtime directories
RUN mkdir -p /app/data/uploads

ENV PORT=10000

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

