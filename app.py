"""
Main FastAPI application for the Farmer RAG Agent.
Provides API endpoints for querying the RAG system and accessing evaluations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from config import settings
from logger import get_logger
from rag_agent import query_rag, graph
from evaluation import RAGEvaluator, EvaluationCache
from experiment_tracker import get_tracker
from langchain_core.messages import HumanMessage

# Initialize logger
logger = get_logger("app")

# =========================
# FastAPI Setup
# =========================

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered agricultural advisory system with RAG and evaluation",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

logger.info(
    "FastAPI application initialized",
    extra={"app_name": settings.APP_NAME, "debug": settings.DEBUG}
)

# =========================
# Request/Response Models
# =========================

class QueryRequest(BaseModel):
    """Request model for farming questions."""
    question: str = Field(..., min_length=1, max_length=1000)


class QueryResponse(BaseModel):
    """Response model for RAG answers."""
    question: str
    answer: str
    status: str
    timestamp: str


class EvaluationRequest(BaseModel):
    """Request model for evaluation."""
    questions: List[str] = Field(..., min_length=1)
    contexts: List[List[str]] = Field(..., min_length=1)
    answers: List[str] = Field(..., min_length=1)
    ground_truths: Optional[List[str]] = None
    experiment_name: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    experiment_name: str
    metrics: Dict[str, Any]
    timestamp: str
    status: str


# =========================
# Health Check
# =========================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }


# =========================
# Static Frontend
# =========================

@app.get("/")
def root():
    """Serve the main chat interface."""
    logger.info("Root endpoint accessed")
    return FileResponse("static/index.html")


# =========================
# Core RAG API
# =========================

@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest):
    """
    Ask a farming question and get AI-powered answers.
    
    Args:
        request: QueryRequest containing the question
        
    Returns:
        QueryResponse with answer and metadata
    """
    try:
        logger.info(f"Received query", extra={"question": request.question})
        
        result = query_rag(request.question)
        
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            status=result["status"],
            timestamp=datetime.now().isoformat(),
        )
    
    except Exception as e:
        logger.error(
            f"Error processing query: {str(e)}",
            extra={"question": request.question, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# Evaluation Endpoints
# =========================

@app.post("/evaluate", response_model=EvaluationResponse)
def evaluate_rag(request: EvaluationRequest):
    """
    Evaluate RAG performance using RAGAS metrics.
    
    Args:
        request: EvaluationRequest with questions, contexts, and answers
        
    Returns:
        EvaluationResponse with evaluation metrics
    """
    
    if not settings.EVALUATION_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Evaluation is not enabled. Set EVALUATION_ENABLED=true"
        )
    
    try:
        logger.info(
            "Starting RAGAS evaluation",
            extra={
                "num_samples": len(request.questions),
                "experiment_name": request.experiment_name,
            }
        )
        
        # Check cache
        cache_key = EvaluationCache.get_cache_key(
            request.questions,
            request.contexts,
            request.answers,
        )
        
        cached_results = EvaluationCache.load_cached_results(cache_key)
        if cached_results:
            logger.info("Using cached evaluation results", extra={"cache_key": cache_key})
            return EvaluationResponse(
                experiment_name=request.experiment_name or "cached",
                metrics=cached_results.get("metrics", {}),
                timestamp=cached_results.get("timestamp", datetime.now().isoformat()),
                status="success",
            )
        
        # Run evaluation
        evaluator = RAGEvaluator(
            llm=graph.nodes["assistant"],
            experiment_name=request.experiment_name,
        )
        
        results = evaluator.evaluate_samples(
            questions=request.questions,
            contexts=request.contexts,
            answers=request.answers,
            ground_truths=request.ground_truths,
        )
        
        # Save results
        evaluator.save_results()
        
        # Cache results
        EvaluationCache.save_cached_results(cache_key, results)
        
        # Track experiment
        if settings.EXPERIMENT_TRACKING_ENABLED:
            tracker = get_tracker()
            tracker.save_experiment(
                experiment_name=request.experiment_name or "ragas_eval",
                config={
                    "num_samples": len(request.questions),
                    "has_ground_truths": request.ground_truths is not None,
                },
                metrics=results.get("metrics", {}),
                num_samples=len(request.questions),
                status="success",
            )
        
        logger.info("Evaluation completed successfully")
        
        return EvaluationResponse(
            experiment_name=request.experiment_name or "default",
            metrics=results.get("metrics", {}),
            timestamp=results.get("timestamp", datetime.now().isoformat()),
            status="success",
        )
    
    except Exception as e:
        logger.error(
            f"Error during evaluation: {str(e)}",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        
        if settings.EXPERIMENT_TRACKING_ENABLED:
            tracker = get_tracker()
            tracker.save_experiment(
                experiment_name=request.experiment_name or "ragas_eval",
                config={"num_samples": len(request.questions)},
                metrics={},
                num_samples=len(request.questions),
                status="failed",
                error_message=str(e),
            )
        
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# =========================
# Experiment Tracking Endpoints
# =========================

@app.get("/experiments")
def list_experiments(
    experiment_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    """
    List experiments with optional filtering.
    
    Args:
        experiment_name: Filter by experiment name
        status: Filter by status (success/failed)
        limit: Maximum number of results
        
    Returns:
        List of experiments
    """
    
    if not settings.EXPERIMENT_TRACKING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Experiment tracking is not enabled"
        )
    
    try:
        logger.info(
            "Listing experiments",
            extra={"experiment_name": experiment_name, "status": status, "limit": limit}
        )
        
        tracker = get_tracker()
        experiments = tracker.list_experiments(
            experiment_name=experiment_name,
            status=status,
            limit=limit,
        )
        
        return {
            "total": len(experiments),
            "experiments": [
                {
                    "experiment_id": exp.experiment_id,
                    "experiment_name": exp.experiment_name,
                    "timestamp": exp.timestamp,
                    "status": exp.status,
                    "num_samples": exp.num_samples,
                    "metrics_keys": list(exp.metrics.keys()),
                }
                for exp in experiments
            ],
        }
    
    except Exception as e:
        logger.error(f"Error listing experiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    """
    Get a specific experiment by ID.
    
    Args:
        experiment_id: The experiment ID
        
    Returns:
        Experiment details
    """
    
    if not settings.EXPERIMENT_TRACKING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Experiment tracking is not enabled"
        )
    
    try:
        logger.info("Fetching experiment", extra={"experiment_id": experiment_id})
        
        tracker = get_tracker()
        experiment = tracker.get_experiment(experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return {
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.experiment_name,
            "timestamp": experiment.timestamp,
            "config": experiment.config,
            "metrics": experiment.metrics,
            "num_samples": experiment.num_samples,
            "status": experiment.status,
            "error_message": experiment.error_message,
            "notes": experiment.notes,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching experiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/experiments/export/json")
def export_experiments():
    """
    Export all experiments to JSON.
    
    Returns:
        Path to exported file
    """
    
    if not settings.EXPERIMENT_TRACKING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Experiment tracking is not enabled"
        )
    
    try:
        logger.info("Exporting experiments to JSON")
        
        tracker = get_tracker()
        export_path = tracker.export_to_json()
        
        return {"export_path": export_path, "status": "success"}
    
    except Exception as e:
        logger.error(f"Error exporting experiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# Error Handlers
# =========================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={"status_code": exc.status_code, "detail": exc.detail}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"error": str(exc), "error_type": type(exc).__name__}
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# =========================
# Startup/Shutdown Events
# =========================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(
        "Application startup",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Application shutdown")
