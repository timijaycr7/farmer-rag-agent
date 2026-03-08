# Farmer RAG Agent

Farmer RAG Agent is an AI-powered agricultural assistant that combines retrieval-augmented generation (RAG) with a simple web chat frontend.

It uses:
- A local FAISS vector database (`farmer_vector_db`) for agricultural knowledge retrieval
- A Groq-hosted LLM for answer generation
- FastAPI for backend APIs and frontend serving

## Features

- Ask farming questions from a browser UI (`/`) or API (`/ask`)
- Retrieve domain-specific context from local FAISS embeddings
- Generate structured, readable answers with LangGraph tool-calling
- Run RAG evaluation and experiment tracking
- Compare a provided answer against retrieved vector DB content via `evaluate_rag.py`

## Architecture

1. User sends a question from the frontend or API.
2. LangGraph assistant invokes the retriever tool.
3. Retriever pulls top-k chunks from `farmer_vector_db`.
4. Groq LLM produces the final response.
5. FastAPI returns JSON and/or renders the static frontend.

## Project Layout

```text
app.py                   FastAPI app, endpoints, frontend route
rag_agent.py             RAG pipeline (embeddings, FAISS, retriever, graph)
evaluate_rag.py          Evaluation script + retrieved-answer comparison flow
evaluation.py            RAGAS evaluator wrapper
experiment_tracker.py    Experiment persistence
config.py                Environment-driven settings
static/index.html        Frontend chat UI
farmer_vector_db/        Local FAISS index
evaluations/             Saved evaluation outputs
logs/                    Runtime logs
```

## Requirements

- Python 3.10+
- Groq API key
- Existing vector DB at `farmer_vector_db`

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` in project root:

```dotenv
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

GROQ_API_KEY=your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
LLM_TEMPERATURE=0

# Optional: mainly for some RAGAS/OpenAI-backed setups
OPENAI_API_KEY=your_openai_key

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DB_PATH=farmer_vector_db
RETRIEVER_K=5

LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_FORMAT=json

EVALUATION_ENABLED=true
EXPERIMENT_TRACKING_ENABLED=true
EVALUATION_CACHE_DIR=evaluation_cache
EXPERIMENT_DB_PATH=experiments.db
RAGAS_BATCH_SIZE=4
RAGAS_TIMEOUT=300
```

3. Start the app:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

4. Open frontend:

```text
http://localhost:8000
```

## API Endpoints

- `GET /` serve chat frontend
- `GET /health` health status
- `POST /ask` ask a farming question
- `POST /evaluate` run RAG evaluation
- `GET /experiments` list tracked experiments
- `GET /experiments/{experiment_id}` fetch a single experiment
- `GET /experiments/export/json` export experiments

## Frontend Usage

1. Start the server.
2. Open `http://localhost:8000`.
3. Ask farming questions in plain language.
4. The UI sends requests to `/ask` and displays formatted answers.

## Evaluation Script (Updated)

`evaluate_rag.py` now includes a direct comparison workflow for the prompt:

- Question: `Give me only the definition of crop rotation`
- Provided answer: your supplied definition text

What it does:

1. Retrieves top chunks from `farmer_vector_db` for the question.
2. Extracts a crop-rotation definition from retrieved text when available.
3. Computes similarity metrics:
- `best_chunk_similarity_ratio`
- `definition_similarity_ratio`
4. Generates a live RAG answer for side-by-side comparison.
5. Writes results to `evaluation_report.json` under:
- `comparison`
- `rag_generated_answer`

Run it with:

```bash
python evaluate_rag.py
```

## Security Notes

- Do not commit real API keys to git.
- Keep `.env` private and rotate any exposed keys immediately.
- Use placeholder values in `.env.example`.

## Troubleshooting

- App fails at startup:
	- Confirm `GROQ_API_KEY` is set and valid.
	- Confirm `farmer_vector_db/` exists.
- Empty/poor retrieval:
	- Increase `RETRIEVER_K`.
	- Rebuild/refresh vector index quality.
- Evaluation warnings/errors:
	- Verify dependency versions for `ragas` and related integrations.

## License

Provided as-is for educational and research use.
