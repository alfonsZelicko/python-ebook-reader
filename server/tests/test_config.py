"""
Unit tests for ServerConfig class.

Tests configuration loading, validation, and default values.
"""

import os
import tempfile

import pytest

from server.core.config import ServerConfig


def test_default_config():
    """Test ServerConfig with default values."""
    config = ServerConfig()

    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.log_level == "INFO"
    assert config.log_file is None
    assert config.max_upload_size_mb == 50
    assert config.temp_directory == "./temp"
    assert "OFFLINE" in config.allowed_tts_engines
    assert "ONLINE" in config.allowed_tts_engines
    assert "G_CLOUD" in config.allowed_tts_engines
    assert "OPENAI" in config.allowed_translator_engines
    assert "GEMINI" in config.allowed_translator_engines
    assert "DEEPL" in config.allowed_translator_engines
    assert config.max_concurrent_jobs == 4
    assert config.job_cleanup_hours == 24
    assert config.request_timeout_seconds == 300


def test_load_from_env_with_missing_file():
    """Test loading configuration when .env.server doesn't exist."""
    # Use a non-existent file
    config = ServerConfig.load_from_env("nonexistent.env")

    # Should use defaults
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.log_level == "INFO"


def test_load_from_env_with_custom_values():
    """Test loading configuration from a custom .env file."""
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
        f.write("SERVER_HOST=127.0.0.1\n")
        f.write("SERVER_PORT=9000\n")
        f.write("LOG_LEVEL=DEBUG\n")
        f.write("LOG_FILE=./logs/test.log\n")
        f.write("MAX_UPLOAD_SIZE_MB=100\n")
        f.write("TEMP_DIRECTORY=./custom_temp\n")
        f.write("ALLOWED_TTS_ENGINES=OFFLINE,ONLINE\n")
        f.write("ALLOWED_TRANSLATOR_ENGINES=OPENAI\n")
        f.write("MAX_CONCURRENT_JOBS=8\n")
        f.write("JOB_CLEANUP_HOURS=48\n")
        f.write("REQUEST_TIMEOUT_SECONDS=600\n")
        temp_file = f.name

    try:
        config = ServerConfig.load_from_env(temp_file)

        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.log_level == "DEBUG"
        assert config.log_file == "./logs/test.log"
        assert config.max_upload_size_mb == 100
        assert config.temp_directory == "./custom_temp"
        assert config.allowed_tts_engines == ["OFFLINE", "ONLINE"]
        assert config.allowed_translator_engines == ["OPENAI"]
        assert config.max_concurrent_jobs == 8
        assert config.job_cleanup_hours == 48
        assert config.request_timeout_seconds == 600
    finally:
        os.unlink(temp_file)


def test_engine_allowlist_parsing():
    """Test parsing of comma-separated engine allowlists."""
    # Save current env vars
    old_tts = os.environ.get("ALLOWED_TTS_ENGINES")
    old_trans = os.environ.get("ALLOWED_TRANSLATOR_ENGINES")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
        f.write("ALLOWED_TTS_ENGINES=OFFLINE, ONLINE, G_CLOUD\n")
        f.write("ALLOWED_TRANSLATOR_ENGINES=OPENAI, GEMINI\n")
        temp_file = f.name

    try:
        config = ServerConfig.load_from_env(temp_file)

        # Should strip whitespace
        assert config.allowed_tts_engines == ["OFFLINE", "ONLINE", "G_CLOUD"]
        assert config.allowed_translator_engines == ["OPENAI", "GEMINI"]
    finally:
        os.unlink(temp_file)
        # Restore env vars
        if old_tts:
            os.environ["ALLOWED_TTS_ENGINES"] = old_tts
        elif "ALLOWED_TTS_ENGINES" in os.environ:
            del os.environ["ALLOWED_TTS_ENGINES"]
        if old_trans:
            os.environ["ALLOWED_TRANSLATOR_ENGINES"] = old_trans
        elif "ALLOWED_TRANSLATOR_ENGINES" in os.environ:
            del os.environ["ALLOWED_TRANSLATOR_ENGINES"]


def test_invalid_port_validation():
    """Test validation of invalid port numbers."""
    with pytest.raises(ValueError, match="Invalid port number"):
        ServerConfig(port=0)

    with pytest.raises(ValueError, match="Invalid port number"):
        ServerConfig(port=70000)

    with pytest.raises(ValueError, match="Invalid port number"):
        ServerConfig(port=-1)


def test_invalid_log_level_validation():
    """Test validation of invalid log levels."""
    with pytest.raises(ValueError, match="Invalid log level"):
        ServerConfig(log_level="INVALID")


def test_invalid_max_upload_size_validation():
    """Test validation of invalid max upload size."""
    with pytest.raises(ValueError, match="Invalid max_upload_size_mb"):
        ServerConfig(max_upload_size_mb=0)

    with pytest.raises(ValueError, match="Invalid max_upload_size_mb"):
        ServerConfig(max_upload_size_mb=-10)


def test_invalid_tts_engine_validation():
    """Test validation of invalid TTS engines."""
    with pytest.raises(ValueError, match="Invalid TTS engine"):
        ServerConfig(allowed_tts_engines=["INVALID_ENGINE"])


def test_invalid_translator_engine_validation():
    """Test validation of invalid translation engines."""
    with pytest.raises(ValueError, match="Invalid translation engine"):
        ServerConfig(allowed_translator_engines=["INVALID_ENGINE"])


def test_invalid_max_concurrent_jobs_validation():
    """Test validation of invalid max concurrent jobs."""
    with pytest.raises(ValueError, match="Invalid max_concurrent_jobs"):
        ServerConfig(max_concurrent_jobs=0)

    with pytest.raises(ValueError, match="Invalid max_concurrent_jobs"):
        ServerConfig(max_concurrent_jobs=-5)


def test_invalid_job_cleanup_hours_validation():
    """Test validation of invalid job cleanup hours."""
    with pytest.raises(ValueError, match="Invalid job_cleanup_hours"):
        ServerConfig(job_cleanup_hours=0)


def test_invalid_request_timeout_validation():
    """Test validation of invalid request timeout."""
    with pytest.raises(ValueError, match="Invalid request_timeout_seconds"):
        ServerConfig(request_timeout_seconds=0)


def test_generate_env_template():
    """Test generation of .env.server template file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.env")
        ServerConfig.generate_env_template(output_path)

        # Verify file was created
        assert os.path.exists(output_path)

        # Verify file contains expected content
        with open(output_path, "r") as f:
            content = f.read()
            assert "SERVER_HOST" in content
            assert "SERVER_PORT" in content
            assert "LOG_LEVEL" in content
            assert "ALLOWED_TTS_ENGINES" in content
            assert "ALLOWED_TRANSLATOR_ENGINES" in content


def test_config_repr():
    """Test string representation of ServerConfig."""
    config = ServerConfig()
    repr_str = repr(config)

    assert "ServerConfig" in repr_str
    assert "host=0.0.0.0" in repr_str
    assert "port=8000" in repr_str
    assert "log_level=INFO" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
