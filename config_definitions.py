# File: config_definitions.py

# Define the structure for configuration keys.
# Each entry requires:
# - key: The internal Python/ENV variable name (uppercase, used for dest in argparse)
# - default: The fallback value if neither CLI nor ENV is set.
# - help_text: The description for both --help and the .env file comment.
# - group: For structuring the .env file.

CONFIG_DEFS = [
    # --- CORE CONFIGURATION ---
    {
        "key": "TTS_ENGINE",
        "default": "ONLINE",
        "help_text": "Sets the TTS engine to use. Choices: OFFLINE, ONLINE, G_CLOUD, COQUI.",
        "group": "CORE CONFIGURATION & CONTROL"
    },
    {
        "key": "CHUNK_SIZE",
        "default": 3500,
        "type": int,
        "help_text": "The maximum number of characters per segment for TTS processing.",
        "group": "CORE CONFIGURATION & CONTROL"
    },
    {
        "key": "SPEAKING_RATE",
        "default": 1.1,
        "type": float,
        "help_text": "The speaking rate (speed). 1.0 is normal. Use a float (e.g., 1.1).",
        "group": "CORE CONFIGURATION & CONTROL"
    },

    # --- OFFLINE ENGINE CONFIGURATION ---
    {
        "key": "OFFLINE_VOICE_ID",
        "default": "",
        "help_text": "ID/Name of the desired voice. (e.g., 'Microsoft Jakub').",
        "group": "OFFLINE ENGINE CONFIGURATION (pyttsx3/SAPI)"
    },

    # --- LANGUAGE CONFIGURATION (Shared between ONLINE & G_CLOUD) ---
    {
        "key": "LANGUAGE_CODE",
        "default": "cs-CZ",
        "help_text": "Language code (IETF BCP 47) for G_CLOUD/gTTS processing (e.g., cs-CZ, en-US).",
        "group": "LANGUAGE CONFIGURATION"
    },

    # --- GOOGLE CLOUD CONFIGURATION ---
    {
        "key": "G_CLOUD_CREDENTIALS",
        "default": "./google-key.json",
        "help_text": "Path to the Google Cloud service account JSON key file.",
        "group": "GOOGLE CLOUD CONFIGURATION (G_CLOUD)"
    },
    {
        "key": "WAVENET_VOICE",
        "default": "cs-CZ-Wavenet-B",
        "help_text": "Name of the WaveNet/Studio voice to use.",
        "group": "GOOGLE CLOUD CONFIGURATION (G_CLOUD)"
    },

    # --- COQUI CONFIGURATION ---
    {
        "key": "COQUI_MODEL_NAME",
        "default": "tts_models/cs/cv/vits",
        "help_text": "COQUI model path/name (e.g., tts_models/cs/cv/vits).",
        "group": "COQUI CONFIGURATION (Offline AI TTS)"
    },
    {
        "key": "COQUI_SPEAKER_NAME",
        "default": "",
        "help_text": "Speaker ID for multi-speaker models (leave empty if not applicable).",
        "group": "COQUI CONFIGURATION (Offline AI TTS)"
    },
    {
        "key": "COQUI_SAMPLE_RATE",
        "default": 22050,
        "type": int,
        "help_text": "Sample rate for exported audio.",
        "group": "COQUI CONFIGURATION (Offline AI TTS)"
    },
]