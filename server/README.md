# GraphQL Server for TTS & Translation Services

A unified GraphQL API that provides access to Text-to-Speech (TTS) and Translation services. This server wraps existing Python scripts and exposes their functionality through a modern, type-safe GraphQL interface.

## Features

- **Unified API**: Single GraphQL endpoint for both TTS and translation operations
- **Multiple Engines**: Support for various TTS engines (OFFLINE, ONLINE, G_CLOUD, COQUI) and translation engines (OPENAI, GEMINI, DEEPL)
- **Async Support**: Execute long-running operations asynchronously with progress tracking
- **File Handling**: Upload text files for processing and download generated audio/text files
- **Dynamic Schema**: GraphQL schema automatically generated from argument definitions
- **GraphiQL Playground**: Interactive API explorer for testing and development
- **Configurable**: Extensive configuration options via `.env.server`

## Installation

### Prerequisites

- Python 3.8 or higher
- pip or poetry for package management

### Install Dependencies

The server requires the following packages (already defined in `pyproject.toml`):

```bash
# Install all project dependencies including server packages
pip install -e .

# Or if using poetry
poetry install
```

Key dependencies:

- `strawberry-graphql` - GraphQL framework
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-dotenv` - Configuration management

## Setup

### 1. Generate Configuration File

Create a `.env.server` configuration file with default settings:

```bash
python -m server.main --generate-env
```

This creates a `.env.server` file in your project root with all available configuration options.

### 2. Configure the Server

Edit `.env.server` to customize your server settings. See [Configuration](#configuration) section for details.

### 3. Configure TTS and Translation Services

Ensure you have the existing configuration files set up:

- `.env.tts` - TTS service configuration (API keys, credentials)
- `.env.translator` - Translation service configuration (API keys, credentials)

These files are used by the underlying TTS and translation engines.

### 4. Start the Server

```bash
python -m server.main
```

The server will start and display:

- GraphQL endpoint: `http://localhost:8000/graphql`
- GraphiQL playground: `http://localhost:8000/graphql` (open in browser)
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Configuration

The `.env.server` file contains all server configuration options:

### Server Settings

```bash
# Host address (0.0.0.0 = all interfaces, 127.0.0.1 = localhost only)
SERVER_HOST=0.0.0.0

# Port number
SERVER_PORT=8000
```

### Logging

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Path to log file (leave empty to disable file logging)
LOG_FILE=./logs/server.log

# Log format string
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### File Handling

```bash
# Maximum file upload size in megabytes
MAX_UPLOAD_SIZE_MB=50

# Directory for temporary file storage
TEMP_DIRECTORY=./temp
```

### Engine Allowlists

Control which engines are available via the API:

```bash
# Allowed TTS engines (comma-separated)
# Options: OFFLINE, ONLINE, G_CLOUD, COQUI
ALLOWED_TTS_ENGINES=OFFLINE,ONLINE,G_CLOUD,COQUI

# Allowed translation engines (comma-separated)
# Options: OPENAI, GEMINI, DEEPL
ALLOWED_TRANSLATOR_ENGINES=OPENAI,GEMINI,DEEPL
```

**Note**: Only engines listed here can be used via the GraphQL API. Requests for unlisted engines will return an error.

### Job Management

```bash
# Maximum number of concurrent jobs
MAX_CONCURRENT_JOBS=4

# Hours to keep completed/failed jobs in memory before cleanup
JOB_CLEANUP_HOURS=24
```

### Performance

```bash
# Request timeout in seconds
REQUEST_TIMEOUT_SECONDS=300
```

## Usage

### GraphiQL Playground

The easiest way to explore the API is through the GraphiQL playground:

1. Start the server
2. Open `http://localhost:8000/graphql` in your browser
3. Use the interactive interface to build and test queries

The playground provides:

- Auto-completion for queries and mutations
- Schema documentation
- Query history
- Variable editor

### Example Queries

#### Check Available Engines

Query which TTS and translation engines are currently enabled:

```graphql
query {
  availableEngines {
    ttsEngines {
      name
      description
      requiredParameters
      optionalParameters
    }
    translationEngines {
      name
      description
      requiredParameters
      optionalParameters
    }
  }
}
```

#### Check Job Status

Query the status of an asynchronous job:

```graphql
query {
  jobStatus(jobId: "abc123-def456") {
    jobId
    status
    progress {
      percentage
      currentChunk
      totalChunks
      stage
      estimatedTimeRemaining
    }
    result {
      ... on TTSResult {
        success
        message
        outputFiles
        metadata {
          engineUsed
          totalChunks
          totalDurationSeconds
        }
      }
      ... on TranslationResult {
        success
        message
        outputFile
        metadata {
          engineUsed
          sourceLanguage
          targetLanguage
          totalChunks
        }
      }
    }
    error
  }
}
```

#### Download File

Get download information for a generated file:

```graphql
query {
  downloadFile(fileId: "xyz789") {
    fileId
    filename
    contentType
    sizeBytes
    downloadUrl
  }
}
```

### Example Mutations

#### Generate Speech (Synchronous)

Convert text to speech and wait for completion:

```graphql
mutation {
  generateSpeech(
    engine: "ONLINE"
    textContent: "Hello, this is a test of the text-to-speech system."
    languageCode: "en-US"
    speakingRate: 1.0
    chunkSize: 3500
  ) {
    success
    message
    outputFiles
    metadata {
      engineUsed
      totalChunks
      totalDurationSeconds
      outputDirectory
    }
  }
}
```

#### Generate Speech (Asynchronous)

Start a TTS job and get a job ID for tracking:

```graphql
mutation {
  generateSpeech(
    engine: "ONLINE"
    textContent: "This is a longer text that will be processed asynchronously..."
    languageCode: "en-US"
    asyncMode: true
  ) {
    jobId
    message
  }
}
```

Then poll for status using the `jobStatus` query with the returned `jobId`.

#### Generate Speech with File Upload

Upload a text file for TTS processing:

```graphql
mutation {
  generateSpeech(
    engine: "G_CLOUD"
    fileUpload: "/path/to/input.txt"
    languageCode: "cs-CZ"
    googleVoice: "cs-CZ-Standard-B"
    googleCredentials: "/path/to/credentials.json"
    speakingRate: 1.1
    maxFileDuration: 600
  ) {
    success
    message
    outputFiles
  }
}
```

#### Translate Text (Synchronous)

Translate text from one language to another:

```graphql
mutation {
  translateText(
    engine: "OPENAI"
    sourceLanguage: "en"
    targetLanguage: "cs"
    textContent: "Hello world! This is a test translation."
    openaiModel: "gpt-4o-mini"
    chunkSize: 4000
    chunkByParagraph: true
  ) {
    success
    message
    outputFile
    metadata {
      engineUsed
      sourceLanguage
      targetLanguage
      totalChunks
      outputDirectory
    }
  }
}
```

#### Translate Text (Asynchronous)

Start a translation job for long-running operations:

```graphql
mutation {
  translateText(
    engine: "GEMINI"
    sourceLanguage: "en"
    targetLanguage: "de"
    fileUpload: "/path/to/book.txt"
    geminiModel: "gemini-pro"
    asyncMode: true
  ) {
    jobId
    message
  }
}
```

### Using with cURL

You can also interact with the API using cURL or any HTTP client:

```bash
# Query available engines
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { availableEngines { ttsEngines { name } } }"
  }'

# Generate speech
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: TTSInput!) { generateSpeech(input: $input) { success message } }",
    "variables": {
      "input": {
        "engine": "ONLINE",
        "textContent": "Hello world",
        "languageCode": "en-US"
      }
    }
  }'
```

## Architecture

### Directory Structure

```
server/
├── __init__.py
├── main.py                    # FastAPI app + server entry point
├── schema.py                  # GraphQL schema (Query, Mutation types)
├── schema_generator.py        # Dynamic input type generation
├── config.py                  # Configuration management
├── logger.py                  # Logging setup
├── context.py                 # GraphQL context (for future auth)
├── resolvers/
│   ├── query.py              # Query resolvers
│   └── mutation.py           # Mutation resolvers
├── services/
│   ├── tts_service.py        # TTS operations wrapper
│   ├── translation_service.py # Translation operations wrapper
│   └── job_manager.py        # Async job management
├── handlers/
│   └── file_handler.py       # File upload/download
└── types/
    ├── inputs.py             # GraphQL input types
    └── outputs.py            # GraphQL output types
```

### How It Works

1. **Request Flow**: Client → GraphQL endpoint → Resolver → Service → Existing processor → Engine
2. **Dynamic Schema**: Input types are automatically generated from `TTS_CONFIG_DEFS` and `TRANSLATOR_CONFIG_DEFS`
3. **Service Layer**: Services wrap existing TTS/translation logic without modifying it
4. **Job Management**: Async operations run in background threads with progress tracking

## Adding New Parameters

The GraphQL schema automatically stays synchronized with the underlying TTS and translation scripts. When you add a new parameter to the config definitions, it automatically appears in the GraphQL API.

### Step 1: Add Parameter to Config Definition

Edit the appropriate config file:

**For TTS parameters**: `core/tts_args_definition.py`

```python
TTS_CONFIG_DEFS = [
    # ... existing parameters ...
    {
        'short': 'NP',  # Short key
        'long': 'new_parameter',  # Long name (becomes GraphQL field name)
        'type': str,  # Python type (maps to GraphQL type)
        'default': 'default_value',
        'help_text': 'Description of the new parameter',
        'required': False,  # Whether parameter is required
        'choices': None,  # Optional: list of valid values (creates Enum)
    },
]
```

**For Translation parameters**: `core/translator_args_definition.py`

```python
TRANSLATOR_CONFIG_DEFS = [
    # ... existing parameters ...
    {
        'short': 'NP',
        'long': 'new_parameter',
        'type': int,
        'default': 100,
        'help_text': 'Description of the new parameter',
        'required': False,
        'choices': None,
    },
]
```

### Step 2: Restart the Server

The schema generator reads the config definitions at startup:

```bash
python -m server.main
```

You'll see log output confirming the new parameter was added:

```
✓ Generated TTSInput type with 17 parameters
```

### Step 3: Use the New Parameter

The new parameter is now available in GraphQL:

```graphql
mutation {
  generateSpeech(
    engine: "ONLINE"
    textContent: "Hello world"
    newParameter: "custom_value" # Your new parameter
  ) {
    success
  }
}
```

### Type Mapping

Python types are automatically mapped to GraphQL types:

| Python Type           | GraphQL Type |
| --------------------- | ------------ |
| `str`                 | `String`     |
| `int`                 | `Int`        |
| `float`               | `Float`      |
| `bool`                | `Boolean`    |
| `list` with `choices` | `Enum`       |

### Field Name Conversion

Short keys are converted to readable GraphQL field names:

| Short Key   | Long Name            | GraphQL Field       |
| ----------- | -------------------- | ------------------- |
| `TE`        | `tts_engine`         | `engine`            |
| `CS`        | `chunk_size`         | `chunkSize`         |
| `G_CRED`    | `google_credentials` | `googleCredentials` |
| `NEW_PARAM` | `new_parameter`      | `newParameter`      |

The conversion follows these rules:

1. Use the `long` name from config
2. Convert snake_case to camelCase for GraphQL
3. Special handling for `TE` → `engine`

### Creating Enum Parameters

If your parameter has a fixed set of valid values, use the `choices` field:

```python
{
    'short': 'MODE',
    'long': 'processing_mode',
    'type': str,
    'default': 'FAST',
    'choices': ['FAST', 'BALANCED', 'QUALITY'],  # Creates Enum
    'help_text': 'Processing mode',
}
```

This automatically creates a GraphQL Enum:

```graphql
enum ProcessingMode {
  FAST
  BALANCED
  QUALITY
}
```

## Error Handling

The server provides structured error responses with helpful information:

### Validation Errors

```json
{
  "errors": [
    {
      "message": "Missing required parameter: textContent or fileUpload",
      "extensions": {
        "code": "VALIDATION_ERROR",
        "field": "textContent"
      }
    }
  ]
}
```

### Engine Not Allowed

```json
{
  "errors": [
    {
      "message": "Engine 'COQUI' is not allowed. Available TTS engines: OFFLINE, ONLINE, G_CLOUD",
      "extensions": {
        "code": "ENGINE_NOT_ALLOWED",
        "details": {
          "provided": "COQUI",
          "allowed": ["OFFLINE", "ONLINE", "G_CLOUD"]
        }
      }
    }
  ]
}
```

### Service Errors

```json
{
  "errors": [
    {
      "message": "An error occurred during processing. Please check your input and try again.",
      "extensions": {
        "code": "SERVICE_ERROR",
        "service": "TTSService"
      }
    }
  ]
}
```

**Note**: Sensitive information (API keys, file paths, credentials) is automatically redacted from error messages.

## Health Check

Check if the server is running and view its configuration:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "service": "TTS & Translation GraphQL API",
  "version": "1.0.0",
  "endpoints": {
    "graphql": "/graphql",
    "graphiql": "/graphql (browser)",
    "health": "/health"
  },
  "configuration": {
    "allowed_tts_engines": ["OFFLINE", "ONLINE", "G_CLOUD"],
    "allowed_translator_engines": ["OPENAI", "GEMINI", "DEEPL"],
    "max_concurrent_jobs": 4,
    "max_upload_size_mb": 50
  }
}
```

## Troubleshooting

### Server Won't Start

**Problem**: `Failed to start server: No module named 'strawberry'`

**Solution**: Install dependencies:

```bash
pip install strawberry-graphql fastapi uvicorn
```

### Engine Not Available

**Problem**: `Engine 'COQUI' is not allowed`

**Solution**: Add the engine to `ALLOWED_TTS_ENGINES` in `.env.server`:

```bash
ALLOWED_TTS_ENGINES=OFFLINE,ONLINE,G_CLOUD,COQUI
```

### File Upload Fails

**Problem**: `File size exceeds maximum allowed (50MB)`

**Solution**: Increase the limit in `.env.server`:

```bash
MAX_UPLOAD_SIZE_MB=100
```

### Missing API Keys

**Problem**: `OpenAI API key not found`

**Solution**: Set API keys in `.env.translator`:

```bash
OPENAI_API_KEY=your_key_here
```

### Port Already in Use

**Problem**: `Address already in use`

**Solution**: Change the port in `.env.server`:

```bash
SERVER_PORT=8001
```

Or stop the process using port 8000:

```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Development

### Running Tests

```bash
# Run all tests
pytest server/

# Run specific test file
pytest server/test_config.py

# Run with coverage
pytest --cov=server server/
```

### Viewing Logs

Logs are written to both console and file (if `LOG_FILE` is configured):

```bash
# View log file
tail -f logs/server.log

# Change log level for more detail
# Edit .env.server:
LOG_LEVEL=DEBUG
```

### Schema Introspection

Query the GraphQL schema programmatically:

```graphql
query {
  __schema {
    types {
      name
      description
    }
  }
}
```

## Future Enhancements

The server architecture is designed to support future features:

- **Authentication**: JWT-based user authentication (context prepared)
- **Database Integration**: Persistent job storage
- **WebSocket Subscriptions**: Real-time progress updates
- **Rate Limiting**: Per-user request limits
- **Caching**: Response caching for repeated queries

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review server logs for detailed error information
3. Ensure `.env.server`, `.env.tts`, and `.env.translator` are properly configured
4. Verify all dependencies are installed

## License

This server is part of the TTS & Translation project. See the main project README for license information.
