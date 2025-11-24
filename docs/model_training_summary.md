# Model Training Summary

## Model Overview
- **Architecture**: MobileNetV3-Small fine-tuned for two classes (Science Center A vs Emerson Hall markers).
- **Rationale**: MobileNetV3 provides <5M parameters, keeps inference under ~40 ms on CPU, and is supported by both PyTorch + TensorFlow Lite for future on-device deployment.
- **Artifacts**: `models/harv_cnn_v1/weights.pt` and `models/harv_cnn_v1/metadata.json`.

## Training Pipeline
1. **Data Preparation**
   - Raw photo captures live under `data/raw/vision/*`.
   - DVC stages (`dvc.yaml`) transform them into `data/processed/vision/train|val` using augmentation + blur for privacy.
   - If training data is not present, `ml/train_cnn.py` falls back to a deterministic synthetic dataset so CI stays reproducible.
2. **Configuration**
   - Hyperparameters stored in `ml/configs/harv_vision_v1.yaml` (batch size, LR, augmentations).
   - `ml/train_cnn.py --config ml/configs/harv_vision_v1.yaml` loads the YAML, seeds RNG, builds dataloaders, and fine-tunes the classifier head.
3. **Metrics + Outputs**
   - Accuracy, precision, recall, false-positive rate, and latency are written to `artifacts/metrics/harv_cnn_v1.json`.
   - Metadata is synced to `models/harv_cnn_v1/metadata.json` for the FastAPI loader.
4. **Latency Checks**
   - Script benchmarks 20 forward passes to produce a `latency_ms` estimate (38.2 ms on CPU).

## Results
| Metric | Value |
| --- | --- |
| Accuracy | 96.2% |
| Precision | 95.5% |
| Recall | 96.8% |
| False Positive Rate | 1.0% |
| Avg. latency | 38.2 ms |

The above numbers use the synthetic dataset run tracked in `artifacts/metrics/harv_cnn_v1.json`. Replace with campus captures for production.

## Deployment Implications
- The FastAPI `/api/checkin/vision` endpoint loads weights via `backend/ml/model_loader.py`. Because the MobileNet head is small, CPU hosting on a MacBook or cloud VM meets the <3s latency requirement.
- For Milestone 5 cloud deployment, we can either:
  1. Serve this PyTorch module from a GPU-less Cloud Run container (since CPU inference suffices for a handful of concurrent calls), or
  2. Export to TorchScript / ONNX for even faster cold-start and embed inside the backend container image.
- Model versions are tracked by directory name (`models/harv_cnn_v1`). Updating requires:
  1. Running `ml/train_cnn.py` with a new config,
  2. Committing the new `metadata.json` + metrics,
  3. Updating `backend/app/config/settings.py` to point to the new version path.
