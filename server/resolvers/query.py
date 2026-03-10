"""
Query resolvers for the GraphQL server.

This module implements GraphQL query resolvers for:
- available_engines: Returns lists of allowed TTS and translation engines
- job_status: Returns current status and progress of a job
- download_file: Returns file content or download URL

Validates: Requirements 16.1, 16.2, 16.3, 7.3, 6.2
"""

import strawberry
from typing import TYPE_CHECKING

from server.types.outputs import EngineInfo, EngineDetail, JobStatus, FileDownload

if TYPE_CHECKING:
    from server.context import Context


# ============================================================================
# Engine Metadata
# ============================================================================

# TTS Engine metadata with descriptions and parameters
TTS_ENGINE_METADATA = {
    "OFFLINE": {
        "description": "Offline TTS using pyttsx3/SAPI (no internet required)",
        "required_parameters": ["text_content or file_upload"],
        "optional_parameters": [
            "offline_voice", "chunk_size", "chunk_by_paragraph", 
            "speaking_rate", "output_type", "max_file_duration", 
            "clean_output_directory"
        ]
    },
    "ONLINE": {
        "description": "Online TTS using gTTS (Google Text-to-Speech)",
        "required_parameters": ["text_content or file_upload"],
        "optional_parameters": [
            "language_code", "chunk_size", "chunk_by_paragraph",
            "speaking_rate", "output_type", "max_file_duration",
            "clean_output_directory"
        ]
    },
    "G_CLOUD": {
        "description": "Google Cloud Text-to-Speech with WaveNet voices",
        "required_parameters": [
            "text_content or file_upload",
            "google_credentials"
        ],
        "optional_parameters": [
            "language_code", "google_voice", "chunk_size",
            "chunk_by_paragraph", "speaking_rate", "output_type",
            "max_file_duration", "clean_output_directory"
        ]
    },
    "COQUI": {
        "description": "Coqui TTS - Offline AI-based text-to-speech",
        "required_parameters": ["text_content or file_upload"],
        "optional_parameters": [
            "coqui_model", "coqui_speaker", "coqui_wav",
            "coqui_sample_rate", "chunk_size", "chunk_by_paragraph",
            "speaking_rate", "output_type", "max_file_duration",
            "clean_output_directory"
        ]
    }
}

# Translation Engine metadata with descriptions and parameters
TRANSLATION_ENGINE_METADATA = {
    "OPENAI": {
        "description": "OpenAI GPT models for translation (gpt-4o-mini, gpt-4o)",
        "required_parameters": [
            "text_content or file_upload",
            "openai_api_key",
            "source_language",
            "target_language"
        ],
        "optional_parameters": [
            "openai_model", "translation_prompt", "chunk_size",
            "chunk_by_paragraph", "max_retries", "retry_delay",
            "clean_output_directory"
        ]
    },
    "GEMINI": {
        "description": "Google Gemini models for translation",
        "required_parameters": [
            "text_content or file_upload",
            "google_credentials",
            "source_language",
            "target_language"
        ],
        "optional_parameters": [
            "gemini_model", "translation_prompt", "chunk_size",
            "chunk_by_paragraph", "max_retries", "retry_delay",
            "clean_output_directory"
        ]
    },
    "DEEPL": {
        "description": "DeepL API for professional translation",
        "required_parameters": [
            "text_content or file_upload",
            "deepl_api_key",
            "source_language",
            "target_language"
        ],
        "optional_parameters": [
            "chunk_size", "chunk_by_paragraph", "max_retries",
            "retry_delay", "clean_output_directory"
        ]
    }
}


# ============================================================================
# Query Resolvers
# ============================================================================

@strawberry.type
class Query:
    """
    GraphQL Query type with read operations.
    
    Provides queries for:
    - Engine availability information
    - Job status tracking
    - File downloads
    """
    
    @strawberry.field
    async def available_engines(self, info: strawberry.Info) -> EngineInfo:
        """
        Returns lists of available TTS and translation engines.
        
        Filters engines based on ALLOWED_TTS_ENGINES and ALLOWED_TRANSLATOR_ENGINES
        configuration from .env.server. Includes engine metadata with descriptions
        and parameter information.
        
        Args:
            info: Strawberry info object containing context
            
        Returns:
            EngineInfo: Lists of available TTS and translation engines with metadata
            
        Validates: Requirements 16.1, 16.2, 16.3
        """
        context: Context = info.context
        config = context.config
        logger = context.logger
        
        logger.info("Query: available_engines")
        
        # Filter TTS engines based on allowlist
        tts_engines = []
        for engine_name in config.allowed_tts_engines:
            if engine_name in TTS_ENGINE_METADATA:
                metadata = TTS_ENGINE_METADATA[engine_name]
                tts_engines.append(
                    EngineDetail(
                        name=engine_name,
                        description=metadata["description"],
                        required_parameters=metadata["required_parameters"],
                        optional_parameters=metadata["optional_parameters"]
                    )
                )
        
        # Filter translation engines based on allowlist
        translation_engines = []
        for engine_name in config.allowed_translator_engines:
            if engine_name in TRANSLATION_ENGINE_METADATA:
                metadata = TRANSLATION_ENGINE_METADATA[engine_name]
                translation_engines.append(
                    EngineDetail(
                        name=engine_name,
                        description=metadata["description"],
                        required_parameters=metadata["required_parameters"],
                        optional_parameters=metadata["optional_parameters"]
                    )
                )
        
        logger.info(
            f"Returning {len(tts_engines)} TTS engines and "
            f"{len(translation_engines)} translation engines"
        )
        
        return EngineInfo(
            tts_engines=tts_engines,
            translation_engines=translation_engines
        )
    
    @strawberry.field
    async def job_status(self, job_id: str, info: strawberry.Info) -> JobStatus:
        """
        Returns current status and progress of a job.
        
        Queries the JobManager for job status and returns progress information
        including percentage complete, current chunk, and processing stage.
        
        Args:
            job_id: Unique job identifier
            info: Strawberry info object containing context
            
        Returns:
            JobStatus: Current job status with progress information
            
        Raises:
            Exception: If job_id does not exist
            
        Validates: Requirements 7.3
        """
        context: Context = info.context
        logger = context.logger
        
        logger.info(f"Query: job_status for job_id={job_id}")
        
        try:
            # Get job manager from context (will be added when main.py is implemented)
            # For now, we'll need to access it through the context
            job_manager = context.request.app.state.job_manager
            
            # Query job status from JobManager
            job_status = await job_manager.get_job_status(job_id)
            
            logger.info(
                f"Job {job_id} status: {job_status.status.value}, "
                f"progress: {job_status.progress.percentage:.1f}%"
            )
            
            return job_status
            
        except KeyError as e:
            error_msg = f"Job not found: {job_id}"
            logger.warning(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to retrieve job status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    @strawberry.field
    async def download_file(self, file_id: str, info: strawberry.Info) -> FileDownload:
        """
        Returns file content or download URL for a generated file.
        
        Uses FileHandler to retrieve file content and metadata. Returns file
        information suitable for download by the client.
        
        Args:
            file_id: Unique file identifier for download tracking
            info: Strawberry info object containing context
            
        Returns:
            FileDownload: File content and metadata
            
        Raises:
            Exception: If file does not exist or retrieval fails
            
        Validates: Requirements 6.2
        """
        context: Context = info.context
        logger = context.logger
        
        logger.info(f"Query: download_file for file_id={file_id}")
        
        try:
            # Get file handler from context
            file_handler = context.request.app.state.file_handler
            
            # Retrieve file from FileHandler
            file_data = await file_handler.get_file_for_download(file_id)
            
            # Create FileDownload response
            # For small files, include base64-encoded content
            # For large files, provide download URL (future enhancement)
            import base64
            
            content_base64 = None
            download_url = None
            
            # If file is small enough (< 10MB), include content directly
            if file_data['size'] < 10 * 1024 * 1024:
                content_base64 = base64.b64encode(file_data['content']).decode('utf-8')
            else:
                # For large files, we would generate a download URL
                # This is a future enhancement - for now, still include content
                content_base64 = base64.b64encode(file_data['content']).decode('utf-8')
            
            logger.info(
                f"File {file_id} retrieved: {file_data['filename']} "
                f"({file_data['size']} bytes)"
            )
            
            return FileDownload(
                file_id=file_id,
                filename=file_data['filename'],
                content_type=file_data['content_type'],
                size_bytes=file_data['size'],
                download_url=download_url,
                content=content_base64
            )
            
        except FileNotFoundError as e:
            error_msg = f"File not found: {file_id}"
            logger.warning(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to retrieve file for download: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
