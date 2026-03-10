"""
GraphQL input types for TTS and Translation services.

This module dynamically generates input types from existing argument definitions
using SchemaGenerator to maintain a single source of truth.
"""

from server.schema_generator import SchemaGenerator
from core.tts_args_definition import TTS_CONFIG_DEFS
from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS


# ============================================================================
# Dynamically Generated Input Types
# ============================================================================

# Generate TTSInput from TTS_CONFIG_DEFS
# This creates a Strawberry input type with fields for:
# - text_content: Optional[str] - Direct text input
# - file_upload: Optional[Upload] - File upload input
# - All TTS parameters from TTS_CONFIG_DEFS (engine, chunk_size, etc.)
TTSInput = SchemaGenerator.generate_input_type(
    config_defs=TTS_CONFIG_DEFS,
    type_name="TTSInput"
)

# Generate TranslationInput from TRANSLATOR_CONFIG_DEFS
# This creates a Strawberry input type with fields for:
# - text_content: Optional[str] - Direct text input
# - file_upload: Optional[Upload] - File upload input
# - All translation parameters from TRANSLATOR_CONFIG_DEFS (engine, source_language, etc.)
TranslationInput = SchemaGenerator.generate_input_type(
    config_defs=TRANSLATOR_CONFIG_DEFS,
    type_name="TranslationInput"
)


# ============================================================================
# Benefits of Dynamic Generation
# ============================================================================
# 1. Single Source of Truth: Parameters defined once in *_args_definition.py
# 2. Automatic Synchronization: Adding a parameter to config automatically adds it to GraphQL schema
# 3. Consistent Defaults: GraphQL defaults match script defaults
# 4. Type Safety: Python types automatically mapped to GraphQL types
# 5. Documentation: help_text becomes GraphQL field descriptions
