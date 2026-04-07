#!/bin/bash
# Quick Start Script for Big Homie
# This script will set up and run Big Homie in one command

echo "🏠 Big Homie Quick Start"
echo "========================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys before running!"
    echo "   At minimum, add one of:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - OPENAI_API_KEY"
    echo "   - OPENROUTER_API_KEY"
    echo ""
    echo "   Then run this script again."
    exit 0
fi

# Check if at least one API key is configured
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env && \
   ! grep -q "OPENAI_API_KEY=sk-" .env && \
   ! grep -q "OPENROUTER_API_KEY=sk-" .env; then
    echo "⚠️  No API keys found in .env file!"
    echo "   Please edit .env and add at least one API key."
    exit 1
fi

echo "✅ Configuration file found"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Big Homie..."
echo ""

# Run the application
python main.py

# Deactivate virtual environment on exit
deactivate
