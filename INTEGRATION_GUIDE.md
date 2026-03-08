# Production-Grade RAG System Implementation Guide

## Overview

This implementation adds production-grade evaluation, logging, and experiment tracking to the Farmer RAG Agent. The system measures RAG performance using RAGAS metrics and provides comprehensive logging and monitoring capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                     │
├──────────────────────────┬──────────────────────────────────────┤
│  Core RAG API            │  Evaluation & Tracking API          │
│  • /ask                  │  • /evaluate                        │
│  • /health               │  • /experiments (CRUD)              │
│                          │  • /experiments/export/json         │
└──────────────────────────┴──────────────────────────────────────┘
         │                          │
         v                          v
┌─────────────────────┐    ┌──────────────────────┐
│   RAG Agent         │    │  Evaluation Engine   │
│  rag_agent.py       │    │  evaluation.py       │
│  • Retriever        │    │  • RAGEvaluator      │
│  • LLM Invocation   │    │  • RAGAS Metrics     │
│  • LangGraph        │    │  • Result Caching    │
└─────────────────────┘    └──────────────────────┘
         │                          │
         └──────────────┬───────────┘
                        v
         ┌──────────────────────────┐
         │ Structured Logging       │
         │ logger.py                │
         │ • JSON/Text Formats      │
         │ • Log Rotation           │
         │ • Error Tracking         │
         └──────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         v                             v
   ┌──────────────┐          ┌──────────────────┐
   │ Experiment   │          │ Application      │
   │ Tracking     │          │ Logs             │
   │ experiments. │          │ logs/app.log     │
   │ db (SQLite)  │          │ logs/errors.log  │
   └──────────────┘          └──────────────────┘
```

## File Structure

```
farmer-rag-agent/
├── app.py                    # Main FastAPI application
├── rag_agent.py              # LangGraph RAG pipeline
├── config.py                 # Configuration management
├── logger.py                 # Structured logging setup
├── evaluation.py             # RAGAS evaluation module
├── experiment_tracker.py      # Experiment persistence
├── evaluate_rag.py           # Evaluation script
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── EVALUATION_GUIDE.md        # User guide
├── INTEGRATION_GUIDE.md       # This file
├── logs/                     # Application logs (auto-created)
├── evaluations/              # Evaluation results (auto-created)
├── evaluation_cache/         # Cache for evaluations (auto-created)
├── experiments.db            # Experiment database (auto-created)
└── static/
    └── index.html            # Frontend UI
```

## Key Components

### 1. Configuration Management (`config.py`)

**Purpose**: Centralized configuration from environment variables

**Features**:
- Type-safe settings using Pydantic
- Environment variable support
- Default values
- Automatic directory creation

**Usage**:
```python
from config import settings

print(settings.GROQ_API_KEY)
print(settings.LOG_LEVEL)
print(settings.EVALUATION_ENABLED)
```

### 2. Structured Logging (`logger.py`)

**Purpose**: Production-grade logging with multiple formats and handlers

**Features**:
- JSON and text formatting
- Log rotation (10MB per file, 5 backups)
- Separate error log
- Experiment-specific logs
- Multiple output handlers (console, file, error file)

**Usage**:
```python
from logger import get_logger

logger = get_logger("my_module")
logger.info("Message", extra={"key": "value"})
logger.error("Error occurred", extra={"error": str(e)})
```

### 3. RAG Evaluation (`evaluation.py`)

**Purpose**: RAGAS-based evaluation of RAG performance

**Components**:
- **RAGEvaluator**: Main evaluation class
  - `evaluate_samples()`: Run evaluation
  - `save_results()`: Persist results
  - `get_summary()`: Get metrics summary

- **EvaluationCache**: Caching system
  - `get_cache_key()`: Generate cache key
  - `load_cached_results()`: Load from cache
  - `save_cached_results()`: Save to cache

**Metrics Evaluated**:
- Faithfulness
- Answer Relevancy
- Context Relevancy  
- Context Precision

**Usage**:
```python
from evaluation import RAGEvaluator
from config import settings

evaluator = RAGEvaluator(llm=llm, experiment_name="test")
results = evaluator.evaluate_samples(
    questions=["Q1", "Q2"],
    contexts=[["C1"], ["C2"]],
    answers=["A1", "A2"],
    ground_truths=["T1", "T2"]
)
evaluator.save_results()
```

### 4. Experiment Tracking (`experiment_tracker.py`)

**Purpose**: Persistent storage and retrieval of experiment metadata

**Features**:
- SQLite database backend
- CRUD operations
- Filtering and search
- Export to JSON
- Experiment result dataclass

**Usage**:
```python
from experiment_tracker import get_tracker

tracker = get_tracker()
exp_id = tracker.save_experiment(
    experiment_name="my_eval",
    config={...},
    metrics={...},
    num_samples=10,
    status="success"
)

experiments = tracker.list_experiments(
    experiment_name="my_eval",
    limit=10
)
```

### 5. Enhanced RAG Agent (`rag_agent.py`)

**Changes from original**:
- Added comprehensive logging at each step
- Component initialization functions
- Error handling and logging
- New `query_rag()` API function
- Configurable parameters

**Usage**:
```python
from rag_agent import query_rag

result = query_rag("How to grow tomatoes?")
print(result["answer"])
```

### 6. Enhanced FastAPI App (`app.py`)

**New Endpoints**:
- `POST /evaluate` - Run RAGAS evaluation
- `GET /experiments` - List experiments
- `GET /experiments/{id}` - Get experiment details
- `GET /experiments/export/json` - Export all experiments
- `GET /health` - Health check

**Features**:
- Structured error handling
- Request/response validation
- Comprehensive logging
- Cache integration
- Experiment persistence

## Data Flow

### Query Flow
```
User Request (/ask)
    ↓
FastAPI Endpoint (with logging)
    ↓
query_rag() in rag_agent.py
    ↓
Retriever (logs context retrieval)
    ↓
LLM (logs invocation)
    ↓
Response (logs result)
    ↓
Return to User
```

### Evaluation Flow
```
Evaluation Request (/evaluate)
    ↓
Check Cache
    ├→ Cache Hit: Return cached results
    └→ Cache Miss: Continue
    ↓
RAGEvaluator
    ├→ Prepare Dataset (with logging)
    ├→ Run RAGAS Metrics (with logging)
    └→ Convert Results
    ↓
Save Results to File
    ↓
Save to Cache
    ↓
Track in Database
    ↓
Return Metrics
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Required:
```env
GROQ_API_KEY=your_key
OPENAI_API_KEY=your_key  # For RAGAS evaluation
```

Optional (all have defaults):
```env
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json         # json or text
DEBUG=false
EVALUATION_ENABLED=true
EXPERIMENT_TRACKING_ENABLED=true
```

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Application

```bash
# Development
uvicorn app:app --reload

# Production
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 4. Access Services

- **API Documentation**: http://localhost:8000/docs
- **Chat UI**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health

## Usage Examples

### Example 1: Running RAG Query

```python
import requests

response = requests.post("http://localhost:8000/ask", json={
    "question": "How should I prepare soil for planting rice?"
})

print(response.json())
```

### Example 2: Evaluating RAG Performance

```python
import requests

eval_data = {
    "questions": [
        "How to grow tomatoes?",
        "What is crop rotation?"
    ],
    "contexts": [
        ["Tomatoes need full sunlight...", "Water regularly..."],
        ["Crop rotation involves...", "It prevents disease..."]
    ],
    "answers": [
        "Plant tomatoes in full sunlight and water regularly.",
        "Crop rotation involves planting different crops in succession."
    ],
    "ground_truths": [
        "Tomatoes require sunlight, proper watering, and temperature control.",
        "Crop rotation is a practice of growing different crops on the same land."
    ],
    "experiment_name": "tomato_rotation_eval"
}

response = requests.post(
    "http://localhost:8000/evaluate",
    json=eval_data
)

print(response.json())
```

### Example 3: Listing Experiments

```python
import requests

response = requests.get("http://localhost:8000/experiments?limit=10")
experiments = response.json()

for exp in experiments["experiments"]:
    print(f"{exp['experiment_name']}: {exp['status']}")
```

### Example 4: Running Evaluation Script

```bash
python evaluate_rag.py
```

This runs a complete evaluation pipeline with sample agricultural data.

## Logging

### Log Files

```
logs/
├── app.log              # All logs
├── errors.log           # Errors only
└── experiment_*.jsonl   # Per-experiment logs
```

### Log Rotation

- **Max Size**: 10MB per file
- **Backup Count**: 5 files retained
- **Format**: ISO timestamp + structured data

### Viewing Logs

```bash
# Real-time
tail -f logs/app.log

# Last 50 lines
tail -50 logs/app.log

# Errors only
grep "ERROR" logs/app.log

# Specific query
grep "faithfulness" logs/app.log
```

### JSON Log Parsing

```bash
# Pretty print
jq '.' logs/app.log | head -50

# Filter by level
jq 'select(.level=="ERROR")' logs/app.log

# Extract metrics
jq '.metric_name' logs/experiment_*.jsonl
```

## Database

### Experiment Database Schema

```sql
CREATE TABLE experiments (
    experiment_id TEXT PRIMARY KEY,
    experiment_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    config TEXT NOT NULL (JSON),
    metrics TEXT NOT NULL (JSON),
    num_samples INTEGER,
    status TEXT NOT NULL,
    error_message TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX idx_experiment_name ON experiments(experiment_name);
CREATE INDEX idx_timestamp ON experiments(timestamp);
CREATE INDEX idx_status ON experiments(status);
```

### Querying Database

```python
from experiment_tracker import get_tracker

tracker = get_tracker()

# Get latest
latest = tracker.get_latest_experiment("my_eval")

# List with filters
results = tracker.list_experiments(
    experiment_name="my_eval",
    status="success",
    limit=20
)

# Export all
export_path = tracker.export_to_json()
```

## Performance Optimization

### Tips for Large Evaluations

1. **Increase Batch Size**: `RAGAS_BATCH_SIZE=8` for powerful machines
2. **Enable Caching**: Duplicate evaluations are cached
3. **Parallel Processing**: Run multiple evaluations in separate processes
4. **Log Level**: Set `LOG_LEVEL=WARNING` to reduce I/O

### Caching Strategy

- Cache key is hash of questions, contexts, answers
- Cache expires if inputs change
- Cache location: `evaluation_cache/`

### Database Optimization

- Indexes on `experiment_name`, `timestamp`, `status`
- Consider archiving old experiments
- Regular exports to JSON for backup

## Troubleshooting

### RAGAS Evaluation Fails

**Issue**: `ModuleNotFoundError: No module named 'ragas'`
**Solution**: `pip install ragas>=0.1.0`

**Issue**: OPENAI_API_KEY error
**Solution**: Ensure `OPENAI_API_KEY` is set in `.env`

**Issue**: Timeout error
**Solution**: Increase `RAGAS_TIMEOUT=600`

### Logging Issues

**Issue**: No logs appearing
**Solution**: 
- Check `LOG_LEVEL` setting
- Verify `logs/` directory permissions
- Check `LOG_FILE` path

**Issue**: Log file too large
**Solution**: Archive old logs or reduce `LOG_LEVEL`

### Database Issues

**Issue**: "database is locked"
**Solution**: Wait for other processes to complete, or reduce SQLite timeout

### Import Errors

**Issue**: Module import fails
**Solution**: 
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Verify imports
python -c "from config import settings; print('OK')"
```

## Best Practices

### 1. Experiment Naming

Use descriptive, consistent names:
```python
# Good
"eval_model_v2_10samples_with_groundtruth"
"baseline_faithfulness_metric_test"

# Avoid
"test", "eval", "exp1"
```

### 2. Ground Truth Data

Always provide when possible:
```python
# Always include
ground_truths=["reference1", "reference2"]

# Don't skip
ground_truths=None  # Less informative
```

### 3. Logging

Use structured logging:
```python
# Good
logger.info("Query processed", extra={
    "question": q,
    "answer_length": len(a),
    "retrieval_time": t
})

# Avoid
logger.info(f"Query: {q}, Answer: {a}")  # String interpolation
```

### 4. Error Handling

Always log and track errors:
```python
try:
    result = evaluate_samples(...)
except Exception as e:
    logger.error(f"Evaluation failed: {str(e)}", extra={"error": str(e)})
    tracker.save_experiment(..., status="failed", error_message=str(e))
    raise
```

### 5. Regular Exports

```bash
# Daily export
0 2 * * * curl http://localhost:8000/experiments/export/json
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3'
services:
  farmer-rag:
    build: .
    ports:
      - "8000:8000"
    environment:
      GROQ_API_KEY: ${GROQ_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LOG_LEVEL: WARNING
      DEBUG: "false"
    volumes:
      - ./logs:/app/logs
      - ./evaluations:/app/evaluations
```

### Environment Variables

For production:
```env
DEBUG=false
LOG_LEVEL=WARNING
EVALUATION_ENABLED=true
EXPERIMENT_TRACKING_ENABLED=true
RAGAS_BATCH_SIZE=8
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Evaluation Metrics**: Faithfulness, Answer Relevancy
2. **System Health**: API response time, error rate
3. **Database**: Table size, query performance
4. **Logs**: Error frequency, anomaly detection

### Setting Up Monitoring

```python
# Example: Check if faithfulness is declining
latest = tracker.get_latest_experiment("main_eval")
faithfulness = latest.metrics["faithfulness"]["mean"]

if faithfulness < 0.7:
    logger.warning(f"Faithfulness below threshold: {faithfulness}")
    # Send alert
```

## Summary

This implementation provides:

✅ **RAGAS Evaluation**: Measure RAG performance with industry-standard metrics
✅ **Structured Logging**: Production-grade logging with JSON format
✅ **Experiment Tracking**: Persistent storage and retrieval
✅ **Caching**: Avoid redundant evaluations
✅ **Error Handling**: Comprehensive error logging and recovery
✅ **API Integration**: Easy-to-use REST endpoints
✅ **Documentation**: Complete user and integration guides

The system is ready for production deployment with monitoring, logging, and evaluation capabilities.
