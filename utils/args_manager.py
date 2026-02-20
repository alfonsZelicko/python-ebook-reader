import argparse
import os
import sys

from core.tts_args_definition import TTS_CONFIG_DEFS
from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS
from utils.env_generator import generate_env_file
from utils.file_manager import select_file
from utils.voice_lister import list_available_voices
from typing import Literal


def parse_arguments(mode="TTS") -> argparse.Namespace:
    """
    Parses command-line arguments using definitions from CONFIG_DEFS,
    ensuring CLI > ENV > Default priority.
    :param mode: "TTS" or "TRANSLATOR" to determine which config to load
    :return: Parsed arguments with CLI > ENV > Default priority
    """

    # Determine config based on mode
    if mode == "TTS":
        config_defs = TTS_CONFIG_DEFS
        description = "A modular TTS reader supporting multiple engines and audiobook export."
    elif mode == "TRANSLATOR":
        config_defs = TRANSLATOR_CONFIG_DEFS
        description = "An AI-powered text translator using OpenAI's API."
    else:
        print(f"ERROR: Invalid mode '{mode}'. Must be 'TTS' or 'TRANSLATOR'.")
        sys.exit(1)

    # => `.env.tts` or `.env.translator`
    env_file = f".env.{mode.lower()}"
    
    # Load environment variables from mode-specific .env file
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("--generate-env", action="store_true",
                        dest="GENERATE_ENV",
                        help="Generates a mode-specific .env file based on the config definitions and exits.")
    
    # Store mode for later use in validation
    parser.add_argument("--mode", type=str, default=mode, dest="MODE",
                        help=argparse.SUPPRESS)  # Hidden argument to pass mode through

    # --- Iterate through definitions to build arguments ---
    for item in config_defs:

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
            # configuration allways beat .env, and the priority is: "CLI | .env.{mode} | default"
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
    args.ENV_FILENAME = env_file

    return args


def _validate_tts(args: argparse.Namespace):
    """Internal validator for TTS-specific logic and utility actions."""
    # Logic for voice listing (HELP trigger)
    is_offline_help = (args.TE == "OFFLINE" and 
                       getattr(args, 'OFF_VOICE', '').upper() == "HELP")
    
    is_coqui_help = (args.TE == "COQUI" and 
                     getattr(args, 'C_SPEAKER', '').upper() == "HELP")

    is_google_help = (args.TE == "G_CLOUD" and 
                     getattr(args, 'G_VOICE', '').upper() == "HELP")

    if is_offline_help or is_coqui_help or is_google_help:
        list_available_voices(args)
        print(f"\n✅ Success: Available {args.TE} voices listed above.")
        sys.exit(0)

    # Logic for engine compatibility
    if args.OT == "FILE" and args.TE == "OFFLINE":
        print("\nERROR: Configuration Incompatibility.")
        print("The OFFLINE engine (SAPI/pyttsx3) is currently not compatible with FILE output type.")
        sys.exit(1)

    # Logic for COQUI path validation
    if args.TE == "COQUI" and args.C_WAV:
        if not os.path.exists(args.C_WAV):
            print(f"\nERROR: The file specified for --c-wav was not found.")
            print(f"Path: {args.C_WAV}")
            sys.exit(1)


def _validate_translator(args: argparse.Namespace):
    """Internal validator for Translator-specific logic."""
    engine = args.TE.upper()

    if engine == "OFFLINE":
        print("\nERROR: Offline engine is currently not supported (it reads, not providing audio data stream.")
        sys.exit(1)
    
    if engine == "OPENAI" and not args.O_KEY:
        print("\nERROR: O_KEY not found.")
        sys.exit(1)
    
    if engine == "GEMINI" and not os.path.exists(args.G_CRED):
        print(f"\nERROR: Google Cloud credentials file not found.")
        sys.exit(1)
    
    if args.CS <= 0:
        print(f"\nERROR: Chunk size must be a positive integer.")
        sys.exit(1)


def validate_pre_execution_actions(args: argparse.Namespace, mode: Literal["TTS", "TRANSLATOR"]) -> str:
    """
    Main router for pre-execution utility actions and validations.
    """
    # Global Utility: Generate .env (.env.tts or .env.translator)
    if args.GENERATE_ENV:
        generate_env_file(mode)
        print(f"\n✅ Success: {args.ENV_FILENAME} file generated successfully.")
        sys.exit(0)

    # Mode-specific routing
    if mode == "TTS":
        _validate_tts(args)
    elif mode == "TRANSLATOR":
        _validate_translator(args)

    # Input File determination
    if args.INPUT_FILE_PATH:
        file_path = args.INPUT_FILE_PATH
        print(f"File selected from command line: {file_path}")
    else:
        print(f"No input file provided via command line. Opening selection dialog...")
        file_path = select_file()

    return file_path