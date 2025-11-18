#!/usr/bin/env bash
# Quick setup script for FastAPI + ScrapeGraphAI Parser with Ollama
# Run with: bash setup.sh or ./setup.sh

set -e

export PATH="$HOME/ollama/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/ollama/lib:$LD_LIBRARY_PATH"

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
$PIP_CMD install -r requirements.txt

echo "Installing Playwright browsers..."
$PYTHON_CMD -m playwright install chromium

# Install Ollama if not present (user-level installation for Pterodactyl)
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    mkdir -p $HOME/ollama
    curl -fsSL https://github.com/ollama/ollama/releases/download/v0.12.11/ollama-linux-amd64.tgz -o "$HOME/ollama/ollama.tgz"
    tar -xzf "$HOME/ollama/ollama.tgz" -C "$HOME/ollama"
    rm -f "$HOME/ollama/ollama.tgz"
    chmod +x $HOME/ollama/bin/ollama
    export PATH="$HOME/ollama/bin:$PATH"
    export LD_LIBRARY_PATH="$HOME/ollama/lib:$LD_LIBRARY_PATH"
    echo "✓ Ollama installed to $HOME/ollama"
fi

# Start Ollama in background if not running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 3
fi

# Run tinyllama:1.1b model (auto-pulls if missing)
echo "Starting tinyllama:1.1b model..."
ollama run tinyllama:1.1b "" &>/dev/null &
sleep 2

echo ""
echo "✅ Setup complete!"
echo "Starting API server on 0.0.0.0:2058..."
$PYTHON_CMD -m uvicorn parserapi.api:app --host 0.0.0.0 --port 2058
