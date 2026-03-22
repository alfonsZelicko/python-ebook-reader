# TTS Reader & AI Translator

A modular Python toolkit for **Text‑to‑Speech generation**, **AI
translation**, and a **GraphQL API layer** that exposes both services.

The project started as a simple tool for translating and listening to
books, but evolved into a flexible platform for text processing,
audiobook generation, and API-driven workflows.

------------------------------------------------------------------------

# Overview

The project consists of three main components:

  -----------------------------------------------------------------------
Component Description
  ----------------------------------- -----------------------------------
**TTS Reader**                      Converts large text files into
speech using offline and cloud
engines

**AI Translator [BETA]**                   Translates large texts using AI
models with chunking and resume
support

**GraphQL Server [BETA]**                  Provides an API layer for
automation and external
applications
  -----------------------------------------------------------------------

Each component can be used **independently** or combined together.

The GraphQL server documentation is located here:

**→ `server/README.md`**

------------------------------------------------------------------------

# Key Features

## TTS Reader

- Supports **offline and cloud TTS engines**
- Handles **large text files** with automatic chunking
- **Audiobook export** to segmented MP3 files
- **Resume support** if generation is interrupted
- Flexible configuration via `.env.tts` or CLI arguments

Supported engines:

- `OFFLINE`
- `ONLINE`
- `G_CLOUD`
- `COQUI`
- `ELEVENLABS`[BETA]

------------------------------------------------------------------------

## AI Translator

- Multiple translation engines
- Automatic chunking of large texts
- Resume interrupted translations
- Custom prompts for translation style
- Built‑in retry logic for API errors

Supported engines:

- `OPENAI`[BETA]
- `GEMINI`
- `DEEPL`[BETA]

The translator processes long documents safely by splitting them into
chunks and tracking progress.

In this cases [BETA] means the engine is still in development and may
have bugs/is not fully tested...

------------------------------------------------------------------------

## GraphQL Server

The optional server exposes the tools through a **single GraphQL API**.

Capabilities:

- unified API for TTS and translation
- synchronous and asynchronous processing
- job status tracking
- file upload and download

See:

**→ `server/README.md`**

Quick install (server deps are optional):

``` bash
pip install ".[server]"
```

Quick GraphQL examples:

``` graphql
query {
  availableEngines {
    ttsEngines { name description }
    translationEngines { name description }
  }
}
```

``` graphql
mutation {
  generateSpeech(
    input: { textContent: "Hello world", ttsEngine: ONLINE, languageCode: "en-US" }
  ) {
    ... on TTSResult { success message outputFiles }
    ... on JobCreated { jobId message }
  }
}
```

------------------------------------------------------------------------

# Installation

## Requirements

- Python **3.10+**

Install the project:

``` bash
pip install .
```

------------------------------------------------------------------------

# CLI Help

It is generated based on `tts_args_definition.py` or `translator_args_definition.py` or `server/

```bash
python tts_reader.py --help
python ai_translator.py --help
# even
python start_server.py --help
```

# Optional Engines

Some engines require additional dependencies.

### Windows Offline Voices

``` bash
pip install .[windows]
```

### Coqui Neural TTS

Example with CUDA PyTorch build:

``` bash
pip install .[coqui] --extra-index-url https://download.pytorch.org/whl/cu121
```

Linux users may also need:

``` bash
sudo apt install espeak
```

------------------------------------------------------------------------

# Engine Setup

Some engines require API credentials.

### Google Cloud TTS

1. Create a Google Cloud service account
2. Download the JSON key
3. Set the path in `.env.tts`

Example:

    G_CLOUD_CREDENTIALS=/path/to/google-key.json

------------------------------------------------------------------------

### ElevenLabs

Add your API key to `.env.tts`:

    ELEVENLABS_API_KEY=your_key_here

------------------------------------------------------------------------

### AI Translator APIs

Depending on the engine, configure `.env.translator`:

    OPENAI_API_KEY=...
    DEEPL_API_KEY=...

Google Gemini uses the same Google Cloud credentials as the TTS engine.

------------------------------------------------------------------------

# Basic Usage

## TTS Reader

Read a text file:

``` bash
python tts_reader.py book.txt
```

Use a specific engine:

``` bash
python tts_reader.py --te G_CLOUD book.txt
```

Generate audiobook files:

``` bash
python tts_reader.py --te G_CLOUD --ot FILE --mfd 600 book.txt
```

The export can resume automatically if interrupted.

------------------------------------------------------------------------

## AI Translator

Generate configuration:

``` bash
python ai_translator.py --generate-env
```

Translate a file:

``` bash
python ai_translator.py document.txt
```

Choose engine:

``` bash
python ai_translator.py --te GEMINI document.txt
```

Change language pair:

``` bash
python ai_translator.py --sl en --tl de document.txt
```

The translator automatically resumes unfinished work.

------------------------------------------------------------------------

# Configuration

Two environment files control the system.

File Purpose
  ------------------- ----------------------------------
`.env.tts`          TTS engine configuration
`.env.translator`   Translation engine configuration

Both can be generated automatically:

``` bash
python tts_reader.py --generate-env
python ai_translator.py --generate-env
# even
python start_Server.py --generate-env
```

CLI arguments always override environment settings.

------------------------------------------------------------------------

# Project Structure

    .
    ├── tts_reader.py
    ├── ai_translator.py
    ├── core/
    ├── utils/
    ├── server/
    └── README.md

Core logic lives in `core/`, while CLI tools act as entry points.

------------------------------------------------------------------------

How it works in flow diagram:

```mermaid
flowchart TD

%% Shared Translation Core
    subgraph CORE[Translation Core]
        CORE_Engine[Initialize Translation Engine]
        CORE_Process[Start Translation Process]
        CORE_Engine --> CORE_Process
    end

%% GraphQL Flow
    subgraph GraphQL[GraphQL Translation Flow]
        GQL_Start[GraphQL Request] --> GQL_Validate[Validate Input Parameters]
        GQL_Validate --> GQL_Async{Async Mode?}
        GQL_Async -->|Yes| GQL_CreateJob[Create Job via JobManager]
        GQL_Async -->|No| GQL_Sync[Execute Synchronously]
        GQL_CreateJob --> GQL_JobCreated[Return JobCreated Response]
        GQL_JobCreated --> GQL_Background[Background Execution]
        GQL_Sync --> GQL_Prepare[Prepare Temporary Input File]
        GQL_Background --> GQL_Prepare
        GQL_Prepare --> GQL_Resolve[Resolve Arguments]
        GQL_Resolve --> CORE_Engine
        CORE_Process --> GQL_Result[Process Translation Result]
        GQL_Result --> GQL_File[Create File Download Object]
        GQL_File --> GQL_Return[Return TranslationResultWithFile]
    end

%% CLI Flow
    subgraph CLI[CLI Translation Flow]
        CLI_Start[CLI Command] --> CLI_Parse[Parse Arguments]
        CLI_Parse --> CLI_Validate[Validate Pre-execution Actions]
        CLI_Validate --> CORE_Engine
        CORE_Process --> CLI_Complete[Complete Translation]
    end

%% Shared Translation Process
    subgraph Core[Core Translation Process]
        Core_Read[Read Input File] --> Core_Chunk[Split Text into Chunks]
        Core_Chunk --> Core_Progress[Initialize Progress Manager]
        Core_Progress --> Core_Translate[Translate Each Chunk]
        Core_Translate --> Core_Write[Write Output File]
        Core_Write --> Core_Cleanup[Clean Up Progress File]
    end

%% Connections
    GQL_Process --> Core_Read
    CLI_Process --> Core_Read
%% Styling
    classDef graphql fill: #e1f5fe, stroke: #01579b, stroke-width: 2px
    classDef cli fill: #f3e5f5, stroke: #4a148c, stroke-width: 2px
    classDef core fill: #e8f5e8, stroke: #1b5e20, stroke-width: 2px
    classDef decision fill: #fff3e0, stroke: #e65100, stroke-width: 2px
    class GQL_Start, GQL_Validate, GQL_Async, GQL_CreateJob, GQL_JobCreated, GQL_Background, GQL_Sync, GQL_Service, GQL_Prepare, GQL_Resolve, GQL_Engine, GQL_Process, GQL_Result, GQL_File, GQL_Return graphql
    class CLI_Start, CLI_Parse, CLI_Validate, CLI_Engine, CLI_Process, CLI_Complete cli
    class Core_Read, Core_Chunk, Core_Progress, Core_Translate, Core_Write, Core_Cleanup core
    class GQL_Async decision
```

------------------------------------------------------------------------

# Development Status

Current focus areas:

- GraphQL orchestration layer
- web frontend for the API
- improved translation chunking
- better pronunciation handling
- additional TTS engines

------------------------------------------------------------------------

# Troubleshooting

### Missing API Keys

Ensure your `.env` files contain the required credentials.

### Interrupted Processing

Both tools support automatic resume. Simply run the same command again.

### Voice Not Found

List available voices:

``` bash
python tts_reader.py --offline-voice HELP
```

------------------------------------------------------------------------

# License

See the project license in the repository root.
