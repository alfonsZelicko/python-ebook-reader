import pyttsx3

def list_available_voices():
    """Lists all available voices and their IDs for the OFFLINE_VOICE_ID configuration."""
    print("--- Discovering Available OFFLINE Voices ---")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        if not voices:
            print("Error: No voices were found on your system.")
            return

        print(f"Found {len(voices)} voices. Listing details:")
        print("-" * 50)

        for i, voice in enumerate(voices):
            # pyttsx3/SAPI format:
            print(f"[{i}] Name: {voice.name}")
            print(f"    ID: {voice.id}")
            print(f"    Lang: {voice.languages}")
            print(f"    Gender: {voice.gender}")
            print("-" * 50)

    except Exception as e:
        print(f"An error occurred during pyttsx3 initialization: {e}")


if __name__ == "__main__":
    list_available_voices()