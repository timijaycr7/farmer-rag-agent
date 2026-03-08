# Quick Reference Guide

## Quick Start (5 minutes)

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GROQ_API_KEY and OPENAI_API_KEY
```

### 2. Run Application
```bash
uvicorn app:app --reload
```

### 3. Test
```bash
# Query the RAG
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to grow tomatoes?"}'

# Run evaluation
python evaluate_rag.py
```

## Common Commands

### Start Application
```bash
# Dev mode with hot reload
uvicorn app:app --reload

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### View Logs
```bash
# All logs
tail -f logs/app.log

# Errors only
tail -f logs/errors.log

# Search
grep "faithfulness" logs/app.log
tail -50 logs/app.log | grep "ERROR"
```

### Check Health
```bash
curl http://localhost:8000/health
```

### Run Evaluation
```bash
# Using script
python evaluate_rag.py

# Using API
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "questions": ["Q1", "Q2"],
    "contexts": [["C1"], ["C2"]],
    "answers": ["A1", "A2"],
    "ground_truths": ["T1", "T2"]
  }'
```

### List Experiments
```bash
# All experiments
curl http://localhost:8000/experiments

# Filter by status
curl "http://localhost:8000/experiments?status=success"

# Get specific experiment
curl http://localhost:8000/experiments/{experiment_id}

# Export all
curl http://localhost:8000/experiments/export/json
```

## Environment Variables

```env
# Required
GROQ_API_KEY=sk-...
OPENAI_API_KEY=sk-...

# Optional with defaults
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
EVALUATION_ENABLED=true
EXPERIMENT_TRACKING_ENABLED=true
RAGAS_BATCH_SIZE=4
RAGAS_TIMEOUT=300
```

## API Endpoints Cheat Sheet

### Core RAG
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ask` | Query the RAG system |
| GET | `/health` | Health check |

### Evaluation
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/evaluate` | Run RAGAS evaluation |

### Experiments
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/experiments` | List all experiments |
| GET | `/experiments?experiment_name=X` | Filter by name |
| GET | `/experiments?status=success` | Filter by status |
| GET | `/experiments/{id}` | Get specific experiment |
| GET | `/experiments/export/json` | Export all to JSON |

## Code Snippets

### Log Messages
```python
from logger import get_logger

logger = get_logger("my_module")

# Info
logger.info("Operation started")

# With data
logger.info("Query processed", extra={"question": q, "time": t})

# Error
logger.error(f"Failed: {e}", extra={"error": str(e)})
```

### Run Evaluation
```python
from evaluation import RAGEvaluator
from config import settings
from langchain_groq import ChatGroq

llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY)
evaluator = RAGEvaluator(llm=llm, experiment_name="my_test")

results = evaluator.evaluate_samples(
    questions=["Q1", "Q2"],
    contexts=[["C1"], ["C2"]],
    answers=["A1", "A2"],
    ground_truths=["T1", "T2"]
)

evaluator.save_results()
print(evaluator.get_summary())
```

### Query RAG
```python
from rag_agent import query_rag

result = query_rag("How to grow tomatoes?")
print(result["answer"])
print(result["status"])
```

### Track Experiments
```python
from experiment_tracker import get_tracker

tracker = get_tracker()

# Save experiment
exp_id = tracker.save_experiment(
    experiment_name="my_eval",
    config={"batch_size": 4},
    metrics={"faithfulness": 0.85},
    num_samples=10,
    status="success"
)

# List experiments
experiments = tracker.list_experiments(experiment_name="my_eval")

# Export
path = tracker.export_to_json()
```

## File Locations

```
logs/app.log                    # Main application log
logs/errors.log                 # Errors only
logs/experiment_*.jsonl         # Per-experiment logs
evaluations/                    # Evaluation result files
evaluation_cache/               # Cached evaluation results
experiments.db                  # SQLite experiment database
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import error | `pip install -r requirements.txt --force-reinstall` |
| RAGAS fails | `export OPENAI_API_KEY=sk-...` |
| No logs | Check `ls -la logs/` and `echo $LOG_LEVEL` |
| API won't start | Check port: `lsof -i :8000` |
| Database locked | Wait or restart application |

## Performance Tips

- Increase `RAGAS_BATCH_SIZE` for faster evaluation
- Enable `LOG_FORMAT=json` for log aggregation
- Set `LOG_LEVEL=WARNING` in production
- Cache evaluations (automatic)
- Export experiments regularly

## Next Steps

1. **Read**: See [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) for detailed usage
2. **Integrate**: Check [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for architecture
3. **Deploy**: Use Docker file for production deployment
4. **Monitor**: Set up log aggregation and alerting

## Support Resources

- API Docs: http://localhost:8000/docs
- Logs: `logs/app.log`
- Examples: `evaluate_rag.py`
- Configuration: `.env`
