"""
TTS Service for the GraphQL server.

This module wraps existing TTS functionality and adapts it for GraphQL usage.
It handles TTS generation by invoking existing tts_processor logic.
"""

import argparse
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List

from core.tts_engines import initialize_tts_engine
from core.tts_processor import start_processing
from server.graphql.types import TTSResult, TTSMetadata


class TTSService:
    """
    Service wrapper for TTS operations.

    This service integrates with existing TTS functionality (tts_processor.py,
    tts_engines.py) and provides a GraphQL-friendly interface.

    Responsibilities:
    - Validate TTS engine is in allowed list
    - Prepare input files from uploads or text content
    - Convert GraphQL input to argparse.Namespace
    - Execute TTS processing using existing code
    - Collect output files and metadata
    - Support progress callbacks for async operations
    """

    def __init__(self, config, logger: logging.Logger):
        """
        Initialize TTSService with configuration and logger.

        Args:
            config: ServerConfig instance with TTS settings
            logger: Logger instance for TTS operations
        """
        self.config = config
        self.logger = logger
        self.temp_dir = Path(config.temp_directory)

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("TTSService initialized")

    async def generate_speech(
        self, input_data, progress_callback: Optional[Callable] = None
    ) -> TTSResult:
        """
        Execute TTS generation by invoking existing tts_processor logic.

        Process:
        1. Validate engine is in allowed list
        2. Prepare input file (from upload or text_content)
        3. Convert GraphQL input to argparse.Namespace
        4. Initialize TTS engine using existing initialize_tts_engine()
        5. Execute processing using existing start_processing()
        6. Collect output files and metadata
        7. Clean up temporary files
        8. Return TTSResult

        Args:
            input_data: TTSInput object with TTS parameters
            progress_callback: Optional callback for progress updates

        Returns:
            TTSResult with success status, output files, and metadata

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
                f"Starting TTS generation with engine: {input_data.engine}",
                extra={"engine": input_data.engine, "input_file": temp_input_file},
            )

            # 3. Convert to argparse.Namespace
            args = self._convert_to_args(input_data, temp_input_file)

            # 4. Initialize TTS engine
            tts_engine = initialize_tts_engine(args)

            # 5. Execute processing
            start_time = datetime.now()
            start_processing(temp_input_file, tts_engine, args)
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()

            # 6. Collect output files
            output_files = self._collect_output_files(temp_input_file, args)

            # Calculate total duration from output files
            total_duration = self._calculate_total_duration(output_files)

            # Get output directory
            output_dir = self._get_output_directory(temp_input_file)

            # Create metadata
            metadata = TTSMetadata(
                engine_used=input_data.engine,
                total_chunks=len(output_files),
                total_duration_seconds=total_duration,
                output_directory=str(output_dir),
            )

            self.logger.info(
                f"TTS generation completed successfully",
                extra={
                    "engine": input_data.engine,
                    "output_files": len(output_files),
                    "processing_time": processing_time,
                    "total_duration": total_duration,
                },
            )

            # 7. Return result
            return TTSResult(
                success=True,
                message=f"Successfully generated {len(output_files)} audio file(s) using {input_data.engine} engine",
                output_files=output_files,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"TTS generation failed: {str(e)}"
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
        Check if engine is in ALLOWED_TTS_ENGINES.

        Args:
            engine: TTS engine name to validate

        Raises:
            ValueError: If engine is not in allowed list
        """
        if engine not in self.config.allowed_tts_engines:
            error_msg = (
                f"TTS engine '{engine}' is not allowed. "
                f"Available engines: {', '.join(self.config.allowed_tts_engines)}"
            )
            self.logger.warning(
                f"Engine validation failed: {error_msg}",
                extra={
                    "requested_engine": engine,
                    "allowed_engines": self.config.allowed_tts_engines,
                },
            )
            raise ValueError(error_msg)

    async def _prepare_input_file(self, input_data) -> str:
        """
        Handle uploads and text_content to create input file.

        Args:
            input_data: TTSInput object with file_upload or text_content

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
            filename = f"tts_input_{file_id}.txt"
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
            filename = f"tts_input_{file_id}.txt"
            file_path = self.temp_dir / filename

            # Save text content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(input_data.text_content)

            self.logger.debug(f"Saved text content to: {file_path}")
            return str(file_path)

    def _convert_to_args(self, input_data, input_file: str) -> argparse.Namespace:
        """
        Create argparse.Namespace from TTSInput.

        Converts GraphQL input fields to the format expected by existing
        TTS processing code.

        Args:
            input_data: TTSInput object with TTS parameters
            input_file: Path to input file

        Returns:
            argparse.Namespace with TTS arguments
        """
        # Create namespace with all TTS parameters
        args = argparse.Namespace()

        # Input file
        args.input_file = input_file

        # Core parameters
        args.TE = input_data.engine if hasattr(input_data, "engine") else "ONLINE"
        args.CS = input_data.chunk_size if hasattr(input_data, "chunk_size") else 3500
        args.CP = (
            input_data.chunk_by_paragraph
            if hasattr(input_data, "chunk_by_paragraph")
            else False
        )
        args.SR = (
            input_data.speaking_rate if hasattr(input_data, "speaking_rate") else 1.1
        )

        # Output configuration
        args.OT = (
            input_data.output_type if hasattr(input_data, "output_type") else "FILE"
        )
        args.MFD = (
            input_data.max_file_duration
            if hasattr(input_data, "max_file_duration")
            else 600
        )
        args.COD = (
            input_data.clean_output_directory
            if hasattr(input_data, "clean_output_directory")
            else False
        )

        # Offline engine parameters
        args.OFF_VOICE = (
            input_data.offline_voice if hasattr(input_data, "offline_voice") else ""
        )

        # Language configuration
        args.L_CODE = (
            input_data.language_code
            if hasattr(input_data, "language_code")
            else "cs-CZ"
        )

        # Google Cloud parameters
        args.G_CRED = (
            input_data.google_credentials
            if hasattr(input_data, "google_credentials")
            else "./google-key.json"
        )
        args.G_VOICE = (
            input_data.google_voice
            if hasattr(input_data, "google_voice")
            else "cs-CZ-Standard-B"
        )

        # Coqui parameters
        args.C_MODEL = (
            input_data.coqui_model
            if hasattr(input_data, "coqui_model")
            else "tts_models/multilingual/multi-dataset/xtts_v2"
        )
        args.C_SPEAKER = (
            input_data.coqui_speaker if hasattr(input_data, "coqui_speaker") else ""
        )
        args.C_WAV = input_data.coqui_wav if hasattr(input_data, "coqui_wav") else ""
        args.C_RATE = (
            input_data.coqui_sample_rate
            if hasattr(input_data, "coqui_sample_rate")
            else 22050
        )

        self.logger.debug(
            f"Converted input to args namespace",
            extra={"engine": args.TE, "chunk_size": args.CS, "output_type": args.OT},
        )

        return args

    def _collect_output_files(
        self, input_file: str, args: argparse.Namespace
    ) -> List[str]:
        """
        Gather generated MP3 files from output directory.

        Args:
            input_file: Path to input file (used to determine output directory)
            args: Arguments namespace with output configuration

        Returns:
            List of paths to generated MP3 files
        """
        output_dir = self._get_output_directory(input_file)

        # Check if output directory exists
        if not output_dir.exists():
            self.logger.warning(f"Output directory does not exist: {output_dir}")
            return []

        # Collect all MP3 files in the output directory
        mp3_files = sorted(output_dir.glob("*.mp3"))

        # Convert to string paths
        output_files = [str(f) for f in mp3_files]

        self.logger.debug(
            f"Collected {len(output_files)} output files from {output_dir}",
            extra={"output_dir": str(output_dir), "file_count": len(output_files)},
        )

        return output_files

    def _get_output_directory(self, input_file: str) -> Path:
        """
        Get output directory path based on input file.

        The output directory follows the pattern used by existing TTS code:
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

    def _calculate_total_duration(self, output_files: List[str]) -> float:
        """
        Calculate total duration of all output MP3 files.

        Args:
            output_files: List of paths to MP3 files

        Returns:
            Total duration in seconds
        """
        try:
            from pydub import AudioSegment

            total_duration = 0.0
            for file_path in output_files:
                if os.path.exists(file_path):
                    audio = AudioSegment.from_mp3(file_path)
                    total_duration += len(audio) / 1000.0  # Convert ms to seconds

            return total_duration

        except Exception as e:
            self.logger.warning(
                f"Failed to calculate total duration: {str(e)}", extra={"error": str(e)}
            )
            return 0.0
