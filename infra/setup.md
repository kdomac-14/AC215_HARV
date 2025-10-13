# Infrastructure Setup

## Prerequisites

### Local Development
1. **Docker** (version 24.0+)
   ```bash
   docker --version
   ```

2. **Docker Compose** (version 2.0+)
   ```bash
   docker compose version
   ```

3. **uv** (optional, for local development outside containers)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Cloud VM Setup (Optional)
For deploying to a cloud VM (GCP, AWS, Azure):
- Ubuntu 22.04 or later
- Minimum 4 vCPUs, 16GB RAM
- 50GB storage
- Install Docker and Docker Compose
- Open ports 8000 (API) and 8501 (Dashboard)

## Verification Screenshots

Required screenshots for submission:
1. `docker --version` output
2. `docker compose version` output
3. `docker compose up` showing all services healthy
4. Dashboard screenshot showing successful image verification
5. Sample API response from `/verify` endpoint

Save screenshots in `infra/screenshots/` directory.

## Notes for Future Milestones

### Enabling GPU Support (MS3+)
To enable CUDA support:
1. Install NVIDIA Docker runtime
2. Update `docker-compose.yml` train service:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```
3. Update train Dockerfile to use CUDA base image:
   ```dockerfile
   FROM nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04
   ```

### MediaPipe Liveness Detection (MS3+)
Currently using "word of the day" challenge for liveness.
For MediaPipe blink detection:
1. Add `mediapipe>=0.10` to serve dependencies
2. Implement face mesh + blink detection in `serve/src/app.py`
3. Replace challenge word logic with real-time video frame analysis

## Troubleshooting

### Port conflicts
If ports 8000 or 8501 are in use, update `.env`:
```bash
SERVICE_PORT=8080
DASH_PORT=8502
```

### Memory issues
If containers crash due to memory, increase Docker Desktop memory allocation or reduce batch_size in `params.yaml`.

### Permission issues
On Linux, you may need to run with sudo or add user to docker group:
```bash
sudo usermod -aG docker $USER
```
