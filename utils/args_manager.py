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
        help_text = item['help_text']

        argument_options = {
            'dest': key,
            'help': help_text,
        }

        # get safely optional parameters
        arg_type = item.get('type', str)
        options = item.get('choices')
        action = item.get('action')

        if options is not None:
            argument_options['choices'] = options

        # NOTE: action='store_true' internally sets type=bool and default=False,
        # so we DO NOT pass type or default here.
        if action is None:
            default_val = item['default']
            env_val = os.getenv(key)

            # if default_value is defined in .env -> I must use it as default in parser, otherwise will default from
            # configuration allways beat .env, and priority is: "CLI | .env | default"
            if env_val is not None:
                resolved_default = arg_type(env_val)  # PYTHON type conversion magic!
            else:
                resolved_default = default_val

            argument_options['type'] = arg_type
            argument_options['default'] = resolved_default

            argument_options['help'] = (
                f"{help_text}\n"
                f"Overrides the value from .env. (default: {resolved_default})."
            )
        else:
            argument_options['action'] = action

        argument_name = "--" + key.lower().replace('_', '-')
        parser.add_argument(argument_name, **argument_options)

    # --- NEW: POSITIONAL ARGUMENT FOR INPUT FILE ON THE END :-) ---
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

    # --- Utility Action 1: Generate .env File (Exits if run) ---
    if args.GENERATE_ENV:
        generate_env_file()
        print("\n✅ Success: .env file generated successfully in the current directory.")
        sys.exit(0)

    # --- Utility Action 2: List Offline Voices (Exits if run) ---
    if args.OFFLINE_VOICE_ID and args.OFFLINE_VOICE_ID.upper() == "HELP":
        list_available_voices()
        print("\n✅ Success: Available offline voices listed above.")
        sys.exit(0)

    # --- Validation Checks (Exits on Error) ---
    if args.OUTPUT_TYPE == "FILE" and args.TTS_ENGINE == "OFFLINE":
        print("\nERROR: Configuration Incompatibility.")
        print("The OFFLINE engine (SAPI/pyttsx3) is currently not compatible with FILE output type (Audiobook Export).")
        print("Please set OUTPUT_TYPE=AUDIO or use a different engine (ONLINE, G_CLOUD, or COQUI) for file export.")
        sys.exit(1)

    # --- COQUI Engine Specific Validations ---
    if args.TTS_ENGINE == "COQUI" and args.COQUI_SPEAKER_WAV:
        if not os.path.exists(args.COQUI_SPEAKER_WAV):
            print(f"\nERROR: The file specified for --coqui-speaker-wav was not found.")
            print(f"Path: {args.COQUI_SPEAKER_WAV}")
            sys.exit(1)
        else:
            print(f"INFO: Using custom voice for COQUI engine from: {args.COQUI_SPEAKER_WAV}")

    # --- Input File Determination ---
    if args.INPUT_FILE_PATH:
        file_path = args.INPUT_FILE_PATH
        print(f"File selected from command line: {file_path}")
    else:
        print("No input file provided via command line. Opening file selection dialog...")
        file_path = select_file()

    return file_path