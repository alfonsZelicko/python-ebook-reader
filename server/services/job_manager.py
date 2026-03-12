"""
Job Manager for asynchronous TTS and Translation operations.

This module manages long-running operations by tracking job status, progress,
and results. Jobs are executed in background threads using ThreadPoolExecutor.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional

from server.graphql.types import JobStatusEnum, JobProgress, JobStatus


@dataclass
class Job:
    """Represents an asynchronous job with status and progress tracking."""

    job_id: str
    job_type: str  # "TTS" or "TRANSLATION"
    status: JobStatusEnum
    progress: JobProgress
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class JobManager:
    """
    Manages asynchronous job execution and status tracking.

    Uses ThreadPoolExecutor for concurrent job execution and maintains
    an in-memory dictionary of job states.
    """

    def __init__(self, logger: logging.Logger, max_workers: int = 4):
        """
        Initialize the JobManager.

        Args:
            logger: Logger instance for tracking job operations
            max_workers: Maximum number of concurrent jobs (default: 4)
        """
        self.jobs: Dict[str, Job] = {}
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def create_job(
        self, job_type: str, service_func: Callable, input_data: Any
    ) -> str:
        """
        Creates a new job and starts background execution.

        Args:
            job_type: Type of job ("TTS" or "TRANSLATION")
            service_func: Service function to execute (e.g., tts_service.generate_speech)
            input_data: Input parameters for the service function

        Returns:
            job_id: Unique identifier for tracking the job
        """
        job_id = str(uuid.uuid4())

        # Create initial job with QUEUED status
        job = Job(
            job_id=job_id,
            job_type=job_type,
            status=JobStatusEnum.QUEUED,
            progress=JobProgress(
                percentage=0.0, current_chunk=0, total_chunks=0, stage="initializing"
            ),
        )

        self.jobs[job_id] = job
        self.logger.info(f"Created {job_type} job with ID: {job_id}")

        # Submit job to executor for background execution
        self.executor.submit(self._execute_job, job_id, service_func, input_data)

        return job_id

    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Returns current status and progress of a job.

        Args:
            job_id: Unique job identifier

        Returns:
            JobStatus: Current job status with progress information

        Raises:
            KeyError: If job_id does not exist
        """
        if job_id not in self.jobs:
            raise KeyError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        return JobStatus(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            result=job.result,
            error=job.error,
        )

    def _execute_job(self, job_id: str, service_func: Callable, input_data: Any):
        """
        Background task that executes the service function.

        This method runs in a background thread and updates job status
        as processing progresses.

        Args:
            job_id: Unique job identifier
            service_func: Service function to execute
            input_data: Input parameters for the service function
        """
        try:
            # Update status to RUNNING
            self.jobs[job_id].status = JobStatusEnum.RUNNING
            self.jobs[job_id].updated_at = datetime.now()
            self.logger.info(f"Job {job_id} started execution")

            # Create progress callback
            def progress_callback(progress: JobProgress):
                self._update_progress(job_id, progress)

            # Execute the service function
            # Note: service_func should be synchronous or handle its own async execution
            result = service_func(input_data, progress_callback=progress_callback)

            # Update job with result
            self.jobs[job_id].status = JobStatusEnum.COMPLETED
            self.jobs[job_id].result = result
            self.jobs[job_id].progress.percentage = 100.0
            self.jobs[job_id].progress.stage = "completed"
            self.jobs[job_id].updated_at = datetime.now()

            self.logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            # Update job with error
            self.jobs[job_id].status = JobStatusEnum.FAILED
            self.jobs[job_id].error = str(e)
            self.jobs[job_id].updated_at = datetime.now()

            self.logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)

    def _update_progress(self, job_id: str, progress: JobProgress):
        """
        Updates job progress (called by progress_callback).

        Args:
            job_id: Unique job identifier
            progress: Updated progress information
        """
        if job_id in self.jobs:
            self.jobs[job_id].progress = progress
            self.jobs[job_id].updated_at = datetime.now()

            self.logger.debug(
                f"Job {job_id} progress: {progress.percentage:.1f}% "
                f"({progress.current_chunk}/{progress.total_chunks}) - {progress.stage}"
            )

    async def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Removes old completed/failed jobs from memory.

        Args:
            max_age_hours: Maximum age in hours for completed jobs (default: 24)
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        jobs_to_remove = []

        for job_id, job in self.jobs.items():
            # Only cleanup completed or failed jobs
            if job.status in [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]:
                if job.updated_at < cutoff_time:
                    jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            self.logger.info(f"Cleaned up old job: {job_id}")

        if jobs_to_remove:
            self.logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
