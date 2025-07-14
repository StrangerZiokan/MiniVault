import json
import os
from datetime import datetime
from typing import Dict, Any
import threading
import logging

logger = logging.getLogger(__name__)


class InteractionLogger:
    """Service for logging API interactions to JSONL format."""
    
    def __init__(self, log_file: str = "logs/log.jsonl"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """Create logs directory if it doesn't exist."""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logger.info(f"Created log directory: {log_dir}")
    
    def log_interaction(self, prompt: str, response_data: Dict[str, Any]):
        """
        Log an interaction to the JSONL file.
        
        Args:
            prompt: The input prompt
            response_data: Dict containing response, model, timestamp, etc.
        """
        log_entry = {
            "timestamp": response_data.get("timestamp", datetime.now()).isoformat(),
            "prompt": prompt,
            "response": response_data.get("response", ""),
            "model": response_data.get("model", "unknown"),
            "duration_ms": response_data.get("duration_ms", 0),
            "success": response_data.get("success", True)
        }
        
        # Add error information if present
        if "error_reason" in response_data:
            log_entry["error_reason"] = response_data["error_reason"]
        
        try:
            with self.lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            logger.debug(f"Logged interaction to {self.log_file}")
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
    
    def get_recent_logs(self, limit: int = 10) -> list:
        """
        Get recent log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent log entries
        """
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Get the last 'limit' lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            # Parse JSON lines
            logs = []
            for line in recent_lines:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse log line: {e}")
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to read recent logs: {e}")
            return []
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged interactions.
        
        Returns:
            Dict containing log statistics
        """
        if not os.path.exists(self.log_file):
            return {
                "total_interactions": 0,
                "successful_interactions": 0,
                "failed_interactions": 0,
                "average_duration_ms": 0
            }
        
        try:
            total = 0
            successful = 0
            failed = 0
            total_duration = 0
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        total += 1
                        
                        if entry.get("success", True):
                            successful += 1
                        else:
                            failed += 1
                        
                        total_duration += entry.get("duration_ms", 0)
                        
                    except json.JSONDecodeError:
                        continue
            
            avg_duration = total_duration / total if total > 0 else 0
            
            return {
                "total_interactions": total,
                "successful_interactions": successful,
                "failed_interactions": failed,
                "average_duration_ms": round(avg_duration, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate log stats: {e}")
            return {
                "total_interactions": 0,
                "successful_interactions": 0,
                "failed_interactions": 0,
                "average_duration_ms": 0
            }
