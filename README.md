# TTS Reader & AI Translator

A highly modular **Python-based toolkit** featuring:

- **TTS Reader**: Text-to-Speech tool for processing large text files using both **offline and online engines**, with full support for **high-quality cloud services** and **audiobook generation**
- **AI Translator**: OpenAI-powered text translator with chunking support, progress tracking, and resumable translations

---

## 🚀 Key Features

### TTS Reader

- **Modular Architecture:** Refactored into distinct `core/` and `utils/` modules, adhering to the Single Source of Truth (SSOT) principle for configuration.
- **Audiobook Generation:** Supports saving generated speech directly to MP3 files via the `--output-file` flag, enabling full **audiobook export**.
- **Offline TTS:** Uses `pyttsx3` (cross-platform) or `SAPI` (Windows) for local voice output.
- **Online TTS:** Uses `gTTS` or **Google Cloud TTS (WaveNet)** for premium voice quality.
- **Flexible Configuration:** All parameters are managed by **`config_definitions.py`** and can be overridden by environment variables (`.env`) or command-line arguments.
- **Cross-Platform Ready:** Core processing and API calls are OS-agnostic, enabling **`ONLINE`** and **`G_CLOUD`** modes on all systems. _Note: Full platform independence for dependencies is a future plan._

### AI Translator

- **Multiple Translation Engines:** Support for OpenAI GPT, Google Gemini, and DeepL
- **Smart Chunking:** Automatically splits large texts while preserving sentence boundaries
- **Progress Tracking:** Resume interrupted translations from where you left off
- **Customizable Prompts:** Tailor translation style for different content types (OpenAI & Gemini)
- **Retry Logic:** Automatic retry with exponential backoff for failed API calls
- **Error Handling:** Graceful handling of rate limits and API errors
- **Flexible Configuration:** Mode-specific `.env.translator` file with CLI override support
- **Google Cloud Integration:** Reuses existing google-key.json for Gemini translations

---

## 🛠️ Installation and Setup

This project uses a modular dependency system. Start with a minimal installation and add features as needed.

### Prerequisites

You need Python 3.10+ installed.

### 1. Minimal Installation

This command installs the core dependencies required to run the application.

```bash
pip install .
```

By default, this enables the following engines:

- **`ONLINE`**: Works out-of-the-box.
- **`G_CLOUD`**: Works after completing the engine-specific setup below.

### 2. Activating Additional Engines

To use other engines, you need to install extra dependencies.

#### `OFFLINE` Engine (Platform-Specific)

- **On Windows**, to use the high-quality native SAPI voices, install the `windows` extra:
  ```bash
  pip install .[windows]
  ```
- **On Linux**, the `OFFLINE` engine relies on `pyttsx3`, which may require a system-level TTS package like `espeak`. You can install it with:
  ```bash
  sudo apt update && sudo apt install espeak
  ```

#### `COQUI` Engine (Advanced Offline)

This engine provides high-quality, modern offline TTS. For GPU acceleration (recommended), you must also specify the correct PyTorch index for your CUDA version.

1.  **Determine your CUDA version:** Check the [official PyTorch website](https://pytorch.org/get-started/locally/) for the correct URL (e.g., for CUDA 12.1 -> this works modern nVidia cards...).
2.  **Install with extras:**
    ```bash
    # Example for CUDA 12.1. Optional: Add 'windows' for Windows SAPI support.
    pip install .[coqui,windows] --extra-index-url https://download.pytorch.org/whl/cu121
    ```

---

## 🌐 Engine-Specific Setup

Some engines require external resources or configuration steps outside of Python package installation.

### A) Coqui XTTS Engine (Voice Options)

The Coqui XTTS engine requires loading speaker voice profiles.

- **Custom Voices:** To use your own cloned voices, place the speaker WAV files and corresponding configuration files (if applicable) in the designated project folder.
- **Default Voices:** For a list of officially supported voices and their IDs, please refer to the [Official Coqui TTS Documentation](https://docs.coqui.ai/en/latest/).

```bash
# Available voices for your model you can get by typping (not every model has more)
python tts_reader.py --coqui-speaker-name HELP
```

### B) Google Cloud TTS (WaveNet)

To use the high-quality Google Cloud Text-to-Speech service, you must authenticate your application.

1.  **Create a Service Account:** In the Google Cloud Console, create a service account and grant it the `Cloud Text-to-Speech API User` role.
2.  **Download JSON Key:** Download the generated JSON key file for your service account.
3.  **Configure the Application:** Set the path to your downloaded key file using one of the following methods:
    - **In the `.env` file:**
      ```
      G_CLOUD_CREDENTIALS="/path/to/your/keyfile.json"
      ```
    - **As a command-line argument:**
      ```bash
      python tts_reader.py --g-cloud-credentials "/path/to/your/keyfile.json" ...
      ```

```bash
# Available voices for your model you can get by typping (not every model has more)
python tts_reader --wavenet-voice HELP
```

The application will automatically handle authentication. You can find a more detailed official guide here: [Google Cloud Authentication Documentation](https://cloud.google.com/docs/authentication/getting-started) or [Youtube Step by Step instructions - 2025](https://www.youtube.com/watch?v=vlYWt3qcYkc).

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

```bash
python tts_reader.py --tts-engine OFFLINE --speaking-rate 1.25 ./path/to/my_book.txt
```

### 3. Audiobook Export Mode

Exports segmented MP3 files instead of real-time playback.  
The optional value defines the **maximum segment length in seconds**.

If the export process is interrupted (e.g., due to loss of internet connection, insufficient disk space, exhausted cloud TTS credits, or unexpected termination), the script will **automatically attempt to resume from the last successfully completed MP3 segment**.  
Resumption is based strictly on the **input source file** and the presence of the `--output-file` flag. All other parameters — **including the original `--output-file` duration value** — are automatically restored from the unfinished export state.

```bash
# Export with max 600-second segments
python tts_reader.py --tts-engine G_CLOUD --output-file 600 ./long_novel.txt
```

This will initiate a process that creates a directory named _long_novel_ and generates 600-second audio segments named _XX_long_novel.mp3_.

During execution, a temporary progress file _long_novel.progress_ is created to store the current processing state and the initial parameters. If the command is re-run before the generation finishes, the stored parameters from this file will override any newly provided parameters and the process will resume from the saved progress.
To restart the process from the beginning and apply new parameters, delete the progress file before re-running the command.

---

## 🌐 AI Translator Usage

The AI Translator supports multiple translation engines: OpenAI GPT, Google Gemini, and DeepL.

### 1. Setup

First, generate the configuration file:

```bash
python ai_translator.py --generate-env
```

This creates `.env.translator` with all available parameters. **Important:** Add your API key(s) based on which engine you want to use:

**For OpenAI (default):**

```bash
OPENAI_API_KEY=your_api_key_here
```

Get your API key at: https://platform.openai.com/api-keys

**For Google Gemini:**

```bash
TRANSLATION_ENGINE=GEMINI
G_CLOUD_CREDENTIALS=./google-key.json
```

Uses your existing Google Cloud credentials (same as TTS G_CLOUD engine)

**For DeepL:**

```bash
TRANSLATION_ENGINE=DEEPL
DEEPL_API_KEY=your_deepl_api_key_here
```

Get your API key at: https://www.deepl.com/pro-api

### 2. Basic Translation

Translate a file using default settings (OpenAI, English to Czech):

```bash
# Option A: Command-line path
python ai_translator.py ./path/to/document.txt

# Option B: File picker dialog
python ai_translator.py
```

### 3. Choose Translation Engine

```bash
# Use Google Gemini
python ai_translator.py --translation-engine GEMINI ./document.txt

# Use DeepL
python ai_translator.py --translation-engine DEEPL ./document.txt

# Use OpenAI (default)
python ai_translator.py --translation-engine OPENAI ./document.txt
```

### 4. Custom Language Pair

```bash
python ai_translator.py --source-language en --target-language de ./document.txt
```

### 5. Custom Translation Prompt (OpenAI & Gemini only)

Tailor the translation style for different content types:

```bash
# For technical documentation
python ai_translator.py --translation-prompt "You are a technical translator. Translate accurately while preserving technical terms." ./technical_doc.txt

# For literary works
python ai_translator.py --translation-prompt "You are a literary translator. Preserve the author's style and tone." ./novel.txt
```

**Note:** DeepL does not support custom prompts. If you provide `--translation-prompt` with DeepL engine, you'll see a warning and the prompt will be ignored.

### 6. Adjust Chunk Size

For very long sentences or specific formatting needs:

```bash
python ai_translator.py --chunk-size 3000 ./document.txt
```

### 7. Resume Interrupted Translation

If translation is interrupted (network issues, API limits, etc.), simply run the same command again. The translator will automatically resume from the last completed chunk:

```bash
python ai_translator.py ./document.txt
# Interrupted...
# Run again to resume:
python ai_translator.py ./document.txt
```

### 8. Clean Start

To restart translation from the beginning (discarding progress):

```bash
python ai_translator.py --clean-output-directory ./document.txt
```

### AI Translator Configuration Parameters

| CLI Flag                   | ENV Key                      | Description                                                                  | Default Value                                                                                |
| :------------------------- | :--------------------------- | :--------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| `--translation-engine`     | **`TRANSLATION_ENGINE`**     | Translation engine to use. Choices: `OPENAI`, `GEMINI`, `DEEPL`              | `OPENAI`                                                                                     |
| `--source-language`        | **`SOURCE_LANGUAGE`**        | Source language code (ISO 639-1, e.g., en, cs, de)                           | `en`                                                                                         |
| `--target-language`        | **`TARGET_LANGUAGE`**        | Target language code (ISO 639-1, e.g., en, cs, de)                           | `cs`                                                                                         |
| `--translation-prompt`     | **`TRANSLATION_PROMPT`**     | Custom prompt to guide AI translation (OpenAI/Gemini only, ignored by DeepL) | `You are a professional book translator. Translate the following fantasy text accurately...` |
| `--chunk-size`             | **`CHUNK_SIZE`**             | Maximum characters per chunk for translation                                 | `2000`                                                                                       |
| `--openai-api-key`         | **`OPENAI_API_KEY`**         | OpenAI API key (required for OPENAI engine)                                  | `""`                                                                                         |
| `--openai-model`           | **`OPENAI_MODEL`**           | OpenAI model to use (e.g., gpt-4o-mini, gpt-4o)                              | `gpt-4o-mini`                                                                                |
| `--g-cloud-credentials`    | **`G_CLOUD_CREDENTIALS`**    | Path to Google Cloud JSON key file (required for GEMINI engine)              | `./google-key.json`                                                                          |
| `--gemini-model`           | **`GEMINI_MODEL`**           | Gemini model to use (e.g., gemini-pro, gemini-1.5-pro)                       | `gemini-pro`                                                                                 |
| `--deepl-api-key`          | **`DEEPL_API_KEY`**          | DeepL API key (required for DEEPL engine)                                    | `""`                                                                                         |
| `--max-retries`            | **`MAX_RETRIES`**            | Maximum number of retries for failed API calls                               | `3`                                                                                          |
| `--retry-delay`            | **`RETRY_DELAY`**            | Initial delay in seconds between retries (exponential backoff)               | `1.0`                                                                                        |
| `--clean-output-directory` | **`CLEAN_OUTPUT_DIRECTORY`** | Remove existing output directory before starting                             | `False`                                                                                      |

> The translator uses `.env.translator` for configuration, separate from the TTS reader's `.env.tts` file.

**Translation Engine Notes:**

- **OPENAI**: Supports custom prompts, requires API key from OpenAI
- **GEMINI**: Supports custom prompts, uses your existing Google Cloud credentials (google-key.json)
- **DEEPL**: Does not support custom prompts (warning shown if provided via CLI), requires DeepL API key

---

## ⚙️ TTS Configuration Parameters and Description

This table lists all available configuration parameters, which can be set in your **`.env` file`** or overridden by the corresponding **Command-Line Interface (CLI) flag**.

| CLI Flag                | ENV Key (`dest`)          | Description                                                                                          | Default Value           |
| :---------------------- | :------------------------ | :--------------------------------------------------------------------------------------------------- | :---------------------- |
| `--tts-engine`          | **`TTS_ENGINE`**          | Sets the TTS engine to use. Choices: `OFFLINE`, `ONLINE`, `G_CLOUD`, `COQUI`.                        | `ONLINE`                |
| `--chunk-size`          | **`CHUNK_SIZE`**          | The maximum number of characters per text segment for TTS processing.                                | `3500`                  |
| `--speaking-rate`       | **`SPEAKING_RATE`**       | The speech rate multiplier (1.0 is normal speed).                                                    | `1.1`                   |
| `--offline-voice-id`    | **`OFFLINE_VOICE_ID`**    | ID or Name of the voice for the OFFLINE engine (e.g., `Microsoft Jakub` or `HELP`).                  | `""`                    |
| `--language-code`       | **`LANGUAGE_CODE`**       | IETF BCP 47 language code for G_CLOUD/gTTS (e.g., cs-CZ).                                            | `cs-CZ`                 |
| `--g-cloud-credentials` | **`G_CLOUD_CREDENTIALS`** | Path to the Google Cloud service account JSON key file.                                              | `./google-key.json`     |
| `--wavenet-voice`       | **`WAVENET_VOICE`**       | Name of the G_CLOUD voice (WaveNet/Studio) to use. (choose `HELP` for available options)             | `cs-CZ-Wavenet-B`       |
| `--output-type `        | **`OUTPUT_TYPE`**         | Sets the output - reading or creating audio files. Choices: `FILE`, `AUDIO`                          | `AUDIO`                 |
| `--max-file-duration `  | **`MAX_FILE_DURATION`**   | Max. audio duration {in sec} per MP3 segment. Exceeding this limit automatically creates a new file. | `600`                   |
| `--coqui-model-name`    | **`COQUI_MODEL_NAME`**    | COQUI model path/name (e.g., `tts_models/cs/cv/vits`).                                               | `tts_models/cs/cv/vits` |
| `--coqui-speaker-name`  | **`COQUI_SPEAKER_NAME`**  | Speaker ID for COQUI multi-speaker models. (choose `HELP` for available options)                     | `""`                    |
| `--coqui-sample-rate`   | **`COQUI_SAMPLE_RATE`**   | Sample rate for exported COQUI audio.                                                                | `22050`                 |

> Parameters are defined in the `config_definitions.py` file, which serves as the single source of truth (SSOT). All other scripts (`args_manager.py`, `env_generator.py`) operate exclusively on parameters generated from this file.

---

### Utility Flags (Actions)

These flags trigger specific actions and cause the script to exit immediately without performing TTS reading:

| CLI Flag               | Action                                                                                     |
| :--------------------- | :----------------------------------------------------------------------------------------- |
| `--generate-env`       | Generates a template `.env` file based on these definitions and exits.                     |
| `--offline-voice HELP` | Prints a list of available OFFLINE (SAPI/pyttsx3) voices on your current system and exits. |

---

## 🔧 Troubleshooting

### AI Translator Issues

**Missing API Key Error**

```
ERROR: OPENAI_API_KEY not found in environment variables
```

**Solution:** Add your OpenAI API key to `.env.translator` or pass it via `--openai-api-key`

**Rate Limit Errors**

```
Rate limit exceeded. Waiting Xs before retry...
```

**Solution:** The translator automatically handles rate limits with exponential backoff. If you consistently hit limits, consider:

- Using a slower model (gpt-3.5-turbo)
- Increasing `--retry-delay`
- Upgrading your OpenAI plan

**Translation Fails for Specific Chunks**

```
✗ Chunk X failed - continuing with next chunk
```

**Solution:** The translator logs errors and continues. Check the output file - failed chunks are marked as `[TRANSLATION FAILED FOR CHUNK X]`. You can:

- Manually translate the failed chunk
- Adjust `--chunk-size` to avoid problematic text segments
- Check the error log for specific API error messages

**Resume Not Working**
**Solution:** Ensure you're running the command from the same directory and using the same input file path. The progress file is stored in `<filename>/<filename>.progress`

### TTS Reader Issues

**Google Cloud Authentication Errors**
**Solution:** Ensure your `google-key.json` file path is correct in `.env.tts` and the service account has Text-to-Speech API enabled

**Offline Voice Not Found**
**Solution:** Run `python tts_reader.py --offline-voice HELP` to see available voices on your system

---

## 🔮 Future Roadmap (Platform Independence & AI Evolution)

The following priorities outline the development path for enhancing the platform's capabilities, intelligence, and accessibility.

---

### 📦 System Architecture & Distribution

- **Version Control & Release Management**
  ✓ Implementation of **Semantic Versioning** (e.g., `v1.0.0`) for stable release tracking

  - Development of an **Automated Release Pipeline** using CI/CD to generate standalone executables via **PyInstaller**
  - Primary targets: **Windows & Linux**

- **Critical Platform Independence** ✅

  - Conditional loading of OS-specific dependencies (e.g., `pywin32` for Windows)
  - Ensuring clean, isolated environments for **Linux and macOS** without redundant Windows-specific packages

- **HTML-based UI & Web Integration**
  - Development of a web-based interface to expose the script as a service (via Django?)
  - Implementation of **Throttling & Credits**: Due to AI API costs, functionality will be throttled, with future plans for paid credit tiers or account linking

---

### 🎙️ Advanced TTS & Voice Synthesis

- **Offline COQUI TTS Integration** (Experimental)

  - Enabling high-quality, local AI voice synthesis to eliminate cloud dependency
  - **Current Status:** Experimental support is functional but exhibits Czech accent artifacts. Compatibility issues between `XTTS-v2` and specific `torch`/CUDA versions are currently blocking stable release. Development is paused pending upstream fixes

- **Contextual Google Voice Studio Integration**
  - Moving beyond simple text-to-speech by generating **Contextual Prompts** to control tone, speed, and emotion
  - **Global Character Memory:** Maintaining consistent vocal identities for specific characters throughout the narrative
  - **Emotional Awareness:** Dynamically adjusting voice parameters based on the story's mood (e.g., tension, excitement)

---

### 🤖 AI-Driven Translation & Linguistics

- **Intelligent Text Translation Workflow**

  - Multi-stage pipeline: **Source Text → AI Translation → Audio Generation**
  - **Context-Aware Translation:** Behavior is governed by specialized prompts (e.g., _"Translate as a professional fantasy novelist"_)
  - **Prompt Inference:** System can manually or automatically infer the best translation style based on metadata like title or genre

- **Intelligent Name Normalization (Phonetic TTS)**
  - Handling complex proper nouns (e.g., _"Omtose Phellack"_) to ensure natural pronunciation in the target language
  - **Translation Logic:** Configurable rules to decide whether names should be translated, transliterated, or preserved
  - **Phonetic Rewriting:** Leveraging AI to generate TTS-optimized phonetic representations to bypass engine-specific pronunciation errors

---

### 🚧 Current Development Status

> **Note on Translation Engine:** The AI translation layer is fully functional internally but remains in a "Private Beta" stage. It is currently undergoing additional debugging and stabilization before being merged into the public repository
