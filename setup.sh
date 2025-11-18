#!/usr/bin/env bash
# Quick setup script for FastAPI + ScrapeGraphAI Parser with Ollama
# Run with: bash setup.sh or ./setup.sh

set -e

export PATH="$HOME/.local/bin:$PATH"

echo "🚀 Setting up Parser with Ollama"

PYTHON_CMD="python3.12"
PIP_CMD="pip3.12"

if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

if ! command -v $PIP_CMD &> /dev/null; then
    PIP_CMD="$PYTHON_CMD -m pip"
fi

echo "Installing Python packages..."
$PIP_CMD install -r parserapi/requirements.txt

echo "Installing Playwright browsers..."
$PYTHON_CMD -m playwright install chromium

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama in background if not running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 3
fi

# Pull llama3.2:3b model
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "Pulling llama3.2:3b model..."
    ollama pull llama3.2:3b
fi

echo ""
echo "✅ Setup complete!"
echo "Starting API server on 0.0.0.0:2058..."
$PYTHON_CMD -m uvicorn parserapi.api:app --host 0.0.0.0 --port 2058
