import sys
from core.tts_args_definition import TTS_CONFIG_DEFS
from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS


def generate_env_file(mode="TTS"):
    """
    Generates a mode-specific .env file based on configuration definitions.
    
    Args:
        mode: "TTS" or "TRANSLATOR" to determine which config to use
        
    Output:
        - TTS mode: Creates .env.tts
        - TRANSLATOR mode: Creates .env.translator
    """
    # Determine config and filename based on mode
    if mode == "TTS":
        config_defs = TTS_CONFIG_DEFS
        filename = ".env.tts"
    elif mode == "TRANSLATOR":
        config_defs = TRANSLATOR_CONFIG_DEFS
        filename = ".env.translator"
    else:
        print(f"ERROR: Invalid mode '{mode}'. Must be 'TTS' or 'TRANSLATOR'.")
        sys.exit(1)
    
    print(f"--- Generating {filename} file for {mode} mode ---")

    last_group = None
    output_lines = []

    for item in config_defs:
        group = item['group']
        key = item['key']
        default_val = item['default']
        help_text = item['help_text']

        if group != last_group:
            output_lines.append("\n#" + "*" * 65)
            output_lines.append(f"# {group}")
            output_lines.append("#" + "*" * 65)
            last_group = group

        # Format the help text for comments
        comment = "# " + help_text.replace('\n', '\n# ')
        output_lines.append(comment)

        # Ensure string defaults are not wrapped, but special types like paths are treated as strings!
        output_lines.append(f"{key}={default_val}")

    try:
        with open(filename, 'w') as f:
            f.write('\n'.join(output_lines).strip())
        print(f"Successfully generated configuration file: {filename}")
    except IOError as e:
        print(f"Error writing file {filename}: {e}")
        sys.exit(1)