import sys
from config_definitions import CONFIG_DEFS


def generate_env_file(filename=".env"):
    """
    It is basically a .env file generator. It creates a <filename>, based on config_definitions.py file
    :param filename:
    :return: void
    """
    print(f"--- Generating {filename} file ---")

    last_group = None
    output_lines = []

    for item in CONFIG_DEFS:
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