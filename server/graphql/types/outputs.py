"""
GraphQL Output Types for TTS and Translation services.

This module defines the structured response objects returned by GraphQL
queries and mutations. It handles the "Output" side of the single source
of truth, ensuring that metadata, results, and job statuses remain
consistent across all translation and TTS operations.
"""

from enum import Enum
from typing import List, Optional, Union

import strawberry


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
    """Metadata about TTS processing, including engine info and audio duration."""

    engine_used: str
    total_chunks: int
    total_duration_seconds: float
    output_directory: str


@strawberry.type
class TTSResult:
    """Result of a TTS generation operation, returning a list of generated file paths."""

    success: bool
    message: str
    output_files: List[str]  # Paths to generated MP3 files
    metadata: TTSMetadata


# =========================== Translation Output Types =========================== #


@strawberry.type
class TranslationMetadata:
    """Metadata about translation processing, tracking languages and output location."""

    engine_used: str
    source_language: str
    target_language: str
    total_chunks: int
    output_directory: str


@strawberry.type
class TranslationResult:
    """Result of a translation operation, returning the final translated file path."""

    success: bool
    message: str
    output_file: str  # Path to translated text file
    metadata: TranslationMetadata


# =========================== Engine Information Types =========================== #


@strawberry.type
class EngineDetail:
    """Detailed information about an available engine and its required parameters."""

    name: str
    description: str
    required_parameters: List[str]
    optional_parameters: List[str]


@strawberry.type
class EngineInfo:
    """Information about available TTS and translation engines filtered by server config."""

    tts_engines: List[EngineDetail]
    translation_engines: List[EngineDetail]


# =========================== File Download Types =========================== #


@strawberry.type
class FileDownload:
    """File metadata and delivery mechanism (URL or Base64 content)."""

    file_id: str
    filename: str
    content_type: str
    size_bytes: int
    download_url: Optional[str] = None
    content: Optional[str] = None  # Base64 encoded content for small files


@strawberry.type
class TranslationResultWithFile(TranslationResult):
    """Extended translation result with direct file download."""

    file_download: Optional[FileDownload] = None
