def list_offline_voices():
    """Import and list SAPI5 voices from pyttsx3."""
    try:
        import pyttsx3
        print("\n--- Discovering Available OFFLINE Voices (SAPI5/pyttsx3) ---")
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        if not voices:
            print("ERROR: No voices were found on your system.")
            return

        print(f"Found {len(voices)} voices. Listing details:")
        print("-" * 50)
        for i, voice in enumerate(voices):
            print(f"[{i}] Name: {voice.name}")
            print(f"    ID: {voice.id}")
            print("-" * 50)
    except ImportError:
        print("ERROR: 'pyttsx3' library is not installed. Please install: pip install pyttsx3")
    except Exception as e:
        print(f"An error occurred during offline voice discovery: {e}")

def list_coqui_voices(model_name: str):
    """Import and list speakers for Coqui XTTS v2 models."""
    try:
        from TTS.api import TTS
        print(f"\n--- Discovering Available COQUI Voices ---")
        print(f"Model: {model_name}")

        if "xtts_v2" in model_name.lower():
            print("Loading model metadata to fetch speakers (this may take a moment)...")
            tts = TTS(model_name=model_name, progress_bar=False, gpu=False)
            
            if hasattr(tts, 'speakers') and tts.speakers:
                print(f"Found {len(tts.speakers)} speakers in XTTS v2:")
                print("-" * 50)
                for speaker in sorted(tts.speakers):
                    print(f" - {speaker}")
                print("-" * 50)
            else:
                print("This XTTS model doesn't seem to have multiple speaker IDs.")
        else:
            print(f"INFO: Model '{model_name}' is a single-voice model.")
            print("There are no alternative Speaker IDs for this model.")
    except ImportError:
        print("ERROR: 'TTS' library not found. Please install: pip install coqui-tts")
    except Exception as e:
        print(f"Could not list Coqui speakers: {e}")

def list_available_voices(args):
    """Router function to call the specific voice lister based on the engine."""
    engine_choice = args.TTS_ENGINE.upper()

    if engine_choice == "OFFLINE":
        list_offline_voices()
    elif engine_choice == "COQUI":
        model_name = getattr(args, 'COQUI_MODEL_NAME', 'tts_models/multilingual/multi-dataset/xtts_v2')
        list_coqui_voices(model_name)
    elif engine_choice == "G_CLOUD":
        print("\n--- GOOGLE CLOUD TTS Voices ---")
        print("\nFull list at: https://cloud.google.com/text-to-speech/docs/voices")
    else:
        print(f"Voice listing is not supported for engine: {engine_choice}")