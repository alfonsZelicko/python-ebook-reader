"""
Dynamic GraphQL Input Types for TTS and Translation services.

This module acts as the bridge between the core argument definitions and the
GraphQL schema. It uses SchemaGenerator to dynamically build Strawberry
input classes from TTS_CONFIG_DEFS and TRANSLATOR_CONFIG_DEFS.

Key Feature:
- Translates internal short keys (e.g., 'TE', 'CS') into descriptive
  GraphQL field names (e.g., 'engine', 'chunk_size') to maintain a clean API
  while keeping a single source of truth.
"""

from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS
from core.tts_args_definition import TTS_CONFIG_DEFS
from server.graphql.schema_generator import SchemaGenerator

# =========================== Dynamically Generated Input Types =========================== #

# TTSInput: Dynamically mapped from TTS_CONFIG_DEFS.
# Includes 'text_content', 'file_upload' and all core TTS parameters
# automatically converted to snake_case descriptive names.
TTSInput = SchemaGenerator.generate_input_type(
    config_defs=TTS_CONFIG_DEFS, type_name="TTSInput"
)

# TranslationInput: Dynamically mapped from TRANSLATOR_CONFIG_DEFS.
# Includes 'text_content', 'file_upload' and all translation parameters
# (e.g., engine, source_language, target_language, chunk_size).
TranslationInput = SchemaGenerator.generate_input_type(
    config_defs=TRANSLATOR_CONFIG_DEFS, type_name="TranslationInput"
)

# =========================== Benefits of Dynamic Generation =========================== #
# 1. Single Source of Truth: Parameters defined once in core definitions.
# 2. Automated API Mapping: Short CLI/ENV keys -> Descriptive GraphQL fields.
# 3. Validation: Enums (choices) and Python types are enforced at the GraphQL layer.
# 4. Effortless Maintenance: Adding a parameter to definitions instantly
#    updates both the CLI and the GraphQL API.
