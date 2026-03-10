"""
Logging setup for the GraphQL server.

This module configures Python logging with console and file handlers,
custom formatters, and request logging middleware for GraphQL operations.

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds color to console output based on log level.
    
    Colors:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red + Bold
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[1;31m', # Bold Red
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with color for console output.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message with color codes
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for subsequent handlers
        record.levelname = levelname
        
        return formatted


def setup_logger(config) -> logging.Logger:
    """
    Configure Python logging with console and file handlers.
    
    Creates a logger with:
    - Console handler with colored output
    - File handler (if log_file is specified in config)
    - Custom formatter with timestamps and component names
    - Configurable log level from ServerConfig
    
    Args:
        config: ServerConfig instance with logging configuration
        
    Returns:
        Configured logger instance for the GraphQL server
        
    Validates: Requirements 8.1, 8.3, 8.6, 8.7, 8.8
    """
    # Create root logger for the server
    logger = logging.getLogger("graphql_server")
    
    # Set log level from config
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use colored formatter for console
    console_formatter = ColoredFormatter(
        config.log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if config.log_file:
        # Create log directory if it doesn't exist
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(config.log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Use standard formatter for file (no colors)
        file_formatter = logging.Formatter(
            config.log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logger initialized with level: {config.log_level}")
    if config.log_file:
        logger.info(f"Logging to file: {config.log_file}")
    
    return logger


class RequestLogger:
    """
    Middleware for logging GraphQL requests and responses.
    
    Logs:
    - Incoming GraphQL requests with operation name and parameters
    - Response timing and success status
    - Errors with full context
    
    Validates: Requirements 8.2, 8.4, 8.5
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize RequestLogger with a logger instance.
        
        Args:
            logger: Logger instance to use for request logging
        """
        self.logger = logger
    
    def log_request(self, operation_name: str, variables: dict) -> None:
        """
        Log incoming GraphQL request.
        
        Logs the operation name and sanitized variables (sensitive data redacted).
        
        Args:
            operation_name: Name of the GraphQL operation (query/mutation)
            variables: GraphQL variables provided with the request
            
        Validates: Requirement 8.2
        """
        # Sanitize variables to remove sensitive data
        sanitized_vars = self._sanitize_variables(variables)
        
        self.logger.info(
            f"GraphQL Request: {operation_name}",
            extra={
                'operation': operation_name,
                'variables': sanitized_vars
            }
        )
    
    def log_response(
        self, 
        operation_name: str, 
        duration_ms: float, 
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Log GraphQL response with timing information.
        
        Args:
            operation_name: Name of the GraphQL operation
            duration_ms: Request duration in milliseconds
            success: Whether the request succeeded
            error: Error message if request failed
            
        Validates: Requirement 8.4
        """
        if success:
            self.logger.info(
                f"GraphQL Response: {operation_name} completed in {duration_ms:.2f}ms",
                extra={
                    'operation': operation_name,
                    'duration_ms': duration_ms,
                    'success': True
                }
            )
        else:
            self.logger.error(
                f"GraphQL Response: {operation_name} failed after {duration_ms:.2f}ms - {error}",
                extra={
                    'operation': operation_name,
                    'duration_ms': duration_ms,
                    'success': False,
                    'error': error
                }
            )
    
    def log_service_start(self, service_type: str, input_file: str) -> None:
        """
        Log when a service operation starts.
        
        Args:
            service_type: Type of service (TTS or Translation)
            input_file: Path to input file being processed
            
        Validates: Requirement 8.3
        """
        self.logger.info(
            f"{service_type} operation started",
            extra={
                'service': service_type,
                'input_file': input_file
            }
        )
    
    def log_service_complete(
        self, 
        service_type: str, 
        execution_time: float, 
        output_file: str
    ) -> None:
        """
        Log when a service operation completes.
        
        Args:
            service_type: Type of service (TTS or Translation)
            execution_time: Total execution time in seconds
            output_file: Path to output file generated
            
        Validates: Requirement 8.4
        """
        self.logger.info(
            f"{service_type} operation completed in {execution_time:.2f}s",
            extra={
                'service': service_type,
                'execution_time': execution_time,
                'output_file': output_file
            }
        )
    
    def log_error(
        self, 
        error_message: str, 
        context: dict,
        exc_info: bool = True
    ) -> None:
        """
        Log an error with full context and stack trace.
        
        Args:
            error_message: Human-readable error message
            context: Additional context information (operation, parameters, etc.)
            exc_info: Whether to include exception stack trace
            
        Validates: Requirement 8.5
        """
        self.logger.error(
            error_message,
            extra=context,
            exc_info=exc_info
        )
    
    def _sanitize_variables(self, variables: dict) -> dict:
        """
        Remove sensitive data from variables before logging.
        
        Redacts:
        - API keys (openai_api_key, deepl_api_key)
        - Credentials (google_credentials)
        - File content (text_content, file_upload)
        
        Args:
            variables: Original variables dictionary
            
        Returns:
            Sanitized variables with sensitive data redacted
        """
        if not variables:
            return {}
        
        # List of sensitive field names to redact
        sensitive_fields = {
            'openai_api_key',
            'deepl_api_key',
            'google_credentials',
            'text_content',
            'file_upload',
            'openaiApiKey',
            'deeplApiKey',
            'googleCredentials',
            'textContent',
            'fileUpload'
        }
        
        sanitized = {}
        for key, value in variables.items():
            if key in sensitive_fields:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self._sanitize_variables(value)
            else:
                sanitized[key] = value
        
        return sanitized


def get_component_logger(component_name: str) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Creates a child logger under the main graphql_server logger
    with the component name for better log organization.
    
    Args:
        component_name: Name of the component (e.g., 'tts_service', 'job_manager')
        
    Returns:
        Logger instance for the component
        
    Example:
        >>> logger = get_component_logger('tts_service')
        >>> logger.info('Processing TTS request')
        # Output: 2024-01-15 10:30:45 - graphql_server.tts_service - INFO - Processing TTS request
    """
    return logging.getLogger(f"graphql_server.{component_name}")
