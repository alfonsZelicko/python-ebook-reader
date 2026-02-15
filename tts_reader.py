import sys

from dotenv import load_dotenv

from core.tts_engines import initialize_tts_engine
from core.tts_processor import start_processing
from utils.args_manager import parse_arguments, validate_pre_execution_actions
from core.tts_args_definition import TTS_CONFIG_DEFS;

# Load TTS-specific environment variables
load_dotenv('.env.tts')

def main():
    """The main entry point, orchestrating the script's execution reading flow."""

    # PARSE ARGUMENTS
    args = parse_arguments(mode="TTS")

    # PRE-EXECUTION VALIDATION & ACTIONS (Handles --generate-env, --offline-voice HELP, yada yada yada...)
    file_path = validate_pre_execution_actions(args, mode="TTS")

    # ENGINE INITIALIZATION
    tts_engine = initialize_tts_engine(args)

    # EXECUTION
    start_processing(file_path, tts_engine, args)

    print("\nScript execution finished.")


if __name__ == "__main__":
    main()