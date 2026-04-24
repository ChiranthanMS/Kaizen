#!/usr/bin/env python3
"""
Setup script for Travel Expense Auditing System
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_node_version():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run("node --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version} is installed")
            return True
    except:
        pass
    
    print("❌ Node.js is not installed or not in PATH")
    print("Please install Node.js from https://nodejs.org/")
    return False

def setup_backend():
    """Setup backend dependencies"""
    print("\n📦 Setting up Backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    os.chdir(backend_dir)
    
    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    # Activate virtual environment and install dependencies
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    os.chdir("..")
    return True

def setup_frontend():
    """Setup frontend dependencies"""
    print("\n🎨 Setting up Frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    os.chdir(frontend_dir)
    
    if not run_command("npm install", "Installing Node.js dependencies"):
        os.chdir("..")
        return False
    
    os.chdir("..")
    return True

def create_env_file():
    """Create .env file from template"""
    print("\n⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        # Copy example file
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Created .env file from .env.example")
        print("⚠️  Please update .env file with your actual credentials")
    else:
        # Create basic .env file
        env_content = """# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/auth_db
GOOGLE_CLIENT_ID=your_google_client_id_here
JWT_SECRET_KEY=your_jwt_secret_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
SENDGRID_FROM=your_email@domain.com

# OCR Configuration
OCR_SPACE_API_KEY=your_ocr_space_api_key_here

# PostgreSQL Configuration
POSTGRES_URL=postgresql://postgres:password@localhost:5432/travel_expense_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=travel_expense_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created basic .env file")
        print("⚠️  Please update .env file with your actual credentials")
    
    return True

def check_database_requirements():
    """Check database requirements"""
    print("\n🗄️ Checking database requirements...")
    
    print("📋 Database Requirements:")
    print("  1. MongoDB - for user authentication")
    print("     - Local: Install MongoDB Community Server")
    print("     - Cloud: Use MongoDB Atlas (recommended)")
    print("  2. PostgreSQL - for bill data storage")
    print("     - Local: Install PostgreSQL")
    print("     - Cloud: Use Supabase, AWS RDS, or Google Cloud SQL (recommended)")
    
    print("\n⚠️  Make sure to:")
    print("  - Create databases with appropriate names")
    print("  - Update connection strings in .env file")
    print("  - Ensure network connectivity to cloud databases")
    
    return True

def create_start_scripts():
    """Create start scripts for easy development"""
    print("\n📝 Creating start scripts...")
    
    # Backend start script
    if platform.system() == "Windows":
        backend_script = """@echo off
echo Starting Travel Expense Auditing Backend...
cd backend
call venv\\Scripts\\activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
"""
        with open("start_backend.bat", 'w') as f:
            f.write(backend_script)
        
        frontend_script = """@echo off
echo Starting Travel Expense Auditing Frontend...
cd frontend
npm start
pause
"""
        with open("start_frontend.bat", 'w') as f:
            f.write(frontend_script)
        
        print("✅ Created start_backend.bat and start_frontend.bat")
    else:
        backend_script = """#!/bin/bash
echo "Starting Travel Expense Auditing Backend..."
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
        with open("start_backend.sh", 'w') as f:
            f.write(backend_script)
        os.chmod("start_backend.sh", 0o755)
        
        frontend_script = """#!/bin/bash
echo "Starting Travel Expense Auditing Frontend..."
cd frontend
npm start
"""
        with open("start_frontend.sh", 'w') as f:
            f.write(frontend_script)
        os.chmod("start_frontend.sh", 0o755)
        
        print("✅ Created start_backend.sh and start_frontend.sh")
    
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Update .env file with your actual database credentials")
    print("2. Set up your databases:")
    print("   - MongoDB for user authentication")
    print("   - PostgreSQL for bill data storage")
    print("3. Start the backend server:")
    if platform.system() == "Windows":
        print("   - Run: start_backend.bat")
    else:
        print("   - Run: ./start_backend.sh")
    print("4. Start the frontend server (in a new terminal):")
    if platform.system() == "Windows":
        print("   - Run: start_frontend.bat")
    else:
        print("   - Run: ./start_frontend.sh")
    print("5. Access the application:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:8000")
    print("   - API Documentation: http://localhost:8000/docs")
    print("\n📚 For detailed setup instructions, see API_DOCUMENTATION.md")

def main():
    """Main setup function"""
    print("🚀 Travel Expense Auditing System Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        (create_env_file, "Environment configuration"),
        (setup_backend, "Backend setup"),
        (setup_frontend, "Frontend setup"),
        (check_database_requirements, "Database requirements check"),
        (create_start_scripts, "Start scripts creation")
    ]
    
    failed_steps = []
    for step_func, step_name in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Setup failed. The following steps had errors:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease resolve the errors and run setup again.")
        sys.exit(1)
    
    print_next_steps()

if __name__ == "__main__":
    main()