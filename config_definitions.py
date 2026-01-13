# Define the structure for configuration keys.
# Each entry requires:
# - key: The internal Python/ENV variable name (uppercase, used for dest in argparse)
# - default: The fallback value if neither CLI nor ENV is set.
# - help_text: The description for both --help and the .env file comment.
# - group: For structuring the .env file.
# - choices (Optional): A list of valid strings to restrict CLI input (used by argparse).

# - the file is used (at this point) in env_generator.py & args_manager.py - to unify place with possible params for the script

CONFIG_DEFS = [
    # --- CORE CONFIGURATION ---
    {
        "key": "TTS_ENGINE",
        "default": "ONLINE",
        "type": str,
        "help_text": "Sets the TTS engine to use.",
        "group": "CORE CONFIGURATION & CONTROL",
        "choices": ["OFFLINE", "ONLINE", "G_CLOUD", "COQUI"]
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

    # --- NEW OUTPUT MODE CONFIGURATION ---
    {
        "key": "OUTPUT_TYPE",
        "default": "AUDIO",
        "type": str,
        "help_text": "Sets the output mode. AUDIO (read aloud) or FILE (export to MP3).",
        "group": "OUTPUT CONFIGURATION",
        "choices": ["AUDIO", "FILE"]
    },
    {
        "key": "MAX_FILE_DURATION",
        "default": 600,
        "type": int,
        "help_text": "Maximum duration in seconds for a single exported MP3 segment (used only when OUTPUT_TYPE=FILE).",
        "group": "OUTPUT CONFIGURATION"
    },
    {
        "key": "CLEAN_OUTPUT_DIRECTORY",
        "default": False,
        "action": "store_true",
        "help_text": "If provided, deletes the output directory and all contents (MP3s and .progress file) before starting.",
        "group": "OUTPUT CONFIGURATION"
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
        "help_text": "Path to the Google Cloud service account JSON key file. \n Link on how to obtain: https://www.youtube.com/watch?v=dOlV_oD_dr8",
        "group": "GOOGLE CLOUD CONFIGURATION (G_CLOUD)"
    },
    {
        "key": "WAVENET_VOICE",
        "default": "cs-CZ-Standard-B",
        "help_text": "Name of the WaveNet/Studio voice to use. \nList of options here: https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types",
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
        "key": "COQUI_SPEAKER_WAV",
        "default": "",
        "help_text": "Path to a WAV file for custom speaker cloning (e.g., /path/to/my_voice.wav).",
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