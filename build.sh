#!/bin/bash
# Build a .pytex document into a PDF using tectonic.
# Usage: ./build.sh [input.pytex]   (defaults to example.pytex)

set -e  # Exit on error

INPUT="${1:-example.pytex}"
PDF="${INPUT%.pytex}.pdf"

echo "Building PyTeX document: $INPUT"
echo "================================================"

if ! command -v tectonic &> /dev/null; then
    echo "Error: tectonic is not installed!"
    echo "Install it with:"
    echo "  - Arch Linux: sudo pacman -S tectonic"
    echo "  - Ubuntu/Debian: sudo apt install tectonic"
    echo "  - macOS: brew install tectonic"
    echo "  - Or download from: https://tectonic-typesetting.github.io/"
    exit 1
fi

# Generate the .tex file and (with --compile) the PDF via tectonic.
python -m pytex.scripts.build_pytex "$INPUT" --compile

echo "================================================"
echo "Build complete! PDF output: $PDF"

# Open the PDF if possible
if command -v xdg-open &> /dev/null; then
    xdg-open "$PDF" 2>/dev/null &
elif command -v open &> /dev/null; then
    open "$PDF"
fi
