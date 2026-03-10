"""
Unit tests for CLI commands.

Tests the --generate-env command functionality.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.config import ServerConfig


class TestCLICommands(unittest.TestCase):
    """Test CLI command functionality."""
    
    def test_generate_env_template_default_path(self):
        """Test generating .env.server template at default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, ".env.server")
            
            # Generate template
            ServerConfig.generate_env_template(output_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(output_path))
            
            # Verify file content
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for key configuration sections
            self.assertIn("SERVER_HOST=", content)
            self.assertIn("SERVER_PORT=", content)
            self.assertIn("LOG_LEVEL=", content)
            self.assertIn("ALLOWED_TTS_ENGINES=", content)
            self.assertIn("ALLOWED_TRANSLATOR_ENGINES=", content)
            self.assertIn("MAX_CONCURRENT_JOBS=", content)
            
            # Check for comments
            self.assertIn("# GraphQL Server Configuration", content)
            self.assertIn("# SERVER SETTINGS", content)
            self.assertIn("# LOGGING CONFIGURATION", content)
            self.assertIn("# ENGINE ALLOWLISTS", content)
    
    def test_generate_env_template_custom_path(self):
        """Test generating .env.server template at custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "custom.env")
            
            # Generate template
            ServerConfig.generate_env_template(output_path)
            
            # Verify file exists at custom path
            self.assertTrue(os.path.exists(output_path))
    
    def test_generated_template_has_all_options(self):
        """Test that generated template includes all configuration options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, ".env.server")
            
            # Generate template
            ServerConfig.generate_env_template(output_path)
            
            # Read content
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify all configuration options are present
            required_options = [
                "SERVER_HOST",
                "SERVER_PORT",
                "LOG_LEVEL",
                "LOG_FILE",
                "LOG_FORMAT",
                "MAX_UPLOAD_SIZE_MB",
                "TEMP_DIRECTORY",
                "ALLOWED_TTS_ENGINES",
                "ALLOWED_TRANSLATOR_ENGINES",
                "MAX_CONCURRENT_JOBS",
                "JOB_CLEANUP_HOURS",
                "REQUEST_TIMEOUT_SECONDS"
            ]
            
            for option in required_options:
                self.assertIn(option, content, f"Missing configuration option: {option}")
    
    def test_generated_template_has_helpful_comments(self):
        """Test that generated template includes helpful comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, ".env.server")
            
            # Generate template
            ServerConfig.generate_env_template(output_path)
            
            # Read content
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify helpful comments are present
            helpful_comments = [
                "Use 0.0.0.0 to accept connections from any network interface",
                "Available options: OFFLINE, ONLINE, G_CLOUD, COQUI",
                "Available options: OPENAI, GEMINI, DEEPL",
                "Maximum time allowed for a single GraphQL request",
                "Changes require server restart to take effect"
            ]
            
            for comment in helpful_comments:
                self.assertIn(comment, content, f"Missing helpful comment: {comment}")


if __name__ == "__main__":
    unittest.main()
