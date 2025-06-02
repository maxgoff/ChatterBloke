# GPU Server Setup for ChatterBloke

This guide covers setting up ChatterBloke on a Linux server with GPU acceleration.

## Prerequisites

- Linux server with NVIDIA GPU
- CUDA 11.x or 12.x installed
- Python 3.9+
- Conda (recommended) or venv

## Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ChatterBloke.git
   cd ChatterBloke
   ```

2. **Create conda environment**
   ```bash
   conda create -n chatterbloke python=3.9
   conda activate chatterbloke
   ```

3. **Run the setup script**
   ```bash
   chmod +x setup_gpu_server.sh
   ./setup_gpu_server.sh
   ```

## Manual Setup (if script fails)

### Fix the TensorFlow dependency issue
```bash
pip install absl-py
```

### Install PyTorch with CUDA
```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Install requirements
```bash
pip install -r requirements.txt
```

### Verify GPU setup
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

## Configuration

Edit the `.env` file:

```env
# IMPORTANT: Change this to allow external connections
API_HOST=0.0.0.0  # Listens on all interfaces
API_PORT=8000

# GPU Configuration
CUDA_VISIBLE_DEVICES=0  # Use GPU 0
# For multiple GPUs: CUDA_VISIBLE_DEVICES=0,1
```

## Running the Server

1. **Start the API server**
   ```bash
   python run_api.py
   ```

2. **For production use with auto-restart**
   ```bash
   # Using screen
   screen -S chatterbloke
   python run_api.py
   # Detach with Ctrl+A, D

   # Or using systemd (see below)
   ```

## Systemd Service (Recommended for Production)

Create `/etc/systemd/system/chatterbloke.service`:

```ini
[Unit]
Description=ChatterBloke API Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ChatterBloke
Environment="PATH=/home/youruser/.conda/envs/chatterbloke/bin"
ExecStart=/home/youruser/.conda/envs/chatterbloke/bin/python run_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chatterbloke
sudo systemctl start chatterbloke
sudo systemctl status chatterbloke
```

## Firewall Configuration

Allow port 8000:
```bash
# Using ufw
sudo ufw allow 8000

# Using firewall-cmd
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Connecting from Frontend

On your laptop, configure the frontend to connect to the GPU server:

1. Create/edit `.env`:
   ```env
   API_HOST=YOUR_GPU_SERVER_IP
   API_PORT=8000
   ```

2. Or modify `src/utils/config.py` temporarily:
   ```python
   api_host: str = Field(default="YOUR_GPU_SERVER_IP", env="API_HOST")
   ```

## Performance Optimization

### GPU Memory Management
- Monitor GPU usage: `nvidia-smi -l 1`
- If running out of memory, reduce batch size in TTS settings

### Multiple GPUs
- Set `CUDA_VISIBLE_DEVICES=0,1` to use multiple GPUs
- ChatterBox will automatically use available GPUs

### CPU Cores
- The server will use all available CPU cores for preprocessing
- Limit with: `export OMP_NUM_THREADS=8`

## Troubleshooting

### Protobuf/TensorFlow/ONNX conflicts
If you get protobuf errors when importing chatterbox:

For TensorFlow conflicts:
```bash
chmod +x fix_gpu_tensorflow.sh
./fix_gpu_tensorflow.sh
```

For ONNX builder import errors:
```bash
chmod +x fix_onnx_protobuf.sh
./fix_onnx_protobuf.sh
```

Then deactivate and reactivate your conda environment:
```bash
conda deactivate
conda activate chatterbox
```

### "No module named 'absl'"
```bash
pip install absl-py
```

### CUDA out of memory
- Reduce text chunk size
- Restart the server to clear GPU memory
- Check other processes: `nvidia-smi`

### Connection refused from frontend
- Check firewall: `sudo ufw status`
- Verify server is listening: `netstat -tlnp | grep 8000`
- Check API_HOST is set to 0.0.0.0

### Slow model loading
- First load takes time to download models
- Subsequent loads use cached models
- Models are stored in `~/.cache/chatterbox/`

## Monitoring

### Server logs
```bash
tail -f data/logs/chatterbloke-*.log
```

### GPU usage
```bash
watch -n 1 nvidia-smi
```

### API health check
```bash
curl http://YOUR_SERVER_IP:8000/health
```

## Expected Performance

With GPU acceleration, expect:
- **Model loading**: 10-30 seconds (first time)
- **TTS generation**: 1-5 seconds per 200 characters
- **10-20x faster** than CPU processing

Example timings on RTX 3090:
- 200 chars: ~3 seconds
- 1000 chars: ~15 seconds
- 5000 chars: ~75 seconds