"""
TTS Service for the GraphQL server.
Handles speech generation by invoking the core tts_processor.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List

from core.tts_args_definition import TTS_CONFIG_DEFS
from core.tts_engines import initialize_tts_engine
from core.tts_processor import start_processing
from server.graphql.schema_generator import SchemaGenerator
from server.graphql.types import TTSResult, TTSMetadata
from utils.args_manager import resolve_args, validate_pre_execution_actions


class TTSService:
    def __init__(self, config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.temp_dir = Path(config.temp_directory)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Mapping: {graphql_field_name: short_key}
        # Dynamically builds mapping from TTS_CONFIG_DEFS -> syntax is python speciality :-)
        self._field_to_key = {
            SchemaGenerator.convert_key_to_field_name(d["key"], TTS_CONFIG_DEFS): d[
                "key"
            ]
            for d in TTS_CONFIG_DEFS
        }
        self.logger.info("TTSService initialized with dynamic mapping")

    async def generate_speech(
        self, input_data, progress_callback: Optional[Callable] = None
    ) -> TTSResult:
        """
        Handles TTS generation by invoking existing tts_processor logic.
        """
        temp_input_file = None

        try:
            temp_input_file = await self._prepare_input_file(input_data)

            provided_data = {}
            for field_name, short_key in self._field_to_key.items():
                val = getattr(input_data, field_name, None)
                if val is not None:
                    # Handle Strawberry Enums if present
                    provided_data[short_key] = (
                        val.value if hasattr(val, "value") else val
                    )

            args = resolve_args(mode="TTS", provided_data=provided_data)

            args.INPUT_FILE_PATH = temp_input_file

            if not getattr(args, "OT", None):
                args.OT = "FILE"

            self._validate_server_constraints(args.TE)

            validate_pre_execution_actions(args, mode="TTS")

            tts_engine = initialize_tts_engine(args)

            start_time = datetime.now()
            # Processor handles the splitting and audio generation
            start_processing(temp_input_file, tts_engine, args)
            end_time = datetime.now()

            output_files = self._collect_output_files(temp_input_file)
            total_duration = self._calculate_total_duration(output_files)

            metadata = TTSMetadata(
                engine_used=args.TE,
                total_chunks=len(output_files),
                total_duration_seconds=total_duration,
                output_directory=str(self._get_output_directory(temp_input_file)),
            )

            return TTSResult(
                success=True,
                message=f"Generated {len(output_files)} audio file(s) using {args.TE}",
                output_files=output_files,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"TTS generation failed: {str(e)}", exc_info=True)
            # GraphQL will catch this ValueError and return it to the user
            raise ValueError(str(e))

        finally:
            # Clean up the temporary input_data text file
            if temp_input_file and os.path.exists(temp_input_file):
                try:
                    os.remove(temp_input_file)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp file: {e}")

    def _validate_server_constraints(self, engine: str) -> None:
        """Checks if the requested engine is allowed by server configuration."""
        if engine not in self.config.allowed_tts_engines:
            raise ValueError(f"TTS Engine '{engine}' is not allowed by server config.")

    async def _prepare_input_file(self, input_data) -> str:
        """Saves text content or uploaded file to a temporary location."""
        file_id = str(uuid.uuid4())
        file_path = self.temp_dir / f"tts_in_{file_id}.txt"

        if hasattr(input_data, "file_upload") and input_data.file_upload:
            content = await input_data.file_upload.read()
            with open(file_path, "wb") as f:
                f.write(content)
        elif hasattr(input_data, "text_content") and input_data.text_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(input_data.text_content)
        else:
            raise ValueError("No input_data source provided (text or file).")

        return str(file_path)

    def _collect_output_files(self, input_file: str) -> List[str]:
        """Finds all generated audio files in the output directory."""
        output_dir = self._get_output_directory(input_file)
        if not output_dir.exists():
            return []

        # Sort files to ensure 001.mp3 comes before 002.mp3
        return [str(f) for f in sorted(output_dir.glob("*.mp3"))]

    def _get_output_directory(self, input_file: str) -> Path:
        """Returns the path where the processor stores generated audio."""
        input_path = Path(input_file)
        return input_path.parent / f"{input_path.stem}_output"

    def _calculate_total_duration(self, output_files: List[str]) -> float:
        """Calculates total duration of all generated MP3 files in seconds."""
        try:
            from pydub import AudioSegment

            duration_ms = 0.0
            for f in output_files:
                if os.path.exists(f):
                    duration_ms += len(AudioSegment.from_mp3(f))
            return duration_ms / 1000.0
        except Exception as e:
            self.logger.warning(f"Duration calculation failed: {e}")
            return 0.0
