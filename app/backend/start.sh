#!/bin/bash

# Start Backend service script

echo "Starting Hyperliquid Backend Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using default configuration."
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Starting server..."
python main.py
