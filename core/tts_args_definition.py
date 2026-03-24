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
    # --- CORE CONFIGURATION & CONTROL ---
    {
        "key": "TE",
        "long_name": "TTS_ENGINE",
        "default": "ONLINE",
        "type": str,
        "choices": ["OFFLINE", "ONLINE", "G_CLOUD", "COQUI", "ELEVENLABS"],
        "engines": ["ALL"],
    },
    {
        "key": "CS",
        "long_name": "CHUNK_SIZE",
        "default": 3500,
        "type": int,
        "engines": ["ALL"],
    },
    {
        "key": "CP",
        "long_name": "CHUNK_BY_PARAGRAPH",
        "default": False,
        "action": "store_true",
        "engines": ["ALL"],
    },
    {
        "key": "SR",
        "long_name": "SPEAKING_RATE",
        "default": 1.1,
        "type": float,
        "engines": ["ALL"],
    },
    # --- OUTPUT CONFIGURATION ---
    {
        "key": "OT",
        "long_name": "OUTPUT_TYPE",
        "default": "AUDIO",
        "type": str,
        "choices": ["AUDIO", "FILE"],
        "engines": ["ALL"],
    },
    {
        "key": "MFD",
        "long_name": "MAX_FILE_DURATION",
        "default": 600,
        "type": int,
        "engines": ["ALL"],
    },
    {
        "key": "COD",
        "long_name": "CLEAN_OUTPUT_DIRECTORY",
        "default": False,
        "action": "store_true",
        "engines": ["ALL"],
    },
    # --- LANGUAGE & VOICES ---
    {
        "key": "L_CODE",
        "long_name": "LANGUAGE_CODE",
        "default": "cs-CZ",
        "type": str,
        "engines": ["ONLINE", "G_CLOUD"],
    },
    {
        "key": "OFF_VOICE",
        "long_name": "OFFLINE_VOICE_ID",
        "default": "",
        "type": str,
        "engines": ["OFFLINE"],
    },
    # --- GOOGLE CLOUD CONFIGURATION ---
    {
        "key": "G_KEY",
        "long_name": "G_CLOUD_CREDENTIALS",
        "default": "./google-key.json",
        "type": str,
        "engines": ["G_CLOUD"],
    },
    {
        "key": "G_VOICE",
        "long_name": "WAVENET_VOICE",
        "default": "cs-CZ-Standard-B",
        "type": str,
        "engines": ["G_CLOUD"],
    },
    # --- COQUI CONFIGURATION ---
    {
        "key": "C_MODEL",
        "long_name": "COQUI_MODEL_NAME",
        "default": "tts_models/multilingual/multi-dataset/xtts_v2",
        "type": str,
        "engines": ["COQUI"],
    },
    {
        "key": "C_SPEAKER",
        "long_name": "COQUI_SPEAKER_ID",
        "default": "",
        "type": str,
        "engines": ["COQUI"],
    },
    {
        "key": "C_WAV",
        "long_name": "COQUI_SPEAKER_WAV",
        "default": "",
        "type": str,
        "engines": ["COQUI"],
    },
    {
        "key": "C_RATE",
        "long_name": "COQUI_SAMPLE_RATE",
        "default": 22050,
        "type": int,
        "engines": ["COQUI"],
    },
    # --- ELEVENLABS CONFIGURATION ---
    {
        "key": "EL_CRED",
        "long_name": "ELEVENLABS_CRED",
        "default": "",
        "type": str,
        "engines": ["ELEVENLABS"],
    },
]

TTS_DESCRIPTIONS = {
    "OFFLINE": "Offline TTS using pyttsx3/SAPI (no internet required)",
    "ONLINE": "Online TTS using gTTS (Google Text-to-Speech)",
    "G_CLOUD": "Google Cloud Text-to-Speech with WaveNet voices",
    "COQUI": "Coqui TTS - Offline AI-based text-to-speech",
    "ELEVENLABS": "ElevenLabs cloud TTS",
}
