# TTS Reader

A Python-based text-to-speech (TTS) script to read text files using offline or online engines, with support for Google Cloud WaveNet for high-quality speech.

---

## Features

* **Offline TTS:** Uses `pyttsx3` (cross-platform) or `SAPI` (Windows) for offline voice output.
* **Online TTS:** Uses `gTTS` for higher-quality online speech synthesis.
* **Google Cloud TTS (WaveNet):** Optionally use Google Cloud for premium voice quality.
* **Chunked Reading:** Splits large text files into manageable chunks to prevent memory or playback issues.
* **Customizable:** Adjust speaking rate, chunk size, and TTS engine via `.env` or command-line arguments.
* **Cross-Platform:** Works on Windows, Linux, and macOS (offline engine may differ per OS).

---

## Requirements

* Python 3.10+ recommended
* Dependencies listed in `requirements.txt`:

```txt
python-dotenv
tqdm
pyttsx3
gTTS
pydub
simpleaudio
google-cloud-texttospeech
pywin32  # Windows only
```

Install dependencies with (optional):

```bash
pip install -r requirements.txt
```

---

## Setup

1. Copy `.env.example` to `.env` and configure your settings:

```env
# Default TTS engine: OFFLINE, ONLINE, or G_CLOUD
DEFAULT_ENGINE=ONLINE

# Maximum characters per chunk
CHUNK_SIZE=3500

# Speaking rate (1.0 is normal)
SPEAKING_RATE=1.1

# Optional offline voice
OFFLINE_VOICE_ID=

# Google Cloud credentials (optional)
G_CLOUD_CREDENTIALS="./google-key.json"
WAVENET_VOICE="cs-CZ-Wavenet-B"
LANGUAGE_CODE="cs-CZ"
```

### Dynamic setup option:
all this `.env` params are possible to overwrite with params:

2. Ensure you have the Google Cloud credentials file if using `G_CLOUD` engine.

---

## Usage

Run the script with:

```bash
python main.py [--install-deps --engine ENGINE --rate SPEAKING_RATE --chunk-size CHUNK_SIZE --wavenet-voice WAVENET_VOICE --credentials G_CLOUD_CREDENTIALS]
```

All this params are optional and overriding the default `.env` values
* `--engine` Options: `OFFLINE`, (DEFAULT) `ONLINE`, `G_CLOUD`.
* `--rate` Options: (DEFAULT) `1.0` = normal speed; `<1.0` = slower; `>1.0` = faster
* `--chunk-size` Options: (DEFAULT) `3500`
* `--wavenet-voice` Options: (DEFAULT) `cs-CZ-Wavenet-B`
* `--credentials` Options: `Path to the Google Cloud JSON key file.`

This param is optional and if used - script will install its dependencies: you need to do it if you are lazy, and only 1st time :-)
* `--install-deps`: it will try to install all necessary dependencies to run script properly (from `requirements.txt`)

Example:

```bash
python tts_reader.py --engine G_CLOUD --wavenet-voice cs-CZ-Wavenet-B
```

A file picker will appear. Select a text file, and the script will read it aloud in chunks.

---

## Notes

* The offline engine uses Windows SAPI if available, otherwise falls back to `pyttsx3`.
* The online engine (`gTTS`) requires an internet connection.
* The Google Cloud engine requires proper `.env` credentials and voice settings.
* Large text files are automatically split into chunks for smoother playback.
* Czech voices are prioritized if available in offline engines.

---

## Troubleshooting

* **Missing dependencies:** Ensure `pip install -r requirements.txt` completes successfully.
* **Google Cloud errors:** Check that `G_CLOUD_CREDENTIALS` path is correct and the file exists.
* **Voice not found:** If `OFFLINE_VOICE_ID` is empty, the script will attempt to auto-detect a Czech voice or use the system default.

---

⚠️ **G_CLOUD Warning (Cost & Security)**

**Free Tier (Safe Mode):**  
WaveNet voices (`cs-CZ-Wavenet-*`) are safe to use and have a free usage limit.

**High-Cost / Risky Mode:**  
Studio voices (Gemini) and newer Premium voices (Chirp3, HD) are the most expensive and often do **not** have a free tier. Using one of these IDs in `WAVENET_VOICE` may result in charges starting from the very first character you generate (I did not test it on my own ;-D).

**Security Tip:**  
To maintain full control over costs, stick to WaveNet IDs and set up a budget alert in the Google Cloud Console.

**Key Setup:**  
Ensure that the service account corresponding to your key has the **Service Usage Consumer** role assigned. This grants the necessary permissions to call the API properly.

---

## Future Plans

The main roadmap includes:

- **AI-based Translation Pipeline:**  
  Add an intermediate step that automatically translates the input text into Czech using an AI translation model with a properly designed prompt for book-style narration.

- **Audio File Export:**  
  Implement support for saving generated speech directly to the file system (e.g., MP3/WAV), enabling full audiobook generation instead of real-time playback only.

---

## License

MIT License
