"""
Unit tests for error handling utilities in server/schema.py.

Tests the ErrorCode, ErrorFormatter, and ErrorLogger classes to ensure
proper error formatting, sensitive data redaction, and structured error responses.
"""

import logging

import pytest

from server.graphql.schema import ErrorCode, ErrorFormatter, ErrorLogger


class TestErrorCode:
    """Tests for ErrorCode constants."""

    def test_error_codes_defined(self):
        """Verify all required error codes are defined."""
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.ENGINE_NOT_ALLOWED == "ENGINE_NOT_ALLOWED"
        assert ErrorCode.FILE_UPLOAD_ERROR == "FILE_UPLOAD_ERROR"
        assert ErrorCode.JOB_NOT_FOUND == "JOB_NOT_FOUND"
        assert ErrorCode.FILE_NOT_FOUND == "FILE_NOT_FOUND"
        assert ErrorCode.SERVICE_ERROR == "SERVICE_ERROR"
        assert ErrorCode.RATE_LIMIT_EXCEEDED == "RATE_LIMIT_EXCEEDED"
        assert ErrorCode.TIMEOUT_ERROR == "TIMEOUT_ERROR"


class TestErrorFormatter:
    """Tests for ErrorFormatter class."""

    def test_redact_api_key(self):
        """Test that API keys are redacted from error messages."""
        message = "Failed to authenticate with api_key=sk-abc123xyz"
        redacted = ErrorFormatter.redact_sensitive_data(message)
        assert "sk-abc123xyz" not in redacted
        assert "[REDACTED_API_KEY]" in redacted

    def test_redact_token(self):
        """Test that tokens are redacted from error messages."""
        message = "Invalid token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = ErrorFormatter.redact_sensitive_data(message)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "[REDACTED_TOKEN]" in redacted

    def test_redact_password(self):
        """Test that passwords are redacted from error messages."""
        message = "Authentication failed with password=secret123"
        redacted = ErrorFormatter.redact_sensitive_data(message)
        assert "secret123" not in redacted
        assert "[REDACTED_PASSWORD]" in redacted

    def test_redact_file_paths(self):
        """Test that file paths are redacted but filenames are preserved."""
        message = "File not found: /home/user/documents/secret/file.txt"
        redacted = ErrorFormatter.redact_sensitive_data(message)
        assert "/home/user/documents/secret/" not in redacted
        assert "file.txt" in redacted

    def test_format_validation_error_basic(self):
        """Test basic validation error formatting."""
        error = ErrorFormatter.format_validation_error("Missing required parameter")

        assert error["message"] == "Missing required parameter"
        assert error["extensions"]["code"] == ErrorCode.VALIDATION_ERROR

    def test_format_validation_error_with_field(self):
        """Test validation error formatting with field name."""
        error = ErrorFormatter.format_validation_error(
            "Missing required parameter", field="text_content"
        )

        assert error["message"] == "Missing required parameter"
        assert error["extensions"]["code"] == ErrorCode.VALIDATION_ERROR
        assert error["extensions"]["field"] == "text_content"

    def test_format_validation_error_with_details(self):
        """Test validation error formatting with additional details."""
        error = ErrorFormatter.format_validation_error(
            "Invalid value",
            field="chunk_size",
            details={"provided": -100, "minimum": 1},
        )

        assert error["extensions"]["code"] == ErrorCode.VALIDATION_ERROR
        assert error["extensions"]["field"] == "chunk_size"
        assert error["extensions"]["details"]["provided"] == -100
        assert error["extensions"]["details"]["minimum"] == 1

    def test_format_engine_not_allowed_error(self):
        """Test engine not allowed error formatting."""
        error = ErrorFormatter.format_engine_not_allowed_error(
            "COQUI", ["OFFLINE", "ONLINE", "G_CLOUD"], "TTS"
        )

        assert "COQUI" in error["message"]
        assert "OFFLINE" in error["message"]
        assert error["extensions"]["code"] == ErrorCode.ENGINE_NOT_ALLOWED
        assert error["extensions"]["details"]["provided"] == "COQUI"
        assert error["extensions"]["details"]["allowed"] == [
            "OFFLINE",
            "ONLINE",
            "G_CLOUD",
        ]
        assert error["extensions"]["details"]["engine_type"] == "TTS"

    def test_format_file_upload_error(self):
        """Test file upload error formatting."""
        error = ErrorFormatter.format_file_error(
            "File size exceeds maximum allowed (50MB)", error_type="upload"
        )

        assert "File size exceeds maximum" in error["message"]
        assert error["extensions"]["code"] == ErrorCode.FILE_UPLOAD_ERROR
        assert error["extensions"]["details"]["error_type"] == "upload"

    def test_format_file_download_error(self):
        """Test file download error formatting."""
        error = ErrorFormatter.format_file_error(
            "File not found", error_type="download"
        )

        assert "File not found" in error["message"]
        assert error["extensions"]["code"] == ErrorCode.FILE_NOT_FOUND
        assert error["extensions"]["details"]["error_type"] == "download"

    def test_format_service_error(self):
        """Test service error formatting with generic message."""
        error = ErrorFormatter.format_service_error(
            "TTS processing failed with api_key=secret123", service_name="TTSService"
        )

        # Should return generic message to user
        assert "An error occurred during processing" in error["message"]
        # Should not expose sensitive data
        assert "secret123" not in error["message"]
        assert error["extensions"]["code"] == ErrorCode.SERVICE_ERROR
        assert error["extensions"]["service"] == "TTSService"

    def test_format_not_found_error_job(self):
        """Test job not found error formatting."""
        error = ErrorFormatter.format_not_found_error("job", "abc123")

        assert "job" in error["message"].lower()
        assert "abc123" in error["message"]
        assert error["extensions"]["code"] == ErrorCode.JOB_NOT_FOUND
        assert error["extensions"]["details"]["resource_type"] == "job"
        assert error["extensions"]["details"]["resource_id"] == "abc123"

    def test_format_not_found_error_file(self):
        """Test file not found error formatting."""
        error = ErrorFormatter.format_not_found_error("file", "xyz789")

        assert "file" in error["message"].lower()
        assert "xyz789" in error["message"]
        assert error["extensions"]["code"] == ErrorCode.FILE_NOT_FOUND
        assert error["extensions"]["details"]["resource_type"] == "file"
        assert error["extensions"]["details"]["resource_id"] == "xyz789"


class TestErrorLogger:
    """Tests for ErrorLogger class."""

    def test_log_error_basic(self, caplog):
        """Test basic error logging."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        error = ValueError("Invalid chunk size")

        with caplog.at_level(logging.ERROR):
            ErrorLogger.log_error(logger, error, operation="generate_speech")

        assert "generate_speech" in caplog.text
        assert "Invalid chunk size" in caplog.text

    def test_log_error_with_context(self, caplog):
        """Test error logging with context information."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        error = ValueError("Invalid parameter")
        context = {"chunk_size": -100, "engine": "ONLINE"}

        with caplog.at_level(logging.ERROR):
            ErrorLogger.log_error(
                logger, error, context=context, operation="generate_speech"
            )

        assert "generate_speech" in caplog.text
        assert "Invalid parameter" in caplog.text
        assert "chunk_size" in caplog.text
        assert "-100" in caplog.text

    def test_log_error_includes_stack_trace(self, caplog):
        """Test that error logging includes stack trace."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        try:
            raise RuntimeError("Test error with stack trace")
        except RuntimeError as e:
            with caplog.at_level(logging.ERROR):
                ErrorLogger.log_error(logger, e, operation="test_operation")

        # Stack trace should be included
        assert "Traceback" in caplog.text or "RuntimeError" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
