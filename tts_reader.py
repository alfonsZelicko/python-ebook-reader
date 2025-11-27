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

# ENGINE IMPLEMENTATIONS ##

class BaseTTSEngine:
    """Abstract base class for all TTS engines."""

    def __init__(self, speaking_rate: float):
        self.speaking_rate = speaking_rate

    def generate_audio_chunk(self, text: str):
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

    def generate_audio_chunk(self, text: str):
        """Reads the chunk using the initialized backend. in OFFLINE mod we will only read."""
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

    def generate_audio_chunk(self, text: str):
        """Generates MP3 and plays it using pydub/simpleaudio."""
        try:
            tts = gtts.gTTS(text, lang='cs')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            audio = AudioSegment.from_file(mp3_fp, format="mp3")

            if self.speaking_rate != 1.0:
                audio = audio.speedup(playback_speed=self.speaking_rate)

            # play_obj = sa.play_buffer(
            #     audio.raw_data,
            #     num_channels=audio.channels,
            #     bytes_per_sample=audio.sample_width,
            #     sample_rate=audio.frame_rate
            # )
            # play_obj.wait_done()

            return audio

        except Exception as e:
            print(f"Error processing gTTS chunk: {e}")
            raise

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

    def generate_audio_chunk(self, text: str):
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
            # play_obj = sa.play_buffer(
            #     audio.raw_data,
            #     num_channels=audio.channels,
            #     bytes_per_sample=audio.sample_width,
            #     sample_rate=audio.frame_rate
            # )
            # play_obj.wait_done()

            return audio

        except Exception as e:
            print(f"Error processing Google Cloud TTS chunk: {e}")
            raise

# PROGRESS MANAGER ##

import json
from typing import Dict, Any

class ProgressManager:
    """Manages reading, writing, and deleting the .progress file for state restoration."""

    def __init__(self, file_path: str, args: argparse.Namespace):
        """Initializes manager paths and determines the output folder."""

        # Příklad: /cesta/k/test.txt -> 'test'
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        # Příklad: /cesta/k/test.txt -> /cesta/k/
        file_dir = os.path.dirname(file_path) or '.'

        # Výstupní složka: /cesta/k/test/
        self.output_dir = os.path.join(file_dir, base_name)

        # Progress soubor: /cesta/k/test/test.progress
        self.progress_file = os.path.join(self.output_dir, f"{base_name}.progress")

        self.current_args = vars(args)  # Uložíme aktuální argumenty jako slovník
        self.state: Dict[str, Any] = {}  # Uložený stav

    def load_state(self) -> bool:
        """Attempts to load the progress state from disk."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)

                print(f"\n--- RESTORING STATE from {os.path.basename(self.progress_file)} ---")

                # Přepíšeme aktuální parametry těmi uloženými
                for key, value in self.state['parameters'].items():
                    # Nechceme přepsat ty argumenty, které nejsou v CLI (např. 'current_mp3_index')
                    if key in self.current_args:
                        print(f"   [OVERRIDE] {key.upper()}: {self.current_args[key]} -> {value}")
                        self.current_args[key] = value

                print("-----------------------------------------------------")
                return True

            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                print(f"Warning: Corrupted or unreadable progress file found. Starting fresh. ({e})")
                self.delete_state()
                return False

        return False

    def update_state(self, last_chunk_index: int, last_mp3_index: int):
        """Saves the current progress state to disk."""

        # 1. Zajistíme existenci složky
        os.makedirs(self.output_dir, exist_ok=True)

        # 2. Uložíme kompletní stav
        self.state = {
            # Uložíme parametry, pod kterými se generuje (pro obnovu)
            'parameters': self.current_args,
            # Index posledního CHUNKU, který byl úspěšně zařazen do MP3
            'last_chunk_index': last_chunk_index,
            # Index posledního MP3, který byl ÚSPĚŠNĚ UZAVŘEN (dokončen)
            'last_mp3_index': last_mp3_index
        }

        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to save progress file: {e}")

    def delete_state(self):
        """Deletes the progress file upon 100% completion."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print(f"Progress file deleted: {os.path.basename(self.progress_file)}")

    @property
    def is_restored(self) -> bool:
        return 'parameters' in self.state

    # Funkce pro získání indexů
    @property
    def get_last_chunk_index(self) -> int:
        return self.state.get('last_chunk_index', -1)

    @property
    def get_last_mp3_index(self) -> int:
        return self.state.get('last_mp3_index', 0)

    # Funkce pro získání názvu souboru pro další MP3
    def get_next_mp3_filename(self, mp3_index: int) -> str:
        base_name = os.path.splitext(os.path.basename(self.progress_file))[0]
        # Formát: 01_test.mp3
        return os.path.join(self.output_dir, f"{mp3_index:02d}_{base_name}.mp3")

# ------------------------------------

## UTILITIES ##

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

def parse_arguments():
    """Parses command-line arguments and returns the populated args object."""
    parser = argparse.ArgumentParser(
        description="A TTS script to read a text file, supporting online and offline engines.")

    parser.add_argument("--output-file", type=int, nargs='?', const=900, default=None,
                        help="Activates audiobook export mode. Value is the max duration of each MP3 segment in seconds (default: 900).")
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

    return parser.parse_args()

def select_file():
    """Opens a file dialog for user file selection."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    file_path = filedialog.askopenfilename(
        title="Select a text file to read",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not file_path:
        print("File selection cancelled by the user. Exiting.")
        sys.exit(0)

    return file_path

def initialize_tts_engine(args):
    """Initializes and returns the appropriate TTS engine based on arguments."""

    engine_choice = args.engine
    speaking_rate = args.rate

    try:
        if engine_choice == "OFFLINE":
            return OfflineTTSEngine(speaking_rate)

        elif engine_choice == "ONLINE":
            return OnlineTTSEngine(speaking_rate)

        elif engine_choice == "G_CLOUD":
            wavenet_voice = args.wavenet_voice
            credentials = args.credentials
            if wavenet_voice:
                os.environ["WAVENET_VOICE"] = wavenet_voice
            if credentials:
                os.environ["G_CLOUD_CREDENTIALS"] = credentials

            if not (wavenet_voice or os.getenv("WAVENET_VOICE")) or \
                    not (credentials or os.getenv("G_CLOUD_CREDENTIALS")):
                raise ValueError(
                    "WAVENET_VOICE and G_CLOUD_CREDENTIALS must be set for G_CLOUD engine (either via CLI or environment).")

            return GoogleCloudTTSEngine(speaking_rate)

        else:
            raise ValueError(f"Unknown engine choice: {engine_choice}")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize the selected TTS engine ({engine_choice}).")
        print(f"Details: {e}")
        sys.exit(1)

def process_reading(file_path, engine, chunk_size):
    """Handles file loading, text chunking, and the main reading loop."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)

    chunks = chunk_text(full_text, chunk_size)
    print(f"Total chunks to read: {len(chunks)}")

    # We must ensure the engine supports playback if it's not OFFLINE (which handles playback internally)
    is_offline_engine = isinstance(engine, OfflineTTSEngine)

    for i, chunk in enumerate(tqdm.tqdm(chunks, desc="Reading Progress")):
        if is_offline_engine:
            # OFFLINE engine handles playback internally and doesn't return data
            engine.read_text_chunk(chunk)
        else:
            # ONLINE/GCLOUD engine generates audio data
            audio_data = engine.generate_audio_chunk(chunk)

            # Explicitly play the returned audio data
            play_obj = sa.play_buffer(
                audio_data.raw_data,
                num_channels=audio_data.channels,
                bytes_per_sample=audio_data.sample_width,
                sample_rate=audio_data.frame_rate
            )
            play_obj.wait_done()

    print("\n--- Reading Complete ---")

def export_audiobook(file_path, tts_engine, args):
    """
    Handles file loading, chunking, audiobook segment generation,
    and progress state management. This function is for silent export only.
    """

    # --- 1. INITIALIZE PROGRESS MANAGER AND LOAD STATE ---
    manager = ProgressManager(file_path, args)
    manager.load_state()

    # Note: If state was loaded, manager.current_args now holds the restored parameters,
    # and tts_engine should be re-initialized if its state (e.g., rate) relies on args.
    # Since we re-initialize the manager after parsing, let's trust the manager logic
    # and re-initialize the engine here to ensure consistency if rate was changed.
    # We will skip re-initialization here for simplicity, assuming rate is handled inside engine init.

    # --- 2. LOAD TEXT AND DETERMINE STARTING POINT ---
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except Exception as e:
        print(f"Error reading source file {file_path}: {e}")
        sys.exit(1)

    all_chunks = chunk_text(full_text, args.chunk_size)
    total_chunks = len(all_chunks)

    # Determine where to start reading from based on progress file
    start_chunk_index = manager.get_last_chunk_index + 1
    current_mp3_index = manager.get_last_mp3_index + 1

    # Check if all chunks were already processed
    if start_chunk_index >= total_chunks:
        print("INFO: All chunks have been processed. Starting cleanup.")
        manager.delete_state()
        return

    print(f"Total chunks to read: {total_chunks}. Starting from chunk index {start_chunk_index}")

    # --- 3. MAIN EXPORT LOOP ---

    # Duration limit in milliseconds
    max_duration_ms = manager.current_args['output_file'] * 1000

    # Start accumulation from the first unprocessed chunk
    chunks_to_process = all_chunks[start_chunk_index:]

    current_segment_audio = AudioSegment.empty()
    last_processed_chunk_index = start_chunk_index - 1

    # We use tqdm only over the remaining chunks to process
    for i, chunk in enumerate(tqdm.tqdm(chunks_to_process, desc="Export Progress")):

        # Calculate the absolute index within the full text chunk list
        absolute_chunk_index = start_chunk_index + i

        try:
            # Generate audio data (this is now silent)
            new_audio_chunk = tts_engine.generate_audio_chunk(chunk)

            # --- DECISION POINT: CHECK DURATION LIMIT ---

            # Check if adding the new chunk would exceed the max duration
            if (len(current_segment_audio) + len(new_audio_chunk) > max_duration_ms and
                    len(current_segment_audio) > 0):
                # 1. LIMIT EXCEEDED: Save the current accumulated segment (before adding the new one)
                output_filename = manager.get_next_mp3_filename(current_mp3_index)

                print(
                    f"\n[SAVE] Saving segment {current_mp3_index} to {os.path.basename(output_filename)} (Duration: {len(current_segment_audio) / 1000:.2f}s)")

                # Export the completed audio file
                current_segment_audio.export(output_filename, format="mp3")

                # 2. UPDATE PROGRESS FILE: Mark the last chunk included in this successfully saved segment
                manager.update_state(
                    last_chunk_index=last_processed_chunk_index,
                    last_mp3_index=current_mp3_index
                )

                # 3. RESET FOR NEXT SEGMENT
                current_mp3_index += 1
                current_segment_audio = AudioSegment.empty()  # Start the new segment from empty

            # Add the new audio chunk to the current segment
            current_segment_audio += new_audio_chunk
            last_processed_chunk_index = absolute_chunk_index

        except Exception as e:
            # If an error occurs (like API failure), the loop breaks, and
            # the progress file is NOT updated, allowing safe restart.
            print(f"\nFATAL ERROR during synthesis at chunk index {absolute_chunk_index}. Progress NOT SAVED.")
            print(f"Details: {e}")
            sys.exit(1)

    # --- 4. FINAL CLEANUP AFTER LOOP ---

    # Save any remaining audio segment (the last file)
    if len(current_segment_audio) > 0:
        output_filename = manager.get_next_mp3_filename(current_mp3_index)
        print(
            f"\n[SAVE] Saving final segment {current_mp3_index} to {os.path.basename(output_filename)} (Duration: {len(current_segment_audio) / 1000:.2f}s)")

        current_segment_audio.export(output_filename, format="mp3")

        # FINAL PROGRESS UPDATE: Mark the last chunk of the entire text as processed
        manager.update_state(
            last_chunk_index=total_chunks - 1,
            last_mp3_index=current_mp3_index
        )

    print("\n--- Reading Complete: FULL AUDIOBOOK EXPORTED ---")

    # Delete the progress file only upon 100% completion of the entire text
    manager.delete_state()

## MAIN FUNCTION ##

def main():
    """The main entry point, orchestrating the script's execution flow."""

    # 1. PARSE ARGUMENTS
    args = parse_arguments()

    # --- OFFLINE engine reading on his own - cant save it as mp3 -> incompatible with --output-file ---
    if args.output_file is not None and args.engine == "OFFLINE":
        print("\nCRITICAL ERROR: OFFLINE engine is not compatible with audiobook export (--output-file).")
        print("Please choose ONLINE, G_CLOUD, or remove the --output-file argument.")
        sys.exit(1)
    # ---------------------------------------------

    # 2. FILE SELECTION
    file_path = select_file()

    # 3. ENGINE INITIALIZATION
    tts_engine = initialize_tts_engine(args)

    if args.output_file is not None:
        # Režim EXPORTU
        print(f"\n--- Starting Audiobook Export (Engine: {args.engine}) ---")
        export_audiobook(file_path, tts_engine, args)
    else:
        # Režim ČTENÍ (Výchozí)
        print(f"\n--- Starting Live Reading (Engine: {args.engine}) ---")
        process_reading(file_path, tts_engine, args.chunk_size)

    # 4. START PROCESSING
    print(f"\n--- Starting Reading (Engine: {args.engine}) ---")
    print(f"File: {os.path.basename(file_path)}")
    print(f"Rate: {args.rate}")
    print(f"Chunk Size: {args.chunk_size}")

    process_reading(file_path, tts_engine, args.chunk_size)

if __name__ == "__main__":
    main()
