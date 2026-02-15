import os
import io
import argparse
import platform
import sys
from pydub import AudioSegment
import logging

class BaseTTSEngine:
    def __init__(self, speaking_rate: float):
        self.speaking_rate = speaking_rate
    def generate_audio_chunk(self, text: str):
        raise NotImplementedError

class OfflineTTSEngine(BaseTTSEngine):
    def __init__(self, speaking_rate: float, offline_voice_id: str):
        super().__init__(speaking_rate)
        self.offline_voice_id = offline_voice_id
        
        if platform.system() == "Windows":
            try:
                self._init_win32_sapi()
            except (ImportError, Exception):
                print("SAPI (pywin32) not available, trying pyttsx3...")
                self._init_pyttsx3()
        else:
            self._init_pyttsx3()

    def _init_win32_sapi(self):
        import win32com.client
        self.win32client = win32com.client
        
        print("Initializing OFFLINE engine (pywin32 SAPI)...")
        self.speaker = self.win32client.Dispatch("SAPI.SpVoice")

    def _init_pyttsx3(self):
        try:
            import pyttsx3
            self.pyttsx3 = pyttsx3
        except ImportError:
            print("ERROR: Offline TTS requires 'pyttsx3' or 'pywin32'.")
            print("FIX: Run 'pip install pyttsx3'")
            sys.exit(1)
            
        print("Initializing OFFLINE engine (pyttsx3)...")
        try:
            self.engine = self.pyttsx3.init()
            self.engine.setProperty('rate', int(175 * self.speaking_rate))

            target_voice_id = self.offline_voice_id.strip().strip('"')
            voices = self.engine.getProperty('voices')
            voice_to_use = next((v.id for v in voices if v.id == target_voice_id), None)

            if voice_to_use:
                self.engine.setProperty('voice', voice_to_use)
                print(f"Using configured pyttsx3 voice: {target_voice_id}")
            elif target_voice_id:
                print(f"WARNING: Voice '{target_voice_id}' not found. Using default.")
        except Exception as e:
            print(f"\nFATAL ERROR: Could not initialize pyttsx3. ({e})")
            if platform.system() == "Linux":
                print("HINT: On Linux, ensure 'espeak' is installed: 'sudo apt install espeak'")
            sys.exit(1)

    def generate_audio_chunk(self, text: str):
        if hasattr(self, 'speaker'):
            self.speaker.Speak(text)
        elif hasattr(self, 'engine'):
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print("ERROR: No active offline engine found.")

class OnlineTTSEngine(BaseTTSEngine):
    def __init__(self, speaking_rate: float, lang_code: str):
        super().__init__(speaking_rate)
        try:
            import gtts
            self.gtts_module = gtts
        except ImportError:
            print("ERROR: 'gTTS' library not found. Required for ONLINE mode.")
            print("FIX: Run 'pip install gTTS'")
            sys.exit(1)

        print("Initializing ONLINE engine (gTTS)...")
        self.gtts_lang_code = lang_code.split('-')[0].lower()

    def generate_audio_chunk(self, text: str) -> AudioSegment:
        try:
            tts = self.gtts_module.gTTS(text, lang=self.gtts_lang_code)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio = AudioSegment.from_file(mp3_fp, format="mp3")
            if self.speaking_rate != 1.0:
                audio = audio.speedup(playback_speed=self.speaking_rate)
            return audio
        except Exception as e:
            print(f"Error processing gTTS chunk: {e}")
            raise

class GoogleCloudTTSEngine(BaseTTSEngine):
    def __init__(self, speaking_rate: float, credentials_path: str, voice_id: str, lang_code: str):
        super().__init__(speaking_rate)
        try:
            from google.cloud import texttospeech
            self.tts_module = texttospeech
        except ImportError:
            print("ERROR: Google Cloud TTS library not found.")
            print("FIX: Run 'pip install google-cloud-texttospeech'")
            sys.exit(1)

        if not voice_id or not credentials_path:
            raise ValueError("WAVENET_VOICE and G_CLOUD_CREDENTIALS must be set.")
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google Cloud key file not found at: {credentials_path}")

        try:
            self.client = self.tts_module.TextToSpeechClient.from_service_account_json(credentials_path)
        except Exception as e:
            print(f"ERROR: Failed to authorize Google Cloud with provided key. ({e})")
            sys.exit(1)

        self.voice = self.tts_module.VoiceSelectionParams(language_code=lang_code, name=voice_id)
        self.audio_config = self.tts_module.AudioConfig(
            audio_encoding=self.tts_module.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )
        print(f"Using Google Cloud Voice: {voice_id}")

    def generate_audio_chunk(self, text: str) -> AudioSegment:
        try:
            synthesis_input = self.tts_module.SynthesisInput(text=text)
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=self.voice, audio_config=self.audio_config
            )
            mp3_fp = io.BytesIO(response.audio_content)
            mp3_fp.seek(0)
            return AudioSegment.from_file(mp3_fp, format="mp3")
        except Exception as e:
            print(f"Error processing Google Cloud TTS chunk: {e}")
            raise

class CoquiTTSEngine(BaseTTSEngine):
    def __init__(self, speaking_rate: float, model_name: str, speaker_name: str, speaker_wav: str, lang_code: str):
        super().__init__(speaking_rate)
        logging.getLogger("TTS").setLevel(logging.ERROR)
        
        try:
            import torch
            import numpy as np
            from TTS.api import TTS
            self.torch = torch
            self.np = np
            self.TTS = TTS
        except ImportError:
            print("ERROR: Coqui TTS dependencies not found.")
            sys.exit(1)

        self.model_name = model_name
        self.speaker_name = speaker_name
        self.speaker_wav = speaker_wav
        self.target_lang = lang_code.split('-')[0].lower()
        
        device = "cuda" if self.torch.cuda.is_available() else "cpu"
        print(f"Coqui TTS: Using {device.upper()}. Loading model '{model_name}'...")
        
        try:
            self.tts = self.TTS(model_name=model_name, progress_bar=False).to(device)
        except Exception as e:
            print(f"ERROR: Failed to load Coqui model. ({e})")
            sys.exit(1)

    def _float_to_pcm(self, waveform) -> bytes:
        return (self.np.array(waveform) * 32767).astype(self.np.int16).tobytes()

    def generate_audio_chunk(self, text: str) -> AudioSegment:
        options = {"text": text}
        
        # Handle Multi-lingual models (like XTTS v2)
        if hasattr(self.tts, 'is_multi_lingual') and self.tts.is_multi_lingual:
            options["language"] = self.target_lang
            
            # XTTS requires a speaker reference (wav or name)
            if self.speaker_wav and os.path.exists(self.speaker_wav):
                options["speaker_wav"] = self.speaker_wav
            elif self.speaker_name and self.speaker_name.lower() != 'none':
                options["speaker"] = self.speaker_name
            else:
                # Fallback to the first available speaker if none provided
                if hasattr(self.tts, 'speakers') and self.tts.speakers:
                    options["speaker"] = self.tts.speakers[0]
                else:
                    options["speaker"] = "Ana Lucia"
        else:
            # Standard single-voice models (like VITS)
            if self.speaker_name and self.speaker_name.lower() != 'none':
                options["speaker"] = self.speaker_name

        try:
            # Generate audio using the TTS API
            waveform = self.tts.tts(**options)
            pcm_data = self._float_to_pcm(waveform)
            
            audio = AudioSegment(
                data=pcm_data,
                sample_width=2,
                frame_rate=self.tts.synthesizer.output_sample_rate,
                channels=1
            )
            
            # Adjust playback speed if needed
            if self.speaking_rate != 1.0:
                audio = audio.speedup(playback_speed=self.speaking_rate)
            return audio
        except Exception as e:
            print(f"Error processing Coqui chunk: {e}")
            raise

def initialize_tts_engine(args: argparse.Namespace):
    engine_choice = args.TTS_ENGINE.upper()
    try:
        if engine_choice == "OFFLINE":
            return OfflineTTSEngine(
                args.SPEAKING_RATE, 
                args.OFFLINE_VOICE_ID
                )
        elif engine_choice == "ONLINE":
            return OnlineTTSEngine(
                args.SPEAKING_RATE, 
                args.LANGUAGE_CODE
                )
        elif engine_choice == "G_CLOUD":
            return GoogleCloudTTSEngine(
                args.SPEAKING_RATE, 
                args.G_CLOUD_CREDENTIALS, 
                args.WAVENET_VOICE, 
                args.LANGUAGE_CODE
                )
        if engine_choice == "COQUI":
            return CoquiTTSEngine(
                args.SPEAKING_RATE, 
                args.COQUI_MODEL_NAME, 
                args.COQUI_SPEAKER_NAME, 
                args.COQUI_SPEAKER_WAV,
                args.LANGUAGE_CODE
                )
        else:
            raise ValueError(f"Unknown engine: {engine_choice}")
    except Exception as e:
        print(f"\nCRITICAL ERROR during TTS initialization: {e}")
        sys.exit(1)