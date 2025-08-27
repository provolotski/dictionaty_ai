#!/bin/bash

# Script to run flake8 with the virtual environment
# Usage: ./run_flake8.sh [file_or_directory] [additional_options]

# Activate virtual environment
source venv/bin/activate

# Default options
DEFAULT_OPTIONS="--max-line-length=120 --ignore=E203,W503"

# Run flake8
if [ $# -eq 0 ]; then
    # No arguments - check common directories
    echo "Running flake8 on backend and frontend directories..."
    flake8 backend/ frontend/ $DEFAULT_OPTIONS
else
    # Run with provided arguments
    flake8 "$@" $DEFAULT_OPTIONS
fi
