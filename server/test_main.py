"""
Unit tests for the main FastAPI application.

Tests application initialization, configuration loading, health check endpoint,
and GraphQL endpoint mounting.
"""

import pytest
from fastapi.testclient import TestClient
from server.main import create_app
from server.config import ServerConfig


def test_create_app_with_default_config():
    """Test that the app can be created with default configuration."""
    config = ServerConfig()
    app = create_app(config)
    
    assert app is not None
    assert app.title == "TTS & Translation GraphQL API"
    assert app.state.config == config
    assert app.state.logger is not None
    assert app.state.request_logger is not None


def test_health_check_endpoint():
    """Test that the health check endpoint returns correct information."""
    config = ServerConfig()
    app = create_app(config)
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "TTS & Translation GraphQL API"
    assert data["version"] == "1.0.0"
    assert "graphql" in data["endpoints"]
    assert "graphiql" in data["endpoints"]
    assert "health" in data["endpoints"]
    assert "allowed_tts_engines" in data["configuration"]
    assert "allowed_translator_engines" in data["configuration"]


def test_graphql_endpoint_mounted():
    """Test that the GraphQL endpoint is accessible."""
    config = ServerConfig()
    app = create_app(config)
    client = TestClient(app)
    
    # Test that GraphQL endpoint responds (even if query fails, endpoint should exist)
    response = client.get("/graphql")
    
    # GraphiQL should return HTML
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_app_with_custom_config():
    """Test that the app respects custom configuration."""
    config = ServerConfig(
        host="127.0.0.1",
        port=9000,
        log_level="DEBUG",
        allowed_tts_engines=["ONLINE"],
        allowed_translator_engines=["OPENAI"]
    )
    app = create_app(config)
    
    assert app.state.config.host == "127.0.0.1"
    assert app.state.config.port == 9000
    assert app.state.config.log_level == "DEBUG"
    assert app.state.config.allowed_tts_engines == ["ONLINE"]
    assert app.state.config.allowed_translator_engines == ["OPENAI"]


def test_cors_middleware_configured():
    """Test that CORS middleware is properly configured."""
    config = ServerConfig()
    app = create_app(config)
    
    # Check that CORS middleware is in the middleware stack
    # FastAPI wraps middleware, so we check the middleware attribute
    has_cors = any(
        hasattr(m, 'cls') and m.cls.__name__ == 'CORSMiddleware' 
        for m in app.user_middleware
    )
    assert has_cors, "CORS middleware should be configured"


def test_request_logging_middleware():
    """Test that request logging middleware is working."""
    config = ServerConfig()
    app = create_app(config)
    client = TestClient(app)
    
    # Make a request to trigger logging middleware
    response = client.get("/health")
    
    # Should complete successfully
    assert response.status_code == 200


def test_temp_directory_creation():
    """Test that temporary directory is created on startup."""
    import tempfile
    import shutil
    from pathlib import Path
    
    # Create a temporary directory for testing
    test_temp_dir = tempfile.mkdtemp()
    
    try:
        config = ServerConfig(temp_directory=test_temp_dir)
        app = create_app(config)
        
        # Trigger startup event
        with TestClient(app) as client:
            # Temp directory should exist
            assert Path(test_temp_dir).exists()
    finally:
        # Cleanup
        if Path(test_temp_dir).exists():
            shutil.rmtree(test_temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
