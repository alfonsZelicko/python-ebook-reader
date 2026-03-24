# GraphQL Server (TTS & Translation API)

This directory contains a **GraphQL server** that exposes the
functionality of the TTS Reader and AI Translator tools through a
unified API.

The server does **not implement TTS or translation itself**.\
It acts as an orchestration layer that wraps the existing scripts and
provides a modern API interface.

For full documentation of the underlying tools, configuration files, and
engine setup see:

**→ `../README.md`**

------------------------------------------------------------------------

# Overview

The server provides a single **GraphQL endpoint** that allows clients
to:

- Generate speech from text using available TTS engines
- Translate text using supported translation engines
- Run operations synchronously or asynchronously
- Track long‑running jobs
- Upload input files and download generated output

Typical usage scenarios:

- Web frontends
- Automation pipelines
- Local API service for other applications

## To access some HELP

```bash
   python server/main.py --help
```

------------------------------------------------------------------------

# Features

- **Unified GraphQL API** for TTS and translation
- **Async job processing** with progress tracking
- **Dynamic schema generation** from existing argument definitions
- **File upload and download support**
- **Engine allowlists** to control which engines can be used
- **GraphiQL playground** for development and testing -> it will be removed

The server relies on the same **configuration definitions** used by the
CLI tools.\
When new parameters are added to the TTS or Translator modules, the
GraphQL schema automatically updates.

------------------------------------------------------------------------

# Installation

## Requirements

- Python 3.10+
- Project dependencies installed

From the repository root:

``` bash
pip install ".[server]"
```

The server uses the following core libraries:

- `fastapi`
- `strawberry-graphql`
- `uvicorn`
- `python-dotenv`

------------------------------------------------------------------------

# Configuration

Server configuration is stored in:

    .env.server

Generate the file with:

``` bash
python -m server.main --generate-env
```

Important settings include:

Variable Description
  ------------------------------ ---------------------------------------
`SERVER_HOST`                  Server host address
`SERVER_PORT`                  Server port
`LOG_LEVEL`                    Logging level
`ALLOWED_TTS_ENGINES`          Allowed TTS engines
`ALLOWED_TRANSLATOR_ENGINES`   Allowed translation engines
`MAX_CONCURRENT_JOBS`          Maximum number of parallel async jobs
`MAX_UPLOAD_SIZE_MB`           Maximum upload file size

The server **does not manage engine credentials or API keys**.\
Those are configured in the main project configuration described in:

**→ `../README.md`**

------------------------------------------------------------------------

# Running the Server

From the repository root:

``` bash
poe server
```

> or `python -m server.main`

Default endpoints:

Endpoint Description
  ------------ ------------------------------------------
`/graphql`   GraphQL API
`/health`    Health check
`/docs`      FastAPI documentation (development only)

During development you can open:

    http://localhost:8000/graphql

to access the **GraphiQL playground**.

------------------------------------------------------------------------

# Example GraphQL Operations

## Query Available Engines

``` graphql
query {
  availableEngines {
    ttsEngines {
      name
      description
    }
    translationEngines {
      name
      description
    }
  }
}
```

## Generate Speech

``` graphql
mutation {
  generateSpeech(
    input: {
      textContent: "Hello world"
      ttsEngine: ONLINE
      languageCode: "en-US"
    }
  ) {
    ... on JobCreated {
      jobId
    }
  }
}
```

## Translate Text

``` graphql
mutation {
  translateText(
    input: {
      textContent: "Hello world"
      translationEngine: OPENAI
      sourceLanguage: "en"
      targetLanguage: "cs"
    }
  ) {
    success
    outputFile
  }
}
```

## Check Job Status

``` graphql
query {
  jobStatus(jobId: "example-id") {
    jobId
    status
    progress {
      percentage
      stage
    }
  }
}
```

------------------------------------------------------------------------

# Architecture

The server follows a layered structure:

    server/
    ├── main.py
    ├── config.py
    ├── logger.py
    ├── graphql/
    │   ├── schema.py
    │   ├── schema_generator.py
    │   └── resolvers/
    ├── services/
    │   ├── tts_service.py
    │   ├── translation_service.py
    │   └── job_manager.py
    └── handlers/
        └── file_handler.py

### Request Flow

    Client
       ↓
    GraphQL Endpoint
       ↓
    Resolver
       ↓
    Service Layer
       ↓
    TTS / Translator Script

The service layer acts as a wrapper around the existing CLI tools
without modifying their logic.

------------------------------------------------------------------------

# Development

## Run Tests

```bash
   poe test
```

> or `pytest server/tests`

## View Logs

Logs are written to the console and optionally to a file defined in
`.env.server`.

``` bash
tail -f logs/server.log
```

------------------------------------------------------------------------

# Notes

- Engine configuration, credentials, and CLI usage are documented in:

**→ `../README.md`**

- The GraphQL playground and API docs are intended **for development
  only** and may be removed in production.

------------------------------------------------------------------------
