#!/usr/bin/env bash
# AIrys Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "🚀 Starting AIrys setup..."
echo ""

# Check Python version
python_version=$(python --version | awk '{print $2}')
if [[ ! "$python_version" =~ ^3\.(10|11|12) ]]; then
    echo "❌ Error: Python 3.10+ is required. Current version: $python_version"
    exit 1
fi

echo "✓ Python version OK: $python_version"

# Create data directories if they don't exist
echo "✓ Creating data directories..."
mkdir -p data/conversations data/embeddings

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure Ollama is running: ollama serve"
echo "2. Pull a model in Ollama: ollama run llama3.2"
echo "3. Start the backend server: python backend/server.py"
echo "4. Start frontend (optional): cd frontend && npm install && npm run dev"
echo ""
