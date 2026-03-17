# Define the structure for server configuration keys.
# Each entry requires:
# - key: The internal Python/ENV variable name (uppercase, used for dest in argparse) - SHORT VERSION
# - long_name: The descriptive long name for documentation purposes
# - default: The fallback value if neither CLI nor ENV is set.
# - help_text: The description for both --help and the .env file comment.
# - group: For structuring the .env file.
# - type (Optional): The Python type for the parameter (str, int, float, bool).
# - action (Optional): For boolean flags (e.g., 'store_true').
# - choices (Optional): A list of valid strings to restrict CLI input.

# This file is used in env_generator.py & args_manager.py to unify possible params for the server script

SERVER_CONFIG_DEFS = [
    # --- SERVER SETTINGS ---
    {
        "key": "SERVER_HOST",
        "long_name": "SERVER_HOST",
        "default": "0.0.0.0",
        "type": str,
        "help_text": "Host address to bind the server to.",
        "group": "SERVER SETTINGS",
    },
    {
        "key": "SERVER_PORT",
        "long_name": "SERVER_PORT",
        "default": 8000,
        "type": int,
        "help_text": "Port number for the server.",
        "group": "SERVER SETTINGS",
    },
    # --- LOGGING CONFIGURATION ---
    {
        "key": "LOG_LEVEL",
        "long_name": "LOG_LEVEL",
        "default": "INFO",
        "type": str,
        "help_text": "Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL.",
        "group": "LOGGING CONFIGURATION",
        "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    },
    {
        "key": "LOG_FILE",
        "long_name": "LOG_FILE",
        "default": "",
        "type": str,
        "help_text": "Path to log file (leave empty to disable file logging).",
        "group": "LOGGING CONFIGURATION",
    },
    {
        "key": "LOG_FORMAT",
        "long_name": "LOG_FORMAT",
        "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "type": str,
        "help_text": "Log format string.",
        "group": "LOGGING CONFIGURATION",
    },
    # --- FILE HANDLING ---
    {
        "key": "MAX_UPLOAD_SIZE_MB",
        "long_name": "MAX_UPLOAD_SIZE_MB",
        "default": 50,
        "type": int,
        "help_text": "Maximum file upload size in megabytes.",
        "group": "FILE HANDLING",
    },
    {
        "key": "TEMP_DIRECTORY",
        "long_name": "TEMP_DIRECTORY",
        "default": "./temp",
        "type": str,
        "help_text": "Directory for temporary file storage.",
        "group": "FILE HANDLING",
    },
    # --- ENGINE ALLOWLISTS ---
    {
        "key": "ALLOWED_TTS_ENGINES",
        "long_name": "ALLOWED_TTS_ENGINES",
        "default": "OFFLINE,ONLINE,G_CLOUD,COQUI",
        "type": str,
        "help_text": "Allowed TTS engines (comma-separated list).",
        "group": "ENGINE ALLOWLISTS",
    },
    {
        "key": "ALLOWED_TRANSLATOR_ENGINES",
        "long_name": "ALLOWED_TRANSLATOR_ENGINES",
        "default": "OPENAI,GEMINI,DEEPL",
        "type": str,
        "help_text": "Allowed translation engines (comma-separated list).",
        "group": "ENGINE ALLOWLISTS",
    },
    # --- JOB MANAGEMENT ---
    {
        "key": "MAX_CONCURRENT_JOBS",
        "long_name": "MAX_CONCURRENT_JOBS",
        "default": 4,
        "type": int,
        "help_text": "Maximum number of concurrent jobs.",
        "group": "JOB MANAGEMENT",
    },
    {
        "key": "JOB_CLEANUP_HOURS",
        "long_name": "JOB_CLEANUP_HOURS",
        "default": 24,
        "type": int,
        "help_text": "Hours to keep completed/failed jobs in memory before cleanup.",
        "group": "JOB MANAGEMENT",
    },
    # --- PERFORMANCE ---
    {
        "key": "REQUEST_TIMEOUT_SECONDS",
        "long_name": "REQUEST_TIMEOUT_SECONDS",
        "default": 300,
        "type": int,
        "help_text": "Request timeout in seconds.",
        "group": "PERFORMANCE",
    },
]
