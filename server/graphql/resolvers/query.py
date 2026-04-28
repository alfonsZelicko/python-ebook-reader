"""
Query resolvers for the GraphQL server.

This module implements GraphQL query resolvers for:
- available_engines: Returns lists of allowed TTS and translation engines
- job_status: Returns current status and progress of a job
- download_file: Returns file content or download URL
"""

from typing import TYPE_CHECKING

import strawberry

from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS, TRANS_DESCRIPTIONS
from core.tts_args_definition import TTS_CONFIG_DEFS, TTS_DESCRIPTIONS
from server.graphql.types.outputs import (
    EngineInfo,
    EngineDetail,
    ParameterDetail,
    JobStatus,
    FileDownload,
)

if TYPE_CHECKING:
    from server.graphql.context import Context

# =========================== Engine Metadata =========================== #


def _infer_field_type(conf: dict) -> str:
    """Infer the UI field type from an arg definition."""
    if conf.get("action") == "store_true":
        return "boolean"
    choices = conf.get("choices")
    if choices:
        return "select"
    param_type = conf.get("type")
    if param_type == int or param_type == float:
        return "number"
    long_name = conf.get("long_name", "").lower()
    if any(x in long_name for x in ["key", "credentials", "cred", "wav", "file"]):
        return "file" if "wav" in long_name else "string"
    return "string"


def _to_camel_case(snake: str) -> str:
    """Convert snake_case to camelCase."""
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _build_parameter_detail(conf: dict, required: bool) -> ParameterDetail:
    """Build a ParameterDetail from an arg definition dict."""
    snake_name = conf["long_name"].lower()
    camel_name = _to_camel_case(snake_name)
    label = conf["long_name"].replace("_", " ").title()
    field_type = _infer_field_type(conf)
    choices = conf.get("choices")
    default = conf.get("default")
    # For booleans, don't serialize default_value — frontend infers false from fieldType
    if field_type == "boolean":
        default_value = None
    else:
        default_value = str(default) if default is not None and default != "" else None
    help_text = conf.get("help_text")
    accept = ".wav" if "wav" in snake_name else None

    return ParameterDetail(
        name=camel_name,
        label=label,
        field_type=field_type,
        choices=choices,
        accept=accept,
        default_value=default_value,
        help_text=help_text,
        required=required,
    )


def generate_engine_metadata(config_defs, engine_key_name, descriptions):
    engine_selector = next(c for c in config_defs if c["long_name"] == engine_key_name)
    engines = engine_selector.get("choices", [])

    result = {}

    for engine in engines:
        result[engine] = {
            "description": descriptions.get(engine, ""),
            "required_parameters": [],
            "optional_parameters": [],
        }

        seen = set()
        for conf in config_defs:
            if conf["long_name"] == engine_key_name:
                continue

            snake_name = conf["long_name"].lower()
            if snake_name in seen:
                continue

            supported_engines = conf.get("engines", ["ALL"])
            if "ALL" not in supported_engines and engine not in supported_engines:
                continue

            seen.add(snake_name)
            is_mandatory = any(
                x in snake_name
                for x in ["_key", "_credentials", "_cred", "language"]
            )

            detail = _build_parameter_detail(conf, required=is_mandatory)
            if is_mandatory:
                result[engine]["required_parameters"].append(detail)
            else:
                result[engine]["optional_parameters"].append(detail)

    return result


TTS_ENGINE_METADATA = generate_engine_metadata(
    TTS_CONFIG_DEFS, "TTS_ENGINE", TTS_DESCRIPTIONS
)

TRANSLATION_ENGINE_METADATA = generate_engine_metadata(
    TRANSLATOR_CONFIG_DEFS, "TRANSLATION_ENGINE", TRANS_DESCRIPTIONS
)

# =========================== Query Resolvers =========================== #


@strawberry.type
class Query:
    """
    GraphQL Query type with read operations.

    Provides queries for:
    - Engine availability information
    - Job status tracking
    - File downloads
    """

    @strawberry.field  # type: ignore
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
                        optional_parameters=metadata["optional_parameters"],
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
                        optional_parameters=metadata["optional_parameters"],
                    )
                )

        logger.info(
            f"Returning {len(tts_engines)} TTS engines and "
            f"{len(translation_engines)} translation engines"
        )

        return EngineInfo(
            tts_engines=tts_engines, translation_engines=translation_engines
        )

    @strawberry.field  # type: ignore
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

        Example query:
        ```graphql
            query {
              jobStatus(jobId: "job-status-id") {
                status
                progress {
                  percentage
                  stage
                }
                result {
                  ... on TranslationResultWithFile {
                    outputFile
                    fileDownload {
                      fileId
                      filename
                      downloadUrl
                      content
                    }
                  }
                }
              }
            }
        ```
        """
        context: Context = info.context
        logger = context.logger

        logger.info(f"Query: job_status for job_id={job_id}")

        try:
            # Get job manager from context
            job_manager = context.job_manager

            # Query job status from JobManager
            job_status = await job_manager.get_job_status(job_id)

            logger.info(
                f"Job {job_id} status: {job_status.status.value}, "
                f"progress: {job_status.progress.percentage:.1f}%"
            )

            return job_status

        except KeyError:
            error_msg = f"Job not found: {job_id}"
            logger.warning(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to retrieve job status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

    @strawberry.field  # type: ignore
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
        """
        context: Context = info.context
        logger = context.logger

        logger.info(f"Query: download_file for file_id={file_id}")

        try:
            # Get file handler from context
            file_handler = context.request.app.state.file_handler

            # Retrieve file from FileHandler
            # TODO -> add this module :-)
            file_data = await file_handler.get_file_for_download(file_id)

            # Create FileDownload response
            # For small files, include base64-encoded content
            # For large files, provide download URL (future enhancement)
            import base64

            content_base64 = None
            download_url = None

            # If file is small enough (< 10MB), include content directly
            if file_data["size"] < 10 * 1024 * 1024:
                content_base64 = base64.b64encode(file_data["content"]).decode("utf-8")
            else:
                # For large files, we would generate a download URL
                # This is a future enhancement - for now, still include content
                content_base64 = base64.b64encode(file_data["content"]).decode("utf-8")

            logger.info(
                f"File {file_id} retrieved: {file_data['filename']} "
                f"({file_data['size']} bytes)"
            )

            return FileDownload(
                file_id=file_id,
                filename=file_data["filename"],
                content_type=file_data["content_type"],
                size_bytes=file_data["size"],
                download_url=download_url,
                content=content_base64,
            )

        except FileNotFoundError:
            error_msg = f"File not found: {file_id}"
            logger.warning(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unable to retrieve the file for download: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
