#!/usr/bin/env bash
# Build script for Render

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Add any other build steps here if needed
echo "Build completed successfully!"