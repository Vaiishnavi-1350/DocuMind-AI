# DocuMind AI

**An AI-powered document intelligence platform using Retrieval-Augmented Generation (RAG).**

DocuMind AI enables users to upload PDF documents, ask questions about their content, and receive AI-generated answers supported by retrieved document context.

## Features

- PDF document upload and ingestion
- Document-based question answering
- BGE-M3 embeddings
- Qdrant vector database
- Hybrid retrieval and Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- Gemini-powered answer generation
- User authentication and access tokens
- Document management and chat history
- Subscription and payment workflow
- Offline evaluation utilities

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| API documentation | Swagger UI |
| Embeddings | BGE-M3 |
| Vector database | Qdrant |
| Reranking | Cross-encoder |
| Language model | Google Gemini |
| Database | SQLite, SQLAlchemy |
| PDF processing | PyPDF |
| Frontend | HTML, CSS, JavaScript |
| Containerization | Docker Compose |
| CI/CD | GitHub Actions |

## Project Structure

```text
documind-ai/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth/
│   ├── database/
│   ├── rag/
│   └── evaluation/
├── frontend/
├── data/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11 or another Python version compatible with the installed dependencies
- Docker Desktop
- Git
- A Google Gemini API key for features that call Gemini

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd documind-ai
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local `.env` file by copying the template:

```powershell
Copy-Item .env.example .env
```

Set the required values in `.env`, including a secure `JWT_SECRET_KEY`. Configure `GEMINI_API_KEY` and `GEMINI_MODEL` if you intend to use Gemini-powered generation.

**Never commit `.env` or expose API keys, passwords, or JWT secrets.**

### 5. Start Qdrant

Start Docker Desktop, then run:

```powershell
docker compose up -d qdrant
```

Check its health endpoint:

```powershell
Invoke-RestMethod http://localhost:6333/healthz
```

### 6. Start the application

From the repository root:

```powershell
uvicorn app.main:app --reload
```

Open the application at:

- Application: http://127.0.0.1:8000
- Swagger API documentation: http://127.0.0.1:8000/docs

These URLs assume the application serves the frontend at its root URL.

## Environment Configuration

The `.env.example` file documents configuration options for:

- Application metadata and environment
- Database connection
- JWT authentication
- Qdrant connection and collection
- Embedding and reranking models
- Gemini generation
- Retrieval and chunking
- Upload storage
- CORS

Use `.env.example` as a template. Keep real credentials in your local `.env` file or your deployment platform's secret manager.

## Docker

Docker Compose currently defines the Qdrant service and a persistent storage volume.

Start Qdrant:

```powershell
docker compose up -d qdrant
```

Stop it:

```powershell
docker compose down
```

The FastAPI application is started separately using Uvicorn in the current development setup.

## Evaluation

The project includes offline evaluation utilities for assessing saved RAG answers and consolidating evaluation reports. Offline evaluation can be run without additional Gemini requests when the evaluation scripts use saved outputs.

Consult the `app/evaluation/` directory for the available scripts and reports.

## Security Notes

- Keep `.env` out of version control.
- Use a strong, unique JWT secret.
- Avoid committing uploaded documents, private chat history, databases, or personal data.
- Configure production CORS origins explicitly.
- Use HTTPS and production-grade secret management when deploying.

## Project Status

DocuMind AI is under active development. Docker deployment, automated CI/CD validation, and production deployment should be considered complete only after their workflows have been tested successfully.

## License

Add a license before distributing this project publicly.