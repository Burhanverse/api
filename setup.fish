#!/usr/bin/env fish
# Quick setup script for FastAPI + ScrapeGraphAI Parser
# Run with: fish setup.fish

echo "🚀 Setting up FastAPI + ScrapeGraphAI Parser"
echo "============================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
set python_version (python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "   Python version: $python_version"

if test (echo $python_version | cut -d. -f1) -lt 3
    echo "❌ Python 3.8+ required"
    exit 1
end
echo "✓ Python version OK"
echo ""

# Check for GEMINI_API_KEY
if test -z "$GEMINI_API_KEY"
    echo "⚠️  GEMINI_API_KEY not set"
    echo ""
    echo "You need a Gemini API key to use AI parsing."
    echo "Get one from: https://makersuite.google.com/app/apikey"
    echo ""
    echo "After getting your key, set it with:"
    echo "  set -x GEMINI_API_KEY 'your-api-key-here'"
    echo ""
    read -P "Press Enter to continue without API key (you can set it later)..."
else
    echo "✓ GEMINI_API_KEY found"
    echo ""
end

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r parserapi/requirements.txt

if test $status -ne 0
    echo "❌ Failed to install Python packages"
    exit 1
end
echo "✓ Python packages installed"
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers (this may take a while)..."
playwright install

if test $status -ne 0
    echo "❌ Failed to install Playwright browsers"
    exit 1
end
echo "✓ Playwright browsers installed"
echo ""

# Summary
echo "============================================="
echo "✅ Setup complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo ""

if test -z "$GEMINI_API_KEY"
    echo "1. Get your Gemini API key:"
    echo "   → https://makersuite.google.com/app/apikey"
    echo ""
    echo "2. Set the API key:"
    echo "   set -x GEMINI_API_KEY 'your-api-key'"
    echo ""
    echo "3. Start the server:"
else
    echo "1. Start the server:"
end

echo "   python -m parserapi"
echo ""
echo "4. Open the interactive API docs:"
echo "   → http://localhost:5000/docs"
echo ""
echo "5. Test with curl:"
echo '   curl "http://localhost:5000/parse?url=https://techcrunch.com"'
echo ""
echo "6. Run tests:"
echo "   python test_fastapi.py"
echo ""
echo "For more info, see README.md"
echo ""
