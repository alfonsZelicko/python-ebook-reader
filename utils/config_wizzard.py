import questionary

def run_config_wizard(config_defs):
    print("\n--- 🧙 TTS Reader Interactive Wizard ---\n")
    results = {}

    engine_def = next(item for item in config_defs if item['key'] == 'TTS_ENGINE')
    selected_engine = questionary.select(
        "Select TTS Engine:",
        choices=engine_def['choices'],
        default=engine_def['default']
    ).ask()

    if not selected_engine: sys.exit(0)
    results['TTS_ENGINE'] = selected_engine

    for item in config_defs:
        key = item['key']
        if key == 'TTS_ENGINE': continue

        group = item['group'].upper()
        if "OFFLINE ENGINE" in group and selected_engine != "OFFLINE": continue
        if "GOOGLE CLOUD" in group and selected_engine != "G_CLOUD": continue
        if "COQUI" in group and selected_engine != "COQUI": continue

        prompt_text = f"{key} ({item['group']}):"
        default_val = str(item['default'])

        if 'choices' in item:
            val = questionary.select(
                prompt_text,
                choices=item['choices'],
                default=default_val,
                instruction=item['help_text'].split('\n')[0]
            ).ask()
        elif item.get('action') == 'store_true' or item.get('type') == bool:
            val = questionary.confirm(
                prompt_text,
                default=item['default']
            ).ask()
        else:
            val = questionary.text(
                prompt_text,
                default=default_val,
                instruction=item['help_text'].split('\n')[0]
            ).ask()

        if val is None: sys.exit(0)

        if 'type' in item and not isinstance(val, bool):
            try:
                results[key] = item['type'](val)
            except ValueError:
                results[key] = item['default']
        else:
            results[key] = val

    return results
