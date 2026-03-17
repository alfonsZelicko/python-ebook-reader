"""
Schema Generator for GraphQL Server

Dynamically generates GraphQL input types from existing argument definitions
to maintain a single source of truth between CLI arguments and GraphQL schema.
"""

import logging
from enum import Enum
from typing import Type, List, Dict, Any, Optional

import strawberry
from strawberry.file_uploads import Upload


class SchemaGenerator:
    """Generates Strawberry GraphQL input types from configuration definitions."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @staticmethod
    def generate_input_type(config_defs: List[Dict[str, Any]], type_name: str) -> Type:
        """
        Generates a Strawberry input type from config definitions.
        """
        annotations = {
            "text_content": Optional[str],
            "file_upload": Optional[Upload],
        }
        namespace = {
            "text_content": None,
            "file_upload": None,
        }

        # List if params that should be UNSET in GraphQL
        CORE_ENV_PARAMS = [
            # Translator
            "TE",
            # "SL",
            # "TL",
            "O_KEY",
            "G_KEY",
            "D_KEY",
            "O_MODEL",
            "G_MODEL",
            # TTS
            "L_CODE",
            "G_VOICE",
            "OFF_VOICE",
            "C_MODEL",
            "C_SPEAKER",
            "C_WAV",
        ]

        for config in config_defs:
            # field_name = SchemaGenerator._convert_key_to_field_name(config["key"])
            field_name = config["long_name"].lower().replace("-", "_")

            # 1. Determine the Field Type
            if "choices" in config and config["choices"]:
                enum_name = f"{type_name}{''.join(x.capitalize() for x in field_name.split('_'))}Enum"
                field_type = SchemaGenerator._create_enum_from_choices(
                    enum_name, config["choices"]
                )
            else:
                py_type = config.get("type", str)
                field_type = py_type if py_type in (str, int, float, bool) else str

            # 2. Handle specific argument actions
            if config.get("action") == "store_true":
                field_type = bool

            # 3. Handle Optionality & Defaults
            # If it's a core parameter like 'translationEngine' (TE), we might want it required
            # or keep it Optional to fall back to global defaults.
            field_type = Optional[field_type]

            # 4. Create the Strawberry Field with description
            description = config.get("help", "")
            # default_value = config.get("default")

            annotations[field_name] = field_type
            # Strawberry uses strawberry.field for defaults and metadata
            if config["key"] in CORE_ENV_PARAMS:
                default_to_use = strawberry.UNSET
            else:
                default_to_use = config.get("default", strawberry.UNSET)

            namespace[field_name] = strawberry.field(
                default=default_to_use, description=config.get("help", "")
            )

        # Create the class dynamically
        input_class = type(type_name, (), {"__annotations__": annotations, **namespace})
        return strawberry.input(input_class)

    @staticmethod
    def _create_enum_from_choices(name: str, choices: List[str]) -> Type[Enum]:
        # Sanitize choice names (must be valid Python identifiers for Enum)
        # e.g. "gpt-4" -> "GPT_4"
        members = {}
        for choice in choices:
            clean_name = str(choice).replace("-", "_").replace(".", "_").upper()
            if clean_name[0].isdigit():
                clean_name = f"V_{clean_name}"
            members[clean_name] = choice

        enum_class = Enum(name, members)
        return strawberry.enum(enum_class)

    @staticmethod
    def convert_key_to_field_name(key: str, CONFIG_DEFS: List[Dict[str, Any]]) -> str:
        """
        Dynamically converts short key (TE, CS) to descriptive field name
        using the 'name' attribute from the imported definitions.
        """
        special_mappings = {
            item["key"]: item["long_name"].lower() for item in CONFIG_DEFS
        }

        if key in special_mappings:
            return special_mappings[key]

        return key.lower()
