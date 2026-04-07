#!/bin/bash
# Build Big Homie executable for all platforms

set -e

echo "🚀 Building Big Homie..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Convert logo if needed (PyInstaller works better with .ico on Windows)
if command -v convert &> /dev/null; then
    echo "Converting logo to .ico format..."
    convert logo.png -resize 256x256 logo.ico
else
    echo "ImageMagick not found, skipping .ico conversion"
fi

# Build executable
echo "Building executable..."
pyinstaller big_homie.spec --clean --noconfirm

echo "✅ Build complete!"
echo ""
echo "Executable location:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  macOS: dist/BigHomie.app"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  Windows: dist/BigHomie.exe"
else
    echo "  Linux: dist/BigHomie"
fi

echo ""
echo "To run the application:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  open dist/BigHomie.app"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  dist\\BigHomie.exe"
else
    echo "  ./dist/BigHomie"
fi
