import uuid
import time
from typing import Dict, Any, Optional

class JobManager:
    """In-memory tracking for long-running inference and reporting tasks."""
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, initial_message: str = "Job initialized") -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0,
            "message": initial_message,
            "result_id": None,
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        return job_id

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        if job_id not in self._jobs:
            return
        job = self._jobs[job_id]
        if status is not None:
            job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if message is not None:
            job["message"] = message
        if result_id is not None:
            job["result_id"] = result_id
        if error is not None:
            job["error"] = error
        job["updated_at"] = time.time()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

    def cleanup_old_jobs(self, max_age_seconds: int = 7200):
        now = time.time()
        expired = [jid for jid, j in self._jobs.items() if now - j["updated_at"] > max_age_seconds]
        for jid in expired:
            del self._jobs[jid]

job_manager = JobManager()
