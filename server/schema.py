"""
GraphQL schema definition for TTS and Translation services.

This module defines the main GraphQL schema including Query and Mutation types.
The resolvers are implemented in separate files (server/resolvers/query.py and
server/resolvers/mutation.py) and will be connected in later tasks.

Requirements: 2.1, 2.2, 2.8, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""

import strawberry
import logging
import re
from server.resolvers.query import Query  as ResolverQuery
# from server.resolvers.mutation import Mutation
from typing import Optional, Union, Dict, Any
from server.types.outputs import (
    EngineInfo,
    JobStatus,
    FileDownload,
    TTSResult,
    TranslationResult,
)


# ============================================================================
# Job Created Response Type (for async operations)
# ============================================================================

@strawberry.type
class JobCreated:
    """Response when an asynchronous job is created."""
    job_id: str
    message: str = "Job created successfully"


# ============================================================================
# Error Handling Utilities
# ============================================================================

class ErrorCode:
    """
    Standard error codes for GraphQL error extensions.
    
    These codes provide structured error information to clients and help
    categorize different types of failures.
    
    Requirements: 10.6
    """
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ENGINE_NOT_ALLOWED = "ENGINE_NOT_ALLOWED"
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    SERVICE_ERROR = "SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class ErrorFormatter:
    """
    Formats GraphQL errors with structured extensions and sensitive data redaction.
    
    This class provides utilities for creating consistent, informative error
    responses while protecting sensitive information from exposure.
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    
    # Patterns for sensitive data that should be redacted
    SENSITIVE_PATTERNS = [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[REDACTED_API_KEY]'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[REDACTED_TOKEN]'),
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[REDACTED_PASSWORD]'),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[REDACTED_SECRET]'),
        (r'credentials["\']?\s*[:=]\s*["\']?([^"\'\s]+)', '[REDACTED_CREDENTIALS]'),
        # Redact file paths except for output filenames
        (r'/[a-zA-Z0-9_\-./]+/([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)', r'\1'),
    ]
    
    @staticmethod
    def redact_sensitive_data(message: str) -> str:
        """
        Removes sensitive information from error messages.
        
        This method scans error messages for patterns that might contain
        sensitive data (API keys, tokens, passwords, file paths) and
        replaces them with safe placeholders.
        
        Args:
            message: Original error message that may contain sensitive data
            
        Returns:
            Sanitized error message with sensitive data redacted
            
        Requirements: 10.7
        
        Example:
            >>> ErrorFormatter.redact_sensitive_data("API key abc123 is invalid")
            "API key [REDACTED_API_KEY] is invalid"
        """
        redacted = message
        for pattern, replacement in ErrorFormatter.SENSITIVE_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        return redacted
    
    @staticmethod
    def format_validation_error(
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates a formatted validation error with extensions.
        
        Args:
            message: User-friendly error message
            field: Name of the field that failed validation (optional)
            details: Additional error details (optional)
            
        Returns:
            Dictionary with error message and extensions
            
        Requirements: 10.1, 10.6
        
        Example:
            >>> ErrorFormatter.format_validation_error(
            ...     "Missing required parameter",
            ...     field="text_content",
            ...     details={"hint": "Provide either text_content or file_upload"}
            ... )
        """
        extensions = {
            "code": ErrorCode.VALIDATION_ERROR,
        }
        
        if field:
            extensions["field"] = field
        
        if details:
            extensions["details"] = details
        
        return {
            "message": ErrorFormatter.redact_sensitive_data(message),
            "extensions": extensions
        }
    
    @staticmethod
    def format_engine_not_allowed_error(
        engine: str,
        allowed_engines: list,
        engine_type: str = "engine"
    ) -> Dict[str, Any]:
        """
        Creates a formatted error for disallowed engine usage.
        
        Args:
            engine: The engine that was requested
            allowed_engines: List of engines that are allowed
            engine_type: Type of engine (e.g., "TTS", "Translation")
            
        Returns:
            Dictionary with error message and extensions
            
        Requirements: 10.2, 10.6
        
        Example:
            >>> ErrorFormatter.format_engine_not_allowed_error(
            ...     "COQUI",
            ...     ["OFFLINE", "ONLINE", "G_CLOUD"],
            ...     "TTS"
            ... )
        """
        message = (
            f"Engine '{engine}' is not allowed. "
            f"Available {engine_type} engines: {', '.join(allowed_engines)}"
        )
        
        return {
            "message": message,
            "extensions": {
                "code": ErrorCode.ENGINE_NOT_ALLOWED,
                "details": {
                    "provided": engine,
                    "allowed": allowed_engines,
                    "engine_type": engine_type
                }
            }
        }
    
    @staticmethod
    def format_file_error(
        message: str,
        error_type: str = "upload"
    ) -> Dict[str, Any]:
        """
        Creates a formatted error for file-related failures.
        
        Args:
            message: User-friendly error message
            error_type: Type of file error ("upload" or "download")
            
        Returns:
            Dictionary with error message and extensions
            
        Requirements: 10.4, 10.6
        
        Example:
            >>> ErrorFormatter.format_file_error(
            ...     "File size exceeds maximum allowed (50MB)",
            ...     error_type="upload"
            ... )
        """
        code = ErrorCode.FILE_UPLOAD_ERROR if error_type == "upload" else ErrorCode.FILE_NOT_FOUND
        
        return {
            "message": ErrorFormatter.redact_sensitive_data(message),
            "extensions": {
                "code": code,
                "details": {
                    "error_type": error_type
                }
            }
        }
    
    @staticmethod
    def format_service_error(
        message: str,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a formatted error for service processing failures.
        
        This method creates generic error messages for users while logging
        detailed information separately. Sensitive data is automatically redacted.
        
        Args:
            message: Error message (will be redacted)
            service_name: Name of the service that failed (optional)
            
        Returns:
            Dictionary with error message and extensions
            
        Requirements: 10.3, 10.5, 10.6, 10.7
        
        Example:
            >>> ErrorFormatter.format_service_error(
            ...     "TTS processing failed",
            ...     service_name="TTSService"
            ... )
        """
        # Create generic user-facing message
        user_message = "An error occurred during processing. Please check your input and try again."
        
        extensions = {
            "code": ErrorCode.SERVICE_ERROR,
        }
        
        if service_name:
            extensions["service"] = service_name
        
        return {
            "message": user_message,
            "extensions": extensions
        }
    
    @staticmethod
    def format_not_found_error(
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """
        Creates a formatted error for resource not found failures.
        
        Args:
            resource_type: Type of resource (e.g., "job", "file")
            resource_id: ID of the resource that was not found
            
        Returns:
            Dictionary with error message and extensions
            
        Requirements: 10.6
        
        Example:
            >>> ErrorFormatter.format_not_found_error("job", "abc123")
        """
        code = ErrorCode.JOB_NOT_FOUND if resource_type == "job" else ErrorCode.FILE_NOT_FOUND
        
        return {
            "message": f"{resource_type.capitalize()} with ID '{resource_id}' not found",
            "extensions": {
                "code": code,
                "details": {
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }
            }
        }


class ErrorLogger:
    """
    Logs errors with full details for debugging and monitoring.
    
    This class separates user-facing error messages from detailed logging,
    ensuring that sensitive information is logged for debugging but never
    exposed to clients.
    
    Requirements: 10.5
    """
    
    @staticmethod
    def log_error(
        logger: logging.Logger,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None
    ) -> None:
        """
        Logs an error with full details including stack trace and context.
        
        Args:
            logger: Logger instance to use
            error: The exception that occurred
            context: Additional context information (e.g., input parameters)
            operation: Name of the operation that failed
            
        Requirements: 10.5
        
        Example:
            >>> ErrorLogger.log_error(
            ...     logger,
            ...     ValueError("Invalid chunk size"),
            ...     context={"chunk_size": -100, "engine": "ONLINE"},
            ...     operation="generate_speech"
            ... )
        """
        log_message = f"Error in operation: {operation or 'unknown'}"
        
        if context:
            log_message += f"\nContext: {context}"
        
        log_message += f"\nError: {str(error)}"
        
        logger.error(log_message, exc_info=True)


# ============================================================================
# Query Type
# ============================================================================

@strawberry.type
class Query:
    """
    GraphQL Query type for read operations.
    
    Provides queries for:
    - Checking available TTS and translation engines
    - Querying job status for asynchronous operations
    - Downloading generated files
    """

    @strawberry.field
    async def available_engines(self, info: strawberry.Info) -> EngineInfo:
        """
        Returns lists of available TTS and translation engines.
        
        The returned engines are filtered based on the server configuration
        (ALLOWED_TTS_ENGINES and ALLOWED_TRANSLATOR_ENGINES in .env.server).
        
        Returns:
            EngineInfo: Lists of available engines with their metadata
            
        Example query:
            ```graphql
            query {
              availableEngines {
                ttsEngines {
                  name
                  description
                  requiredParameters
                  optionalParameters
                }
                translationEngines {
                  name
                  description
                  requiredParameters
                  optionalParameters
                }
              }
            }
            ```
        """
        return await ResolverQuery.available_engines(self, info)
        # Resolver implementation will be added in task 13.1
        raise NotImplementedError("Resolver not yet implemented")

    @strawberry.field
    async def job_status(self, job_id: str) -> JobStatus:
        """
        Returns current status and progress of an asynchronous job.
        
        Args:
            job_id: Unique identifier of the job to query
            
        Returns:
            JobStatus: Current status, progress, and result (if completed)
            
        Raises:
            GraphQL error if job_id is not found
            
        Example query:
            ```graphql
            query {
              jobStatus(jobId: "abc123") {
                jobId
                status
                progress {
                  percentage
                  currentChunk
                  totalChunks
                  stage
                  estimatedTimeRemaining
                }
                result {
                  ... on TTSResult {
                    success
                    message
                    outputFiles
                  }
                }
                error
              }
            }
            ```
        """
        # Resolver implementation will be added in task 13.1
        raise NotImplementedError("Resolver not yet implemented")

    @strawberry.field
    async def download_file(self, file_id: str) -> FileDownload:
        """
        Returns file content or download URL for a generated file.
        
        Args:
            file_id: Unique identifier of the file to download
            
        Returns:
            FileDownload: File metadata and content or download URL
            
        Raises:
            GraphQL error if file_id is not found or file does not exist
            
        Example query:
            ```graphql
            query {
              downloadFile(fileId: "xyz789") {
                fileId
                filename
                contentType
                sizeBytes
                downloadUrl
              }
            }
            ```
        """
        # Resolver implementation will be added in task 13.1
        raise NotImplementedError("Resolver not yet implemented")


# ============================================================================
# Mutation Type
# ============================================================================

@strawberry.type
class Mutation:
    """
    GraphQL Mutation type for TTS and translation operations.
    
    Provides mutations for:
    - Generating speech from text (TTS)
    - Translating text between languages
    
    Both mutations support synchronous and asynchronous execution modes.
    """

    @strawberry.mutation
    async def generate_speech(
        self,
        engine: str,
        text_content: Optional[str] = None,
        file_upload: Optional[str] = None,
        chunk_size: int = 3500,
        chunk_by_paragraph: bool = False,
        speaking_rate: float = 1.1,
        output_type: str = "AUDIO",
        max_file_duration: int = 600,
        clean_output_directory: bool = False,
        offline_voice: Optional[str] = None,
        language_code: str = "cs-CZ",
        google_credentials: Optional[str] = None,
        google_voice: str = "cs-CZ-Standard-B",
        coqui_model: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        coqui_speaker: Optional[str] = None,
        coqui_wav: Optional[str] = None,
        coqui_sample_rate: int = 22050,
        async_mode: bool = False,
    ) -> Union[TTSResult, JobCreated]:
        """
        Generates speech from text using the specified TTS engine.
        
        Args:
            engine: TTS engine to use (OFFLINE, ONLINE, G_CLOUD, COQUI)
            text_content: Text to convert to speech (alternative to file_upload)
            file_upload: Path to text file to convert (alternative to text_content)
            chunk_size: Maximum characters per chunk (default: 3500)
            chunk_by_paragraph: Split by paragraphs instead of sentences (default: False)
            speaking_rate: Speech rate multiplier (default: 1.1)
            output_type: Output format - AUDIO or FILE (default: AUDIO)
            max_file_duration: Maximum duration per audio file in seconds (default: 600)
            clean_output_directory: Remove existing files in output directory (default: False)
            offline_voice: Voice name for OFFLINE engine
            language_code: Language code for speech (default: cs-CZ)
            google_credentials: Path to Google Cloud credentials JSON
            google_voice: Voice name for Google Cloud TTS (default: cs-CZ-Standard-B)
            coqui_model: Model name for Coqui TTS
            coqui_speaker: Speaker name for Coqui TTS
            coqui_wav: Path to reference WAV file for Coqui TTS
            coqui_sample_rate: Sample rate for Coqui TTS (default: 22050)
            async_mode: Execute asynchronously and return job ID (default: False)
            
        Returns:
            TTSResult: Result with output files and metadata (if async_mode=False)
            JobCreated: Job information for status tracking (if async_mode=True)
            
        Raises:
            GraphQL error if:
            - Neither text_content nor file_upload is provided
            - Engine is not in ALLOWED_TTS_ENGINES
            - Invalid parameter values
            - Processing fails
            
        Example mutation (synchronous):
            ```graphql
            mutation {
              generateSpeech(
                engine: "ONLINE"
                textContent: "Hello world"
                languageCode: "en-US"
              ) {
                success
                message
                outputFiles
                metadata {
                  engineUsed
                  totalChunks
                  totalDurationSeconds
                }
              }
            }
            ```
            
        Example mutation (asynchronous):
            ```graphql
            mutation {
              generateSpeech(
                engine: "ONLINE"
                textContent: "Hello world"
                asyncMode: true
              )
            }
            ```
        """
        # Resolver implementation will be added in task 14.1
        raise NotImplementedError("Resolver not yet implemented")

    @strawberry.mutation
    async def translate_text(
        self,
        engine: str,
        source_language: str,
        target_language: str,
        text_content: Optional[str] = None,
        file_upload: Optional[str] = None,
        translation_prompt: str = "You are a professional book translator...",
        chunk_size: int = 4000,
        chunk_by_paragraph: bool = True,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
        google_credentials: Optional[str] = None,
        gemini_model: str = "gemini-pro",
        deepl_api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        clean_output_directory: bool = False,
        async_mode: bool = False,
    ) -> Union[TranslationResult, JobCreated]:
        """
        Translates text from source language to target language.
        
        Args:
            engine: Translation engine to use (OPENAI, GEMINI, DEEPL)
            source_language: Source language code (e.g., "en", "cs", "de")
            target_language: Target language code (e.g., "en", "cs", "de")
            text_content: Text to translate (alternative to file_upload)
            file_upload: Path to text file to translate (alternative to text_content)
            translation_prompt: System prompt for AI translation engines
            chunk_size: Maximum characters per chunk (default: 4000)
            chunk_by_paragraph: Split by paragraphs instead of sentences (default: True)
            openai_api_key: OpenAI API key (if not in .env.translator)
            openai_model: OpenAI model name (default: gpt-4o-mini)
            google_credentials: Path to Google Cloud credentials JSON
            gemini_model: Gemini model name (default: gemini-pro)
            deepl_api_key: DeepL API key (if not in .env.translator)
            max_retries: Maximum retry attempts on failure (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            clean_output_directory: Remove existing files in output directory (default: False)
            async_mode: Execute asynchronously and return job ID (default: False)
            
        Returns:
            TranslationResult: Result with output file and metadata (if async_mode=False)
            JobCreated: Job information for status tracking (if async_mode=True)
            
        Raises:
            GraphQL error if:
            - Neither text_content nor file_upload is provided
            - Engine is not in ALLOWED_TRANSLATOR_ENGINES
            - Invalid parameter values
            - Processing fails
            
        Example mutation (synchronous):
            ```graphql
            mutation {
              translateText(
                engine: "OPENAI"
                sourceLanguage: "en"
                targetLanguage: "cs"
                textContent: "Hello world"
              ) {
                success
                message
                outputFile
                metadata {
                  engineUsed
                  sourceLanguage
                  targetLanguage
                  totalChunks
                }
              }
            }
            ```
            
        Example mutation (asynchronous):
            ```graphql
            mutation {
              translateText(
                engine: "OPENAI"
                sourceLanguage: "en"
                targetLanguage: "cs"
                textContent: "Hello world"
                asyncMode: true
              )
            }
            ```
        """
        # Resolver implementation will be added in task 14.1
        raise NotImplementedError("Resolver not yet implemented")


# ============================================================================
# Schema Definition
# ============================================================================

# The schema will be instantiated in server/main.py with:
# schema = strawberry.Schema(query=Query, mutation=Mutation)
