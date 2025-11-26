import sys
import os
import subprocess
import argparse
import io
import platform
import tkinter as tk
from tkinter import filedialog
from typing import List


# --- Dependency check and installation ---
# TODO: mby change this approach to another - to check separately as in linux-clip-board.py
# --- Dependency check and installation ---

def install_dependencies():
    """Installs required dependencies from requirements.txt."""
    print("Required Python packages are missing. Installing dependencies now...")
    try:
        # Attempt to install everything from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies. Please run 'pip install -r requirements.txt' manually: {e}")
        sys.exit(1)


def check_and_run_dependency_install():
    """Checks for the --install-deps argument and runs the installation if present."""

    install_parser = argparse.ArgumentParser(add_help=False)
    install_parser.add_argument("--install-deps", action="store_true",
                                help="Installs dependencies from requirements.txt and exits.")

    known_args, unknown_args = install_parser.parse_known_args()

    if known_args.install_deps:
        install_dependencies()
        sys.exit(0)

    try:
        import dotenv
    except ImportError:
        print("FATAL ERROR: Core dependencies missing. Please run with '--install-deps' first.")
        sys.exit(1)

from dotenv import load_dotenv

load_dotenv()
import tqdm
import pyttsx3
import gtts
from pydub import AudioSegment
import simpleaudio as sa

try:
    from google.cloud import texttospeech
except ImportError:
    # This is fine (rly), we'll rely on the dependency check or graceful failure if G_CLOUD is chosen
    pass

# Conditional imports for Windows SAPI integration
if platform.system() == "Windows":
    try:
        import win32com.client
    except ImportError:
        print("Warning: pywin32 not available, falling back to pyttsx3 for offline on Windows.")

load_dotenv()

# --- Engine Implementations ---

class BaseTTSEngine:
    """Abstract base class for all TTS engines."""

    def __init__(self, speaking_rate: float):
        self.speaking_rate = speaking_rate

    def read_text_chunk(self, text: str):
        """Reads a single chunk of text."""
        raise NotImplementedError

class OfflineTTSEngine(BaseTTSEngine):
    """Implementation using pywin32 on Windows or pyttsx3 fallback on other OS. (Omitted for brevity, using previous implementation)"""

    def __init__(self, speaking_rate: float):
        super().__init__(speaking_rate)
        self.is_windows = platform.system() == "Windows"

        # Check if pywin32 was successfully imported
        if self.is_windows and 'win32com.client' in sys.modules:
            self._init_win32_sapi()
        else:
            self._init_pyttsx3()

    def _init_win32_sapi(self):
        """Initializes SAPI via pywin32 COM object."""
        print("Initializing OFFLINE engine (pywin32 SAPI)...")
        try:
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            sapi_rate = int((self.speaking_rate - 1.0) * 10)
            self.speaker.Rate = sapi_rate

            target_voice_id = os.getenv("OFFLINE_VOICE_ID", "").strip().strip('"')
            voices = self.speaker.GetVoices()
            voice_to_use = None

            if target_voice_id:
                voice_to_use = next((v for v in voices if target_voice_id.lower() in v.GetDescription().lower()), None)

            if voice_to_use:
                self.speaker.Voice = voice_to_use
                print(f"Using configured SAPI voice: {voice_to_use.GetDescription()}")
            else:
                czech_voice = next((v for v in voices if
                                    'czech' in v.GetDescription().lower() or 'cs-cz' in v.GetDescription().lower()),
                                   None)
                if czech_voice:
                    self.speaker.Voice = czech_voice
                    print(f"Using auto-detected SAPI voice: {czech_voice.GetDescription()}")
                else:
                    print("Warning: Czech voice not found or configured. Using default SAPI voice.")

        except Exception as e:
            print(f"Error initializing pywin32 SAPI, falling back to pyttsx3: {e}")
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        """Initializes pyttsx3 for non-Windows or as a Windows fallback."""
        print("Initializing OFFLINE engine (pyttsx3)...")
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', int(175 * self.speaking_rate))

        target_voice_id = os.getenv("OFFLINE_VOICE_ID", "").strip().strip('"')
        voices = self.engine.getProperty('voices')
        voice_to_use = None

        if target_voice_id:
            voice_to_use = next((v.id for v in voices if v.id == target_voice_id), None)

        if not voice_to_use:
            voice_to_use = next((v.id for v in voices if 'czech' in v.name.lower() or 'cs-cz' in v.id.lower()), None)

        if voice_to_use:
            self.engine.setProperty('voice', voice_to_use)
            voice_name = next((v.name for v in voices if v.id == voice_to_use), "Unknown Name")
            print(f"Using configured pyttsx3 voice: {voice_name}")
        else:
            print("Warning: Czech voice not found or configured. Using default system voice.")

    def read_text_chunk(self, text: str):
        """Reads the chunk using the initialized backend."""
        if hasattr(self, 'speaker'):
            self.speaker.Speak(text)
        elif hasattr(self, 'engine'):
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print("Error: TTS engine not initialized.")

class OnlineTTSEngine(BaseTTSEngine):
    """Implementation using gTTS for online, higher-quality TTS."""

    def __init__(self, speaking_rate: float):
        super().__init__(speaking_rate)
        print("Initializing ONLINE engine (gTTS)...")

    def read_text_chunk(self, text: str):
        """Generates MP3 and plays it using pydub/simpleaudio."""
        try:
            tts = gtts.gTTS(text, lang='cs')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            audio = AudioSegment.from_file(mp3_fp, format="mp3")

            if self.speaking_rate != 1.0:
                audio = audio.speedup(playback_speed=self.speaking_rate)

            play_obj = sa.play_buffer(
                audio.raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate
            )
            play_obj.wait_done()

        except Exception as e:
            print(f"Error processing gTTS chunk: {e}")

class GoogleCloudTTSEngine(BaseTTSEngine):
    """Implementation using Google Cloud Text-to-Speech (WaveNet/Studio)."""

    def __init__(self, speaking_rate: float):
        super().__init__(speaking_rate)
        print("Initializing ONLINE engine (Google Cloud TTS - WaveNet/Studio)...")

        voice_id = os.getenv("WAVENET_VOICE") or "cs-CZ-Wavenet-B"
        lang_code = os.getenv("LANGUAGE_CODE") or "cs-CZ"
        credentials_path = os.getenv("G_CLOUD_CREDENTIALS")

        if not voice_id or not credentials_path:
            raise ValueError("WAVENET_VOICE and G_CLOUD_CREDENTIALS must be set in .env for G_CLOUD engine.")

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google Cloud key file not found at: {credentials_path}")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_id
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )
        print(f"Using Google Cloud Voice: {voice_id} at rate {speaking_rate}")

    def read_text_chunk(self, text: str):
        """Generates high-quality speech and plays it."""
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )

            mp3_fp = io.BytesIO(response.audio_content)
            mp3_fp.seek(0)

            audio = AudioSegment.from_file(mp3_fp, format="mp3")
            play_obj = sa.play_buffer(
                audio.raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate
            )
            play_obj.wait_done()

        except Exception as e:
            print(f"Error processing Google Cloud TTS chunk: {e}")
# ------------------------------------

# --- Main Logic ---

def chunk_text(text: str, chunk_size: int) -> List[str]:
    """Splits text into chunks of maximum size, trying to split by paragraphs."""

    # Simple split by double newline (paragraph)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(current_chunk) + len(paragraph) + 2 < chunk_size:
            current_chunk += ('\n\n' + paragraph) if current_chunk else paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = paragraph

            while len(current_chunk) > chunk_size:
                break_point = current_chunk[:chunk_size].rfind('.')
                if break_point == -1:
                    break_point = chunk_size

                chunks.append(current_chunk[:break_point])
                current_chunk = current_chunk[break_point:].strip()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def main():
    """Main function to select file, parse arguments, load config, and start reading."""

    parser = argparse.ArgumentParser(
        description="A TTS script to read a text file, supporting online and offline engines.")
    parser.add_argument("--engine", type=str,
                        default=os.getenv("DEFAULT_ENGINE", "OFFLINE").upper(),
                        choices=["OFFLINE", "ONLINE", "G_CLOUD"],
                        help="Select the TTS engine: OFFLINE, ONLINE (gTTS), or G_CLOUD (WaveNet/Studio).")

    parser.add_argument("--rate", type=float,
                        default=float(os.getenv("SPEAKING_RATE", 1.0)),
                        help="The speaking rate (speed). 1.0 is normal.")
    parser.add_argument("--chunk-size", type=int,
                        default=int(os.getenv("CHUNK_SIZE", 3500)),
                        help="The maximum number of characters per segment to be processed by the TTS engine.")

    parser.add_argument("--wavenet-voice", type=str,
                        default=os.getenv("WAVENET_VOICE"),
                        help="The ID of the WaveNet/Studio voice to use (e.g., cs-CZ-Wavenet-A).")
    parser.add_argument("--credentials", type=str,
                        default=os.getenv("G_CLOUD_CREDENTIALS"),
                        help="Path to the Google Cloud JSON key file.")

    args = parser.parse_args()
    engine_choice = args.engine

    speaking_rate = args.rate
    chunk_size = args.chunk_size

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select a text file to read",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not file_path:
        print("File selection cancelled by the user. Exiting.")
        sys.exit(0)

    tts_engine = None
    try:
        if engine_choice == "OFFLINE": # working not well, because windows are stupid and are not adding langs into SAPI5
            tts_engine = OfflineTTSEngine(speaking_rate)
        elif engine_choice == "ONLINE":
            tts_engine = OnlineTTSEngine(speaking_rate)
        elif engine_choice == "G_CLOUD":
            if args.wavenet_voice:
                os.environ["WAVENET_VOICE"] = args.wavenet_voice
            if args.credentials:
                os.environ["G_CLOUD_CREDENTIALS"] = args.credentials
            if not os.getenv("WAVENET_VOICE") or not os.getenv("G_CLOUD_CREDENTIALS"):
                raise ValueError("WAVENET_VOICE and G_CLOUD_CREDENTIALS must be set for G_CLOUD engine.")

            tts_engine = GoogleCloudTTSEngine(speaking_rate)
        else:
            raise ValueError(f"Unknown engine choice: {engine_choice}")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize the selected TTS engine ({engine_choice}).")
        print(f"Details: {e}")
        sys.exit(1)

    print(f"\n--- Starting Reading (Engine: {engine_choice}) ---")
    print(f"File: {os.path.basename(file_path)}")
    print(f"Rate: {speaking_rate}")

    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    chunks = chunk_text(full_text, chunk_size)
    print(f"Total chunks to read: {len(chunks)}")

    for i, chunk in enumerate(tqdm.tqdm(chunks, desc="Reading Progress")):
        tts_engine.read_text_chunk(chunk)

    print("\n--- Reading Complete ---")


if __name__ == "__main__":
    main()