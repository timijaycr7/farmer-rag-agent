# RAG Evaluation & Logging Guide

This document describes the production-grade evaluation and logging infrastructure for the Farmer RAG Agent.

## Overview

The system includes:
- **RAGAS Evaluation**: Measure RAG performance with metrics like faithfulness, answer relevancy, and context precision
- **Structured Logging**: JSON and text-based logging with rotation and error tracking
- **Experiment Tracking**: Persistent storage of experiments and results in SQLite
- **Evaluation Caching**: Avoid redundant evaluations with intelligent caching
- **Production Grade**: Error handling, monitoring, and audit trails

## Features

### 1. RAGAS Evaluation Metrics

The system evaluates RAG performance using the following metrics:

- **Faithfulness**: Measures if the generated answer is faithful to the retrieved context
- **Answer Relevancy**: Evaluates if the answer is relevant to the question
- **Context Relevancy**: Measures if the retrieved context is relevant to the question
- **Context Precision**: Evaluates if the retrieved context contains useful information

### 2. Structured Logging

Comprehensive logging with multiple output formats:

```
logs/
├── app.log              # Main application log
├── errors.log           # Error-only log
├── experiment_*.jsonl   # Experiment-specific logs
```

**Log Formats:**
- JSON: Machine-readable, ideal for log aggregation systems
- Text: Human-readable, good for development

**Log Levels:**
- DEBUG: Detailed debug information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### 3. Experiment Tracking

Persistent storage of experiments with:
- Configuration parameters
- Evaluation metrics
- Timestamps
- Status (success/failed)
- Error messages and notes

## Setup

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Set required environment variables:

```env
# Required
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional (defaults provided)
LOG_LEVEL=INFO
LOG_FORMAT=json
EVALUATION_ENABLED=true
EXPERIMENT_TRACKING_ENABLED=true
```

### 3. Initialize Directories

The system automatically creates these directories:

```
logs/                       # Application logs
evaluations/               # Evaluation results
evaluation_cache/          # Cached evaluation results
experiments.db             # Experiment database
```

## Usage

### 1. Running the Application

```bash
uvicorn app:app --reload
```

Access the API at `http://localhost:8000`

### 2. Evaluating RAG Performance

#### Option A: Using the Evaluation Script

```bash
python evaluate_rag.py
```

This runs a complete evaluation pipeline with sample data.

#### Option B: Using the API Endpoint

```python
import requests

# Prepare evaluation data
eval_request = {
    "questions": [
        "How should I prepare soil for planting rice?",
        "What are the best practices for preventing crop diseases?"
    ],
    "contexts": [
        ["Rice soil preparation involves...", "Ensure soil pH..."],
        ["Crop disease prevention includes...", "Use disease-resistant..."]
    ],
    "answers": [
        "Prepare rice soil properly...",
        "Prevent diseases through..."
    ],
    "ground_truths": [
        "Proper soil preparation is essential...",
        "Implement integrated pest management..."
    ],
    "experiment_name": "my_evaluation"
}

# Run evaluation
response = requests.post(
    "http://localhost:8000/evaluate",
    json=eval_request
)

print(response.json())
```

#### Option C: Using the Python API

```python
from langchain_groq import ChatGroq
from evaluation import RAGEvaluator
from config import settings

# Initialize
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
)

evaluator = RAGEvaluator(llm=llm, experiment_name="my_test")

# Run evaluation
results = evaluator.evaluate_samples(
    questions=["question1", "question2"],
    contexts=[["context1"], ["context2"]],
    answers=["answer1", "answer2"],
    ground_truths=["truth1", "truth2"]
)

# Save results
evaluator.save_results()

# Print summary
print(evaluator.get_summary())
```

### 3. Accessing Logs

#### View Recent Logs

```bash
# Last 50 lines of application log
tail -50 logs/app.log

# Last 20 lines of errors
tail -20 logs/errors.log

# Watch logs in real-time
tail -f logs/app.log
```

#### Search Logs

```bash
# Find all errors
grep "ERROR" logs/app.log

# Find specific query
grep "question1" logs/app.log

# Count occurrences
grep -c "faithfulness" logs/app.log
```

#### Parse JSON Logs

```bash
# Pretty print JSON logs
jq '.' logs/app.log

# Filter by log level
jq 'select(.level=="ERROR")' logs/app.log

# Extract specific field
jq '.experiment_name' logs/experiment_*.jsonl
```

### 4. Tracking Experiments

#### List All Experiments

```bash
curl http://localhost:8000/experiments
```

#### Get Specific Experiment

```bash
curl http://localhost:8000/experiments/{experiment_id}
```

#### Filter Experiments

```bash
# By status
curl "http://localhost:8000/experiments?status=success"

# By name
curl "http://localhost:8000/experiments?experiment_name=my_test"

# With limit
curl "http://localhost:8000/experiments?limit=10"
```

#### Export Experiments to JSON

```bash
curl http://localhost:8000/experiments/export/json
```

## API Endpoints

### RAG Queries

```
POST /ask
Request: {"question": "How to grow tomatoes?"}
Response: {"question": "...", "answer": "...", "status": "success", "timestamp": "..."}
```

### Evaluation

```
POST /evaluate
Request: {
    "questions": [...],
    "contexts": [...],
    "answers": [...],
    "ground_truths": [...],
    "experiment_name": "test"
}
Response: {
    "experiment_name": "test",
    "metrics": {...},
    "timestamp": "...",
    "status": "success"
}
```

### Experiment Management

```
GET /experiments                          # List all experiments
GET /experiments?experiment_name=test     # Filter by name
GET /experiments?status=success           # Filter by status
GET /experiments/{experiment_id}          # Get specific experiment
GET /experiments/export/json              # Export all experiments
```

### Health Check

```
GET /health
Response: {"status": "healthy", "app_name": "...", "version": "...", "timestamp": "..."}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | false | Enable debug mode |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | json | Log format (json or text) |
| `LOG_FILE` | logs/app.log | Log file path |
| `EVALUATION_ENABLED` | true | Enable evaluation endpoints |
| `EXPERIMENT_TRACKING_ENABLED` | true | Enable experiment tracking |
| `RAGAS_BATCH_SIZE` | 4 | Batch size for RAGAS evaluation |
| `RAGAS_TIMEOUT` | 300 | Timeout for RAGAS evaluation (seconds) |

### Performance Tuning

- **Batch Size**: Increase for faster evaluation on large datasets
- **Timeout**: Increase if evaluations timeout on slow systems
- **Log Level**: Set to WARNING or ERROR in production for better performance

## Troubleshooting

### RAGAS Evaluation Fails

1. Check OpenAI API key is set: `echo $OPENAI_API_KEY`
2. Verify internet connectivity
3. Check logs: `tail -50 logs/errors.log`
4. Increase timeout: `RAGAS_TIMEOUT=600`

### Logs Not Appearing

1. Check log level: `echo $LOG_LEVEL`
2. Verify write permissions to `logs/` directory
3. Check disk space: `df -h`

### Database Locked Error

This occurs when multiple processes access the experiment database simultaneously.

**Solutions:**
- Use SQLite WAL mode (enable in advanced configuration)
- Add retry logic (automatically handled in tracker)
- Use connection pooling with larger timeout

### Out of Memory on Large Evaluations

**Solutions:**
1. Reduce batch size: `RAGAS_BATCH_SIZE=2`
2. Evaluate in smaller chunks
3. Enable evaluation cache to avoid re-evaluation

## Examples

### Complete Workflow

```python
from langchain_groq import ChatGroq
from evaluation import RAGEvaluator
from experiment_tracker import get_tracker
from config import settings

# 1. Initialize
llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY)
evaluator = RAGEvaluator(llm=llm, experiment_name="production_eval")

# 2. Evaluate
results = evaluator.evaluate_samples(
    questions=["Q1", "Q2", "Q3"],
    contexts=[["C1"], ["C2"], ["C3"]],
    answers=["A1", "A2", "A3"],
    ground_truths=["T1", "T2", "T3"]
)

# 3. Save results
evaluator.save_results()

# 4. Track experiment
tracker = get_tracker()
tracker.save_experiment(
    experiment_name="production_eval",
    config={"batch_size": 4},
    metrics=results.get("metrics", {}),
    num_samples=3,
)

# 5. Query results
experiments = tracker.list_experiments(experiment_name="production_eval")
print(f"Found {len(experiments)} experiments")
```

### Continuous Evaluation

```python
import schedule
import time
from evaluate_rag import evaluate_with_ragas

def daily_evaluation():
    """Run evaluation daily."""
    print("Starting daily evaluation...")
    try:
        results = evaluate_with_ragas(...)
        print("Daily evaluation completed successfully")
    except Exception as e:
        print(f"Daily evaluation failed: {e}")

# Schedule evaluation
schedule.every().day.at("02:00").do(daily_evaluation)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Best Practices

1. **Always use ground truths** for accurate evaluation
2. **Evaluate regularly** to track performance over time
3. **Cache evaluation results** to avoid redundant computations
4. **Monitor logs** for errors and anomalies
5. **Export experiments** periodically for backup
6. **Use consistent naming** for experiments for easy tracking
7. **Set appropriate log levels** (INFO for production, DEBUG for development)

## Production Deployment

### Docker

The included `Dockerfile` runs the application in production mode:

```bash
docker build -t farmer-rag-agent .
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -e LOG_LEVEL=WARNING \
  farmer-rag-agent
```

### Environment Recommendations

- Set `LOG_LEVEL=WARNING` for production
- Set `DEBUG=false`
- Use external log aggregation (ELK, Datadog, etc.)
- Enable experiment tracking for audit trails
- Regularly export and backup experiments

## Support

For issues or questions:
1. Check the logs: `logs/app.log`
2. Review error logs: `logs/errors.log`
3. Check recent experiments: `GET /experiments?limit=10`
4. Export data for analysis: `GET /experiments/export/json`
