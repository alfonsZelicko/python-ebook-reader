"""
GraphQL schema definition for TTS and Translation services.

This module defines the main GraphQL schema including Query and Mutation types.
The resolvers are implemented in separate files (server/resolvers/query.py and
server/resolvers/mutation.py) and will be connected in later tasks.
"""

import logging
import re
from typing import Optional, Union, Dict, Any

import strawberry

from server.graphql.resolvers import (
    Mutation as ResolverMutation,
    JobCreated as ResolverJobCreated,
)
from server.graphql.resolvers import Query as ResolverQuery
from server.graphql.types import (
    EngineInfo,
    JobStatus,
    FileDownload,
    TTSResult,
    TranslationResult,
)
from server.graphql.types import TTSInput, TranslationInput


# =========================== Error Handling Utilities =========================== #


class ErrorCode:
    """
    Standard error codes for GraphQL error extensions.

    These codes provide structured error information to clients and help
    categorize different types of failures.
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
    """

    # Patterns for sensitive data that should be redacted
    SENSITIVE_PATTERNS = [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', "[REDACTED_API_KEY]"),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)', "[REDACTED_TOKEN]"),
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', "[REDACTED_PASSWORD]"),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)', "[REDACTED_SECRET]"),
        (r'credentials["\']?\s*[:=]\s*["\']?([^"\'\s]+)', "[REDACTED_CREDENTIALS]"),
        # Redact file paths except for output filenames
        (r"/[a-zA-Z0-9_\-./]+/([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)", r"\1"),
    ]

    @staticmethod
    def redact_sensitive_data(message: str) -> str:
        """
        Removes sensitive information from error messages. Borowed from internet > "'trust me bro' code!"

        This method scans error messages for patterns that might contain
        sensitive data (API keys, tokens, passwords, file paths) and
        replaces them with safe placeholders.

        Args:
            message: Original error message that may contain sensitive data

        Returns:
            Sanitized error message with sensitive data redacted

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
            details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a formatted validation error with extensions.

        Args:
            message: User-friendly error message
            field: Name of the field that failed validation (optional)
            details: Additional error details (optional)

        Returns:
            Dictionary with error message and extensions

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
            "extensions": extensions,
        }

    @staticmethod
    def format_engine_not_allowed_error(
            engine: str, allowed_engines: list, engine_type: str = "engine"
    ) -> Dict[str, Any]:
        """
        Creates a formatted error for disallowed engine usage.

        Args:
            engine: The engine that was requested
            allowed_engines: List of engines that are allowed
            engine_type: Type of engine (e.g., "TTS", "Translation")

        Returns:
            Dictionary with error message and extensions

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
                    "engine_type": engine_type,
                },
            },
        }

    @staticmethod
    def format_file_error(message: str, error_type: str = "upload") -> Dict[str, Any]:
        """
        Creates a formatted error for file-related failures.

        Args:
            message: User-friendly error message
            error_type: Type of file error ("upload" or "download")

        Returns:
            Dictionary with error message and extensions

        Example:
            >>> ErrorFormatter.format_file_error(
            ...     "File size exceeds maximum allowed (50MB)",
            ...     error_type="upload"
            ... )
        """
        code = (
            ErrorCode.FILE_UPLOAD_ERROR
            if error_type == "upload"
            else ErrorCode.FILE_NOT_FOUND
        )

        return {
            "message": ErrorFormatter.redact_sensitive_data(message),
            "extensions": {"code": code, "details": {"error_type": error_type}},
        }

    @staticmethod
    def format_service_error(
            message: str, service_name: Optional[str] = None
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

        return {"message": user_message, "extensions": extensions}

    @staticmethod
    def format_not_found_error(resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Creates a formatted error for resource not found failures.

        Args:
            resource_type: Type of resource (e.g., "job", "file")
            resource_id: ID of the resource that was not found

        Returns:
            Dictionary with error message and extensions

        Example:
            >>> ErrorFormatter.format_not_found_error("job", "abc123")
        """
        code = (
            ErrorCode.JOB_NOT_FOUND
            if resource_type == "job"
            else ErrorCode.FILE_NOT_FOUND
        )

        return {
            "message": f"{resource_type.capitalize()} with ID '{resource_id}' not found",
            "extensions": {
                "code": code,
                "details": {"resource_type": resource_type, "resource_id": resource_id},
            },
        }


class ErrorLogger:
    """
    Logs errors with full details for debugging and monitoring.

    This class separates user-facing error messages from detailed logging,
    ensuring that sensitive information is logged for debugging but never
    exposed to clients.
    """

    @staticmethod
    def log_error(
            logger: logging.Logger,
            error: Exception,
            context: Optional[Dict[str, Any]] = None,
            operation: Optional[str] = None,
    ) -> None:
        """
        Logs an error with full details including stack trace and context.

        Args:
            logger: Logger instance to use
            error: The exception that occurred
            context: Additional context information (e.g., input parameters)
            operation: Name of the operation that failed

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


# =========================== Query Type =========================== #


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
        Returns lists of available TTS and translation engines (mostly what is properly implemented and free -> later with credits it will be little more complicated).

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

    @strawberry.field
    async def job_status(self, job_id: str, info: strawberry.Info) -> JobStatus:
        """
        Returns current status and progress of an asynchronous job.

        Args:
            job_id: Unique identifier of the job to query
            info: Strawberry info object containing context

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
        return await ResolverQuery.job_status(self, job_id, info)

    @strawberry.field
    async def download_file(self, file_id: str, info: strawberry.Info) -> FileDownload:
        """
        Returns file content or download URL for a generated file.

        Args:
            file_id: Unique identifier of the file to download
            info: Strawberry info object containing context

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
        return await ResolverQuery.download_file(self, file_id, info)


# =========================== Mutation Type =========================== #


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
            info: strawberry.Info,
            input: TTSInput,
            async_mode: bool = False,
    ) -> Union[TTSResult, ResolverJobCreated]:
        """
        Generates speech from text using the specified TTS engine.

        Args:
            info: Strawberry info object containing context
            input: TTSInput with engine-specific parameters
            async_mode: Execute asynchronously and return job ID (default: False)

        Returns:
            TTSResult: Result with output files and metadata (if async_mode=False)
            JobCreated: Job information for status tracking (if async_mode=True)

        Example mutation (synchronous):
            ```graphql
            mutation {
              generateSpeech(
                input: {
                  engine: "ONLINE"
                  textContent: "Hello world"
                  languageCode: "en-US"
                }
              ) {
                ... on TTSResult {
                  success
                  message
                  outputFiles
                }
              }
            }
            ```
        """
        return await ResolverMutation.generate_speech(self, input, async_mode, info)

    @strawberry.mutation
    async def translate_text(
            self,
            info: strawberry.Info,
            input: TranslationInput,
            async_mode: bool = False,
    ) -> Union[TranslationResult, ResolverJobCreated]:
        """
        Translates text from source language to target language.

        Args:
            info: Strawberry info object containing context
            input: TranslationInput with engine-specific parameters
            async_mode: Execute asynchronously and return job ID (default: False)

        Returns:
            TranslationResult: Result with output file and metadata (if async_mode=False)
            JobCreated: Job information for status tracking (if async_mode=True)

        Example mutation (synchronous):
            ```graphql
            mutation {
              translateText(
                input: {
                  engine: "OPENAI"
                  sourceLanguage: "en"
                  targetLanguage: "cs"
                  textContent: "Hello world"
                }
              ) {
                ... on TranslationResult {
                  success
                  message
                  outputFile
                }
              }
            }
            ```
        """
        return await ResolverMutation.translate_text(self, input, async_mode, info)

# =========================== Schema Definition =========================== #

# The schema will be instantiated in server/main.py with:
# schema = strawberry.Schema(query=Query, mutation=Mutation)
