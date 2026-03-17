import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog


# TODO expand it with params to switch file input type (to .pdb, etc. ...)
def select_file() -> str:
    """
    Opens a GUI file dialog to select the input text file (.txt).
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


def get_work_directory(input_file_path: str, base_temp_dir: str = None) -> Path:
    """
    Returns a unified path for the output directory based on input file name.
    If base_temp_dir is provided, the directory is created inside it.
    """
    input_path = Path(input_file_path)
    base_name = input_path.stem  # 'test_en'

    if base_temp_dir:
        return Path(base_temp_dir) / base_name

    # Fallback pro CLI použití (vytvoří složku vedle souboru)
    return input_path.parent / base_name


def get_progress_file_path(work_dir: Path, base_name: str) -> Path:
    """Returns the path to the .progress file."""
    return work_dir / f"{base_name}.progress"


def get_translated_file_path(work_dir: Path, base_name: str) -> Path:
    """Returns the path to the translated text file."""
    return work_dir / f"{base_name}_translated.txt"
