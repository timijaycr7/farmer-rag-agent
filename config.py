"""
Configuration management for the Farmer RAG Agent.
Handles environment variables, settings, and constants.
"""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Farmer RAG Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    
    # Groq LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", 0.0))
    
    # OpenAI (for RAGAS evaluation)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Embeddings
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Vector Store
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "farmer_vector_db")
    
    # RAG Configuration
    RETRIEVER_K: int = int(os.getenv("RETRIEVER_K", 5))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_FORMAT: Literal["json", "text"] = os.getenv("LOG_FORMAT", "json").lower()  # type: ignore
    
    # Evaluation & Experiments
    EVALUATION_ENABLED: bool = os.getenv("EVALUATION_ENABLED", "true").lower() == "true"
    EVALUATION_CACHE_DIR: str = os.getenv("EVALUATION_CACHE_DIR", "evaluation_cache")
    EXPERIMENT_TRACKING_ENABLED: bool = os.getenv("EXPERIMENT_TRACKING_ENABLED", "true").lower() == "true"
    EXPERIMENT_DB_PATH: str = os.getenv("EXPERIMENT_DB_PATH", "experiments.db")
    
    # RAGAS Metrics
    RAGAS_BATCH_SIZE: int = int(os.getenv("RAGAS_BATCH_SIZE", 4))
    RAGAS_TIMEOUT: int = int(os.getenv("RAGAS_TIMEOUT", 300))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Initialize settings
settings = Settings()


# Project structure
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
EVALUATIONS_DIR = PROJECT_ROOT / "evaluations"
EVALUATION_CACHE_DIR = PROJECT_ROOT / settings.EVALUATION_CACHE_DIR

# Create necessary directories
LOGS_DIR.mkdir(exist_ok=True)
EVALUATIONS_DIR.mkdir(exist_ok=True)
EVALUATION_CACHE_DIR.mkdir(exist_ok=True)
