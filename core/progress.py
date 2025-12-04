import json
import os
import shutil
from typing import Dict, Any
import argparse


class ProgressManager:
    """Manages reading, writing, and deleting the .progress file for state restoration."""

    def __init__(self, file_path: str, args: argparse.Namespace):
        """Initializes manager paths and determines the output folder based on the input file."""

        # 1. Determine paths
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        file_dir = os.path.dirname(file_path) or '.'

        self.output_dir = os.path.join(file_dir, base_name)
        self.progress_file = os.path.join(self.output_dir, f"{base_name}.progress")

        # Save current arguments as a dictionary (used as default state and to check keys)
        self.current_args = vars(args)
        # Stores loaded or current progress state
        self.state: Dict[str, Any] = {}

        # 2. PERFORM CLEANUP IF REQUESTED (Destructive action)
        if args.CLEAN_OUTPUT_DIRECTORY:
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
                print(f"[CLEAN] Deleted old output directory: {self.output_dir}")

        # 3. ENSURE DIRECTORY EXISTS (Guaranteed prerequisite for use!!!)
        os.makedirs(self.output_dir, exist_ok=True)

    def load_state(self) -> bool:
        """Attempts to load the progress state from disk and overrides current args if successful."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)

                print(f"\n--- RESTORING STATE from {os.path.basename(self.progress_file)} ---")

                # Override current CLI parameters with saved parameters (e.g., engine, rate, max-file-duration)
                for key, value in self.state['parameters'].items():
                    # Only override parameters that were originally present in the CLI arguments
                    if key in self.current_args:
                        print(f"   [OVERRIDE] {key.upper()}: {self.current_args[key]} -> {value}")
                        self.current_args[key] = value

                print("-----------------------------------------------------")
                return True

            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                print(f"Warning: Corrupted or unreadable progress file found. Starting fresh. ({e})")
                self.delete_state()
                return False

        return False

    def update_state(self, last_chunk_index: int, last_mp3_index: int):
        """Saves the current progress state to disk."""

        # 1. Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # 2. Save the complete state
        self.state = {
            # Save parameters used for generation (for restoration consistency)
            'parameters': self.current_args,
            # Index of the LAST CHUNK successfully included in a saved MP3 segment
            'last_chunk_index': last_chunk_index,
            # Index of the LAST MP3 segment that was SUCCESSFULLY CLOSED
            'last_mp3_index': last_mp3_index
        }

        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to save progress file: {e}")

    def delete_state(self):
        """Deletes the progress file (upon 100% completion.)"""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print(f"Progress file deleted: {os.path.basename(self.progress_file)}")

    def get_output_directory(self) -> str:
        return self.output_dir

    @property
    def is_restored(self) -> bool:
        """Checks if a state has been successfully loaded."""
        return 'parameters' in self.state

    @property
    def get_last_chunk_index(self) -> int:
        """Returns the index of the last processed chunk, defaults to -1 (start at 0)."""
        return self.state.get('last_chunk_index', -1)

    @property
    def get_last_mp3_index(self) -> int:
        """Returns the index of the last successfully closed MP3 file, defaults to 0."""
        return self.state.get('last_mp3_index', 0)

    def get_next_mp3_filename(self, mp3_index: int) -> str:
        """Generates the filename for the next MP3 segment."""
        base_name = os.path.splitext(os.path.basename(self.progress_file))[0]
        # Format: {NN}_<input_file_name>.mp3
        return os.path.join(self.output_dir, f"{mp3_index:02d}_{base_name}.mp3")