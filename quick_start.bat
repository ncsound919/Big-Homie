@echo off
REM Quick Start Script for Big Homie
REM This script will set up and run Big Homie in one command

echo Big Homie Quick Start
echo ========================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo Python found
echo.

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env and add your API keys before running!
    echo At minimum, add one of:
    echo - ANTHROPIC_API_KEY
    echo - OPENAI_API_KEY
    echo - OPENROUTER_API_KEY
    echo.
    echo Then run this script again.
    pause
    exit /b 0
)

echo Configuration file found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo Setup complete!
echo.
echo Starting Big Homie...
echo.

REM Run the application
python main.py

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat
