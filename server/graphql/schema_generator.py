"""
Schema Generator for GraphQL Server

Dynamically generates GraphQL input types from existing argument definitions
to maintain a single source of truth between CLI arguments and GraphQL schema.
"""

from typing import Type, List, Dict, Any, Optional
from enum import Enum
import strawberry
from strawberry.file_uploads import Upload


class SchemaGenerator:
    """Generates Strawberry GraphQL input types from configuration definitions."""

    @staticmethod
    def generate_input_type(
        config_defs: List[Dict[str, Any]],
        type_name: str
    ) -> Type:
        """
        Generates a Strawberry input type from config definitions.

        Args:
            config_defs: List of parameter definitions (TTS_CONFIG_DEFS or TRANSLATOR_CONFIG_DEFS)
            type_name: Name for the generated type (e.g., "TTSInput")

        Returns:
            Dynamically created Strawberry input class

        Process:
        1. Create field dictionary from config_defs
        2. Map Python types to GraphQL types
        3. Generate Enums for 'choices' fields
        4. Add file_upload and text_content fields
        5. Create Strawberry input class with type()
        """
        fields = {}
        
        # Add input source fields first
        fields['text_content'] = Optional[str]
        fields['file_upload'] = Optional[Upload]
        
        # Process each config definition
        for config in config_defs:
            field_name = SchemaGenerator._convert_key_to_field_name(config['key'])
            
            # Handle choices - create enum type
            if 'choices' in config and config['choices']:
                enum_name = f"{type_name}{field_name.title().replace('_', '')}Enum"
                enum_type = SchemaGenerator._create_enum_from_choices(
                    enum_name, 
                    config['choices']
                )
                field_type = enum_type
            else:
                # Map Python type to GraphQL type
                py_type = config.get('type', str)
                field_type = SchemaGenerator._map_python_type_to_graphql(py_type)
            
            # Handle boolean flags with action='store_true'
            if config.get('action') == 'store_true':
                field_type = bool
            
            # Get default value
            default_value = config.get('default')
            
            # Store field with type and default
            fields[field_name] = (field_type, default_value)
        
        # Create the input class dynamically
        # We need to create annotations dict and set defaults
        annotations = {}
        defaults = {}
        
        for field_name, field_info in fields.items():
            if isinstance(field_info, tuple):
                field_type, default_value = field_info
                annotations[field_name] = field_type
                defaults[field_name] = default_value
            else:
                # For Optional fields without defaults
                annotations[field_name] = field_info
                defaults[field_name] = None
        
        # Create the class
        namespace = {
            '__annotations__': annotations,
            **defaults
        }
        
        input_class = type(type_name, (), namespace)
        
        # Decorate with strawberry.input
        return strawberry.input(input_class)

    @staticmethod
    def _map_python_type_to_graphql(py_type: Type) -> Type:
        """
        Maps Python types to GraphQL scalar types.
        
        Args:
            py_type: Python type (str, int, float, bool)
            
        Returns:
            Corresponding GraphQL type
        """
        type_mapping = {
            str: str,
            int: int,
            float: float,
            bool: bool
        }
        
        return type_mapping.get(py_type, str)

    @staticmethod
    def _create_enum_from_choices(name: str, choices: List[str]) -> Type[Enum]:
        """
        Creates a GraphQL Enum from choices list.
        
        Args:
            name: Name for the enum type
            choices: List of valid string values
            
        Returns:
            Strawberry enum type
        """
        # Create enum members dict
        enum_members = {choice: choice for choice in choices}
        
        # Create the enum class
        enum_class = Enum(name, enum_members)
        
        # Decorate with strawberry.enum
        return strawberry.enum(enum_class)

    @staticmethod
    def _convert_key_to_field_name(key: str) -> str:
        """
        Converts short key to GraphQL field name.
        
        Examples:
            TE -> engine
            CS -> chunk_size
            G_CRED -> google_credentials
            OFF_VOICE -> offline_voice
            
        Rules:
        - TE (TTS_ENGINE/TRANSLATION_ENGINE) -> engine
        - CS (CHUNK_SIZE) -> chunk_size
        - Convert to snake_case
        - Use descriptive names based on common patterns
        
        Args:
            key: Short key from config (e.g., "TE", "CS", "G_CRED")
            
        Returns:
            GraphQL field name in snake_case
        """
        # Special mappings for common abbreviations
        special_mappings = {
            'TE': 'engine',
            'CS': 'chunk_size',
            'CP': 'chunk_by_paragraph',
            'SR': 'speaking_rate',
            'OT': 'output_type',
            'MFD': 'max_file_duration',
            'COD': 'clean_output_directory',
            'OFF_VOICE': 'offline_voice',
            'L_CODE': 'language_code',
            'G_CRED': 'google_credentials',
            'G_VOICE': 'google_voice',
            'C_MODEL': 'coqui_model',
            'C_SPEAKER': 'coqui_speaker',
            'C_WAV': 'coqui_wav',
            'C_RATE': 'coqui_sample_rate',
            'SL': 'source_language',
            'TL': 'target_language',
            'TP': 'translation_prompt',
            'O_KEY': 'openai_api_key',
            'O_MODEL': 'openai_model',
            'G_MODEL': 'gemini_model',
            'D_KEY': 'deepl_api_key',
            'MR': 'max_retries',
            'RD': 'retry_delay'
        }
        
        if key in special_mappings:
            return special_mappings[key]
        
        # Fallback: convert to lowercase and replace underscores
        return key.lower()
