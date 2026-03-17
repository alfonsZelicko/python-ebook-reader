import argparse
import time
from datetime import datetime

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class BaseTranslationEngine:
    """Base class for all translation engines."""

    def __init__(self, source_language: str, target_language: str):
        self.source_language = source_language
        self.target_language = target_language

    def translate_chunk(self, chunk: str, chunk_index: int = 0) -> str:
        """
        Translates a single chunk of text.

        Args:
            chunk: Text to translate
            chunk_index: Index of the chunk (for logging)

        Returns:
            Translated text
        """
        raise NotImplementedError


class OpenAITranslationEngine(BaseTranslationEngine):
    """Translation engine using OpenAI's GPT models."""

    def __init__(self, args: argparse.Namespace):
        super().__init__(args.SL, args.TL)

        # Validate API key
        api_key = args.O_KEY
        if not api_key:
            raise ValueError(
                "O_KEY not found. Please set O_KEY in your .env.translator file or pass it via --o-key. "
                "Get your API key at: https://platform.openai.com/api-keys"
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI library not found. Please install it: pip install openai"
            )

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)

        # Store configuration
        self.model = args.O_MODEL
        self.translation_prompt = args.TP
        self.max_retries = args.MR
        self.retry_delay = args.RD

        print(f"OpenAI Translation Engine initialized:")
        print(f"  Model: {self.model}")
        print(f"  Translation: {self.source_language} -> {self.target_language}")
        print(f"  Max retries: {self.max_retries}")

    def translate_chunk(self, chunk: str, chunk_index: int = 0) -> str:
        """Translates a chunk using OpenAI API with retry logic."""

        # Construct system prompt with language information
        system_prompt = f"{self.translation_prompt}\n\nTranslate from {self.source_language} to {self.target_language}."

        # Construct messages for API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chunk},
        ]

        # Retry loop with exponential backoff
        delay = self.retry_delay
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,  # Lower temperature for consistent translations
                )

                # Extract translation from response
                translated_text = response.choices[0].message.content

                if not translated_text:
                    raise ValueError("Empty translation received from API")

                return translated_text

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Check if it's a rate limit error
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    print(
                        f"[{timestamp}] Rate limit exceeded. Waiting {delay}s before retry..."
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue

                # Log the error
                print(
                    f"[{timestamp}] ERROR: API request failed (attempt {attempt + 1}/{self.max_retries})"
                )
                print(f"  Error type: {error_type}")
                print(f"  Error message: {str(e)}")

                # If not the last attempt, wait and retry
                if attempt < self.max_retries - 1:
                    print(f"  Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(
                        f"  All {self.max_retries} retries exhausted for chunk {chunk_index}"
                    )
                    print(f"  Skipping this chunk and continuing with next...")
                    raise last_error

        raise (
            last_error
            if last_error
            else Exception("Translation failed for unknown reason")
        )


class GeminiTranslationEngine(BaseTranslationEngine):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args.SL, args.TL)

        if genai is None or types is None:
            raise ImportError(
                "Google GenAI library not found. Please install it: pip install google-genai"
            )

        # Validate API Key
        api_key = args.G_KEY
        if not api_key:
            raise ValueError(
                "G_KEY not found. Please set G_KEY in your .env.translator file or pass it via --g-key. "
                "Get your API key at: https://aistudio.google.com/app/apikey"
            )

        # Initialize the new client
        self.client = genai.Client(api_key=api_key)

        # Store configuration
        self.model_name = args.G_MODEL
        self.translation_prompt = args.TP
        self.max_retries = args.MR
        self.retry_delay = args.RD

        print(f"Gemini Translation Engine (google-genai) initialized:")
        print(f"  Model: {self.model_name}")
        print(f"  Translation: {self.source_language} -> {self.target_language}")
        print(f"  Max retries: {self.max_retries}")

    def translate_chunk(self, chunk: str, chunk_index: int = 0) -> str:
        # Construct system instruction and prompt
        system_instruction = f"{self.translation_prompt}\n\nTranslate from {self.source_language} to {self.target_language}."

        delay = self.retry_delay
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=chunk,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3,
                        # for better translations...
                        safety_settings=[
                            types.SafetySetting(
                                category="HARM_CATEGORY_HARASSMENT",
                                threshold="BLOCK_NONE",
                            ),
                            types.SafetySetting(
                                category="HARM_CATEGORY_HATE_SPEECH",
                                threshold="BLOCK_NONE",
                            ),
                            types.SafetySetting(
                                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                threshold="BLOCK_NONE",
                            ),
                            types.SafetySetting(
                                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                threshold="BLOCK_NONE",
                            ),
                        ],
                    ),
                )

                translated_text = response.text

                if not translated_text:
                    raise ValueError("Empty translation received from API")

                return translated_text

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Checking for quota/rate limit errors in the new SDK
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"[{timestamp}] Rate limit exceeded. Waiting {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                    continue

                print(
                    f"[{timestamp}] ERROR: API request failed (attempt {attempt + 1}/{self.max_retries})"
                )
                print(f"  Error type: {error_type}")
                print(f"  Error message: {str(e)}")

                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise last_error

        raise (
            last_error
            if last_error
            else Exception("Translation failed for unknown reason")
        )


class DeepLTranslationEngine(BaseTranslationEngine):
    """Translation engine using DeepL API."""

    def __init__(self, args: argparse.Namespace):
        super().__init__(args.SL, args.TL)

        # Validate API key
        api_key = args.D_KEY
        if not api_key:
            raise ValueError(
                "D_KEY not found in environment variables. "
                "Please set D_KEY in your .env.translator file or pass it via --d-key. "
                "Get your API key at: https://www.deepl.com/pro-api"
            )

        # Import DeepL
        try:
            import deepl
        except ImportError:
            raise ImportError(
                "DeepL library not found. Please install it: pip install deepl"
            )

        # Initialize DeepL translator
        self.translator = deepl.Translator(api_key)

        # Store configuration
        self.max_retries = args.MR
        self.retry_delay = args.RD

        print(f"DeepL Translation Engine initialized:")
        print(f"  Translation: {self.source_language} -> {self.target_language}")
        print(f"  Max retries: {self.max_retries}")

        # Check if custom prompt was provided (DeepL doesn't support it)
        if hasattr(args, "TP") and args.TP != "":
            # Check if it was provided via CLI (not just from .env)
            import sys

            if "--tp" in sys.argv:
                print(
                    "\n[WARNING] DeepL does not support custom translation prompts."
                )
                print("   The --tp parameter will be ignored.")

    def translate_chunk(self, chunk: str, chunk_index: int = 0) -> str:
        """Translates a chunk using DeepL API with retry logic."""

        # Retry loop with exponential backoff
        delay = self.retry_delay
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Make API call
                result = self.translator.translate_text(
                    chunk,
                    source_lang=self.source_language.upper(),
                    target_lang=self.target_language.upper(),
                )

                # Extract translation from response
                translated_text = result.text

                if not translated_text:
                    raise ValueError("Empty translation received from API")

                return translated_text

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Check if it's a rate limit error
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    print(
                        f"[{timestamp}] Rate limit exceeded. Waiting {delay}s before retry..."
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue

                # Log the error
                print(
                    f"[{timestamp}] ERROR: API request failed (attempt {attempt + 1}/{self.max_retries})"
                )
                print(f"  Error type: {error_type}")
                print(f"  Error message: {str(e)}")

                # If not the last attempt, wait and retry
                if attempt < self.max_retries - 1:
                    print(f"  Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(
                        f"  All {self.max_retries} retries exhausted for chunk {chunk_index}"
                    )
                    print(f"  Skipping this chunk and continuing with next...")
                    raise last_error

        raise (
            last_error
            if last_error
            else Exception("Translation failed for unknown reason")
        )


def initialize_translation_engine(args: argparse.Namespace) -> BaseTranslationEngine:
    """Initializes and returns the appropriate translation engine based on arguments."""

    engine_choice = args.TE.upper() if isinstance(args.TE, str) else args.TE.name

    if engine_choice == "OPENAI":
        return OpenAITranslationEngine(args)

    elif engine_choice == "GEMINI":
        return GeminiTranslationEngine(args)

    elif engine_choice == "DEEPL":
        return DeepLTranslationEngine(args)

    else:
        raise ValueError(
            f"Unknown translation engine: {engine_choice}. "
            f"Available options: OPENAI, GEMINI, DEEPL"
        )
