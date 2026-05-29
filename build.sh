#!/bin/bash
# Build the demo LaTeX document using tectonic

set -e  # Exit on error

echo "Building PyLaTeX demo document with tectonic..."
echo "================================================"
echo

# Run the Python demo to generate the .tex file
echo "Step 1: Generating LaTeX file..."
python src/main.py > /dev/null

echo "✓ LaTeX file generated: demo_output.tex"
echo
echo "Step 2: Compiling with tectonic..."

# Check if tectonic is installed
if ! command -v tectonic &> /dev/null; then
    echo "Error: tectonic is not installed!"
    echo "Install it with:"
    echo "  - Arch Linux: sudo pacman -S tectonic"
    echo "  - Ubuntu/Debian: sudo apt install tectonic"
    echo "  - macOS: brew install tectonic"
    echo "  - Or download from: https://tectonic-typesetting.github.io/"
    exit 1
fi

# Compile the document
tectonic demo_output.tex

echo
echo "================================================"
echo "✅ Build complete!"
echo "📄 PDF output: demo_output.pdf ($(du -h demo_output.pdf | cut -f1))"
echo "================================================"

# Open the PDF if possible
if command -v xdg-open &> /dev/null; then
    echo "Opening PDF..."
    xdg-open demo_output.pdf 2>/dev/null &
elif command -v open &> /dev/null; then
    echo "Opening PDF..."
    open demo_output.pdf
fi
