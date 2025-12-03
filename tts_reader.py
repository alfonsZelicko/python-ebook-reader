from dotenv import load_dotenv

# --- PROJECT MODULES ---
from core.engines import initialize_tts_engine
from core.processor import start_processing
from utils.args_manager import parse_arguments, validate_pre_execution_actions
from utils.file_manager import select_file

# Load variables from .env file into environment variables
load_dotenv()


def main():
    """The main entry point, orchestrating the script's execution flow."""

    # 1. PARSE ARGUMENTS
    args = parse_arguments()

    # 2. PRE-EXECUTION VALIDATION & ACTIONS (Handles --generate-env, --offline-voice HELP, and incompatibilities)
    file_path = validate_pre_execution_actions(args)

    # 3. ENGINE INITIALIZATION
    tts_engine = initialize_tts_engine(args)

    # 4. EXECUTION
    start_processing(file_path, tts_engine, args)

    print("\nScript execution finished.")


if __name__ == "__main__":
    main()