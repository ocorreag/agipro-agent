@echo off
REM CAUSA Agent - Installation Script for Windows

echo.
echo ==============================
echo   CAUSA Agent - Installation
echo ==============================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Show Python version
echo [INFO] Found Python:
python --version
echo.

REM Create virtual environment
echo [INFO] Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo [INFO] Installing dependencies...
pip install -r src\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Create .env if it doesn't exist
if not exist .env (
    echo.
    echo [INFO] Creating .env file...
    copy .env.example .env
    echo [WARNING] Please edit .env and add your OPENAI_API_KEY
)

REM Create data directories
echo.
echo [INFO] Creating data directories...
if not exist publicaciones\drafts mkdir publicaciones\drafts
if not exist publicaciones\imagenes mkdir publicaciones\imagenes
if not exist memory mkdir memory
if not exist linea_grafica mkdir linea_grafica

echo.
echo ==============================
echo   Installation complete!
echo ==============================
echo.
echo To run the application:
echo.
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate
echo.
echo   2. Add your OpenAI API key to .env
echo.
echo   3. Start the application:
echo      cd src
echo      streamlit run app.py
echo.
echo ==============================
echo.
pause
