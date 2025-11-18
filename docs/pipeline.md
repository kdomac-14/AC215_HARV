# HARV Pipeline Documentation

## Pipeline Overview

The HARV ML pipeline consists of 5 sequential containerized components that transform raw images into a deployable lecture hall recognition model. Each component is independently containerized, enabling reproducible execution and easy debugging.

**Full Pipeline Flow:**
```
Raw Images → Ingestion → Preprocess → Train → Evaluate → Export → Deploy
```

---

## Component 1: Ingestion

### Purpose
Creates a manifest CSV file that indexes available training data. Supports both real face datasets (e.g., Kaggle) and synthetic data generation.

### Inputs
- **Real Data Mode** (`use_real_faces=true`):
  - `data/raw/` - Directory containing face images
  - Expected structure: subdirectories per class (ProfA/, Room1/, etc.)
- **Synthetic Mode** (`use_real_faces=false`):
  - No input required; creates placeholder manifest

### Process
1. Scans `data/raw/` for image files (if real data enabled)
2. Detects class labels from directory names
3. Creates a CSV manifest mapping image paths to labels
4. Handles fallback to placeholder data if real data unavailable

### Outputs
- `data/interim/manifest.csv` - CSV with columns: `relpath`, `label`

### Configuration (`params.yaml`)
```yaml
use_real_faces: false  # Set to true for real datasets
```

### How to Run

**Docker (Recommended):**
```bash
docker compose run ingestion
```

**Standalone:**
```bash
cd ingestion/
docker build -t harv-ingestion .
docker run -v $(pwd)/../data:/app/data \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-ingestion
```

**Expected Output:**
```
[ingestion] Using synthetic dataset
[ingestion] Wrote manifest: /app/data/interim/manifest.csv
```

### Sample Manifest
```csv
relpath,label
placeholder_1.jpg,ProfA
placeholder_2.jpg,Room1
```

---

## Component 2: Preprocess

### Purpose
Transforms raw or manifested images into model-ready train/val/test splits with augmentation, normalization, and face detection.

### Inputs
- `data/interim/manifest.csv` - Manifest from ingestion
- `data/raw/` - Raw images (if real data mode)
- `params.yaml` - Hyperparameters

### Process
1. **Real Data Mode**:
   - Loads images from manifest paths
   - Detects faces using OpenCV Haar cascades
   - Applies blur augmentation (5 levels: 0.0, 0.5, 1.0, 1.5, 2.0)
   - Splits data: 70% train, 15% val, 15% test
   - Resizes to `img_size × img_size` (default: 224×224)
   
2. **Synthetic Mode**:
   - Generates geometric shapes (circles, rectangles)
   - Creates train/val splits with synthetic images

### Outputs
- `data/processed/train/` - Training images organized by class
- `data/processed/val/` - Validation images organized by class
- `data/processed/test/` - Test images organized by class

### Configuration (`params.yaml`)
```yaml
img_size: 224                 # Target image size
seed: 42                      # Random seed for reproducibility
use_real_faces: false         # Real dataset vs synthetic
blur_augmentation: true       # Enable blur augmentation
blur_strength: 0.3            # Blur intensity multiplier
```

### How to Run

**Docker:**
```bash
docker compose run preprocess
```

**Standalone:**
```bash
cd preprocess/
docker build -t harv-preprocess .
docker run -v $(pwd)/../data:/app/data \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-preprocess
```

**Expected Output:**
```
[preprocess] Processing real face dataset...
[preprocess] Face detection: 145/150 faces found
[preprocess] Blur augmentation: 5 levels per image
[preprocess] Train: 507, Val: 108, Test: 110
```

### Data Augmentation Details

**Blur Levels** (simulating distance):
- `0.0`: No blur (close-up)
- `0.5`: Slight blur (1-2 meters)
- `1.0`: Moderate blur (3-5 meters)
- `1.5`: Heavy blur (6-8 meters)
- `2.0`: Extreme blur (>8 meters)

**Training Augmentations** (applied during training):
- Random horizontal flip (p=0.5)
- Random rotation (±10°)
- Color jitter (brightness, contrast, saturation)

---

## Component 3: Train

### Purpose
Fine-tunes a pretrained model (MobileNetV3 or EfficientNet) on processed face data using transfer learning.

### Inputs
- `data/processed/train/` - Training split
- `data/processed/val/` - Validation split
- `params.yaml` - Training hyperparameters

### Process
1. Loads pretrained ImageNet weights
2. Replaces classifier head with custom layer (num_classes)
3. Freezes early layers (70% by default) for transfer learning
4. Trains with:
   - Adam optimizer
   - Cross-entropy loss
   - Learning rate scheduling (ReduceLROnPlateau)
   - Early stopping (patience=5)
5. Saves best model based on validation accuracy

### Outputs
- `artifacts/checkpoints/best_model.pth` - Best model weights
- `artifacts/checkpoints/final_model.pth` - Final epoch weights
- Console logs with epoch-wise metrics

### Configuration (`params.yaml`)
```yaml
model_name: mobilenet_v3_small  # or efficientnet_b0
epochs: 3                        # Training epochs (increase for real data)
batch_size: 16                   # Batch size (reduce if OOM)
lr: 0.0005                       # Initial learning rate
freeze_ratio: 0.7                # Fraction of layers to freeze
classes: ["ProfA", "Room1"]      # Class labels
```

### How to Run

**Docker:**
```bash
docker compose run train
```

**Local (CPU):**
```bash
cd train/
docker build -t harv-train .
docker run -v $(pwd)/../data:/app/data \
           -v $(pwd)/../artifacts:/app/artifacts \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-train
```

**Expected Output:**
```
[train] Found 2 classes: ['ProfA', 'Room1']
[train] Training samples: 507, Validation samples: 108
[train] Using device: cpu
[train] Epoch 1/3: train_loss=0.652, train_acc=0.724, val_loss=0.432, val_acc=0.852
[train] Epoch 2/3: train_loss=0.401, train_acc=0.865, val_loss=0.389, val_acc=0.870
[train] Epoch 3/3: train_loss=0.321, train_acc=0.892, val_loss=0.367, val_acc=0.889
[train] Best model saved: artifacts/checkpoints/best_model.pth (val_acc=0.889)
```

### Training Time Estimates
- **CPU (MobileNetV3-Small)**: ~2-5 min/epoch (500-1000 images)
- **CPU (EfficientNet-B0)**: ~5-10 min/epoch (500-1000 images)
- **GPU (V100)**: ~10-30 sec/epoch (500-1000 images)

---

## Component 4: Evaluate

### Purpose
Generates comprehensive evaluation metrics on the test set, including classification report, confusion matrix, and per-class performance.

### Inputs
- `artifacts/checkpoints/best_model.pth` - Trained model
- `data/processed/test/` - Test split
- `params.yaml` - Model configuration

### Process
1. Loads best trained model
2. Runs inference on test set
3. Computes:
   - Accuracy, precision, recall, F1-score (macro/weighted)
   - Per-class metrics
   - Confusion matrix
4. Saves metrics to JSON

### Outputs
- `artifacts/metrics.json` - Complete evaluation metrics

### How to Run

**Docker:**
```bash
docker compose run evaluate
```

**Expected Output:**
```
[evaluate] Loading model from artifacts/checkpoints/best_model.pth
[evaluate] Test set: 110 images, 2 classes
[evaluate] Overall accuracy: 0.882
[evaluate] Classification Report:
              precision    recall  f1-score   support
      ProfA       0.91      0.88      0.89        55
      Room1       0.88      0.91      0.89        55

   accuracy                           0.88       110
  macro avg       0.89      0.89      0.89       110
weighted avg      0.89      0.89      0.89       110

[evaluate] Metrics saved: artifacts/metrics.json
```

### Sample `metrics.json`
```json
{
  "accuracy": 0.8818,
  "precision_macro": 0.8923,
  "recall_macro": 0.8902,
  "f1_macro": 0.8912,
  "classes": {
    "ProfA": {"precision": 0.91, "recall": 0.88, "f1": 0.89, "support": 55},
    "Room1": {"precision": 0.88, "recall": 0.91, "f1": 0.89, "support": 55}
  },
  "confusion_matrix": [[48, 7], [5, 50]]
}
```

---

## Component 5: Export

### Purpose
Converts the trained PyTorch model to TorchScript format for deployment, enabling inference without requiring the full training environment.

### Inputs
- `artifacts/checkpoints/best_model.pth` - Trained model
- `params.yaml` - Model architecture configuration

### Process
1. Loads trained model
2. Traces model with dummy input (224×224×3 tensor)
3. Exports to TorchScript (`.pt` format)
4. Saves metadata (class labels, input size, model name)

### Outputs
- `artifacts/model/model.torchscript.pt` - TorchScript model (8-20MB)
- `artifacts/model/metadata.json` - Model metadata

### How to Run

**Docker:**
```bash
docker compose run export
```

**Expected Output:**
```
[export] Loading model from artifacts/checkpoints/best_model.pth
[export] Tracing model with input shape: (1, 3, 224, 224)
[export] TorchScript model saved: artifacts/model/model.torchscript.pt (14.2 MB)
[export] Metadata saved: artifacts/model/metadata.json
```

### Sample `metadata.json`
```json
{
  "model_name": "mobilenet_v3_small",
  "num_classes": 2,
  "classes": ["ProfA", "Room1"],
  "img_size": 224,
  "input_shape": [1, 3, 224, 224],
  "mean": [0.485, 0.456, 0.406],
  "std": [0.229, 0.224, 0.225],
  "export_date": "2025-10-28T17:30:00"
}
```

---

## End-to-End Execution

### Single Command (Makefile)
```bash
make run
```

This executes:
1. `docker compose build` - Build all images
2. Sequential execution: ingestion → preprocess → train → evaluate → export
3. Starts serve and dashboard services

### Manual Sequential Execution
```bash
docker compose run ingestion
docker compose run preprocess
docker compose run train
docker compose run evaluate
docker compose run export
docker compose up serve dashboard
```

### Expected Total Runtime
- **Synthetic data (default)**: 2-3 minutes
- **Real data (500-1000 images)**: 10-15 minutes
- **Real data (5000+ images)**: 30-60 minutes

---

## Evidence & Logs

### Sample Logs

**Ingestion:**
```
[ingestion] Using synthetic dataset
[ingestion] Wrote manifest: /app/data/interim/manifest.csv
```

**Preprocess:**
```
[preprocess] Processing synthetic data...
[preprocess] Train: 100, Val: 20
```

**Train:**
```
[train] Epoch 1/3: train_loss=0.652, val_acc=0.852
[train] Epoch 2/3: train_loss=0.401, val_acc=0.870
[train] Epoch 3/3: train_loss=0.321, val_acc=0.889
[train] Best model saved (val_acc=0.889)
```

**Evaluate:**
```
[evaluate] Test accuracy: 0.882
[evaluate] Metrics saved: artifacts/metrics.json
```

**Export:**
```
[export] TorchScript model saved: 14.2 MB
```

### Sample Input → Output

**Input (raw):** `data/raw/ProfA/img001.jpg` (640×480 RGB)

**After Ingestion:** Entry in `manifest.csv`:
```csv
ProfA/img001.jpg,ProfA
```

**After Preprocess:** 5 augmented versions in `data/processed/train/ProfA/`:
- `img001_blur0.0.jpg` (224×224)
- `img001_blur0.5.jpg` (224×224)
- `img001_blur1.0.jpg` (224×224)
- `img001_blur1.5.jpg` (224×224)
- `img001_blur2.0.jpg` (224×224)

**After Train:** Model checkpoint with validation accuracy 0.889

**After Evaluate:** Metrics in `artifacts/metrics.json`:
```json
{
  "accuracy": 0.882,
  "classes": {"ProfA": {"f1": 0.89}, "Room1": {"f1": 0.89}}
}
```

**After Export:** Deployable `model.torchscript.pt` (14.2 MB)

---

## Troubleshooting

### Common Issues

**Issue:** `FileNotFoundError: manifest.csv`
- **Cause:** Ingestion not run or failed
- **Fix:** Run `docker compose run ingestion` first

**Issue:** `RuntimeError: CUDA out of memory`
- **Cause:** Batch size too large for available memory
- **Fix:** Reduce `batch_size` in `params.yaml` (try 8 or 4)

**Issue:** `OSError: [Errno 28] No space left on device`
- **Cause:** Docker volume full
- **Fix:** `docker system prune -a` to clear cache

**Issue:** Low accuracy (<50%)
- **Cause:** Insufficient training data or epochs
- **Fix:** Increase `epochs` in `params.yaml` or add more training data

### Debugging Commands

```bash
# Check Docker logs
docker compose logs ingestion
docker compose logs train

# Inspect artifacts
ls -lh artifacts/checkpoints/
cat artifacts/metrics.json

# Verify data splits
ls data/processed/train/
ls data/processed/val/
ls data/processed/test/

# Test single component
docker compose run --rm preprocess
```

---

## Next Steps

After completing the pipeline:
1. **Test the model**: `make test` (runs all tests)
2. **Start inference server**: `docker compose up serve dashboard`
3. **Test API**: `curl http://localhost:8000/healthz`
4. **Open dashboard**: http://localhost:8501
5. **Deploy to cloud**: `make gcp-full-deploy` (see `DEPLOYMENT.md`)

For detailed API usage, see the main `README.md` and `docs/RUNBOOK.md`.
