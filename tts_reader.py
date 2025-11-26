import sys
import os
import subprocess
import argparse
import io
import platform
import tkinter as tk
from tkinter import filedialog
from typing import List
from abc import ABC, abstractmethod

# Conditional imports for environment loading
try:
    import dotenv
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("FATAL ERROR: Core dependencies missing (dotenv). Please run with '--install-deps' first.")
    sys.exit(1)


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


# Check for core packages needed for the script to run
try:
    import tqdm
    import pyttsx3
    import gtts
    from pydub import AudioSegment
    from pydub.playback import play
    import simpleaudio as sa
except ImportError:
    # If core packages are missing, the script cannot proceed.
    print("FATAL ERROR: Core packages (tqdm, pyttsx3, gtts, pydub, simpleaudio) missing.")
    print("Please run with '--install-deps' first.")
    sys.exit(1)

# Conditional imports for Windows SAPI integration
if platform.system() == "Windows":
    try:
        import win32com.client
    except ImportError:
        # This is a warning, not fatal, as we fall back to pyttsx3
        print("Warning: pywin32 not available, falling back to pyttsx3 for offline on Windows.")

# Conditional imports for Google Cloud TTS
try:
    from google.cloud import texttospeech
except ImportError:
    # This is fine, we'll rely on graceful failure if G_CLOUD is chosen
    pass


# --- Engine Implementations ---

class BaseTTSEngine(ABC):
    """Abstract base class for all TTS (Text-to-Speech) engines."""

    def __init__(self, speaking_rate: float):
        self.speaking_rate = speaking_rate

    @abstractmethod
    def read_text_chunk(self, text: str):
        """
        Abstract method: Generates audio for a chunk of text.
        In 'reading' mode, it should play the audio.
        In 'saving' mode, it must return an AudioSegment.
        """
        pass

    def _play_audio(self, audio_segment: AudioSegment):
        """Helper method for playing an audio segment using pydub/ffplay."""
        try:
            # play() requires FFmpeg/ffplay in system PATH
            play(audio_segment)
        except FileNotFoundError:
            print("CRITICAL ERROR: Failed to play audio. FFplay/FFmpeg not found.")
            print("Please ensure FFmpeg is installed and added to your system's PATH.")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to play audio due to an unexpected error. Detail: {e}")


class OfflineTTSEngine(BaseTTSEngine):
    """Implementation using pywin32 on Windows or pyttsx3 fallback on other OS."""

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
        """Reads the chunk using the initialized backend. Does NOT return AudioSegment."""
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

    def read_text_chunk(self, text: str) -> AudioSegment:
        """Generates MP3 and returns it as an AudioSegment."""
        try:
            tts = gtts.gTTS(text, lang='cs')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            audio = AudioSegment.from_file(mp3_fp, format="mp3")

            if self.speaking_rate != 1.0:
                # Speed manipulation using pydub
                audio = audio.speedup(playback_speed=self.speaking_rate)

            # NOTE: We play here only if called in 'reading' mode (not saving mode)
            if 'save_output' not in sys.argv:  # Heuristic to check if we are in reading mode
                self._play_audio(audio)

            return audio

        except Exception as e:
            print(f"Error processing gTTS chunk: {e}")
            raise  # Re-raise for graceful error handling in main


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

        # Check if the necessary library is imported
        if 'texttospeech' not in sys.modules:
            raise ImportError("Google Cloud TTS client not found. Ensure 'google-cloud-texttospeech' is installed.")

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

    def read_text_chunk(self, text: str) -> AudioSegment:
        """Generates high-quality speech and returns it as an AudioSegment."""
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

            # NOTE: We play here only if called in 'reading' mode (not saving mode)
            if 'save_output' not in sys.argv:
                self._play_audio(audio)

            return audio

        except Exception as e:
            print(f"Error processing Google Cloud TTS chunk: {e}")
            raise


class CoquiTTSEngine(BaseTTSEngine):
    """Implementation of offline TTS engine using Coqui TTS with lazy loading."""

    def __init__(self, speaking_rate: float):
        super().__init__(speaking_rate)

        # LAZY LOADING: Import heavy dependencies only when this class is instantiated
        try:
            import torch
            from TTS.api import TTS
        except ImportError:
            raise RuntimeError("Coqui TTS dependencies (torch, TTS) not found.")

        self.model_name = os.getenv("COQUI_MODEL_NAME", "tts_models/en/ljspeech/vits")
        self.speaker_name = os.getenv("COQUI_SPEAKER_NAME", "")
        self.sample_rate = int(os.getenv("COQUI_SAMPLE_RATE", 22050))

        # Explicitly setting device to CPU for stability (can be changed to 'cuda' if necessary)
        # device = "cuda" if torch.cuda.is_available() else "cpu"
        device = "cpu"

        print(f"Coqui TTS: Using device {device}. Loading model {self.model_name}...")

        try:
            self.tts = TTS(
                model_name=self.model_name,
                progress_bar=True
            ).to(device)

        except Exception as e:
            raise RuntimeError(
                f"Failed to load Coqui TTS model '{self.model_name}'. Check model name and installation. Detail: {e}")

    def read_text_chunk(self, text: str) -> AudioSegment:
        """Generates audio data, adjusts speed, and returns it as an AudioSegment."""
        temp_file = "temp_coqui.wav"

        tts_kwargs = {
            "text": text,
            "file_path": temp_file
        }

        # Conditionally pass the speaker argument to prevent errors on single-speaker models (VITS)
        if self.speaker_name and self.speaker_name.lower() != 'none':
            tts_kwargs["speaker"] = self.speaker_name

        try:
            self.tts.tts_to_file(**tts_kwargs)

            audio = AudioSegment.from_file(temp_file, format="wav")

            if self.speaking_rate != 1.0:
                audio = audio.speedup(playback_speed=self.speaking_rate)

            # NOTE: We play here only if called in 'reading' mode (not saving mode)
            if 'save_output' not in sys.argv:
                self._play_audio(audio)

            return audio

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


# ------------------------------------

# --- Main Logic ---

def chunk_text(text: str, chunk_size: int) -> List[str]:
    """Splits text into chunks of maximum size, trying to split by paragraphs and sentences."""

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

            # Handle paragraphs longer than chunk_size by splitting at sentence end (.!?)
            while len(current_chunk) > chunk_size:
                # Find the last sentence end before chunk_size
                break_point = max(
                    current_chunk[:chunk_size].rfind('.'),
                    current_chunk[:chunk_size].rfind('!'),
                    current_chunk[:chunk_size].rfind('?')
                )

                # If no sentence break found, or found near the start, just split at chunk_size
                if break_point < chunk_size // 2 or break_point == -1:
                    break_point = chunk_size

                chunks.append(current_chunk[:break_point].strip())
                current_chunk = current_chunk[break_point:].strip()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def main():
    """Main function to select file, parse arguments, load config, and start reading or generating audio."""

    check_and_run_dependency_install()

    parser = argparse.ArgumentParser(
        description="A TTS script to read a text file, supporting online and offline engines. Can generate audio files (--save-output).")
    parser.add_argument("--engine", type=str,
                        default=os.getenv("DEFAULT_ENGINE", "OFFLINE").upper(),
                        choices=["OFFLINE", "ONLINE", "G_CLOUD", "COQUI"],
                        help="Select the TTS engine: OFFLINE, ONLINE (gTTS), G_CLOUD (WaveNet), or COQUI (Offline AI).")

    parser.add_argument("--rate", type=float,
                        default=float(os.getenv("SPEAKING_RATE", 1.0)),
                        help="The speaking rate (speed). 1.0 is normal.")
    parser.add_argument("--chunk-size", type=int,
                        default=int(os.getenv("CHUNK_SIZE", 3500)),
                        help="The maximum number of characters per segment to be processed by the TTS engine.")

    # --- New Arguments for Saving ---
    parser.add_argument("--save-output", action="store_true",
                        help="If set, generates MP3 files instead of reading the text aloud.")
    parser.add_argument("--output-duration", type=int,
                        default=int(os.getenv("OUTPUT_DURATION_SEC", 600)),
                        help="Duration of each output MP3 file in seconds (e.g., 600 for 10 min). (Requires --save-output)")
    parser.add_argument("--output-dir", type=str,
                        default=os.getenv("OUTPUT_DIR", "./output_audio"),
                        help="Directory to save the resulting audio files. (Requires --save-output)")

    # Engine specific arguments
    parser.add_argument("--wavenet-voice", type=str,
                        default=os.getenv("WAVENET_VOICE"),
                        help="G_CLOUD: The ID of the WaveNet/Studio voice to use.")
    parser.add_argument("--credentials", type=str,
                        default=os.getenv("G_CLOUD_CREDENTIALS"),
                        help="G_CLOUD: Path to the Google Cloud JSON key file.")
    parser.add_argument("--coqui-model", type=str,
                        default=os.getenv("COQUI_MODEL_NAME"),
                        help="COQUI: Name of the TTS model to load.")
    parser.add_argument("--coqui-speaker", type=str,
                        default=os.getenv("COQUI_SPEAKER_NAME"),
                        help="COQUI: Specific speaker name within the model.")
    parser.add_argument("--coqui-samplerate", type=int,
                        default=os.getenv("COQUI_SAMPLE_RATE"),
                        help="COQUI: Sample rate for audio output.")

    args = parser.parse_args()
    engine_choice = args.engine
    speaking_rate = args.rate
    chunk_size = args.chunk_size
    save_output = args.save_output

    if save_output and engine_choice == "OFFLINE":
        print("ERROR: OFFLINE engine (SAPI/pyttsx3) does not support file saving.")
        sys.exit(1)

    # Use Tkinter to open file dialog
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

    # --- Apply Environment Overrides from CLI ---
    if args.coqui_model:
        os.environ["COQUI_MODEL_NAME"] = args.coqui_model
    if args.coqui_speaker:
        os.environ["COQUI_SPEAKER_NAME"] = args.coqui_speaker
    if args.coqui_samplerate:
        os.environ["COQUI_SAMPLE_RATE"] = str(args.coqui_samplerate)
    if args.wavenet_voice:
        os.environ["WAVENET_VOICE"] = args.wavenet_voice
    if args.credentials:
        os.environ["G_CLOUD_CREDENTIALS"] = args.credentials

    # --- Engine Initialization ---
    tts_engine = None
    try:
        if engine_choice == "OFFLINE":
            tts_engine = OfflineTTSEngine(speaking_rate)
        elif engine_choice == "ONLINE":
            tts_engine = OnlineTTSEngine(speaking_rate)
        elif engine_choice == "G_CLOUD":
            tts_engine = GoogleCloudTTSEngine(speaking_rate)
        elif engine_choice == "COQUI":
            tts_engine = CoquiTTSEngine(speaking_rate)
        else:
            raise ValueError(f"Unknown engine choice: {engine_choice}")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize the selected TTS engine ({engine_choice}).")
        print(f"Details: {e}")
        sys.exit(1)

    # --- Text Loading and Chunking ---
    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    chunks = chunk_text(full_text, chunk_size)

    # --- MODE 1: DIRECT READING (Playback) ---
    if not save_output:
        print(f"\n--- Starting Reading (Engine: {engine_choice}) ---")
        print(f"File: {os.path.basename(file_path)}")
        print(f"Rate: {speaking_rate}")
        print(f"Total chunks to read: {len(chunks)}")

        # In reading mode, read_text_chunk handles both generation and playback
        for chunk in tqdm.tqdm(chunks, desc="Reading Progress"):
            tts_engine.read_text_chunk(chunk)
        print("\n--- Reading Complete ---")
        return

    # --- MODE 2: AUDIO BOOK GENERATION (Saving) ---
    else:
        output_duration_ms = args.output_duration * 1000
        current_part_number = 1
        current_audio_segment = AudioSegment.empty()
        base_file_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = args.output_dir

        os.makedirs(output_dir, exist_ok=True)

        print(f"\n--- Starting Audio Book Generation (Engine: {engine_choice}) ---")
        print(f"Output Directory: {output_dir}")
        print(f"Target duration per file: {args.output_duration} seconds.")
        print(f"Total chunks to process: {len(chunks)}")

        for chunk in tqdm.tqdm(chunks, desc="Generating Audio Parts"):
            try:
                # read_text_chunk returns AudioSegment in this mode
                chunk_segment = tts_engine.read_text_chunk(chunk)

                # Add segment to the current part
                current_audio_segment += chunk_segment

            except Exception as e:
                print(f"\nERROR processing chunk. Skipping this chunk. Detail: {e}")
                continue

            # Check and Save Part
            if len(current_audio_segment) >= output_duration_ms:
                output_filename = f"{current_part_number:02d}_{base_file_name}.mp3"
                output_path = os.path.join(output_dir, output_filename)

                print(
                    f"\nSaving part {current_part_number} (Duration: {len(current_audio_segment) / 1000:.1f}s) to {output_path}")

                try:
                    current_audio_segment.export(output_path, format="mp3", bitrate="192k")
                except FileNotFoundError:
                    print("\nCRITICAL EXPORT ERROR: FFmpeg not found for MP3 export!")
                    print("Please install FFmpeg and ensure it's in PATH to save files.")
                    sys.exit(1)

                # Reset for the next part
                current_audio_segment = AudioSegment.empty()
                current_part_number += 1

        # Save remaining part
        if current_audio_segment:
            output_filename = f"{current_part_number:02d}_{base_file_name}.mp3"
            output_path = os.path.join(output_dir, output_filename)

            print(
                f"\nSaving final part {current_part_number} (Duration: {len(current_audio_segment) / 1000:.1f}s) to {output_path}")
            current_audio_segment.export(output_path, format="mp3", bitrate="192k")

        print("\n--- Audio Book Generation Complete ---")


if __name__ == "__main__":
    main()