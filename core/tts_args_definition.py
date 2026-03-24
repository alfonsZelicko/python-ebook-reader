# Define the structure for configuration keys.
# Each entry requires:
# - key: The internal Python/ENV variable name (uppercase, used for dest in argparse) - SHORT VERSION
# - long_name: The descriptive long name for documentation purposes
# - default: The fallback value if neither CLI nor ENV is set.
# - help_text: The description for both --help and the .env file comment.
# - group: For structuring the .env file.
# - choices (Optional): A list of valid strings to restrict CLI input_data (used by argparse).
# - engines: What engine is using specific parameter.

# - the file is used (at this point) in env_generator.py & args_manager.py - to unify place with possible params for the script

TTS_CONFIG_DEFS = [
    {
        "key": "TE",
        "long_name": "TTS_ENGINE",  # <--- Tohle tam musí být
        "default": "ONLINE",
        "type": str,
        "help_text": "Sets the TTS engine to use.",
        "group": "CORE CONFIGURATION & CONTROL",
        "choices": ["OFFLINE", "ONLINE", "G_CLOUD", "COQUI", "ELEVENLABS"],
        "engines": ["ALL"],
    },
    {
        "key": "CS",
        "long_name": "CHUNK_SIZE",
        "default": 3500,
        "type": int,
        "group": "CORE CONFIGURATION & CONTROL",
        "engines": ["ALL"],
    },
    {
        "key": "CP",
        "long_name": "CHUNK_BY_PARAGRAPH",
        "default": False,
        "action": "store_true",
        "group": "CORE CONFIGURATION & CONTROL",
        "engines": ["ALL"],
    },
    {
        "key": "SR",
        "long_name": "SPEAKING_RATE",
        "default": 1.1,
        "type": float,
        "group": "CORE CONFIGURATION & CONTROL",
        "engines": ["ALL"],
    },
    {
        "key": "OT",
        "long_name": "OUTPUT_TYPE",
        "default": "AUDIO",
        "type": str,
        "choices": ["AUDIO", "FILE"],
        "group": "OUTPUT CONFIGURATION",
        "engines": ["ALL"],
    },
    {
        "key": "OFF_VOICE",
        "long_name": "OFFLINE_VOICE_ID",
        "default": "",
        "group": "OFFLINE ENGINE CONFIGURATION",
        "engines": ["OFFLINE"],
    },
    {
        "key": "L_CODE",
        "long_name": "LANGUAGE_CODE",
        "default": "cs-CZ",
        "group": "LANGUAGE CONFIGURATION",
        "engines": ["ONLINE", "G_CLOUD"],
    },
    {
        "key": "G_KEY",
        "long_name": "G_CLOUD_CREDENTIALS",
        "default": "./google-key.json",
        "group": "GOOGLE CLOUD CONFIGURATION",
        "engines": ["G_CLOUD"],
    },
    {
        "key": "G_VOICE",
        "long_name": "WAVENET_VOICE",
        "default": "cs-CZ-Standard-B",
        "group": "GOOGLE CLOUD CONFIGURATION",
        "engines": ["G_CLOUD"],
    },
    {
        "key": "C_MODEL",
        "long_name": "COQUI_MODEL_NAME",
        "default": "tts_models/multilingual/multi-dataset/xtts_v2",
        "group": "COQUI CONFIGURATION",
        "engines": ["COQUI"],
    },
    {
        "key": "EL_CRED",
        "long_name": "ELEVENLABS_CRED",
        "default": "",
        "group": "ELEVENLABS CONFIGURATION",
        "engines": ["ELEVENLABS"],
    },
    {
        "key": "COD",
        "long_name": "CLEAN_OUTPUT_DIRECTORY",
        "default": False,
        "action": "store_true",
        "group": "OUTPUT CONFIGURATION",
        "engines": ["ALL"],
    },
]

TTS_DESCRIPTIONS = {
    "OFFLINE": "Offline TTS using pyttsx3/SAPI (no internet required)",
    "ONLINE": "Online TTS using gTTS (Google Text-to-Speech)",
    "G_CLOUD": "Google Cloud Text-to-Speech with WaveNet voices",
    "COQUI": "Coqui TTS - Offline AI-based text-to-speech",
    "ELEVENLABS": "ElevenLabs cloud TTS",
}
