#!/bin/bash
# Fix TensorFlow and protobuf conflicts on GPU server

echo "Fixing TensorFlow installation conflicts..."
echo "=========================================="

# Check if we're in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Error: Not in a conda environment."
    echo "Please activate your conda environment first:"
    echo "  conda activate chatterbox"
    exit 1
fi

echo "Current conda environment: $CONDA_DEFAULT_ENV"
echo ""

# Step 1: Remove local TensorFlow installation that's causing conflicts
echo "1. Removing conflicting local TensorFlow installation..."
pip uninstall -y tensorflow tensorflow-gpu tensorflow-estimator tensorflow-io-gcs-filesystem

# Also remove from local user directory if it exists
if [ -d "$HOME/.local/lib/python3.9/site-packages/tensorflow" ]; then
    echo "   Removing TensorFlow from user directory..."
    rm -rf $HOME/.local/lib/python3.9/site-packages/tensorflow*
    rm -rf $HOME/.local/lib/python3.9/site-packages/keras*
fi

# Step 2: Clean up protobuf
echo ""
echo "2. Cleaning up protobuf installations..."
pip uninstall -y protobuf

# Step 3: Set environment variable
echo ""
echo "3. Setting environment variable..."
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Add to conda environment activation script
CONDA_ENV_DIR="$CONDA_PREFIX"
if [ -d "$CONDA_ENV_DIR/etc/conda/activate.d" ]; then
    mkdir -p "$CONDA_ENV_DIR/etc/conda/activate.d"
fi

cat > "$CONDA_ENV_DIR/etc/conda/activate.d/env_vars.sh" << 'EOF'
#!/bin/bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
EOF

chmod +x "$CONDA_ENV_DIR/etc/conda/activate.d/env_vars.sh"

# Step 4: Install compatible protobuf version
echo ""
echo "4. Installing compatible protobuf..."
pip install 'protobuf>=3.19.0,<3.20.0'

# Step 5: Test the import
echo ""
echo "5. Testing chatterbox import..."
python -c "import os; os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']='python'; import chatterbox; print('✅ Chatterbox imported successfully!')" 2>&1

# Step 6: Additional checks
echo ""
echo "6. Checking package locations..."
echo "   Python location: $(which python)"
echo "   Pip location: $(which pip)"
echo ""
echo "   Package locations:"
python -c "import site; print('   Site packages:', site.getsitepackages())"

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