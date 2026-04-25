#!/usr/bin/env python3
"""
Script to start both backend and frontend servers for development
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def run_backend():
    """Start the FastAPI backend server"""
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Check for virtual environment
    venv_python = Path("venv") / ("Scripts" if os.name == "nt" else "bin") / "python"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable

    print(f"Starting FastAPI backend server using {python_exe}...")
    try:
        subprocess.run([
            python_exe, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\nBackend server stopped")
    except Exception as e:
        print(f"Backend server error: {e}")

def run_frontend():
    """Start the React frontend server"""
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    print("Starting React frontend server...")
    try:
        subprocess.run(["npm", "start"], check=True, shell=True)
    except KeyboardInterrupt:
        print("\nFrontend server stopped")
    except Exception as e:
        print(f"Frontend server error: {e}")

def main():
    print("=== Starting Development Servers ===\n")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\nShutting down servers...")

if __name__ == "__main__":
    main()