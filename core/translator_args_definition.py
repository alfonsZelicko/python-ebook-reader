# Define the structure for translator configuration keys.
# Each entry requires:
# - key: The internal Python/ENV variable name (uppercase, used for dest in argparse) - SHORT VERSION
# - long_name: The descriptive long name for documentation purposes
# - default: The fallback value if neither CLI nor ENV is set.
# - help_text: The description for both --help and the .env file comment.
# - group: For structuring the .env file.
# - type (Optional): The Python type for the parameter (str, int, float, bool).
# - action (Optional): For boolean flags (e.g., 'store_true').
# - choices (Optional): A list of valid strings to restrict CLI input.

# This file is used in env_generator.py & args_manager.py to unify possible params for the translator script

TRANSLATOR_CONFIG_DEFS = [
    # --- CORE TRANSLATION CONFIGURATION ---
    {
        "key": "TE",
        "long_name": "TRANSLATION_ENGINE",
        "default": "OPENAI",
        "type": str,
        "help_text": "Translation engine to use.",
        "group": "CORE TRANSLATION CONFIGURATION",
        "choices": ["OPENAI", "GEMINI", "DEEPL"]
    },
    {
        "key": "SL",
        "long_name": "SOURCE_LANGUAGE",
        "default": "en",
        "type": str,
        "help_text": "Source language code (ISO 639-1 format, e.g., en, cs, de).",
        "group": "CORE TRANSLATION CONFIGURATION"
    },
    {
        "key": "TL",
        "long_name": "TARGET_LANGUAGE",
        "default": "cs",
        "type": str,
        "help_text": "Target language code (ISO 639-1 format, e.g., en, cs, de).",
        "group": "CORE TRANSLATION CONFIGURATION"
    },
    {
        "key": "TP",
        "long_name": "TRANSLATION_PROMPT",
        "default": "You are a professional book translator. Translate the following fantasy text accurately while preserving the style and tone.",
        "type": str,
        "help_text": "Custom prompt to guide the AI translation behavior (OpenAI and Gemini only, ignored by DeepL).",
        "group": "CORE TRANSLATION CONFIGURATION"
    },
    {
        "key": "CS",
        "long_name": "CHUNK_SIZE",
        "default": 4000,
        "type": int,
        "help_text": "Maximum number of characters per chunk for translation.",
        "group": "CORE TRANSLATION CONFIGURATION"
    },
    {
        "key": "CP",
        "long_name": "CHUNK_BY_PARAGRAPH",
        "default": True,
        "action": "store_true",
        "help_text": "Preserve paragraph boundaries when chunking (recommended for translations).",
        "group": "CORE TRANSLATION CONFIGURATION"
    },

    # --- OPENAI API CONFIGURATION ---
    {
        "key": "O_KEY",
        "long_name": "OPENAI_API_KEY",
        "default": "",
        "type": str,
        "help_text": "OpenAI API key (required for OPENAI engine). Get yours at: https://platform.openai.com/api-keys",
        "group": "OPENAI API CONFIGURATION"
    },
    {
        "key": "O_MODEL",
        "long_name": "OPENAI_MODEL",
        "default": "gpt-4o-mini",
        "type": str,
        "help_text": "OpenAI model to use for translation (e.g., gpt-4o-mini, gpt-4o, gpt-3.5-turbo).",
        "group": "OPENAI API CONFIGURATION"
    },

    # --- GOOGLE GEMINI CONFIGURATION ---
    {
        "key": "G_CRED",
        "long_name": "G_CLOUD_CREDENTIALS",
        "default": "./google-key.json",
        "type": str,
        "help_text": "Path to the Google Cloud service account JSON key file (required for GEMINI engine).",
        "group": "GOOGLE GEMINI CONFIGURATION"
    },
    {
        "key": "G_MODEL",
        "long_name": "GEMINI_MODEL",
        "default": "gemini-pro",
        "type": str,
        "help_text": "Gemini model to use for translation (e.g., gemini-pro, gemini-1.5-pro).",
        "group": "GOOGLE GEMINI CONFIGURATION"
    },

    # --- DEEPL API CONFIGURATION ---
    {
        "key": "D_KEY",
        "long_name": "DEEPL_API_KEY",
        "default": "",
        "type": str,
        "help_text": "DeepL API key (required for DEEPL engine). Get yours at: https://www.deepl.com/pro-api",
        "group": "DEEPL API CONFIGURATION"
    },

    # --- RETRY & ERROR HANDLING ---
    {
        "key": "MR",
        "long_name": "MAX_RETRIES",
        "default": 3,
        "type": int,
        "help_text": "Maximum number of retries for failed API calls.",
        "group": "RETRY & ERROR HANDLING"
    },
    {
        "key": "RD",
        "long_name": "RETRY_DELAY",
        "default": 1.0,
        "type": float,
        "help_text": "Initial delay in seconds between retries (uses exponential backoff).",
        "group": "RETRY & ERROR HANDLING"
    },

    # --- OUTPUT CONFIGURATION ---
    {
        "key": "COD",
        "long_name": "CLEAN_OUTPUT_DIRECTORY",
        "default": False,
        "action": "store_true",
        "help_text": "If provided, deletes the output directory and all contents before starting.",
        "group": "OUTPUT CONFIGURATION"
    },
]
