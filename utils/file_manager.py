import logging
import sys
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog
from typing import Optional


# TODO expand it with params to switch file input_data type (to .pdb, etc. ...)
def select_file() -> str:
    """
    Opens a GUI file dialog to select the input_data text file (.txt).
    Returns the path to the selected file or exits if selection is cancelled.
    """
    # Initialize Tkinter and hide the root window (we only need the dialog)
    root = tk.Tk()
    root.withdraw()

    print("\nWaiting for file selection dialog...")

    file_path = filedialog.askopenfilename(
        title="Select the source text file (.txt)", filetypes=[("Text files", "*.txt")]
    )

    if not file_path:
        print("ERROR: File selection cancelled. Exiting.")
        sys.exit(1)

    print(f"File selected: {file_path}")

    return file_path


def get_work_directory(input_file_path: Path, base_temp_dir: str = None) -> Path:
    """
    Returns a unified path for the output directory based on input_data file name.
    If base_temp_dir is provided, the directory is created inside it.
    """
    base_name = input_file_path.stem  # 'test_en'

    if base_temp_dir:
        return Path(base_temp_dir) / base_name

    return input_file_path.parent / base_name


def get_progress_file_path(work_dir: Path, base_name: str) -> Path:
    """Returns the path to the .progress file."""
    return work_dir / f"{base_name}.progress"


def get_translated_file_path(work_dir: Path, base_name: str) -> Path:
    """Returns the path to the translated text file."""
    return work_dir / f"{base_name}_translated.txt"


def compress_output(
    output_dir: Path,
    rm_old: bool = True,
    zip_always: bool = True,
    logger: Optional[logging.Logger] = None,
) -> Path:
    """
    Compress content of given output directory into a ZIP archive and return the path.
    :param output_dir:
    :param rm_old:
    :param zip_always:
    :param logger:
    :return: path to the ZIP archive
    """

    translated_files = [
        p for p in output_dir.iterdir() if p.is_file() and p.suffix != ".zip"
    ]

    # if len(translated_files) <= 1 and not zip_always:
    #     if logger:
    #         logger.info(f"No compression needed: {output_file}")
    #     return Path(output_file)

    zip_path = output_dir / f"{output_dir.name}_translations.zip"

    try:
        with zipfile.ZipFile(
            zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zipf:
            for file_path in translated_files:
                if file_path != zip_path:
                    zipf.write(file_path, file_path.name)

    except Exception as e:
        raise RuntimeError("Failed to create ZIP archive") from e

    if rm_old:
        for file_path in translated_files:
            if file_path != zip_path:
                try:
                    file_path.unlink()
                except Exception as e:
                    if logger:
                        logger.warning(f"Failed to remove {file_path}: {e}")

    return zip_path
