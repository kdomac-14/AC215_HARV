# Model Training Summary

## Model Overview
- **Architecture**: MobileNetV3-Small fine-tuned for two classroom classes (Science Center A vs Emerson Hall markers). The head is replaced with a lightweight linear layer.
- **Rationale**: MobileNetV3 keeps inference under ~40 ms on CPU, fits easily in mobile/edge deployments, and adapts well to limited data via transfer learning.
- **Artifacts**: `models/harv_cnn_v1/weights.pt` (state dict) + `models/harv_cnn_v1/metadata.json` (thresholds, metrics) consumed by the FastAPI loader.

## Dataset & Preprocessing
- Raw captures are checked into DVC under `data/raw/vision/<class>/`. Frames are blurred/cropped for privacy.
- The `preprocess` DVC stage exports train/val folders under `data/processed/vision/{train,val}` so `torchvision.datasets.ImageFolder` can consume them directly.
- When a teammate lacks the private dataset, `SyntheticVisionDataset` inside `ml/train_cnn.py` generates deterministic tensors to keep CI reproducible while still exercising the pipeline.

## Configuration Snapshot
All knobs live in `ml/configs/harv_vision_v1.yaml`. Key values:

| Parameter | Value | Notes |
| --- | --- | --- |
| `seed` | `42` | Ensures deterministic dataloader shuffles and synthetic tensors. |
| `image_size` | `224` | Matches MobileNet defaults and Expo camera aspect ratio. |
| `batch_size` | `16` | Fits comfortably on CPU for local debugging. |
| `epochs` | `5` | Demo-friendly; increase for production capture sets. |
| `learning_rate` | `5e-4` | Tuned for stability with AdamW. |
| `augmentations` | horizontal flip, color jitter, rotation 8° | Simulates mirrored seating and shaky cameras. |

To kick off training:
```bash
python ml/train_cnn.py --config ml/configs/harv_vision_v1.yaml
```
The script hydrates the dataclass config, seeds Python + PyTorch RNGs, builds dataloaders, trains, evaluates, benchmarks latency, and writes JSON metrics.

## Metrics & Outputs
- `artifacts/metrics/harv_cnn_v1.json` tracks accuracy, precision, recall, false-positive rate, and latency (averaged across 20 forward passes).
- `models/harv_cnn_v1/metadata.json` mirrors the metrics plus bookkeeping info (`trained_on`, `threshold`, `classes`), giving the API all context needed to validate inference.

| Metric | Value |
| --- | --- |
| Accuracy | 96.2% |
| Precision | 95.5% |
| Recall | 96.8% |
| False Positive Rate | 1.0% |
| Average Latency | 38.2 ms |

Numbers above stem from the deterministic synthetic dataset baked into CI. Replace them with real classroom captures by running the pipeline against DVC data and committing the refreshed `metrics` + `metadata`.

## Deployment Implications
1. `/api/checkin/vision` lazily instantiates `backend/ml/model_loader.VisionModel`, which reads `metadata.json` and produces deterministic confidences for testing. CPU-only inference keeps Milestone 4 demos simple.
2. For Milestone 5, export options include TorchScript (server-side) or ONNX/TFLite (edge devices). The config-driven training flow makes recreating a new version as simple as copying the YAML, tweaking parameters, and re-running `ml/train_cnn.py`.
3. New versions should live under `models/harv_cnn_v2/`, `harv_cnn_v3/`, etc. Update `backend/app/config/settings.py::vision_model_metadata` to point at the active release and log the change inside this document for traceability.
