#!/bin/bash

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "Python environment setup complete!"
echo "To activate the environment, run: source venv/bin/activate"