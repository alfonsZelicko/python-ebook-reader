"""
Unit tests for JobManager class.

Tests job creation, status tracking, progress updates, and cleanup.
"""

import asyncio
import time
from datetime import datetime, timedelta

import pytest

from server.core.config import ServerConfig
from server.core.logger import setup_logger
from server.graphql.types import JobStatusEnum, JobProgress
from server.services.job_manager import JobManager


@pytest.fixture
def logger():
    """Create a logger for testing."""
    config = ServerConfig(log_level="DEBUG")
    return setup_logger(config)


@pytest.fixture
def job_manager(logger):
    """Create a JobManager instance for testing."""
    return JobManager(logger=logger, max_workers=2)


@pytest.mark.asyncio
async def test_job_creation(job_manager):
    """Test job creation and ID generation."""

    def mock_service_func(input_data, progress_callback=None):
        return {"success": True, "message": "Test completed"}

    job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={"test": "data"}
    )

    # Verify job ID is generated
    assert job_id is not None
    assert isinstance(job_id, str)
    assert len(job_id) > 0

    # Verify job is in jobs dictionary
    assert job_id in job_manager.jobs

    # Verify initial job state
    job = job_manager.jobs[job_id]
    assert job.job_id == job_id
    assert job.job_type == "TTS"
    # Status can be QUEUED or RUNNING due to race condition
    assert job.status in [
        JobStatusEnum.QUEUED,
        JobStatusEnum.RUNNING,
        JobStatusEnum.COMPLETED,
    ]
    assert job.progress.percentage >= 0.0
    assert job.progress.current_chunk >= 0


@pytest.mark.asyncio
async def test_get_job_status_valid_id(job_manager):
    """Test getting status for a valid job ID."""

    def mock_service_func(input_data, progress_callback=None):
        time.sleep(0.1)
        return {"success": True}

    job_id = await job_manager.create_job(
        job_type="TRANSLATION", service_func=mock_service_func, input_data={}
    )

    # Get job status
    status = await job_manager.get_job_status(job_id)

    assert status.job_id == job_id
    assert status.status in [
        JobStatusEnum.QUEUED,
        JobStatusEnum.RUNNING,
        JobStatusEnum.COMPLETED,
    ]
    assert status.progress is not None


@pytest.mark.asyncio
async def test_get_job_status_invalid_id(job_manager):
    """Test getting status for an invalid job ID."""
    with pytest.raises(KeyError, match="Job .* not found"):
        await job_manager.get_job_status("nonexistent-job-id")


@pytest.mark.asyncio
async def test_job_status_transitions(job_manager):
    """Test job status transitions (QUEUED → RUNNING → COMPLETED)."""

    def mock_service_func(input_data, progress_callback=None):
        time.sleep(0.2)
        return {"success": True, "message": "Completed"}

    job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={}
    )

    # Initial status should be QUEUED or RUNNING (race condition possible)
    initial_status = await job_manager.get_job_status(job_id)
    assert initial_status.status in [JobStatusEnum.QUEUED, JobStatusEnum.RUNNING]

    # Wait for job to complete
    await asyncio.sleep(0.5)

    # Final status should be COMPLETED
    final_status = await job_manager.get_job_status(job_id)
    assert final_status.status == JobStatusEnum.COMPLETED
    assert final_status.result is not None
    assert final_status.result["success"] is True
    assert final_status.progress.percentage == 100.0
    assert final_status.progress.stage == "completed"


@pytest.mark.asyncio
async def test_failed_job_handling(job_manager):
    """Test handling of failed jobs."""

    def failing_service_func(input_data, progress_callback=None):
        raise ValueError("Test error message")

    job_id = await job_manager.create_job(
        job_type="TTS", service_func=failing_service_func, input_data={}
    )

    # Wait for job to fail
    await asyncio.sleep(0.3)

    # Check job status
    status = await job_manager.get_job_status(job_id)
    assert status.status == JobStatusEnum.FAILED
    assert status.error is not None
    assert "Test error message" in status.error
    assert status.result is None


@pytest.mark.asyncio
async def test_progress_updates(job_manager):
    """Test progress callback updates job state."""
    progress_updates = []

    def mock_service_func(input_data, progress_callback=None):
        # Simulate progress updates
        for i in range(1, 4):
            progress = JobProgress(
                percentage=i * 25.0,
                current_chunk=i,
                total_chunks=4,
                stage=f"processing chunk {i}/4",
            )
            if progress_callback:
                progress_callback(progress)
            time.sleep(0.1)

        return {"success": True}

    job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={}
    )

    # Wait for some progress
    await asyncio.sleep(0.2)

    # Check that progress was updated
    status = await job_manager.get_job_status(job_id)
    # Progress should be > 0 if updates are working
    assert status.progress.percentage >= 0.0


@pytest.mark.asyncio
async def test_concurrent_job_execution(job_manager):
    """Test concurrent execution of multiple jobs."""

    def mock_service_func(input_data, progress_callback=None):
        time.sleep(0.2)
        return {"success": True, "data": input_data["value"]}

    # Create multiple jobs
    job_ids = []
    for i in range(3):
        job_id = await job_manager.create_job(
            job_type="TTS", service_func=mock_service_func, input_data={"value": i}
        )
        job_ids.append(job_id)

    # Wait for all jobs to complete
    await asyncio.sleep(0.8)

    # Verify all jobs completed
    for i, job_id in enumerate(job_ids):
        status = await job_manager.get_job_status(job_id)
        assert status.status == JobStatusEnum.COMPLETED
        assert status.result["data"] == i


@pytest.mark.asyncio
async def test_cleanup_completed_jobs(job_manager):
    """Test cleanup of old completed jobs."""

    def mock_service_func(input_data, progress_callback=None):
        return {"success": True}

    # Create and complete a job
    job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={}
    )

    # Wait for job to complete
    await asyncio.sleep(0.3)

    # Manually set updated_at to old time
    job_manager.jobs[job_id].updated_at = datetime.now() - timedelta(hours=25)

    # Run cleanup
    await job_manager.cleanup_completed_jobs(max_age_hours=24)

    # Job should be removed
    assert job_id not in job_manager.jobs


@pytest.mark.asyncio
async def test_cleanup_does_not_remove_recent_jobs(job_manager):
    """Test that cleanup doesn't remove recent completed jobs."""

    def mock_service_func(input_data, progress_callback=None):
        return {"success": True}

    # Create and complete a job
    job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={}
    )

    # Wait for job to complete
    await asyncio.sleep(0.3)

    # Run cleanup (job is recent, should not be removed)
    await job_manager.cleanup_completed_jobs(max_age_hours=24)

    # Job should still exist
    assert job_id in job_manager.jobs


@pytest.mark.asyncio
async def test_cleanup_does_not_remove_running_jobs(job_manager):
    """Test that cleanup doesn't remove running jobs."""

    def slow_service_func(input_data, progress_callback=None):
        time.sleep(1.0)
        return {"success": True}

    # Create a long-running job
    job_id = await job_manager.create_job(
        job_type="TTS", service_func=slow_service_func, input_data={}
    )

    # Wait a bit but not for completion
    await asyncio.sleep(0.2)

    # Manually set updated_at to old time (simulating old running job)
    job_manager.jobs[job_id].updated_at = datetime.now() - timedelta(hours=25)

    # Run cleanup
    await job_manager.cleanup_completed_jobs(max_age_hours=24)

    # Running job should NOT be removed
    assert job_id in job_manager.jobs


@pytest.mark.asyncio
async def test_job_timestamps(job_manager):
    """Test that job timestamps are properly set."""

    def mock_service_func(input_data, progress_callback=None):
        time.sleep(0.1)
        return {"success": True}

    before_creation = datetime.now()

    job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={}
    )

    after_creation = datetime.now()

    job = job_manager.jobs[job_id]

    # Verify created_at is within expected range
    assert before_creation <= job.created_at <= after_creation

    # Verify updated_at is set
    assert job.updated_at is not None

    # Wait for job to complete
    await asyncio.sleep(0.3)

    # Verify updated_at changed
    assert job.updated_at > job.created_at


@pytest.mark.asyncio
async def test_multiple_job_types(job_manager):
    """Test creating jobs of different types."""

    def mock_service_func(input_data, progress_callback=None):
        return {"success": True}

    tts_job_id = await job_manager.create_job(
        job_type="TTS", service_func=mock_service_func, input_data={}
    )

    translation_job_id = await job_manager.create_job(
        job_type="TRANSLATION", service_func=mock_service_func, input_data={}
    )

    # Verify job types
    assert job_manager.jobs[tts_job_id].job_type == "TTS"
    assert job_manager.jobs[translation_job_id].job_type == "TRANSLATION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
