"""
RAGAS evaluation module for measuring RAG performance.
Evaluates: accuracy, faithfulness, relevance, and other key metrics.
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from ragas import evaluate
from ragas.metrics.collections import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset
from langchain_core.language_models import BaseChatModel

from logger import get_logger, ExperimentLogger
from config import settings, EVALUATIONS_DIR, EVALUATION_CACHE_DIR

logger = get_logger("evaluation")


class RAGEvaluator:
    """
    RAGAS-based evaluator for RAG systems.
    Measures accuracy, faithfulness, relevance, and other metrics.
    """
    
    def __init__(self, llm: Any, experiment_name: Optional[str] = None):
        """
        Initialize the RAG evaluator.
        
        Args:
            llm: Language model for evaluation
            experiment_name: Optional name for experiment tracking
        """
        self.llm = llm
        self.experiment_name = experiment_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_logger = ExperimentLogger(self.experiment_name)
        self.evaluation_results: Dict[str, Any] = {}
        
        logger.info(
            f"RAG Evaluator initialized",
            extra={"experiment_name": self.experiment_name}
        )
        
    def evaluate_samples(
        self,
        questions: List[str],
        contexts: List[List[str]],
        answers: List[str],
        ground_truths: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate RAG samples using RAGAS metrics.
        
        Args:
            questions: List of input questions
            contexts: List of context lists (retrieved documents)
            answers: List of generated answers
            ground_truths: Optional list of reference answers
            batch_size: Batch size for evaluation
            
        Returns:
            Dictionary containing evaluation metrics
        """
        
        if len(questions) != len(answers):
            logger.error("Mismatched lengths: questions and answers must have same length")
            raise ValueError("Questions and answers must have the same length")

        if len(contexts) != len(questions):
            logger.error("Mismatched lengths: contexts must match questions length")
            raise ValueError("Contexts must match questions length")
            
        if ground_truths and len(ground_truths) != len(questions):
            logger.error("Mismatched lengths: ground_truths must match questions length")
            raise ValueError("Ground truths must match questions length")
        
        batch_size = batch_size or settings.RAGAS_BATCH_SIZE
        
        # Prepare dataset for RAGAS
        eval_data = self._prepare_dataset(questions, contexts, answers, ground_truths)
        
        logger.info(
            "Starting RAGAS evaluation",
            extra={
                "num_samples": len(questions),
                "batch_size": batch_size,
                "metrics": ["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
            }
        )
        
        try:
            self.experiment_logger.log_experiment_start({
                "num_samples": len(questions),
                "batch_size": batch_size,
                "has_ground_truths": ground_truths is not None,
            })
            
            # Run RAGAS evaluation
            result = evaluate(
                eval_data,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                ],
                llm=self.llm,
                batch_size=batch_size,
            )
            
            # Convert to dictionary
            results_dict = self._convert_results(result)
            self.evaluation_results = results_dict
            
            logger.info(
                "RAGAS evaluation completed",
                extra={"results": results_dict}
            )
            
            self.experiment_logger.log_experiment_end(results_dict)
            
            return results_dict
            
        except Exception as e:
            logger.error(
                f"Error during RAGAS evaluation: {str(e)}",
                extra={"error": str(e), "error_type": type(e).__name__}
            )
            raise
    
    def _prepare_dataset(
        self,
        questions: List[str],
        contexts: List[List[str]],
        answers: List[str],
        ground_truths: Optional[List[str]] = None,
    ) -> Dataset:
        """Prepare data for RAGAS evaluation."""
        
        data_dict: Dict[str, List[Any]] = {
            "question": questions,
            "contexts": contexts,
            "answer": answers,
        }
        
        if ground_truths:
            data_dict["ground_truth"] = ground_truths
        
        return Dataset.from_dict(data_dict)
    
    def _convert_results(self, ragas_result: Any) -> Dict[str, Any]:
        """Convert RAGAS result object to dictionary."""
        
        results = {
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "experiment_name": self.experiment_name,
        }
        
        # Extract metrics
        if hasattr(ragas_result, "scores"):
            for metric_name in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                if metric_name in ragas_result.scores:
                    score = ragas_result.scores[metric_name]
                    results["metrics"][metric_name] = {
                        "mean": float(score.mean()),
                        "std": float(score.std()),
                        "min": float(score.min()),
                        "max": float(score.max()),
                    }
                    self.experiment_logger.log_metric(metric_name, float(score.mean()))
        
        return results
    
    def save_results(self, output_path: Optional[str] = None) -> str:
        """
        Save evaluation results to file.
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path where results were saved
        """
        
        if not self.evaluation_results:
            logger.warning("No evaluation results to save")
            return ""
        
        if output_path is None:
            filename = f"evaluation_{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = str(EVALUATIONS_DIR / filename)
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(self.evaluation_results, f, indent=2)
            
            logger.info(
                f"Evaluation results saved",
                extra={"output_path": output_path}
            )
            
            return output_path
            
        except Exception as e:
            logger.error(
                f"Error saving evaluation results: {str(e)}",
                extra={"output_path": output_path, "error": str(e)}
            )
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of evaluation metrics."""
        
        if not self.evaluation_results:
            return {}
        
        summary = {
            "experiment_name": self.experiment_name,
            "timestamp": self.evaluation_results.get("timestamp"),
            "metrics_summary": {},
        }
        
        for metric_name, metric_data in self.evaluation_results.get("metrics", {}).items():
            summary["metrics_summary"][metric_name] = {
                "score": metric_data.get("mean", 0),
                "std": metric_data.get("std", 0),
            }
        
        return summary


class EvaluationCache:
    """Cache evaluation results to avoid redundant evaluations."""
    
    @staticmethod
    def get_cache_key(
        questions: List[str],
        contexts: List[List[str]],
        answers: List[str],
    ) -> str:
        """Generate a cache key for evaluation results."""
        
        # Create a hash from the inputs
        content = json.dumps({
            "questions": questions,
            "contexts": contexts,
            "answers": answers,
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def load_cached_results(cache_key: str) -> Optional[Dict[str, Any]]:
        """Load cached evaluation results if available."""
        
        cache_file = EVALUATION_CACHE_DIR / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    results = json.load(f)
                    logger.info(
                        "Loaded cached evaluation results",
                        extra={"cache_key": cache_key}
                    )
                    return results
            except Exception as e:
                logger.warning(
                    f"Error loading cache: {str(e)}",
                    extra={"cache_key": cache_key}
                )
                return None
        
        return None
    
    @staticmethod
    def save_cached_results(
        cache_key: str,
        results: Dict[str, Any],
    ) -> None:
        """Save evaluation results to cache."""
        
        EVALUATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = EVALUATION_CACHE_DIR / f"{cache_key}.json"
        
        try:
            with open(cache_file, "w") as f:
                json.dump(results, f, indent=2)
                logger.info(
                    "Cached evaluation results",
                    extra={"cache_key": cache_key}
                )
        except Exception as e:
            logger.warning(
                f"Error saving to cache: {str(e)}",
                extra={"cache_key": cache_key}
            )
