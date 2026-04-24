# Professional Travel Expense Management System - Startup Script
# This script starts both backend and frontend servers

Write-Host "🚀 Starting Professional Travel Expense Management System..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan

# Check if required directories exist
if (-not (Test-Path ".\backend")) {
    Write-Host "❌ Backend directory not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".\frontend")) {
    Write-Host "❌ Frontend directory not found!" -ForegroundColor Red
    exit 1
}

# Function to start backend
function Start-Backend {
    Write-Host "🔧 Starting Backend Server..." -ForegroundColor Yellow
    Set-Location ".\backend"
    
    # Check if virtual environment exists
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "📦 Activating Python virtual environment..." -ForegroundColor Blue
        & "venv\Scripts\Activate.ps1"
    }
    
    # Start the backend server
    Write-Host "🌐 Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Function to start frontend
function Start-Frontend {
    Write-Host "🎨 Starting Frontend Server..." -ForegroundColor Yellow
    Set-Location ".\frontend"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Blue
        npm install
    }
    
    # Start the frontend server
    Write-Host "🌐 Starting React development server on http://localhost:3000" -ForegroundColor Green
    npm start
}

# Ask user which component to start
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "1. Start Backend Only" -ForegroundColor White
Write-Host "2. Start Frontend Only" -ForegroundColor White
Write-Host "3. Start Both (Recommended)" -ForegroundColor Green
Write-Host "4. Exit" -ForegroundColor Red

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Start-Backend
    }
    "2" {
        Start-Frontend
    }
    "3" {
        Write-Host "🚀 Starting both Backend and Frontend..." -ForegroundColor Green
        Write-Host "⚠️  Backend will start first. Once it's running, open a new terminal and run this script again to start the frontend." -ForegroundColor Yellow
        Write-Host "⚠️  Or manually run 'npm start' in the frontend directory." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to start the backend server..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Start-Backend
    }
    "4" {
        Write-Host "👋 Goodbye!" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
        exit 1
    }
}

Write-Host "🎉 Application started successfully!" -ForegroundColor Green
Write-Host "📱 Access the application at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend API available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan