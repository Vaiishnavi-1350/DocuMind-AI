# DocuMind AI

**An AI-Powered Document Intelligence Platform Using Retrieval-Augmented Generation (RAG)**

DocuMind AI is an intelligent document question-answering platform that allows users to upload PDF documents, retrieve relevant information, and receive AI-generated answers grounded in document context.

It combines semantic embeddings, hybrid retrieval, Reciprocal Rank Fusion (RRF), and cross-encoder reranking to improve the relevance of retrieved information.

## Features

- PDF document upload and ingestion
- Document-based question answering
- BGE-M3 semantic embeddings
- Qdrant vector database integration
- Hybrid retrieval with Reciprocal Rank Fusion (RRF)
- Cross-encoder document reranking
- Google Gemini-powered answer generation
- JWT-based user authentication
- Document management and chat history
- Subscription and payment workflow prototype
- Offline RAG answer evaluation using saved outputs

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| API Documentation | Swagger UI |
| Embeddings | BGE-M3 |
| Vector Database | Qdrant |
| Retrieval | Hybrid Search, RRF |
| Reranking | Cross-Encoder |
| Language Model | Google Gemini |
| Database | SQLite, SQLAlchemy |
| Authentication | JWT, pwdlib |
| PDF Processing | PyPDF |
| Frontend | HTML, CSS, JavaScript |
| Containerization | Docker Compose |
| Continuous Integration | GitHub Actions |

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

- Python 3.12 (tested development environment)
- Git
- Docker Desktop
- Google Gemini API key for AI answer generation

## Installation and Setup

### 1. Clone the repository

```bash
git clone <https://github.com/Vaiishnavi-1350/DocuMind-AI>
cd documind-ai
```

### 2. Create a virtual environment

**Windows PowerShell:**

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

Create a local `.env` file using the example template:

```powershell
Copy-Item .env.example .env
```

Configure the required environment variables, including:

- `JWT_SECRET_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Refer to `.env.example` for the complete configuration.

**Security:** Never commit your `.env` file or expose API keys, passwords, or authentication secrets.

### 5. Start Qdrant

Make sure Docker Desktop is running.

```powershell
docker compose up -d qdrant
```

Check the Qdrant health endpoint:

```powershell
Invoke-RestMethod http://localhost:6333/healthz
```

### 6. Run the FastAPI application

From the project root:

```powershell
uvicorn app.main:app --reload
```

Access the application:

- Application: http://127.0.0.1:8000
- Swagger API Documentation: http://127.0.0.1:8000/docs

These URLs assume the application serves the frontend at its root URL.

## Environment Configuration

The `.env.example` file provides configuration for:

- Application settings
- Database connection
- JWT authentication
- Qdrant connection and collection
- Embedding and reranking models
- Gemini API integration
- Retrieval and document chunking
- File upload storage
- CORS configuration

Keep all actual credentials and secrets in your local `.env` file or deployment secret manager.

## Docker Configuration

The current Docker Compose configuration runs the Qdrant vector database with persistent storage.

Start Qdrant:

```powershell
docker compose up -d qdrant
```

Stop Qdrant:

```powershell
docker compose down
```

The FastAPI application currently runs separately through Uvicorn. A complete containerized application stack is a future improvement.

## Offline Evaluation

DocuMind AI includes an offline evaluation module for assessing saved question-answering results.

The evaluation workflow:

- Uses previously saved JSON and SQLite chat history.
- Matches saved answers against benchmark questions.
- Generates evaluation reports.
- Avoids additional Gemini API calls.
- Does not modify the production RAG pipeline.

Evaluation scripts are available in `app/evaluation/`.

## Security Considerations

- Keep `.env` and all credentials private.
- Use a strong, unique JWT secret.
- Avoid committing private documents, databases, chat histories, or personal information.
- Configure production CORS origins explicitly.
- Use HTTPS and secure secret management for deployment.

## Project Status

DocuMind AI is an actively developed project.

**Completed:**
- Core document-based RAG functionality
- Hybrid retrieval and reranking
- User authentication and chat history
- Offline answer evaluation
- GitHub Actions CI validation

**Future Improvements:**
- Complete Docker application stack
- Continuous Deployment (CD)
- Production deployment
- Further evaluation and performance improvements

## License

A license has not yet been added. Usage and redistribution permissions will be defined when a license is selected.