import argparse
import os
import sys

from config_definitions import CONFIG_DEFS
from utils.env_generator import generate_env_file
from utils.file_manager import select_file
from utils.voice_lister import list_available_voices


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments using definitions from CONFIG_DEFS,
    ensuring CLI > ENV > Default priority.
    """
    parser = argparse.ArgumentParser(
        description="A modular TTS reader supporting multiple engines and audiobook export.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("--generate-env", action="store_true",
                        dest="GENERATE_ENV",
                        help="Generates a .env file based on the config definitions and exits.")

    # --- Iterate through definitions to build arguments ---
    for item in CONFIG_DEFS:
        key = item['key']
        default_val = item['default']
        help_text = item['help_text']
        arg_type = item.get('type', str)  # Default type is str

        # 1. Determine the effective default (ENV or hardcoded default)
        env_val = os.getenv(key)
        effective_default = arg_type(env_val) if env_val is not None else default_val

        # 2. Convert key name (e.g., TTS_ENGINE) to argument name (e.g., --tts-engine)
        arg_name = "--" + key.lower().replace('_', '-')

        # 3. Build the argument help string with priority context
        full_help = (
            f"{help_text}\n"
            f"Overrides the value from .env. (default: {effective_default})."
        )

        # 4. Add the argument to the parser
        parser.add_argument(
            arg_name,
            type=arg_type,
            dest=key,  # Ensure the destination uses the uppercase key
            default=effective_default,
            help=full_help
        )

    # --- Add the special OUTPUT_FILE argument (since it needs nargs='?') ---
    parser.add_argument("--output-file", type=int, nargs='?', const=900,
                        default=None,
                        dest="OUTPUT_FILE_DURATION",
                        help="Activates audiobook export mode to MP3.\n"
                             "Optional value is the maximum segment duration in seconds.\n"
                             "(default duration when switch is used: 900s).")
    # --- NEW: POSITIONAL ARGUMENT FOR INPUT FILE ---
    parser.add_argument('INPUT_FILE_PATH',
                        type=str,
                        nargs='?',
                        help="The path to the text file that the TTS reader should process (e.g., input.txt).")


    args = parser.parse_args()
    return args


def validate_pre_execution_actions(args: argparse.Namespace) -> str:
    """
    Handles utility actions (exits if done) and determines the final input file path.
    """

    # --- Utility Actions (Exits if run) ---
    if args.GENERATE_ENV or (args.OFFLINE_VOICE_ID and args.OFFLINE_VOICE_ID.upper() == "HELP"):
        # Executes action and sys.exit(0) is called inside the respective utility function
        # e.g., generate_env_file() or list_available_voices()
        if args.GENERATE_ENV:
            generate_env_file()
        else:
            list_available_voices()

        sys.exit(0)

    # --- Validation Check (Exits on Error) ---
    if args.OUTPUT_FILE_DURATION is not None and args.TTS_ENGINE == "OFFLINE":
        sys.exit(1)

    # --- Input File Determination (The new logic) ---
    if args.INPUT_FILE_PATH:
        file_path = args.INPUT_FILE_PATH
        print(f"File selected from command line: {file_path}")
    else:
        print("No input file provided via command line. Opening file selection dialog...")
        file_path = select_file()

    return file_path