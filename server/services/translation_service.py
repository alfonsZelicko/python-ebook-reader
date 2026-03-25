"""
Translation Service for the GraphQL server.

This module wraps existing translation functionality and adapts it for GraphQL usage.
It handles translation by invoking existing translator_processor logic.
"""

import logging
import os
import traceback
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS
from core.translator_engines import initialize_translation_engine
from core.translator_processor import start_translation
from server.graphql.schema_generator import SchemaGenerator
from server.graphql.types.outputs import (
    TranslationResultWithFile,
    TranslationMetadata,
    FileDownload,
)
from server.services.shared_logic import (
    create_file_download,
    validate_server_constraints,
)
from utils.args_manager import resolve_args, validate_pre_execution_actions
from utils.file_manager import (
    get_work_directory,
    get_translated_file_path,
    compress_output,
)


class TranslationService:
    def __init__(self, config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.temp_dir = Path(config.temp_directory)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Mapping: {graphql_field_name: short_key}
        self._field_to_key = {
            SchemaGenerator.convert_key_to_field_name(
                d["key"], TRANSLATOR_CONFIG_DEFS
            ): d["key"]
            for d in TRANSLATOR_CONFIG_DEFS
        }

    async def translate_text(
        self, input_data, progress_callback: Optional[Callable] = None
    ) -> TranslationResultWithFile:
        """
        Handles translation by invoking existing translator_processor logic.

        Args:
            input_data: GraphQL input_data data containing translation parameters.
            progress_callback: Optional callback for progress updates.
                usage smthng like:
                ```python
                    def my_logger(current, total):
                    percent = (current / total) * 100
                    print(f"Progress: {percent:.1f}% ({current}/{total})")
                    ...
                    await self.translate_text(input_data, progress_callback=my_logger)
                ```

        Returns:
            TranslationResult: Result of the translation process.
        """
        temp_input_file = None

        try:
            temp_input_file = await self._prepare_input_file(input_data)
            raw_input_data = asdict(input_data)

            provided_data = {}
            for field_name, short_key in self._field_to_key.items():
                if field_name in raw_input_data:
                    val = raw_input_data[field_name]
                    if val is not None:
                        provided_data[short_key] = (
                            val.value if hasattr(val, "value") else val
                        )

            args = resolve_args(mode="TRANSLATOR", provided_data=provided_data)

            args.INPUT_FILE_PATH = temp_input_file
            validate_server_constraints(self.config.allowed_translator_engines, args.TE)
            validate_pre_execution_actions(args, mode="TRANSLATOR")

            translation_engine = initialize_translation_engine(args)

            start_time = datetime.now()
            # The processor handles the translation logic and file I/O
            start_translation(temp_input_file, translation_engine, args)
            end_time = datetime.now()

            # TODO at this moment i am calculating chunks only from 1 file -> THIS IS NOT PREPARED ON MORE FILES!!! - even compress works well, after all (:o[
            txt_output_file = self._get_output_file(temp_input_file)
            # total_chunks = self._estimate_chunks(txt_output_file)
            final_output_file = compress_output(
                txt_output_file, True, True, self.logger
            )

            metadata = TranslationMetadata(
                engine_used=args.TE,
                source_language=args.SL,
                target_language=args.TL,
                total_chunks=0,
                output_directory=str(final_output_file.parent),
            )

            # Create FileDownload for direct file access
            file_download = self._create_file_download(final_output_file)

            return TranslationResultWithFile(
                success=True,
                message=f"Successfully translated using {args.TE}",
                output_file=final_output_file,
                file_download=file_download,
                metadata=metadata,
            )

        except Exception as e:
            # Log full traceback for the server admin
            self.logger.error(f"Translation failed: {str(e)}", exc_info=True)
            print(traceback.format_exc())
            # Re-raise as ValueError to be caught by GraphQL error handler
            raise ValueError(str(e))

        finally:
            # Clean up the temporary input_data file
            if temp_input_file and os.path.exists(temp_input_file):
                try:
                    os.remove(temp_input_file)
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Failed to delete temp file {temp_input_file}: {cleanup_error}"
                    )

    async def _prepare_input_file(self, input_data) -> Path:
        file_id = str(uuid.uuid4())
        file_path = self.temp_dir / f"trans_in_{file_id}.txt"

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

    def _get_output_file(self, input_path: Path) -> Path:
        work_dir = get_work_directory(input_path, str(self.temp_dir))
        output_file = get_translated_file_path(work_dir, input_path.stem)

        if not output_file.exists():
            self.logger.error(f"Processor did not create output at {output_file}")
            raise FileNotFoundError(f"Processor did not create output at {output_file}")

        return output_file

    def _create_file_download(self, file_path: Path) -> FileDownload:
        return create_file_download(file_path, self.logger)

    # TODO this is some shitty random AI code -> I need to collect chunks from progress_manager.py -> this is bullshit :-)
    # @staticmethod
    # def _estimate_chunks(output_file: Path) -> int:
    #     try:
    #         with open(output_file, "r", encoding="utf-8") as f:
    #             return len([line for line in f if line.strip()])
    #     except OSError:
    #         return 0
