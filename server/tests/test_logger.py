"""
Unit tests for logger setup and RequestLogger middleware.

Tests logging configuration, handlers, formatters, and request logging.
"""

import logging
import os
import tempfile

import pytest

from server.core.config import ServerConfig
from server.core.logger import (
    setup_logger,
    RequestLogger,
    get_component_logger,
    ColoredFormatter,
)


def test_setup_logger_with_defaults():
    """Test logger setup with default configuration."""
    config = ServerConfig(log_level="INFO")
    logger = setup_logger(config)

    assert logger.name == "graphql_server"
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 1  # At least console handler
    assert not logger.propagate


def test_setup_logger_with_file_handler():
    """Test logger setup with file handler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        config = ServerConfig(log_level="DEBUG", log_file=log_file)
        logger = setup_logger(config)

        # Should have both console and file handlers
        assert len(logger.handlers) == 2
        assert logger.level == logging.DEBUG

        # Test logging to file
        logger.info("Test message")

        # Close all handlers to release file locks (Windows compatibility)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # Verify file was created and contains the message
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            content = f.read()
            assert "Test message" in content


def test_setup_logger_creates_log_directory():
    """Test that logger creates log directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "logs", "nested", "test.log")
        config = ServerConfig(log_file=log_file)
        logger = setup_logger(config)

        # Log a message
        logger.info("Test message")

        # Close all handlers to release file locks (Windows compatibility)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # Verify directory and file were created
        assert os.path.exists(log_file)


def test_setup_logger_log_levels():
    """Test logger setup with different log levels."""
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    for level_name in log_levels:
        config = ServerConfig(log_level=level_name)
        logger = setup_logger(config)

        expected_level = getattr(logging, level_name)
        assert logger.level == expected_level


def test_colored_formatter():
    """Test ColoredFormatter adds color codes to log messages."""
    formatter = ColoredFormatter("%(levelname)s - %(message)s")

    # Create a log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    # Should contain ANSI color codes
    assert "\033[" in formatted
    assert "Test message" in formatted


def test_request_logger_log_request():
    """Test RequestLogger logs incoming requests."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Log a request
    variables = {"engine": "ONLINE", "textContent": "Hello world", "chunkSize": 3500}

    # Should not raise any exceptions
    request_logger.log_request("generateSpeech", variables)


def test_request_logger_sanitizes_sensitive_data():
    """Test RequestLogger redacts sensitive data from logs."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Variables with sensitive data
    variables = {
        "engine": "OPENAI",
        "openai_api_key": "sk-secret-key-12345",
        "google_credentials": "/path/to/credentials.json",
        "text_content": "Long text content...",
        "source_language": "en",
    }

    sanitized = request_logger._sanitize_variables(variables)

    # Sensitive fields should be redacted
    assert sanitized["openai_api_key"] == "[REDACTED]"
    assert sanitized["google_credentials"] == "[REDACTED]"
    assert sanitized["text_content"] == "[REDACTED]"

    # Non-sensitive fields should remain
    assert sanitized["engine"] == "OPENAI"
    assert sanitized["source_language"] == "en"


def test_request_logger_sanitizes_nested_data():
    """Test RequestLogger redacts sensitive data in nested dictionaries."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Nested variables
    variables = {
        "input": {
            "engine": "GEMINI",
            "googleCredentials": "/path/to/creds.json",
            "sourceLanguage": "en",
        }
    }

    sanitized = request_logger._sanitize_variables(variables)

    # Nested sensitive field should be redacted
    assert sanitized["input"]["googleCredentials"] == "[REDACTED]"
    assert sanitized["input"]["engine"] == "GEMINI"


def test_request_logger_log_response_success():
    """Test RequestLogger logs successful responses."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Should not raise any exceptions
    request_logger.log_response("generateSpeech", 1234.56, success=True)


def test_request_logger_log_response_failure():
    """Test RequestLogger logs failed responses."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Should not raise any exceptions
    request_logger.log_response(
        "translateText", 567.89, success=False, error="API key invalid"
    )


def test_request_logger_log_service_start():
    """Test RequestLogger logs service operation start."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Should not raise any exceptions
    request_logger.log_service_start("TTS", "/tmp/input.txt")


def test_request_logger_log_service_complete():
    """Test RequestLogger logs service operation completion."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Should not raise any exceptions
    request_logger.log_service_complete("Translation", 45.67, "/tmp/output.txt")


def test_request_logger_log_error():
    """Test RequestLogger logs errors with context."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    context = {"operation": "generateSpeech", "engine": "ONLINE"}

    # Should not raise any exceptions
    request_logger.log_error("Test error message", context, exc_info=False)


def test_get_component_logger():
    """Test getting component-specific loggers."""
    # First setup the main logger
    config = ServerConfig()
    setup_logger(config)

    # Get component logger
    component_logger = get_component_logger("tts_service")

    assert component_logger.name == "graphql_server.tts_service"

    # Should be able to log
    component_logger.info("Test message from component")


def test_multiple_component_loggers():
    """Test multiple component loggers share the same configuration."""
    config = ServerConfig()
    setup_logger(config)

    tts_logger = get_component_logger("tts_service")
    translation_logger = get_component_logger("translation_service")
    job_logger = get_component_logger("job_manager")

    assert tts_logger.name == "graphql_server.tts_service"
    assert translation_logger.name == "graphql_server.translation_service"
    assert job_logger.name == "graphql_server.job_manager"


def test_logger_with_custom_format():
    """Test logger with custom log format."""
    custom_format = "%(levelname)s | %(name)s | %(message)s"
    config = ServerConfig(log_format=custom_format)

    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        config.log_file = log_file

        logger = setup_logger(config)
        logger.info("Test message")

        # Close all handlers to release file locks (Windows compatibility)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # Verify custom format is used in file
        with open(log_file, "r") as f:
            content = f.read()
            assert "INFO | graphql_server | Test message" in content


def test_logger_handles_empty_variables():
    """Test RequestLogger handles empty or None variables."""
    config = ServerConfig()
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)

    # Should handle None
    sanitized = request_logger._sanitize_variables(None)
    assert sanitized == {}

    # Should handle empty dict
    sanitized = request_logger._sanitize_variables({})
    assert sanitized == {}


def test_logger_no_duplicate_handlers():
    """Test that calling setup_logger multiple times doesn't create duplicate handlers."""
    config = ServerConfig()

    logger1 = setup_logger(config)
    handler_count1 = len(logger1.handlers)

    logger2 = setup_logger(config)
    handler_count2 = len(logger2.handlers)

    # Should have the same number of handlers
    assert handler_count1 == handler_count2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
