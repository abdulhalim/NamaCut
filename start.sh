#!/bin/bash
# NamaCut Start Script
# Activates virtual environment and starts the application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
MAIN_PY="$SCRIPT_DIR/main.py"

# Change to script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Error: Virtual environment not found!"
    echo "Please run install.sh first to install NamaCut."
    exit 1
fi

# Activate virtual environment
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Error: Cannot activate virtual environment"
    exit 1
fi

# Run the application
exec python3 "$MAIN_PY" "$@"
