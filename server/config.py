"""
Configuration management for the GraphQL server.

This module loads and validates server configuration from .env.server file.
It provides sensible defaults for all settings and validates configuration values.
"""

import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv


class ServerConfig:
    """
    Server configuration loaded from .env.server file.
    
    This class manages all server settings including:
    - Server host and port
    - Logging configuration
    - File handling settings
    - Engine allowlists
    - Job management settings
    - Performance settings
    
    Validates: Requirements 9.1, 9.2, 9.3, 9.6
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        max_upload_size_mb: int = 50,
        temp_directory: str = "./temp",
        allowed_tts_engines: List[str] = None,
        allowed_translator_engines: List[str] = None,
        max_concurrent_jobs: int = 4,
        job_cleanup_hours: int = 24,
        request_timeout_seconds: int = 300
    ):
        """
        Initialize ServerConfig with provided values or defaults.
        
        Args:
            host: Server host address (default: 0.0.0.0)
            port: Server port number (default: 8000)
            log_level: Logging level (default: INFO)
            log_file: Path to log file (default: None - console only)
            log_format: Log message format string
            max_upload_size_mb: Maximum file upload size in MB (default: 50)
            temp_directory: Directory for temporary files (default: ./temp)
            allowed_tts_engines: List of allowed TTS engines (default: all)
            allowed_translator_engines: List of allowed translation engines (default: all)
            max_concurrent_jobs: Maximum concurrent jobs (default: 4)
            job_cleanup_hours: Hours to keep completed jobs (default: 24)
            request_timeout_seconds: Request timeout in seconds (default: 300)
        """
        self.host = host
        self.port = port
        self.log_level = log_level
        self.log_file = log_file
        self.log_format = log_format
        self.max_upload_size_mb = max_upload_size_mb
        self.temp_directory = temp_directory
        
        # Default engine allowlists if not provided
        self.allowed_tts_engines = allowed_tts_engines or ["OFFLINE", "ONLINE", "G_CLOUD", "COQUI"]
        self.allowed_translator_engines = allowed_translator_engines or ["OPENAI", "GEMINI", "DEEPL"]
        
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_cleanup_hours = job_cleanup_hours
        self.request_timeout_seconds = request_timeout_seconds
        
        # Validate configuration
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any configuration value is invalid
            
        Validates: Requirement 9.6
        """
        # Validate port
        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}. Must be between 1 and 65535.")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log level: {self.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Validate max upload size
        if not isinstance(self.max_upload_size_mb, int) or self.max_upload_size_mb < 1:
            raise ValueError(
                f"Invalid max_upload_size_mb: {self.max_upload_size_mb}. "
                f"Must be a positive integer."
            )
        
        # Validate TTS engines
        valid_tts_engines = ["OFFLINE", "ONLINE", "G_CLOUD", "COQUI"]
        for engine in self.allowed_tts_engines:
            if engine not in valid_tts_engines:
                raise ValueError(
                    f"Invalid TTS engine: {engine}. "
                    f"Must be one of: {', '.join(valid_tts_engines)}"
                )
        
        # Validate translation engines
        valid_translator_engines = ["OPENAI", "GEMINI", "DEEPL"]
        for engine in self.allowed_translator_engines:
            if engine not in valid_translator_engines:
                raise ValueError(
                    f"Invalid translation engine: {engine}. "
                    f"Must be one of: {', '.join(valid_translator_engines)}"
                )
        
        # Validate max concurrent jobs
        if not isinstance(self.max_concurrent_jobs, int) or self.max_concurrent_jobs < 1:
            raise ValueError(
                f"Invalid max_concurrent_jobs: {self.max_concurrent_jobs}. "
                f"Must be a positive integer."
            )
        
        # Validate job cleanup hours
        if not isinstance(self.job_cleanup_hours, int) or self.job_cleanup_hours < 1:
            raise ValueError(
                f"Invalid job_cleanup_hours: {self.job_cleanup_hours}. "
                f"Must be a positive integer."
            )
        
        # Validate request timeout
        if not isinstance(self.request_timeout_seconds, int) or self.request_timeout_seconds < 1:
            raise ValueError(
                f"Invalid request_timeout_seconds: {self.request_timeout_seconds}. "
                f"Must be a positive integer."
            )
    
    @classmethod
    def load_from_env(cls, env_file: str = ".env.server") -> "ServerConfig":
        """
        Load configuration from .env.server file.
        
        If the file doesn't exist, returns a ServerConfig with default values.
        
        Args:
            env_file: Path to the environment file (default: .env.server)
            
        Returns:
            ServerConfig instance with loaded or default values
            
        Validates: Requirements 9.1, 9.2, 9.3
        """
        # Load .env.server if it exists (override=True to replace existing env vars)
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
        
        # Parse configuration from environment variables with defaults
        host = os.getenv("SERVER_HOST", "0.0.0.0")
        port = int(os.getenv("SERVER_PORT", "8000"))
        
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE", "").strip()
        log_file = log_file if log_file else None
        log_format = os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
        temp_directory = os.getenv("TEMP_DIRECTORY", "./temp")
        
        # Parse engine allowlists (comma-separated)
        allowed_tts_engines_str = os.getenv("ALLOWED_TTS_ENGINES", "OFFLINE,ONLINE,G_CLOUD,COQUI")
        allowed_tts_engines = [
            engine.strip() 
            for engine in allowed_tts_engines_str.split(",") 
            if engine.strip()
        ]
        
        allowed_translator_engines_str = os.getenv(
            "ALLOWED_TRANSLATOR_ENGINES", 
            "OPENAI,GEMINI,DEEPL"
        )
        allowed_translator_engines = [
            engine.strip() 
            for engine in allowed_translator_engines_str.split(",") 
            if engine.strip()
        ]
        
        max_concurrent_jobs = int(os.getenv("MAX_CONCURRENT_JOBS", "4"))
        job_cleanup_hours = int(os.getenv("JOB_CLEANUP_HOURS", "24"))
        request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "300"))
        
        return cls(
            host=host,
            port=port,
            log_level=log_level,
            log_file=log_file,
            log_format=log_format,
            max_upload_size_mb=max_upload_size_mb,
            temp_directory=temp_directory,
            allowed_tts_engines=allowed_tts_engines,
            allowed_translator_engines=allowed_translator_engines,
            max_concurrent_jobs=max_concurrent_jobs,
            job_cleanup_hours=job_cleanup_hours,
            request_timeout_seconds=request_timeout_seconds
        )
    
    @classmethod
    def generate_env_template(cls, output_path: str = ".env.server") -> None:
        """
        Generate a template .env.server file with default configuration.
        
        Args:
            output_path: Path where the template file should be created
            
        Validates: Requirement 9.5
        """
        template = """# GraphQL Server Configuration
# This file contains configuration for the GraphQL server that provides
# a unified API interface for TTS and Translation services.

# ============================================================================
# SERVER SETTINGS
# ============================================================================

# Host address to bind the server to
# Use 0.0.0.0 to accept connections from any network interface
# Use 127.0.0.1 to accept only local connections
SERVER_HOST=0.0.0.0

# Port number for the server
SERVER_PORT=8000

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Path to log file (leave empty to disable file logging)
# Example: ./logs/server.log
LOG_FILE=

# Log format string
# Default includes timestamp, component name, log level, and message
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# ============================================================================
# FILE HANDLING
# ============================================================================

# Maximum file upload size in megabytes
MAX_UPLOAD_SIZE_MB=50

# Directory for temporary file storage
# Uploaded files are saved here during processing
TEMP_DIRECTORY=./temp

# ============================================================================
# ENGINE ALLOWLISTS
# ============================================================================

# Allowed TTS engines (comma-separated list)
# Available options: OFFLINE, ONLINE, G_CLOUD, COQUI
# Only engines in this list can be used via the GraphQL API
ALLOWED_TTS_ENGINES=OFFLINE,ONLINE,G_CLOUD,COQUI

# Allowed translation engines (comma-separated list)
# Available options: OPENAI, GEMINI, DEEPL
# Only engines in this list can be used via the GraphQL API
ALLOWED_TRANSLATOR_ENGINES=OPENAI,GEMINI,DEEPL

# ============================================================================
# JOB MANAGEMENT
# ============================================================================

# Maximum number of concurrent jobs
# Limits how many TTS/translation operations can run simultaneously
MAX_CONCURRENT_JOBS=4

# Hours to keep completed/failed jobs in memory before cleanup
JOB_CLEANUP_HOURS=24

# ============================================================================
# PERFORMANCE
# ============================================================================

# Request timeout in seconds
# Maximum time allowed for a single GraphQL request to complete
REQUEST_TIMEOUT_SECONDS=300

# ============================================================================
# NOTES
# ============================================================================
# 
# - This configuration file is loaded at server startup
# - Changes require server restart to take effect
# - Engine-specific configurations (API keys, credentials) should be set
#   in .env.tts and .env.translator files
# - The server will use sensible defaults if this file is missing
# - Use the --generate-env command to regenerate this template
#
"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)
        
        print(f"Generated .env.server template at: {output_path}")
    
    def __repr__(self) -> str:
        """String representation of the configuration."""
        return (
            f"ServerConfig("
            f"host={self.host}, "
            f"port={self.port}, "
            f"log_level={self.log_level}, "
            f"allowed_tts_engines={self.allowed_tts_engines}, "
            f"allowed_translator_engines={self.allowed_translator_engines})"
        )
