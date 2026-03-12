"""
Translation Service for the GraphQL server.

This module wraps existing translation functionality and adapts it for GraphQL usage.
It handles translation by invoking existing translator_processor logic.
"""

import argparse
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from core.translator_engines import initialize_translation_engine
from core.translator_processor import start_translation
from server.graphql.types import TranslationResult, TranslationMetadata


class TranslationService:
    """
    Service wrapper for translation operations.

    This service integrates with existing translation functionality (translator_processor.py,
    translator_engines.py) and provides a GraphQL-friendly interface.

    Responsibilities:
    - Validate translation engine is in allowed list
    - Prepare input files from uploads or text content
    - Convert GraphQL input to argparse.Namespace
    - Execute translation processing using existing code
    - Collect output file and metadata
    - Support progress callbacks for async operations
    """

    def __init__(self, config, logger: logging.Logger):
        """
        Initialize TranslationService with configuration and logger.

        Args:
            config: ServerConfig instance with translation settings
            logger: Logger instance for translation operations
        """
        self.config = config
        self.logger = logger
        self.temp_dir = Path(config.temp_directory)

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("TranslationService initialized")

    async def translate_text(
        self, input_data, progress_callback: Optional[Callable] = None
    ) -> TranslationResult:
        """
        Execute translation by invoking existing translator_processor logic.

        Process:
        1. Validate engine is in allowed list
        2. Prepare input file (from upload or text_content)
        3. Convert GraphQL input to argparse.Namespace
        4. Initialize translation engine using existing initialize_translation_engine()
        5. Execute translation using existing start_translation()
        6. Collect output file and metadata
        7. Clean up temporary files
        8. Return TranslationResult

        Args:
            input_data: TranslationInput object with translation parameters
            progress_callback: Optional callback for progress updates

        Returns:
            TranslationResult with success status, output file, and metadata

        Raises:
            ValueError: If validation fails or processing errors occur
        """
        temp_input_file = None

        try:
            # 1. Validate engine
            self._validate_engine(input_data.engine)

            # 2. Prepare input file
            temp_input_file = await self._prepare_input_file(input_data)

            self.logger.info(
                f"Starting translation with engine: {input_data.engine}",
                extra={
                    "engine": input_data.engine,
                    "source_language": (
                        input_data.source_language
                        if hasattr(input_data, "source_language")
                        else "unknown"
                    ),
                    "target_language": (
                        input_data.target_language
                        if hasattr(input_data, "target_language")
                        else "unknown"
                    ),
                    "input_file": temp_input_file,
                },
            )

            # 3. Convert to argparse.Namespace
            args = self._convert_to_args(input_data, temp_input_file)

            # 4. Initialize translation engine
            translation_engine = initialize_translation_engine(args)

            # 5. Execute translation
            start_time = datetime.now()
            start_translation(temp_input_file, translation_engine, args)
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()

            # 6. Collect output file
            output_file = self._get_output_file(temp_input_file)

            # Get output directory
            output_dir = self._get_output_directory(temp_input_file)

            # Calculate total chunks from output file
            total_chunks = self._estimate_chunks(output_file)

            # Create metadata
            metadata = TranslationMetadata(
                engine_used=input_data.engine,
                source_language=(
                    input_data.source_language
                    if hasattr(input_data, "source_language")
                    else "unknown"
                ),
                target_language=(
                    input_data.target_language
                    if hasattr(input_data, "target_language")
                    else "unknown"
                ),
                total_chunks=total_chunks,
                output_directory=str(output_dir),
            )

            self.logger.info(
                f"Translation completed successfully",
                extra={
                    "engine": input_data.engine,
                    "output_file": output_file,
                    "processing_time": processing_time,
                    "total_chunks": total_chunks,
                },
            )

            # 7. Return result
            return TranslationResult(
                success=True,
                message=f"Successfully translated text using {input_data.engine} engine",
                output_file=output_file,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            self.logger.error(
                error_msg,
                exc_info=True,
                extra={
                    "engine": (
                        input_data.engine
                        if hasattr(input_data, "engine")
                        else "unknown"
                    )
                },
            )
            raise ValueError(error_msg)

        finally:
            # 8. Clean up temporary input file
            if temp_input_file and os.path.exists(temp_input_file):
                try:
                    os.remove(temp_input_file)
                    self.logger.debug(
                        f"Cleaned up temporary input file: {temp_input_file}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to cleanup temp file: {temp_input_file} - {str(e)}"
                    )

    def _validate_engine(self, engine: str) -> None:
        """
        Check if engine is in ALLOWED_TRANSLATOR_ENGINES.

        Args:
            engine: Translation engine name to validate

        Raises:
            ValueError: If engine is not in allowed list
        """
        if engine not in self.config.allowed_translator_engines:
            error_msg = (
                f"Translation engine '{engine}' is not allowed. "
                f"Available engines: {', '.join(self.config.allowed_translator_engines)}"
            )
            self.logger.warning(
                f"Engine validation failed: {error_msg}",
                extra={
                    "requested_engine": engine,
                    "allowed_engines": self.config.allowed_translator_engines,
                },
            )
            raise ValueError(error_msg)

    async def _prepare_input_file(self, input_data) -> str:
        """
        Handle uploads and text_content to create input file.

        Args:
            input_data: TranslationInput object with file_upload or text_content

        Returns:
            Path to prepared input file

        Raises:
            ValueError: If neither file_upload nor text_content is provided
        """
        # Check if we have input
        has_upload = (
            hasattr(input_data, "file_upload") and input_data.file_upload is not None
        )
        has_text = hasattr(input_data, "text_content") and input_data.text_content

        if not has_upload and not has_text:
            raise ValueError("Either file_upload or text_content must be provided")

        # If file upload is provided, use it
        if has_upload:
            # File upload handling is done by FileHandler
            # For now, we'll read the upload and save it
            content = await input_data.file_upload.read()

            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = f"translation_input_{file_id}.txt"
            file_path = self.temp_dir / filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(content)

            self.logger.debug(f"Saved uploaded file to: {file_path}")
            return str(file_path)

        # Otherwise, use text_content
        else:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = f"translation_input_{file_id}.txt"
            file_path = self.temp_dir / filename

            # Save text content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(input_data.text_content)

            self.logger.debug(f"Saved text content to: {file_path}")
            return str(file_path)

    def _convert_to_args(self, input_data, input_file: str) -> argparse.Namespace:
        """
        Create argparse.Namespace from TranslationInput.

        Converts GraphQL input fields to the format expected by existing
        translation processing code.

        Args:
            input_data: TranslationInput object with translation parameters
            input_file: Path to input file

        Returns:
            argparse.Namespace with translation arguments
        """
        # Create namespace with all translation parameters
        args = argparse.Namespace()

        # Input file
        args.input_file = input_file

        # Core parameters
        args.TE = input_data.engine if hasattr(input_data, "engine") else "OPENAI"
        args.SL = (
            input_data.source_language
            if hasattr(input_data, "source_language")
            else "en"
        )
        args.TL = (
            input_data.target_language
            if hasattr(input_data, "target_language")
            else "cs"
        )
        args.TP = (
            input_data.translation_prompt
            if hasattr(input_data, "translation_prompt")
            else "You are a professional book translator. Translate the following fantasy text accurately while preserving the style and tone."
        )
        args.CS = input_data.chunk_size if hasattr(input_data, "chunk_size") else 4000
        args.CP = (
            input_data.chunk_by_paragraph
            if hasattr(input_data, "chunk_by_paragraph")
            else True
        )

        # OpenAI parameters
        args.O_KEY = (
            input_data.openai_api_key if hasattr(input_data, "openai_api_key") else ""
        )
        args.O_MODEL = (
            input_data.openai_model
            if hasattr(input_data, "openai_model")
            else "gpt-4o-mini"
        )

        # Google Gemini parameters
        args.G_CRED = (
            input_data.google_credentials
            if hasattr(input_data, "google_credentials")
            else "./google-key.json"
        )
        args.G_MODEL = (
            input_data.gemini_model
            if hasattr(input_data, "gemini_model")
            else "gemini-pro"
        )

        # DeepL parameters
        args.D_KEY = (
            input_data.deepl_api_key if hasattr(input_data, "deepl_api_key") else ""
        )

        # Retry & error handling
        args.MR = input_data.max_retries if hasattr(input_data, "max_retries") else 3
        args.RD = input_data.retry_delay if hasattr(input_data, "retry_delay") else 1.0

        # Output configuration
        args.COD = (
            input_data.clean_output_directory
            if hasattr(input_data, "clean_output_directory")
            else False
        )

        self.logger.debug(
            f"Converted input to args namespace",
            extra={
                "engine": args.TE,
                "source_language": args.SL,
                "target_language": args.TL,
                "chunk_size": args.CS,
            },
        )

        return args

    def _get_output_file(self, input_file: str) -> str:
        """
        Get output file path based on input file.

        The output file follows the pattern used by existing translation code:
        <input_file_without_extension>_translated.txt in the output directory

        Args:
            input_file: Path to input file

        Returns:
            Path to output file

        Raises:
            FileNotFoundError: If output file doesn't exist
        """
        input_path = Path(input_file)
        output_dir = self._get_output_directory(input_file)
        output_filename = f"{input_path.stem}_translated.txt"
        output_file = output_dir / output_filename

        if not output_file.exists():
            raise FileNotFoundError(f"Output file not found: {output_file}")

        return str(output_file)

    def _get_output_directory(self, input_file: str) -> Path:
        """
        Get output directory path based on input file.

        The output directory follows the pattern used by existing translation code:
        <input_file_without_extension>_output/

        Args:
            input_file: Path to input file

        Returns:
            Path to output directory
        """
        input_path = Path(input_file)
        output_dir_name = f"{input_path.stem}_output"
        output_dir = input_path.parent / output_dir_name

        return output_dir

    def _estimate_chunks(self, output_file: str) -> int:
        """
        Estimate the number of chunks from the output file.

        This is a rough estimate based on the number of newlines in the output file,
        as the translator_processor joins chunks with newlines.

        Args:
            output_file: Path to output file

        Returns:
            Estimated number of chunks
        """
        try:
            if not os.path.exists(output_file):
                return 0

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Count non-empty lines as chunks
                chunks = [line for line in content.split("\n") if line.strip()]
                return len(chunks)

        except Exception as e:
            self.logger.warning(
                f"Failed to estimate chunks: {str(e)}", extra={"error": str(e)}
            )
            return 0
