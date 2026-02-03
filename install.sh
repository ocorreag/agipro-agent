#!/bin/bash
# CAUSA Agent - Installation Script for macOS/Linux

set -e

echo "🦋 CAUSA Agent - Installation"
echo "=============================="

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python is not installed"
    echo "Please install Python 3.11 or higher from https://python.org"
    exit 1
fi

# Verify Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "📦 Found Python $PYTHON_VERSION"

# Check if version is 3.11+
MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "⚠️  Warning: Python 3.11+ is recommended (found $PYTHON_VERSION)"
    echo "Some features may not work correctly."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "📁 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r src/requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p publicaciones/drafts
mkdir -p publicaciones/imagenes
mkdir -p memory
mkdir -p linea_grafica

echo ""
echo "=============================="
echo "✅ Installation complete!"
echo ""
echo "To run the application:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Add your OpenAI API key to .env"
echo ""
echo "  3. Start the application:"
echo "     cd src && streamlit run app.py"
echo ""
echo "=============================="
