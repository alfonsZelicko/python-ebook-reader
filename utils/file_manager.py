import tkinter as tk
from tkinter import filedialog
import sys


# TODO expand it with params to switch file input type (to .pdb, etc. ...)
def select_file() -> str:
    """
    Opens a GUI file dialog to select the input text file (.txt). TODO: in future additional formats
    Returns the path to the selected file or exits if selection is cancelled.
    """
    # Initialize Tkinter and hide the root window (we only need the dialog)
    root = tk.Tk()
    root.withdraw()

    print("\nWaiting for file selection dialog...")

    file_path = filedialog.askopenfilename(
        title="Select the source text file (.txt)",
        filetypes=[("Text files", "*.txt")]
    )

    if not file_path:
        print("ERROR: File selection cancelled. Exiting.")
        sys.exit(1)

    print(f"File selected: {file_path}")

    return file_path