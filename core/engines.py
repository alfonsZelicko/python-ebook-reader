import os
import io
import argparse

import platform
import sys
import numpy as np
import pyttsx3
import gtts
from pydub import AudioSegment
import logging

# 1. Google Cloud Text-to-Speech (G_CLOUD engine)
try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

# 2. Windows SAPI Integration (Offline engine on Windows)
try:
    import win32com.client
except ImportError:
    win32com = None


class BaseTTSEngine:
    def __init__(self, speaking_rate: float):
        self.speaking_rate = speaking_rate
    def generate_audio_chunk(self, text: str):
        raise NotImplementedError


class OfflineTTSEngine(BaseTTSEngine):

    def __init__(self, speaking_rate: float, offline_voice_id: str):
        super().__init__(speaking_rate)
        self.is_windows = platform.system() == "Windows"
        self.offline_voice_id = offline_voice_id

        if self.is_windows and win32com and 'win32com.client' in sys.modules:
            self._init_win32_sapi()
        else:
            self._init_pyttsx3()

    def _init_win32_sapi(self):
        """Initializes SAPI via pywin32 COM object."""
        print("Initializing OFFLINE engine (pywin32 SAPI)...")
        try:
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            self.speaker.Rate = int((self.speaking_rate - 1.0) * 10) # -10 = slow; 0 = normal; +10 = fast

            target_voice_id = self.offline_voice_id.strip().strip('"')
            voices = self.speaker.GetVoices()
            voice_to_use = None

            if target_voice_id:
                voice_to_use = next((v for v in voices if target_voice_id.lower() in v.GetDescription().lower()), None)

            if voice_to_use:
                self.speaker.Voice = voice_to_use
                print(f"Using configured SAPI voice: {voice_to_use.GetDescription()}")
            else:
                print(f"Warning: Configured voice ID '{target_voice_id}' not found. Using default SAPI voice.")

        except Exception as e:
            print(f"Error initializing pywin32 SAPI, falling back to pyttsx3: {e}")
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        """Initializes pyttsx3 for non-Windows or as a Windows fallback."""
        print("Initializing OFFLINE engine (pyttsx3)...")

        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', int(175 * self.speaking_rate)) # words per sec

            target_voice_id = self.offline_voice_id.strip().strip('"')
            voices = self.engine.getProperty('voices')
            voice_to_use = None

            if target_voice_id:
                # # It will try to find ID from configuration
                voice_to_use = next((v.id for v in voices if v.id == target_voice_id), None)

            if voice_to_use:
                self.engine.setProperty('voice', voice_to_use)
                voice_name = next((v.name for v in voices if v.id == voice_to_use), "Unknown Name")
                print(f"Using configured pyttsx3 voice: {voice_name}")
            else:
                print(f"Warning: Configured voice ID '{target_voice_id}' not found. Using default system voice.")

        except Exception as e:
            print(f"\nFATAL ERROR: Failed to initialize pyttsx3 engine. ({e})")

            if platform.system() == "Linux":
                print("HINT: On Linux, pyttsx3 requires a backend TTS engine (like eSpeak) to be installed.")
                print("Try installing it: 'sudo apt install espeak' (Debian/Ubuntu) or similar for your distribution.")
            elif platform.system() == "Darwin":  # macOS
                print("HINT: On macOS, issues may occur if system voices are not configured or if espeak is missing.")

            sys.exit(1)

    def generate_audio_chunk(self, text: str):
        """
        Performs direct playback for the OFFLINE engine.
        Note: This does NOT return AudioSegment, hence incompatibility with --output-type === "FILE".
        """
        if hasattr(self, 'speaker'):
            self.speaker.Speak(text)
        elif hasattr(self, 'engine'):
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print("Error: TTS engine not initialized.")


class OnlineTTSEngine(BaseTTSEngine):
    # ... (No changes needed here, as gTTS needs only lang='cs') ...
    """Implementation using gTTS for online, higher-quality TTS."""

    def __init__(self, speaking_rate: float, lang_code: str):
        super().__init__(speaking_rate)
        print("Initializing ONLINE engine (gTTS)...")

        # 'cs-CZ' -> 'cs'
        self.gtts_lang_code = lang_code.split('-')[0].lower()

    def generate_audio_chunk(self, text: str) -> AudioSegment:
        """Generates MP3 and returns it as an AudioSegment object."""
        try:
            # Setting the language explicitly to Czech
            tts = gtts.gTTS(text, lang=self.gtts_lang_code)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            audio = AudioSegment.from_file(mp3_fp, format="mp3")

            if self.speaking_rate != 1.0:
                audio = audio.speedup(playback_speed=self.speaking_rate)

            return audio

        except Exception as e:
            print(f"Error processing gTTS chunk: {e}")
            raise  # Critical error: Stop the process


class GoogleCloudTTSEngine(BaseTTSEngine):
    """Implementation using Google Cloud Text-to-Speech (WaveNet/Studio)."""

    def __init__(self, speaking_rate: float, credentials_path: str, voice_id: str, lang_code: str):
        super().__init__(speaking_rate)
        print("Initializing ONLINE engine (Google Cloud TTS - WaveNet/Studio)...")

        if not texttospeech:
            raise ImportError("Google Cloud library not found. Please install google-cloud-texttospeech.")

        # VALIDATION (Using values passed from args)
        if not voice_id or not credentials_path:
            raise ValueError("WAVENET_VOICE and G_CLOUD_CREDENTIALS must be set.")

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google Cloud key file not found at: {credentials_path}")

        # Setting ENV variable for the Google Cloud client (required by the library)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # text-to-speech is guaranteed to exist here due to checks above
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

    def generate_audio_chunk(self, text: str) -> AudioSegment:
        """Generates high-quality speech and returns it as an AudioSegment object."""
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

            return audio

        except Exception as e:
            print(f"Error processing Google Cloud TTS chunk: {e}")
            raise  # Re-raise the exception to stop export process


class CoquiTTSEngine(BaseTTSEngine):
    """Implementation of offline TTS engine using Coqui TTS."""

    def __init__(self, speaking_rate: float, model_name: str, speaker_name: str, speaker_wav: str):
        super().__init__(speaking_rate)
        print("Initializing OFFLINE engine (Coqui TTS)...")

        # Suppress verbose logging from Coqui TTS
        logging.getLogger("TTS").setLevel(logging.ERROR)

        try:
            import torch
            from TTS.api import TTS
        except ImportError:
            raise ImportError(
                "Coqui TTS dependencies (torch, coqui-tts) not found. Ensure both are installed.")

        self.model_name = model_name
        self.speaker_name = speaker_name
        self.speaker_wav = speaker_wav

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Coqui TTS: Using device '{device}'. Loading model '{self.model_name}'...")

        try:
            # Load the TTS model and move it to the determined device (cuda/cpu)
            self.tts = TTS(model_name=self.model_name, progress_bar=False).to(device)
        except Exception as e:
            raise RuntimeError(f"Failed to load Coqui TTS model '{self.model_name}'. Check model name. Detail: {e}")

        # # --- MODEL CAPABILITY CHECKS (ROBUST AND FAIL FAST) ---
        # # Fail Fast: Check if speaker_wav is provided but the model lacks the necessary component.
        # if self.speaker_wav and not hasattr(self.tts.synthesizer, 'speaker_manager'):
        #     raise ValueError(f"Model '{self.model_name}' does not support speaker sampling (speaker_wav).")

    @staticmethod
    def _float_to_pcm(waveform: list) -> bytes:
        """
        Converts a list or numpy array of normalized floating-point audio data (range -1.0 to 1.0)
        to a 16-bit signed PCM byte array (range -32767 to 32767).

        This conversion is necessary because TTS models output float data, but standard audio libraries
        (like pydub/AudioSegment) expect raw PCM integer byte data.
        """
        # The scaling factor 32767 corresponds to the maximum amplitude for a 16-bit signed integer (2^15 - 1).
        return (np.array(waveform) * 32767).astype(np.int16).tobytes()

    def generate_audio_chunk(self, text: str) -> AudioSegment:
        """Generates audio data in-memory and returns it as an AudioSegment."""
        tts_options = {"text": text}

        # Set speaker options based on what was provided and validated in __init__
        if self.speaker_wav:
            tts_options["speaker_wav"] = self.speaker_wav
        elif self.speaker_name and self.speaker_name.lower() != 'none':
            tts_options["speaker"] = self.speaker_name

        try:
            # Generate waveform in-memory as a list or numpy array (float data)
            waveform = self.tts.tts(**tts_options)

            # Convert float waveform to 16-bit PCM byte array using the dedicated static method
            pcm_data = CoquiTTSEngine._float_to_pcm(waveform)

            # Create an AudioSegment from raw PCM data
            audio = AudioSegment(
                data=pcm_data,
                sample_width=2,  # 2 bytes = 16-bit
                frame_rate=self.tts.synthesizer.output_sample_rate,
                channels=1
            )

            if self.speaking_rate != 1.0:
                # Use speedup from pydub for speaking rate modification
                audio = audio.speedup(playback_speed=self.speaking_rate)

            return audio

        except Exception as e:
            print(f"Error processing Coqui TTS chunk: {e}")
            raise


def initialize_tts_engine(args: argparse.Namespace):
    """Initializes and returns the appropriate TTS engine based on arguments."""

    engine_choice = args.TTS_ENGINE.upper()
    speaking_rate = args.SPEAKING_RATE
    language_code = args.LANGUAGE_CODE

    try:
        if engine_choice == "OFFLINE":
            offline_voice_id = args.OFFLINE_VOICE_ID
            return OfflineTTSEngine(speaking_rate, offline_voice_id)

        elif engine_choice == "ONLINE":
            return OnlineTTSEngine(speaking_rate, language_code)

        elif engine_choice == "G_CLOUD":
            credentials_path = args.G_CLOUD_CREDENTIALS
            voice_id = args.WAVENET_VOICE
            lang_code = language_code
            return GoogleCloudTTSEngine(speaking_rate, credentials_path, voice_id, lang_code)

        elif engine_choice == "COQUI":
            return CoquiTTSEngine(speaking_rate, args.COQUI_MODEL_NAME, args.COQUI_SPEAKER_NAME, args.COQUI_SPEAKER_WAV)

        else:
            raise ValueError(f"Unknown engine choice: {engine_choice}, available options: ONLINE, G_CLOUD, COQUI, OFFLINE")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize the selected TTS engine ({engine_choice}).")
        print(f"Details: {e}")
        sys.exit(1)
