#!/bin/bash
set -e

# Check if blogwatcher-cli is installed
if ! command -v blogwatcher-cli &> /dev/null; then
    echo "Installing blogwatcher-cli via Homebrew..."
    brew install blogwatcher-cli
fi

# Verify installation
blogwatcher-cli --version

# Initialize blogwatcher-cli if not already
if [ ! -d "$HOME/.blogwatcher-cli" ]; then
    blogwatcher-cli init
fi

echo "Installation successful."
