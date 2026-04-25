#!/usr/bin/env python3
"""
Startup script for the Travel Expense API server
"""
import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Start the FastAPI server with proper configuration"""
    
    # Ensure we're in the backend directory
    backend_dir = Path(__file__).resolve().parent
    os.chdir(backend_dir)
    
    print("Starting Travel Expense API Server")
    print("=" * 50)
    print(f"Working directory: {backend_dir}")
    print(f"Python version: {sys.version}")
    print("=" * 50)
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"Server will start on: http://{host}:{port}")
    print(f"Auto-reload: {'enabled' if reload else 'disabled'}")
    print("=" * 50)
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()