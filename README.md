# TTS Reader

A highly modular **Python-based Text-to-Speech (TTS) tool** designed for
processing large text files using both **offline and online engines**,
with full support for **high-quality cloud services** and **audiobook
generation**.

---

## 🚀 Key Features

* **Modular Architecture:** Refactored into distinct `core/` and `utils/` modules, adhering to the Single Source of Truth (SSOT) principle for configuration.
* **Audiobook Generation:** Supports saving generated speech directly to MP3 files via the `--output-file` flag, enabling full **audiobook export**.
* **Offline TTS:** Uses `pyttsx3` (cross-platform) or `SAPI` (Windows) for local voice output.
* **Online TTS:** Uses `gTTS` or **Google Cloud TTS (WaveNet)** for premium voice quality.
* **Flexible Configuration:** All parameters are managed by **`config_definitions.py`** and can be overridden by environment variables (`.env`) or command-line arguments.
* **Cross-Platform Ready:** Core processing and API calls are OS-agnostic, enabling **`ONLINE`** and **`G_CLOUD`** modes on all systems. *Note: Full platform independence for dependencies is a future plan.*

---

## 🛠️ Setup and Configuration

### Dynamic Setup & Utilities

The script includes built-in utilities for quick setup.

#### Generate `.env` template

``` bash
python tts_reader.py --generate-env
```

#### List available offline voices

``` bash
python tts_reader.py --offline-voice HELP
```

---

## 📖 Usage

The input file path is now a **positional argument** (placed at the end), but if omitted, the script will automatically invoke the file selection dialog.

### 1. Simple Reading (Interactive Mode)

Runs the script using default settings. If no file path is provided, the file selection dialog opens.

```bash
# Option A: Command-line path
python tts_reader.py ./path/to/my_document.txt

# Option B: File picker dialog
python tts_reader.py
```

### 2. Reading with Overrides (Specific Engine)

``` bash
python tts_reader.py --tts-engine OFFLINE --speaking-rate 1.25 ./path/to/my_book.txt
```

### 3. Audiobook Export Mode

Exports segmented MP3 files instead of real-time playback.  
The optional value defines the **maximum segment length in seconds**.

If the export process is interrupted (e.g., due to loss of internet connection, insufficient disk space, exhausted cloud TTS credits, or unexpected termination), the script will **automatically attempt to resume from the last successfully completed MP3 segment**.  
Resumption is based strictly on the **input source file** and the presence of the `--output-file` flag. All other parameters — **including the original `--output-file` duration value** — are automatically restored from the unfinished export state.

``` bash
# Export with max 600-second segments
python tts_reader.py --tts-engine G_CLOUD --output-file 600 ./long_novel.txt
```

This will initiate a process that creates a directory named _long_novel_ and generates 600-second audio segments named _XX_long_novel.mp3_.

During execution, a temporary progress file _long_novel.progress_ is created to store the current processing state and the initial parameters. If the command is re-run before the generation finishes, the stored parameters from this file will override any newly provided parameters and the process will resume from the saved progress.
To restart the process from the beginning and apply new parameters, delete the progress file before re-running the command.

---

## ⚙️ Configuration Parameters and Description

This table lists all available configuration parameters, which can be set in your **`.env` file** or overridden using the corresponding **Command-Line Interface (CLI) flag**.

| CLI Flag               | ENV Key (`dest`)         | Description                                                                                          | Default Value           |
|:-----------------------|:-------------------------|:-----------------------------------------------------------------------------------------------------|:------------------------|
| `--tts-engine`         | **`TTS_ENGINE`**         | Sets the TTS engine to use. Choices: `OFFLINE`, `ONLINE`, `G_CLOUD`, `COQUI`.                        | `ONLINE`                |
| `--chunk-size`         | **`CHUNK_SIZE`**         | The maximum number of characters per text segment for TTS processing.                                | `3500`                  |
| `--speaking-rate`      | **`SPEAKING_RATE`**      | The speech rate multiplier (1.0 is normal speed).                                                    | `1.1`                   |
| `--offline-voice-id`   | **`OFFLINE_VOICE_ID`**   | ID or Name of the voice for the OFFLINE engine (e.g., 'Microsoft Jakub' or `HELP`).                  | `""`                    |
| `--language-code`      | **`LANGUAGE_CODE`**      | IETF BCP 47 language code for G\_CLOUD/gTTS (e.g., cs-CZ).                                           | `cs-CZ`                 |
| `--g-cloud-key-path`   | **`G_CLOUD_KEY_PATH`**   | Path to the Google Cloud service account JSON key file.                                              | `./google-key.json`     |
| `--wavenet-voice`      | **`WAVENET_VOICE`**      | Name of the G\_CLOUD voice (WaveNet/Studio) to use.                                                  | `cs-CZ-Wavenet-B`       |
| `--output-type `       | **`OUTPUT_TYPE`**        | Sets the output - reading or creating audio files. Choices: `FILE`, `AUDIO`                          | `AUDIO`                 |
| `--max-file-duration ` | **`MAX_FILE_DURATION`**  | Max. audio duration {in sec} per MP3 segment. Exceeding this limit automatically creates a new file. | `600`                   |
| `--coqui-model-name`   | **`COQUI_MODEL_NAME`**   | COQUI model path/name (e.g., `tts_models/cs/cv/vits`).                                               | `tts_models/cs/cv/vits` |
| `--coqui-speaker-name` | **`COQUI_SPEAKER_NAME`** | Speaker ID for COQUI multi-speaker models.                                                           | `""`                    |
| `--coqui-sample-rate`  | **`COQUI_SAMPLE_RATE`**  | Sample rate for exported COQUI audio.                                                                | `22050`                 |

---

### Utility Flags (Actions)

These flags trigger specific actions and cause the script to exit immediately without performing TTS reading:

| CLI Flag | Action |
| :--- | :--- |
| `--generate-env` | Generates a template `.env` file based on these definitions and exits. |
| `--offline-voice HELP` | Prints a list of available OFFLINE (SAPI/pyttsx3) voices on your current system and exits. |

## 🔮 Future Plans (Enhanced Platform Independence)

Planned roadmap priorities:

### ✅ Version Control Integration

-   Introduce **semantic versioning** (e.g. `v1.0.0`)
-   Reliable dependency tracking and release management

### ✅ Advanced TTS Support

-   Experimental **offline COQUI TTS integration**
-   High-quality AI voices without cloud dependency

### ✅ Critical Platform Independence

-   Conditional loading of Windows-only dependencies (`pywin32`)
-   Clean Linux/macOS environments without Windows-specific packages

### ✅ Automated Release Pipeline

-   CI/CD pipeline for **standalone executables**
-   Packaging via **PyInstaller**
-   Targets: **Windows & Linux**
