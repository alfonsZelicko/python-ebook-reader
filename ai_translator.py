from dotenv import load_dotenv

from core.translator_engines import initialize_translation_engine
from core.translator_processor import start_translation
from utils.args_manager import parse_arguments, validate_pre_execution_actions

# Load translator-specific environment variables
load_dotenv('.env.translator')


def main():
    """The main entry point, orchestrating the script's execution translation flow."""

    # 1. PARSE ARGUMENTS
    args = parse_arguments(mode="TRANSLATOR")

    # 2. PRE-EXECUTION VALIDATION & ACTIONS (Handles --generate-env, file selection, validation)
    file_path = validate_pre_execution_actions(args, mode="TRANSLATOR")

    # 3. ENGINE INITIALIZATION
    translation_engine = initialize_translation_engine(args)

    # 4. EXECUTION
    start_translation(file_path, translation_engine, args)

    print("\nScript execution finished.")


if __name__ == "__main__":
    main()