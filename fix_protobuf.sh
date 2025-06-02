#!/bin/bash
# Fix protobuf version conflicts for ChatterBloke

echo "Fixing protobuf version conflicts..."

# Option 1: Set environment variable (quick fix)
echo "Setting PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python"
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Add to .bashrc for persistence
echo "" >> ~/.bashrc
echo "# Fix for ChatterBloke protobuf issue" >> ~/.bashrc
echo "export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python" >> ~/.bashrc

# Option 2: Fix by reinstalling with compatible versions
echo "Reinstalling protobuf with compatible version..."
pip uninstall -y protobuf
pip install 'protobuf>=3.19.0,<3.20.0'

# Option 3: If above doesn't work, try updating TensorFlow
# echo "Updating TensorFlow..."
# pip install --upgrade tensorflow

echo "Testing import..."
python -c "import chatterbox; print('Success!')" 2>&1

echo ""
echo "If the import still fails, try one of these options:"
echo "1. Run: export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python"
echo "2. Restart your terminal/shell"
echo "3. Try in a fresh conda environment"
echo ""