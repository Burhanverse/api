#!/usr/bin/env bash
# Quick setup script for FastAPI + ScrapeGraphAI Parser
# Run with: bash setup.sh or ./setup.sh

set -e  # Exit on error

echo "🚀 Setting up FastAPI + ScrapeGraphAI Parser"
echo "============================================="
echo ""

# Set Python and pip commands to use 3.12
PYTHON_CMD="python3.12"
PIP_CMD="pip3.12"

# Check if python3.12 is available
echo "📌 Checking Python 3.12..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ python3.12 not found"
    echo "   Please install Python 3.12 first"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+\.\d+')
echo "   Python version: $python_version"
echo "✓ Python 3.12 OK"
echo ""

# Check if pip3.12 is available
echo "📌 Checking pip3.12..."
if ! command -v $PIP_CMD &> /dev/null; then
    echo "❌ pip3.12 not found"
    echo "   Trying to use: $PYTHON_CMD -m pip instead"
    PIP_CMD="$PYTHON_CMD -m pip"
fi
echo "✓ pip OK"
echo ""

# Check for GEMINI_API_KEY in .env file or environment
if [ -f .env ]; then
    echo "✓ .env file found"
    source .env
elif [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not set"
    echo ""
    echo "You need a Gemini API key to use AI parsing."
    echo "Get one from: https://makersuite.google.com/app/apikey"
    echo ""
    echo "After getting your key, create a .env file:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your API key"
    echo ""
    read -p "Press Enter to continue without API key (you can set it later)..."
else
    echo "✓ GEMINI_API_KEY found"
fi
echo ""

# Install Python dependencies
echo "📦 Installing Python packages..."
$PIP_CMD install -r parserapi/requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    exit 1
fi
echo "✓ Python packages installed"
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers (this may take a while)..."
$PYTHON_CMD -m playwright install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Playwright browsers"
    exit 1
fi
echo "✓ Playwright browsers installed"
echo ""

# Summary
echo "============================================="
echo "✅ Setup complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo ""

if [ -z "$GEMINI_API_KEY" ]; then
    echo "1. Get your Gemini API key:"
    echo "   → https://makersuite.google.com/app/apikey"
    echo ""
    echo "2. Create .env file and set the API key:"
    echo "   cp .env.example .env"
    echo "   # Edit .env and add: GEMINI_API_KEY=your-api-key"
    echo ""
    echo "3. Start the server:"
else
    echo "1. Start the server:"
fi

echo "   $PYTHON_CMD -m parserapi"
echo ""
echo "2. Open the interactive API docs:"
echo "   → http://localhost:5000/docs"
echo ""
echo "3. Test with curl:"
echo '   curl "http://localhost:5000/parse?url=https://techcrunch.com"'
echo ""
echo "For more info, see README.md or PRODUCTION_READY.md"
echo ""
