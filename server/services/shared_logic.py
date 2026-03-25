import base64
import uuid
from logging import Logger
from pathlib import Path

from server.graphql.types import FileDownload


def create_file_download(
    file_path: Path, logger: Logger = None, max_file_size=1024
) -> FileDownload:
    """Universal FileDownload creator for both TTS and Translator."""
    file_size = file_path.stat().st_size
    content = None
    suffix = file_path.suffix.lower()

    if file_size < max_file_size:
        try:
            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("ascii")
        except Exception as e:
            logger.warning(f"Failed to encode file {file_path.name}: {e}")

    if suffix == ".zip":
        content_type = "application/zip"
    elif suffix in [".mp3", ".wav"]:
        content_type = "audio/mpeg"
    else:
        content_type = "text/plain"

    return FileDownload(
        file_id=str(uuid.uuid4()),
        filename=file_path.name,
        content_type=content_type,
        size_bytes=file_size,
        download_url=f"/download/{file_path.parent.name}/{file_path.name}",
        content=content,
    )


def validate_server_constraints(allowed_engines, engine: str) -> None:
    if engine not in allowed_engines:
        raise ValueError(f"Engine '{engine}' is not allowed by server config.")
