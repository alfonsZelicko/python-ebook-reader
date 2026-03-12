"""
Tests for dynamically generated GraphQL input types.

Verifies that TTSInput and TranslationInput are correctly generated
from their respective configuration definitions.
"""

import pytest

from server.graphql.types import TTSInput, TranslationInput


def test_tts_input_has_required_fields():
    """Verify TTSInput has text_content and file_upload fields."""
    # Check that the type has the expected attributes
    assert hasattr(TTSInput, "__annotations__")
    annotations = TTSInput.__annotations__

    # Verify input source fields exist
    assert "text_content" in annotations
    assert "file_upload" in annotations


def test_tts_input_has_engine_field():
    """Verify TTSInput has engine field from TTS_CONFIG_DEFS."""
    annotations = TTSInput.__annotations__
    assert "engine" in annotations


def test_tts_input_has_chunk_size_field():
    """Verify TTSInput has chunk_size field from TTS_CONFIG_DEFS."""
    annotations = TTSInput.__annotations__
    assert "chunk_size" in annotations


def test_tts_input_has_speaking_rate_field():
    """Verify TTSInput has speaking_rate field from TTS_CONFIG_DEFS."""
    annotations = TTSInput.__annotations__
    assert "speaking_rate" in annotations


def test_translation_input_has_required_fields():
    """Verify TranslationInput has text_content and file_upload fields."""
    annotations = TranslationInput.__annotations__

    # Verify input source fields exist
    assert "text_content" in annotations
    assert "file_upload" in annotations


def test_translation_input_has_engine_field():
    """Verify TranslationInput has engine field from TRANSLATOR_CONFIG_DEFS."""
    annotations = TranslationInput.__annotations__
    assert "engine" in annotations


def test_translation_input_has_language_fields():
    """Verify TranslationInput has source_language and target_language fields."""
    annotations = TranslationInput.__annotations__
    assert "source_language" in annotations
    assert "target_language" in annotations


def test_translation_input_has_translation_prompt_field():
    """Verify TranslationInput has translation_prompt field."""
    annotations = TranslationInput.__annotations__
    assert "translation_prompt" in annotations


def test_tts_input_default_values():
    """Verify TTSInput has correct default values from TTS_CONFIG_DEFS."""
    # Check that default values are set
    assert hasattr(TTSInput, "chunk_size")
    assert TTSInput.chunk_size == 3500

    assert hasattr(TTSInput, "speaking_rate")
    assert TTSInput.speaking_rate == 1.1


def test_translation_input_default_values():
    """Verify TranslationInput has correct default values from TRANSLATOR_CONFIG_DEFS."""
    # Check that default values are set
    assert hasattr(TranslationInput, "chunk_size")
    assert TranslationInput.chunk_size == 4000

    assert hasattr(TranslationInput, "source_language")
    assert TranslationInput.source_language == "en"

    assert hasattr(TranslationInput, "target_language")
    assert TranslationInput.target_language == "cs"


def test_tts_input_strawberry_decorated():
    """Verify TTSInput is decorated with @strawberry.input."""
    # Check for Strawberry metadata
    assert hasattr(TTSInput, "__strawberry_definition__")


def test_translation_input_strawberry_decorated():
    """Verify TranslationInput is decorated with @strawberry.input."""
    # Check for Strawberry metadata
    assert hasattr(TranslationInput, "__strawberry_definition__")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
