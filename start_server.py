#!/usr/bin/env python3
"""
Simple startup script for the GraphQL server.

This script provides a convenient way to start the server from the project root
with optional command-line arguments for host and port configuration.

Requirements: 1.1
"""

import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.main import main as server_main
from server.config import ServerConfig
import uvicorn


def main():
    """
    Startup script entry point.
    
    Supports command-line arguments:
    - --host: Server host address (default: from .env.server or 0.0.0.0)
    - --port: Server port (default: from .env.server or 8000)
    - --generate-env: Generate .env.server template file
    """
    parser = argparse.ArgumentParser(
        description="GraphQL Server for TTS & Translation Services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with default configuration
  python start_server.py
  
  # Start server on custom host and port
  python start_server.py --host 127.0.0.1 --port 9000
  
  # Generate .env.server template
  python start_server.py --generate-env
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Server host address (overrides .env.server)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Server port (overrides .env.server)"
    )
    
    parser.add_argument(
        "--generate-env",
        action="store_true",
        help="Generate .env.server template file"
    )
    
    args = parser.parse_args()
    
    # Handle --generate-env command
    if args.generate_env:
        try:
            ServerConfig.generate_env_template(".env.server")
            print("✓ Successfully generated .env.server template")
            print("\nNext steps:")
            print("1. Review and customize the configuration in .env.server")
            print("2. Start the server with: python start_server.py")
            return
        except Exception as e:
            print(f"✗ Failed to generate .env.server template: {e}")
            sys.exit(1)
    
    # Start the server
    try:
        # Load configuration
        config = ServerConfig.load_from_env()
        
        # Override with command-line arguments if provided
        if args.host:
            config.host = args.host
        if args.port:
            config.port = args.port
        
        # Import and create app
        from server.main import create_app
        app = create_app(config)
        
        # Run server with uvicorn
        print(f"Starting GraphQL server on http://{config.host}:{config.port}")
        print(f"GraphQL endpoint: http://{config.host}:{config.port}/graphql")
        print(f"GraphiQL playground: http://{config.host}:{config.port}/graphql")
        print(f"Health check: http://{config.host}:{config.port}/health")
        print(f"API docs: http://{config.host}:{config.port}/docs")
        print("\nPress Ctrl+C to stop the server")
        
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
