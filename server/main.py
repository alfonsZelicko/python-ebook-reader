"""
FastAPI application with Strawberry GraphQL for TTS and Translation services.

This is the main entry point for the GraphQL server. It initializes FastAPI,
loads configuration, sets up logging, generates GraphQL input types from
existing argument definitions, and mounts the GraphQL endpoint.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 14.4
"""

import sys
from pathlib import Path
from typing import Optional
import time

# Add project root to Python path to import core modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
import strawberry
import uvicorn

from server.config import ServerConfig
from server.logger import setup_logger, RequestLogger
from server.schema import Query, Mutation
from server.schema_generator import SchemaGenerator
from core.tts_args_definition import TTS_CONFIG_DEFS
from core.translator_args_definition import TRANSLATOR_CONFIG_DEFS


# ============================================================================
# Application Initialization
# ============================================================================

def create_app(config: Optional[ServerConfig] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        config: ServerConfig instance (if None, loads from .env.server)
        
    Returns:
        Configured FastAPI application
        
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    # Load configuration
    if config is None:
        config = ServerConfig.load_from_env()
    
    # Setup logger
    logger = setup_logger(config)
    request_logger = RequestLogger(logger)
    
    logger.info("=" * 80)
    logger.info("GraphQL Server Initialization")
    logger.info("=" * 80)
    logger.info(f"Configuration: {config}")
    
    # Create FastAPI app
    app = FastAPI(
        title="TTS & Translation GraphQL API",
        description="Unified GraphQL API for Text-to-Speech and Translation services",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store config and logger in app state for access in resolvers
    app.state.config = config
    app.state.logger = logger
    app.state.request_logger = request_logger
    
    # ========================================================================
    # Generate GraphQL Input Types
    # ========================================================================
    
    logger.info("Generating GraphQL input types from argument definitions...")
    
    try:
        # Generate TTSInput from TTS_CONFIG_DEFS
        TTSInput = SchemaGenerator.generate_input_type(
            TTS_CONFIG_DEFS,
            "TTSInput"
        )
        logger.info(f"✓ Generated TTSInput type with {len(TTS_CONFIG_DEFS)} parameters")
        
        # Generate TranslationInput from TRANSLATOR_CONFIG_DEFS
        TranslationInput = SchemaGenerator.generate_input_type(
            TRANSLATOR_CONFIG_DEFS,
            "TranslationInput"
        )
        logger.info(f"✓ Generated TranslationInput type with {len(TRANSLATOR_CONFIG_DEFS)} parameters")
        
    except Exception as e:
        logger.error(f"Failed to generate input types: {e}", exc_info=True)
        raise
    
    # ========================================================================
    # Create Strawberry GraphQL Schema
    # ========================================================================
    
    logger.info("Creating Strawberry GraphQL schema...")
    
    try:
        schema = strawberry.Schema(
            query=Query,
            mutation=Mutation
        )
        logger.info("✓ GraphQL schema created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create GraphQL schema: {e}", exc_info=True)
        raise
    
    # ========================================================================
    # Request Logging Middleware
    # ========================================================================
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        Middleware to log all HTTP requests with timing information.
        
        Requirements: 8.2, 8.4, 14.4
        """
        start_time = time.time()
        
        # Log incoming request
        request_logger.logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'client': request.client.host if request.client else 'unknown'
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            request_logger.logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            request_logger.log_error(
                f"Request failed: {request.method} {request.url.path}",
                context={
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'error': str(e)
                }
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred"
                }
            )
    
    # ========================================================================
    # Mount GraphQL Endpoint
    # ========================================================================
    
    logger.info("Mounting GraphQL endpoint...")
    
    # Create GraphQL router with GraphiQL enabled
    graphql_app = GraphQLRouter(
        schema,
        graphql_ide="graphiql",  # Enable GraphiQL playground
        path="/graphql"
    )
    
    # Mount GraphQL at /graphql
    app.include_router(graphql_app, prefix="")
    
    logger.info("✓ GraphQL endpoint mounted at /graphql")
    logger.info("✓ GraphiQL playground available at /graphql")
    
    # ========================================================================
    # Health Check Endpoint
    # ========================================================================
    
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint for monitoring server status.
        
        Returns:
            JSON response with server status and configuration info
            
        Requirements: 14.4
        """
        return {
            "status": "healthy",
            "service": "TTS & Translation GraphQL API",
            "version": "1.0.0",
            "endpoints": {
                "graphql": "/graphql",
                "graphiql": "/graphql (browser)",
                "health": "/health"
            },
            "configuration": {
                "allowed_tts_engines": config.allowed_tts_engines,
                "allowed_translator_engines": config.allowed_translator_engines,
                "max_concurrent_jobs": config.max_concurrent_jobs,
                "max_upload_size_mb": config.max_upload_size_mb
            }
        }
    
    # ========================================================================
    # Startup Event
    # ========================================================================
    
    @app.on_event("startup")
    async def startup_event():
        """
        Runs when the server starts.
        
        Performs:
        - Validation of required dependencies
        - Creation of temporary directories
        - Logging of startup information
        
        Requirements: 1.3, 1.4
        """
        logger.info("=" * 80)
        logger.info("Server Startup")
        logger.info("=" * 80)
        
        # Create temp directory if it doesn't exist
        temp_dir = Path(config.temp_directory)
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Temporary directory ready: {temp_dir.absolute()}")
        
        # Validate dependencies
        try:
            import strawberry
            import fastapi
            import uvicorn
            logger.info("✓ All required dependencies available")
        except ImportError as e:
            logger.error(f"✗ Missing required dependency: {e}")
            raise
        
        # Log server configuration
        logger.info(f"Server will listen on: http://{config.host}:{config.port}")
        logger.info(f"GraphQL endpoint: http://{config.host}:{config.port}/graphql")
        logger.info(f"GraphiQL playground: http://{config.host}:{config.port}/graphql")
        logger.info(f"Health check: http://{config.host}:{config.port}/health")
        logger.info(f"API docs: http://{config.host}:{config.port}/docs")
        
        logger.info("=" * 80)
        logger.info("Server is ready to accept connections")
        logger.info("=" * 80)
    
    # ========================================================================
    # Shutdown Event
    # ========================================================================
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Runs when the server shuts down.
        
        Performs cleanup tasks like closing connections and removing temp files.
        """
        logger.info("=" * 80)
        logger.info("Server Shutdown")
        logger.info("=" * 80)
        logger.info("Performing cleanup...")
        
        # Future: Add cleanup tasks here (close DB connections, etc.)
        
        logger.info("✓ Cleanup completed")
        logger.info("Server stopped")
    
    return app


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    Main entry point for running the server.
    
    Supports command-line arguments:
    - --generate-env: Generate .env.server template file
    - No arguments: Start the GraphQL server
    
    Requirements: 9.5
    """
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="GraphQL Server for TTS & Translation Services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the server
  python -m server.main
  
  # Generate .env.server template
  python -m server.main --generate-env
  
  # Generate template to custom location
  python -m server.main --generate-env --output custom.env
        """
    )
    
    parser.add_argument(
        "--generate-env",
        action="store_true",
        help="Generate .env.server template file with default configuration"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=".env.server",
        help="Output path for generated .env file (default: .env.server)"
    )
    
    args = parser.parse_args()
    
    # Handle --generate-env command
    if args.generate_env:
        try:
            ServerConfig.generate_env_template(args.output)
            print(f"✓ Successfully generated .env.server template at: {args.output}")
            print(f"\nNext steps:")
            print(f"1. Review and customize the configuration in {args.output}")
            print(f"2. Start the server with: python -m server.main")
            return
        except Exception as e:
            print(f"✗ Failed to generate .env.server template: {e}")
            sys.exit(1)
    
    # Default: Start the server
    try:
        # Load configuration
        config = ServerConfig.load_from_env()
        
        # Create app
        app = create_app(config)
        
        # Run server with uvicorn
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            log_level=config.log_level.lower(),
            timeout_keep_alive=config.request_timeout_seconds
        )
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
