import argparse
import os
import sys
from pathlib import Path
from typing import Literal

import strawberry

from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS
from core.tts_args_definition import TTS_CONFIG_DEFS
from utils.env_generator import generate_env_file
from utils.file_manager import select_file
from utils.voice_lister import list_available_voices


def resolve_args(mode: str, provided_data: dict = None) -> argparse.Namespace:
    """
    Core logic to resolve configuration values based on priority:
    Provided (CLI/GraphQL) > Environment (.env) > Default.
    """
    config_defs = TTS_CONFIG_DEFS if mode == "TTS" else TRANSLATOR_CONFIG_DEFS
    env_file = f".env.{mode.lower()}"

    if os.path.exists(env_file):
        from dotenv import load_dotenv

        load_dotenv(env_file)

    args = argparse.Namespace()
    provided_data = provided_data or {}

    for item in config_defs:
        key = item["key"]
        arg_type = item.get("type", str)
        action = item.get("action")

        # 1. Priority: Provided data (from CLI parser or GraphQL dict)
        val = provided_data.get(key)

        # 2. Priority: Environment variable
        if val is None or val is strawberry.UNSET:
            env_val = os.getenv(key)
            if env_val is not None:
                if action == "store_true" or arg_type == bool:
                    val = env_val.lower() in ("true", "1", "yes")
                else:
                    val = arg_type(env_val)

        # 3. Priority: Default value from definition
        if val is None:
            val = item.get("default")

        setattr(args, key, val)

    return args


def parse_arguments(mode="TTS") -> argparse.Namespace:
    """
    Parses command-line arguments and merges them with ENV/Default priorities.
    """
    if mode == "TTS":
        config_defs = TTS_CONFIG_DEFS
        description = (
            "A modular TTS reader supporting multiple engines and audiobook export."
        )
    elif mode == "TRANSLATOR":
        config_defs = TRANSLATOR_CONFIG_DEFS
        description = "An AI-powered text translator using OpenAI's API."
    else:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'TTS' or 'TRANSLATOR'.")

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--generate-env",
        action="store_true",
        dest="GENERATE_ENV",
        help="Generates a mode-specific .env file based on the config definitions and exits.",
    )

    parser.add_argument(
        "--mode", type=str, default=mode, dest="MODE", help=argparse.SUPPRESS
    )

    # Build CLI parser based on definitions
    for item in config_defs:
        key = item["key"]
        help_text = item["help_text"]
        arg_type = item.get("type", str)
        action = item.get("action")

        argument_options = {"dest": key, "help": help_text}
        if item.get("choices"):
            argument_options["choices"] = item["choices"]

        if action:
            argument_options["action"] = action
        else:
            argument_options["type"] = arg_type

        argument_name = "--" + key.lower().replace("_", "-")
        parser.add_argument(argument_name, **argument_options)

    parser.add_argument(
        "INPUT_FILE_PATH",
        type=str,
        nargs="?",
        help="The path to the text file to process.",
    )

    # Parse CLI (values will be None if not explicitly provided)
    cli_args = parser.parse_args()

    # Merge CLI with ENV and Defaults
    # Filter out None values from cli_args so they don't override ENV
    provided = {k: v for k, v in vars(cli_args).items() if v is not None}

    final_args = resolve_args(mode, provided_data=provided)
    final_args.INPUT_FILE_PATH = cli_args.INPUT_FILE_PATH
    final_args.GENERATE_ENV = cli_args.GENERATE_ENV
    final_args.ENV_FILENAME = f".env.{mode.lower()}"

    return final_args


def _validate_tts(args: argparse.Namespace):
    is_offline_help = (
        args.TE == "OFFLINE" and getattr(args, "OFF_VOICE", "").upper() == "HELP"
    )
    is_coqui_help = (
        args.TE == "COQUI" and getattr(args, "C_SPEAKER", "").upper() == "HELP"
    )
    is_google_help = (
        args.TE == "G_CLOUD" and getattr(args, "G_VOICE", "").upper() == "HELP"
    )

    if is_offline_help or is_coqui_help or is_google_help:
        list_available_voices(args)
        print(f"\n[OK] Success: Available {args.TE} voices listed above.")
        sys.exit(0)

    if args.OT == "FILE" and args.TE == "OFFLINE":
        raise ValueError("OFFLINE engine is not compatible with FILE output type.")

    if args.TE == "COQUI" and getattr(args, "C_WAV", None):
        if not os.path.exists(args.C_WAV):
            raise FileNotFoundError(f"Coqui wav file not found: {args.C_WAV}")


def _validate_translator(args: argparse.Namespace):
    """

    :param args:
    :return:
    """
    engine = args.TE.upper()
    if engine == "OFFLINE":
        raise ValueError("Offline engine is not supported for translation.")

    if engine == "OPENAI" and not getattr(args, "O_KEY", None):
        raise ValueError("OpenAI API key (O_KEY) is missing.")

    if engine == "GEMINI" and not getattr(args, "G_KEY", None):
        raise ValueError("Google Cloud credentials (G_KEY) missing.")

    if int(args.CS) <= 0:
        raise ValueError("Chunk size (CS) must be a positive integer.")


def validate_pre_execution_actions(
    args: argparse.Namespace, mode: Literal["TTS", "TRANSLATOR"]
) -> Path:
    if getattr(args, "GENERATE_ENV", False):
        generate_env_file(mode)
        print(f"\n[OK] Success: {args.ENV_FILENAME} file generated successfully.")
        sys.exit(0)

    if mode == "TTS":
        _validate_tts(args)
    elif mode == "TRANSLATOR":
        _validate_translator(args)

    file_path = args.INPUT_FILE_PATH
    if not file_path:
        print(f"No input file provided. Opening selection dialog...")
        file_path = select_file()

    return Path(file_path)
