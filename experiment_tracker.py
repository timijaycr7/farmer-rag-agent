"""
Experiment tracking and results persistence.
Stores experiment metadata, configuration, and evaluation results.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import uuid

from logger import get_logger
from config import settings, EVALUATIONS_DIR

logger = get_logger("experiment_tracker")


@dataclass
class ExperimentResult:
    """Data class for experiment results."""
    
    experiment_id: str
    experiment_name: str
    timestamp: str
    config: Dict[str, Any]
    metrics: Dict[str, Any]
    num_samples: int
    status: str  # "success" or "failed"
    error_message: Optional[str] = None
    notes: Optional[str] = None


class ExperimentTracker:
    """
    Track and persist experiment results.
    Stores configuration, metrics, and metadata.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize experiment tracker.
        
        Args:
            db_path: Path to SQLite database (default from settings)
        """
        self.db_path = db_path or settings.EXPERIMENT_DB_PATH
        self._initialize_db()
        logger.info(f"Experiment tracker initialized", extra={"db_path": self.db_path})
    
    def _initialize_db(self) -> None:
        """Initialize SQLite database schema."""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create experiments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    experiment_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    config TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    num_samples INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_experiment_name 
                ON experiments(experiment_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON experiments(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON experiments(status)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(
                f"Error initializing database: {str(e)}",
                extra={"error": str(e), "db_path": self.db_path}
            )
            raise
    
    def save_experiment(
        self,
        experiment_name: str,
        config: Dict[str, Any],
        metrics: Dict[str, Any],
        num_samples: int,
        status: str = "success",
        error_message: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Save experiment results to database.
        
        Args:
            experiment_name: Name of the experiment
            config: Experiment configuration
            metrics: Evaluation metrics
            num_samples: Number of samples evaluated
            status: "success" or "failed"
            error_message: Optional error message if failed
            notes: Optional notes about the experiment
            
        Returns:
            experiment_id
        """
        
        experiment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        result = ExperimentResult(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            timestamp=timestamp,
            config=config,
            metrics=metrics,
            num_samples=num_samples,
            status=status,
            error_message=error_message,
            notes=notes,
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO experiments (
                    experiment_id, experiment_name, timestamp, config, 
                    metrics, num_samples, status, error_message, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.experiment_id,
                result.experiment_name,
                result.timestamp,
                json.dumps(result.config),
                json.dumps(result.metrics),
                result.num_samples,
                result.status,
                result.error_message,
                result.notes,
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(
                f"Experiment saved successfully",
                extra={
                    "experiment_id": experiment_id,
                    "experiment_name": experiment_name,
                    "status": status,
                }
            )
            
            return experiment_id
            
        except Exception as e:
            logger.error(
                f"Error saving experiment: {str(e)}",
                extra={"error": str(e), "experiment_name": experiment_name}
            )
            raise
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Retrieve experiment by ID."""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT experiment_id, experiment_name, timestamp, config, 
                       metrics, num_samples, status, error_message, notes
                FROM experiments
                WHERE experiment_id = ?
            """, (experiment_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ExperimentResult(
                    experiment_id=row[0],
                    experiment_name=row[1],
                    timestamp=row[2],
                    config=json.loads(row[3]),
                    metrics=json.loads(row[4]),
                    num_samples=row[5],
                    status=row[6],
                    error_message=row[7],
                    notes=row[8],
                )
            
            return None
            
        except Exception as e:
            logger.error(
                f"Error retrieving experiment: {str(e)}",
                extra={"error": str(e), "experiment_id": experiment_id}
            )
            return None
    
    def list_experiments(
        self,
        experiment_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExperimentResult]:
        """
        List experiments with optional filtering.
        
        Args:
            experiment_name: Filter by experiment name
            status: Filter by status ("success" or "failed")
            limit: Maximum number of results
            
        Returns:
            List of ExperimentResult objects
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM experiments WHERE 1=1"
            params = []
            
            if experiment_name:
                query += " AND experiment_name = ?"
                params.append(experiment_name)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                results.append(ExperimentResult(
                    experiment_id=row[0],
                    experiment_name=row[1],
                    timestamp=row[2],
                    config=json.loads(row[3]),
                    metrics=json.loads(row[4]),
                    num_samples=row[5],
                    status=row[6],
                    error_message=row[7],
                    notes=row[8],
                ))
            
            logger.info(
                f"Retrieved {len(results)} experiments",
                extra={
                    "experiment_name": experiment_name,
                    "status": status,
                    "count": len(results),
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Error listing experiments: {str(e)}",
                extra={"error": str(e)}
            )
            return []
    
    def get_latest_experiment(
        self,
        experiment_name: str,
    ) -> Optional[ExperimentResult]:
        """Get the latest experiment by name."""
        
        results = self.list_experiments(
            experiment_name=experiment_name,
            limit=1
        )
        return results[0] if results else None
    
    def export_to_json(self, output_path: Optional[str] = None) -> str:
        """
        Export all experiments to JSON file.
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path to exported file
        """
        
        if output_path is None:
            filename = f"experiments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = str(EVALUATIONS_DIR / filename)
        
        try:
            experiments = self.list_experiments(limit=10000)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_experiments": len(experiments),
                "experiments": [asdict(exp) for exp in experiments],
            }
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(
                f"Experiments exported to JSON",
                extra={"output_path": output_path, "count": len(experiments)}
            )
            
            return output_path
            
        except Exception as e:
            logger.error(
                f"Error exporting experiments: {str(e)}",
                extra={"error": str(e), "output_path": output_path}
            )
            raise


# Global tracker instance
_tracker: Optional[ExperimentTracker] = None


def get_tracker() -> ExperimentTracker:
    """Get or create global experiment tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ExperimentTracker()
    return _tracker
