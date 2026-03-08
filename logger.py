"""
Logging configuration for production-grade application.
Supports both JSON and text formatting with structured logging.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog

from config import settings, LOGS_DIR


def setup_logging() -> logging.Logger:
    """
    Configure structured logging with support for JSON and text formats.
    Returns the root logger instance.
    """
    
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Standard library logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(filename)s:%(lineno)d - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)s | "
                    "%(funcName)s:%(lineno)d | %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.LOG_FILE,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(LOGS_DIR / "errors.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file", "error_file"],
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "langchain": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "langgraph": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "farmer_rag": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(logging_config)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if settings.LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logger = logging.getLogger("farmer_rag")
    logger.info(
        "Logging initialized",
        extra={
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
            "debug_mode": settings.DEBUG,
        }
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper naming convention."""
    return logging.getLogger(f"farmer_rag.{name}")


class ExperimentLogger:
    """Specialized logger for experiment tracking."""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.logger = get_logger(f"experiments.{experiment_name}")
        self.experiment_file = (
            LOGS_DIR / f"experiment_{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        )
        
    def log_experiment_start(self, config: Dict[str, Any]) -> None:
        """Log the start of an experiment."""
        self.logger.info(
            f"Experiment '{self.experiment_name}' started",
            extra={"config": config, "timestamp": datetime.now().isoformat()}
        )
        
    def log_metric(self, metric_name: str, value: float, step: int = 0) -> None:
        """Log a metric during experiment."""
        self.logger.info(
            f"Metric: {metric_name}",
            extra={
                "metric_name": metric_name,
                "value": value,
                "step": step,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    def log_experiment_end(self, results: Dict[str, Any]) -> None:
        """Log the completion of an experiment."""
        self.logger.info(
            f"Experiment '{self.experiment_name}' completed",
            extra={"results": results, "timestamp": datetime.now().isoformat()}
        )


# Initialize logger on module import
logger = setup_logging()
