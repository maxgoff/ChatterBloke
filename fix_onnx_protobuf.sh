#!/bin/bash
# Fix ONNX and protobuf compatibility for ChatterBloke

echo "Fixing ONNX and protobuf compatibility..."
echo "========================================"

# Check if we're in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Error: Not in a conda environment."
    echo "Please activate your conda environment first:"
    echo "  conda activate chatterbox"
    exit 1
fi

echo "Current conda environment: $CONDA_DEFAULT_ENV"
echo ""

# Step 1: Set environment variable first
echo "1. Setting environment variable..."
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Step 2: Clean up existing installations
echo ""
echo "2. Cleaning up existing protobuf and onnx installations..."
pip uninstall -y protobuf onnx onnxruntime onnxruntime-gpu

# Step 3: Install compatible versions
echo ""
echo "3. Installing compatible versions..."
# Install protobuf 3.20.3 which works with both ONNX and the environment variable
pip install protobuf==3.20.3

# Install ONNX
pip install onnx

# Install onnxruntime with GPU support if available
if nvidia-smi &> /dev/null; then
    echo "   Installing onnxruntime-gpu..."
    pip install onnxruntime-gpu
else
    echo "   Installing onnxruntime (CPU)..."
    pip install onnxruntime
fi

# Step 4: Verify installations
echo ""
echo "4. Verifying installations..."
python -c "import protobuf; print(f'✅ Protobuf version: {protobuf.__version__}')" 2>&1 || echo "❌ Failed to import protobuf"
python -c "import onnx; print(f'✅ ONNX version: {onnx.__version__}')" 2>&1 || echo "❌ Failed to import onnx"

# Step 5: Test the chatterbox import
echo ""
echo "5. Testing chatterbox import..."
python -c "import os; os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']='python'; import chatterbox; print('✅ Chatterbox imported successfully!')" 2>&1

# Step 6: Update the conda environment activation script
echo ""
echo "6. Making environment variable permanent..."
CONDA_ENV_DIR="$CONDA_PREFIX"
mkdir -p "$CONDA_ENV_DIR/etc/conda/activate.d"
mkdir -p "$CONDA_ENV_DIR/etc/conda/deactivate.d"

# Create activation script
cat > "$CONDA_ENV_DIR/etc/conda/activate.d/env_vars.sh" << 'EOF'
#!/bin/bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
EOF

# Create deactivation script
cat > "$CONDA_ENV_DIR/etc/conda/deactivate.d/env_vars.sh" << 'EOF'
#!/bin/bash
unset PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION
EOF

chmod +x "$CONDA_ENV_DIR/etc/conda/activate.d/env_vars.sh"
chmod +x "$CONDA_ENV_DIR/etc/conda/deactivate.d/env_vars.sh"

echo ""
echo "Fix complete!"
echo ""
echo "Next steps:"
echo "1. Deactivate and reactivate your conda environment:"
echo "   conda deactivate"
echo "   conda activate chatterbox"
echo ""
echo "2. Test the import again:"
echo "   python -c 'import chatterbox'"
echo ""
echo "3. If successful, run the API server:"
echo "   python run_api.py"
echo ""
echo "Note: The PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python environment"
echo "variable is now set automatically when you activate this conda environment."