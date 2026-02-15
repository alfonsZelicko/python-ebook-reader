import argparse
import os
import sys
import time
from datetime import datetime


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
        super().__init__(args.SOURCE_LANGUAGE, args.TARGET_LANGUAGE)
        
        # Validate API key
        api_key = args.OPENAI_API_KEY
        if not api_key:
            print("\nERROR: OPENAI_API_KEY not found in environment variables.")
            print("FIX: Please set OPENAI_API_KEY in your .env.translator file or pass it via --openai-api-key")
            print("HINT: Get your API key at: https://platform.openai.com/api-keys")
            sys.exit(1)

        try:
            from openai import OpenAI
        except ImportError:
            print("ERROR: OpenAI library not found. Please install it: pip install openai")
            sys.exit(1)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Store configuration
        self.model = args.OPENAI_MODEL
        self.translation_prompt = args.TRANSLATION_PROMPT
        self.max_retries = args.MAX_RETRIES
        self.retry_delay = args.RETRY_DELAY
        
        print(f"OpenAI Translation Engine initialized:")
        print(f"  Model: {self.model}")
        print(f"  Translation: {self.source_language} → {self.target_language}")
        print(f"  Max retries: {self.max_retries}")
    
    def translate_chunk(self, chunk: str, chunk_index: int = 0) -> str:
        """Translates a chunk using OpenAI API with retry logic."""
        
        # Construct system prompt with language information
        system_prompt = f"{self.translation_prompt}\n\nTranslate from {self.source_language} to {self.target_language}."
        
        # Construct messages for API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chunk}
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
                    temperature=0.3  # Lower temperature for consistent translations
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
                    print(f"[{timestamp}] Rate limit exceeded. Waiting {delay}s before retry...")
                    time.sleep(delay)
                    delay *= 2
                    continue
                
                # Log the error
                print(f"[{timestamp}] ERROR: API request failed (attempt {attempt + 1}/{self.max_retries})")
                print(f"  Error type: {error_type}")
                print(f"  Error message: {str(e)}")
                
                # If not the last attempt, wait and retry
                if attempt < self.max_retries - 1:
                    print(f"  Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(f"  All {self.max_retries} retries exhausted for chunk {chunk_index}")
                    print(f"  Skipping this chunk and continuing with next...")
                    raise last_error
        
        raise last_error if last_error else Exception("Translation failed for unknown reason")


class GeminiTranslationEngine(BaseTranslationEngine):
    """Translation engine using Google's Gemini AI."""
    
    def __init__(self, args: argparse.Namespace):
        super().__init__(args.SOURCE_LANGUAGE, args.TARGET_LANGUAGE)
        
        # Validate credentials
        credentials_path = args.G_CLOUD_CREDENTIALS
        if not os.path.exists(credentials_path):
            print(f"\nERROR: Google Cloud credentials file not found: {credentials_path}")
            print("Please ensure your google-key.json file exists and the path is correct.")
            sys.exit(1)
        
        # Set environment variable for Google Cloud
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # Import Google Generative AI
        try:
            import google.generativeai as genai
        except ImportError:
            print("\nERROR: Google Generative AI library not found. Please install it: pip install google-generativeai")
            sys.exit(1)
        
        # Configure Gemini
        genai.configure()
        
        # Store configuration
        self.model_name = args.GEMINI_MODEL
        self.translation_prompt = args.TRANSLATION_PROMPT
        self.max_retries = args.MAX_RETRIES
        self.retry_delay = args.RETRY_DELAY
        
        # Initialize model
        self.model = genai.GenerativeModel(self.model_name)
        
        print(f"Gemini Translation Engine initialized:")
        print(f"  Model: {self.model_name}")
        print(f"  Translation: {self.source_language} → {self.target_language}")
        print(f"  Max retries: {self.max_retries}")
    
    def translate_chunk(self, chunk: str, chunk_index: int = 0) -> str:
        """Translates a chunk using Gemini API with retry logic."""
        
        # Construct prompt with language information
        full_prompt = f"{self.translation_prompt}\n\nTranslate from {self.source_language} to {self.target_language}.\n\nText to translate:\n{chunk}"
        
        # Retry loop with exponential backoff
        delay = self.retry_delay
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Make API call
                response = self.model.generate_content(full_prompt)
                
                # Extract translation from response
                translated_text = response.text
                
                if not translated_text:
                    raise ValueError("Empty translation received from API")
                
                return translated_text
            
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Check if it's a rate limit error
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    print(f"[{timestamp}] Rate limit exceeded. Waiting {delay}s before retry...")
                    time.sleep(delay)
                    delay *= 2
                    continue
                
                # Log the error
                print(f"[{timestamp}] ERROR: API request failed (attempt {attempt + 1}/{self.max_retries})")
                print(f"  Error type: {error_type}")
                print(f"  Error message: {str(e)}")
                
                # If not the last attempt, wait and retry
                if attempt < self.max_retries - 1:
                    print(f"  Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(f"  All {self.max_retries} retries exhausted for chunk {chunk_index}")
                    print(f"  Skipping this chunk and continuing with next...")
                    raise last_error
        
        raise last_error if last_error else Exception("Translation failed for unknown reason")


class DeepLTranslationEngine(BaseTranslationEngine):
    """Translation engine using DeepL API."""
    
    def __init__(self, args: argparse.Namespace):
        super().__init__(args.SOURCE_LANGUAGE, args.TARGET_LANGUAGE)
        
        # Validate API key
        api_key = args.DEEPL_API_KEY
        if not api_key:
            print("\nERROR: DEEPL_API_KEY not found in environment variables.")
            print("Please set DEEPL_API_KEY in your .env.translator file or pass it via --deepl-api-key")
            print("Get your API key at: https://www.deepl.com/pro-api")
            sys.exit(1)
        
        # Import DeepL
        try:
            import deepl
        except ImportError:
            print("\nERROR: DeepL library not found. Please install it:")
            print("pip install deepl")
            sys.exit(1)
        
        # Initialize DeepL translator
        self.translator = deepl.Translator(api_key)
        
        # Store configuration
        self.max_retries = args.MAX_RETRIES
        self.retry_delay = args.RETRY_DELAY
        
        print(f"DeepL Translation Engine initialized:")
        print(f"  Translation: {self.source_language} → {self.target_language}")
        print(f"  Max retries: {self.max_retries}")
        
        # Check if custom prompt was provided (DeepL doesn't support it)
        if hasattr(args, 'TRANSLATION_PROMPT') and args.TRANSLATION_PROMPT != "":
            # Check if it was provided via CLI (not just from .env)
            import sys
            if '--translation-prompt' in sys.argv:
                print("\n⚠️  WARNING: DeepL does not support custom translation prompts.")
                print("   The --translation-prompt parameter will be ignored.")
    
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
                    target_lang=self.target_language.upper()
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
                    print(f"[{timestamp}] Rate limit exceeded. Waiting {delay}s before retry...")
                    time.sleep(delay)
                    delay *= 2
                    continue
                
                # Log the error
                print(f"[{timestamp}] ERROR: API request failed (attempt {attempt + 1}/{self.max_retries})")
                print(f"  Error type: {error_type}")
                print(f"  Error message: {str(e)}")
                
                # If not the last attempt, wait and retry
                if attempt < self.max_retries - 1:
                    print(f"  Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(f"  All {self.max_retries} retries exhausted for chunk {chunk_index}")
                    print(f"  Skipping this chunk and continuing with next...")
                    raise last_error
        
        raise last_error if last_error else Exception("Translation failed for unknown reason")


def initialize_translation_engine(args: argparse.Namespace) -> BaseTranslationEngine:
    """Initializes and returns the appropriate translation engine based on arguments."""
    
    engine_choice = args.TRANSLATION_ENGINE.upper()
    
    try:
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
    
    except Exception as e:
        print(f"\nCRITICAL ERROR: Could not initialize the selected translation engine ({engine_choice}).")
        print(f"Details: {e}")
        sys.exit(1)
