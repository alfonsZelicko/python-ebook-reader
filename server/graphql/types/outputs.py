"""
GraphQL output types for TTS and Translation services.

This module defines all output types returned by GraphQL queries and mutations,
including result types, metadata, job status, and engine information.
"""

import strawberry
from typing import List, Optional, Union
from enum import Enum


# =========================== Job Status Types =========================== #

@strawberry.enum
class JobStatusEnum(Enum):
    """Status of an asynchronous job."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@strawberry.type
class JobProgress:
    """Progress information for a running job."""
    percentage: float
    current_chunk: int
    total_chunks: int
    stage: str  # "initializing", "processing", "finalizing", etc.
    estimated_time_remaining: Optional[int] = None  # seconds


@strawberry.type
class JobStatus:
    """Status and progress of an asynchronous job."""
    job_id: str
    status: JobStatusEnum
    progress: JobProgress
    result: Optional[Union["TTSResult", "TranslationResult"]] = None
    error: Optional[str] = None


# =========================== TTS Output Types =========================== #

@strawberry.type
class TTSMetadata:
    """Metadata about TTS processing."""
    engine_used: str
    total_chunks: int
    total_duration_seconds: float
    output_directory: str


@strawberry.type
class TTSResult:
    """Result of a TTS generation operation."""
    success: bool
    message: str
    output_files: List[str]  # Paths to generated MP3 files
    metadata: TTSMetadata


# =========================== Translation Output Types =========================== #

@strawberry.type
class TranslationMetadata:
    """Metadata about translation processing."""
    engine_used: str
    source_language: str
    target_language: str
    total_chunks: int
    output_directory: str


@strawberry.type
class TranslationResult:
    """Result of a translation operation."""
    success: bool
    message: str
    output_file: str  # Path to translated text file
    metadata: TranslationMetadata


# =========================== Engine Information Types =========================== #

@strawberry.type
class EngineDetail:
    """Detailed information about an available engine."""
    name: str
    description: str
    required_parameters: List[str]
    optional_parameters: List[str]


@strawberry.type
class EngineInfo:
    """Information about available TTS and translation engines."""
    tts_engines: List[EngineDetail]
    translation_engines: List[EngineDetail]


# =========================== File Download Types =========================== #

@strawberry.type
class FileDownload:
    """File content or download URL for a generated file."""
    file_id: str
    filename: str
    content_type: str
    size_bytes: int
    download_url: Optional[str] = None
    content: Optional[str] = None  # Base64 encoded content for small files
