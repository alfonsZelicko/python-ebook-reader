"""
Unit tests for SchemaGenerator

Tests the dynamic generation of GraphQL input_data types from config definitions.
"""

from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS
from core.tts_args_definition import TTS_CONFIG_DEFS
from server.graphql.schema_generator import SchemaGenerator


def test_generate_tts_input_type():
    """Test generation of TTS input_data type from TTS_CONFIG_DEFS."""
    TTSInput = SchemaGenerator.generate_input_type(TTS_CONFIG_DEFS, "TTSInput")

    # Verify the type was created
    assert TTSInput is not None
    assert TTSInput.__name__ == "TTSInput"

    # Verify it has the required fields
    annotations = TTSInput.__annotations__
    assert "text_content" in annotations
    assert "file_upload" in annotations
    assert "engine" in annotations
    assert "chunk_size" in annotations
    assert "chunk_by_paragraph" in annotations
    assert "speaking_rate" in annotations
    assert "output_type" in annotations


def test_generate_translation_input_type():
    """Test generation of Translation input_data type from TRANSLATOR_CONFIG_DEFS."""
    TranslationInput = SchemaGenerator.generate_input_type(
        TRANSLATOR_CONFIG_DEFS, "TranslationInput"
    )

    # Verify the type was created
    assert TranslationInput is not None
    assert TranslationInput.__name__ == "TranslationInput"

    # Verify it has the required fields
    annotations = TranslationInput.__annotations__
    assert "text_content" in annotations
    assert "file_upload" in annotations
    assert "engine" in annotations
    assert "source_language" in annotations
    assert "target_language" in annotations
    assert "translation_prompt" in annotations


def test_map_python_type_to_graphql():
    """Test Python type to GraphQL type mapping."""
    assert SchemaGenerator._map_python_type_to_graphql(str) == str
    assert SchemaGenerator._map_python_type_to_graphql(int) == int
    assert SchemaGenerator._map_python_type_to_graphql(float) == float
    assert SchemaGenerator._map_python_type_to_graphql(bool) == bool


def test_create_enum_from_choices():
    """Test Enum generation from choices list."""
    choices = ["OFFLINE", "ONLINE", "G_CLOUD", "COQUI"]
    enum_type = SchemaGenerator._create_enum_from_choices("TTSEngineEnum", choices)

    # Verify enum was created
    assert enum_type is not None

    # Verify enum has all choices
    enum_values = [member.value for member in enum_type]
    assert set(enum_values) == set(choices)


def test_convert_key_to_field_name():
    """Test conversion of short keys to GraphQL field names."""
    # Test special mappings
    assert SchemaGenerator.convert_key_to_field_name("TE") == "engine"
    assert SchemaGenerator.convert_key_to_field_name("CS") == "chunk_size"
    assert SchemaGenerator.convert_key_to_field_name("CP") == "chunk_by_paragraph"
    assert SchemaGenerator.convert_key_to_field_name("SR") == "speaking_rate"
    assert SchemaGenerator.convert_key_to_field_name("G_KEY") == "google_credentials"
    assert SchemaGenerator.convert_key_to_field_name("OFF_VOICE") == "offline_voice"
    assert SchemaGenerator.convert_key_to_field_name("L_CODE") == "language_code"

    # Translation-specific mappings
    assert SchemaGenerator.convert_key_to_field_name("SL") == "source_language"
    assert SchemaGenerator.convert_key_to_field_name("TL") == "target_language"
    assert SchemaGenerator.convert_key_to_field_name("O_KEY") == "openai_api_key"
    assert SchemaGenerator.convert_key_to_field_name("O_MODEL") == "openai_model"
    assert SchemaGenerator.convert_key_to_field_name("MR") == "max_retries"


def test_generated_type_has_defaults():
    """Test that generated types include default values from config."""
    TTSInput = SchemaGenerator.generate_input_type(TTS_CONFIG_DEFS, "TTSInput")

    # Create an instance and check defaults
    instance = TTSInput()

    # Check some default values match the config
    assert instance.chunk_size == 3500
    assert instance.speaking_rate == 1.1
    assert instance.max_file_duration == 600
    assert instance.chunk_by_paragraph == False


def test_generated_type_handles_boolean_flags():
    """Test that boolean flags with action='store_true' are handled correctly."""
    TTSInput = SchemaGenerator.generate_input_type(TTS_CONFIG_DEFS, "TTSInput")

    # Check boolean fields
    annotations = TTSInput.__annotations__
    instance = TTSInput()

    # CP has action='store_true', should be bool with default False
    assert instance.chunk_by_paragraph == False
    assert instance.clean_output_directory == False


def test_all_tts_fields_mapped():
    """Test that all TTS config fields are mapped to the input_data type."""
    TTSInput = SchemaGenerator.generate_input_type(TTS_CONFIG_DEFS, "TTSInput")
    annotations = TTSInput.__annotations__

    # Expected fields from TTS_CONFIG_DEFS
    expected_fields = [
        "text_content",
        "file_upload",  # Added by generator
        "engine",
        "chunk_size",
        "chunk_by_paragraph",
        "speaking_rate",
        "output_type",
        "max_file_duration",
        "clean_output_directory",
        "offline_voice",
        "language_code",
        "google_credentials",
        "google_voice",
        "coqui_model",
        "coqui_speaker",
        "coqui_wav",
        "coqui_sample_rate",
    ]

    for field in expected_fields:
        assert field in annotations, f"Field '{field}' missing from generated type"


def test_all_translation_fields_mapped():
    """Test that all translation config fields are mapped to the input_data type."""
    TranslationInput = SchemaGenerator.generate_input_type(
        TRANSLATOR_CONFIG_DEFS, "TranslationInput"
    )
    annotations = TranslationInput.__annotations__

    # Expected fields from TRANSLATOR_CONFIG_DEFS
    expected_fields = [
        "text_content",
        "file_upload",  # Added by generator
        "engine",
        "source_language",
        "target_language",
        "translation_prompt",
        "chunk_size",
        "chunk_by_paragraph",
        "openai_api_key",
        "openai_model",
        "google_credentials",
        "gemini_model",
        "deepl_api_key",
        "max_retries",
        "retry_delay",
        "clean_output_directory",
    ]

    for field in expected_fields:
        assert field in annotations, f"Field '{field}' missing from generated type"
