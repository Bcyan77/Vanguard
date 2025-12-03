@echo off
REM Quick start script for Vanguard development

echo ========================================
echo Vanguard Development Environment
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [!] .env file not found!
    echo [*] Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo [!] Please edit .env and add your Bungie API credentials
    echo [!] Then run this script again
    pause
    exit /b 1
)

echo [*] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [!] Docker is not installed or not running
    echo [!] Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo [*] Docker is ready
echo.

REM Check if Django project exists
if not exist manage.py (
    echo [*] Django project not initialized
    echo [*] Building Docker image...
    docker-compose build
    
    echo [*] Initializing Django project...
    docker-compose run --rm web django-admin startproject vanguard .
    docker-compose run --rm web python manage.py startapp accounts
    docker-compose run --rm web python manage.py startapp parties
    
    echo [*] Creating directories...
    mkdir templates\accounts 2>nul
    mkdir templates\parties 2>nul
    mkdir static 2>nul
    
    echo [*] Running initial migrations...
    docker-compose run --rm web python manage.py migrate
    
    echo.
    echo [*] Django project initialized!
    echo.
)

echo ========================================
echo Starting Development Server
echo ========================================
echo.
echo [!] IMPORTANT: Before starting, make sure:
echo     1. ngrok is running: ngrok http 8000
echo     2. NGROK_URL in .env is updated
echo     3. Bungie app redirect URL is updated
echo.
echo [*] Starting Docker containers...
echo [*] Access the app at your ngrok URL
echo.

docker-compose up
