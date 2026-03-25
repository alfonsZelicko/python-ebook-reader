"""
TTS Service for the GraphQL server.
Handles speech generation by invoking the core tts_processor.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Callable, List

from core.tts_args_definition import TTS_CONFIG_DEFS
from core.tts_engines import initialize_tts_engine
from core.tts_processor import start_processing
from server.graphql.schema_generator import SchemaGenerator
from server.graphql.types import TTSMetadata
from server.graphql.types.outputs import TTSResultWithFile
from server.services.shared_logic import (
    validate_server_constraints,
    create_file_download,
)
from utils.args_manager import resolve_args, validate_pre_execution_actions
from utils.file_manager import compress_output


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
    ) -> TTSResultWithFile:
        """
        Handles TTS generation by invoking existing tts_processor logic.
        """
        temp_input_file_path = None

        try:
            print("BEFORE AWAIT")
            temp_input_file_path = await self._prepare_input_file(input_data)
            print("AFTER AWAIT")

            from dataclasses import asdict

            raw_input_data = asdict(input_data)

            provided_data = {}
            for field_name, short_key in self._field_to_key.items():
                if field_name in raw_input_data:
                    val = raw_input_data[field_name]
                    if val is not None:
                        provided_data[short_key] = (
                            val.value if hasattr(val, "value") else val
                        )

            args = resolve_args(mode="TTS", provided_data=provided_data)

            args.INPUT_FILE_PATH = temp_input_file_path

            # if not getattr(args, "OT", None): # its ALWAYS file :-)
            args.OT = "FILE"

            validate_server_constraints(self.config.allowed_tts_engines, args.TE)
            validate_pre_execution_actions(args, mode="TTS")

            tts_engine = initialize_tts_engine(args)

            # start_time = datetime.now()
            # Processor handles the splitting and audio generation
            start_processing(temp_input_file_path, tts_engine, args)
            # end_time = datetime.now()

            output_files = self._collect_output_files(temp_input_file_path)
            total_duration = self._calculate_total_duration(output_files)

            metadata = TTSMetadata(
                engine_used=args.TE,
                total_chunks=len(output_files),
                total_duration_seconds=total_duration,
                output_directory=str(
                    temp_input_file_path.parent / f"{temp_input_file_path.stem}"
                ),
            )

            # Compress all in
            if not output_files:
                raise ValueError("No files found in output directory.")

            file_download = compress_output(
                Path(output_files[0]).parent, True, True, self.logger
            )

            file_download = create_file_download(file_download)

            return TTSResultWithFile(
                success=True,
                message=f"Generated {len(output_files)} audio file(s) using {args.TE}",
                output_files=output_files,
                file_download=file_download,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"TTS generation failed: {str(e)}", exc_info=True)
            raise ValueError(str(e))

        finally:
            # Clean up the temporary input_data text file
            if temp_input_file_path and os.path.exists(temp_input_file_path):
                try:
                    os.remove(temp_input_file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp file: {e}")

    async def _prepare_input_file(self, input_data) -> Path:
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

        return file_path

    @staticmethod
    def _collect_output_files(input_path: Path) -> List[str]:
        temp_dir = input_path.parent

        if not temp_dir.exists():
            return []

        uuid_part = input_path.stem.split("_")[-1]

        result = []
        for d in temp_dir.glob(f"*tts_in_{uuid_part}*"):
            if d.is_dir():
                result.extend(str(f) for f in sorted(d.glob("*.mp3")))

        return result

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
