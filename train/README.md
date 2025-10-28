# Train Component

Fine-tunes a pretrained model (MobileNetV3 or EfficientNet) on processed face data using transfer learning.

## Purpose

The training component implements transfer learning on ImageNet-pretrained models to create a face recognition classifier. It freezes early layers, fine-tunes top layers, and implements best practices like early stopping and learning rate scheduling.

**Key responsibilities:**
- Load pretrained ImageNet weights
- Replace classifier head for target classes
- Implement transfer learning with layer freezing
- Train with data augmentation
- Save best model based on validation accuracy
- Apply early stopping to prevent overfitting

## Inputs

### From Preprocessing

- `data/processed/train/` - Training images organized by class
- `data/processed/val/` - Validation images organized by class

**Expected structure (PyTorch ImageFolder format):**
```
data/processed/
├── train/
│   ├── ProfA/
│   │   ├── img001_blur0.0.jpg
│   │   └── ...
│   └── Room1/
│       └── ...
└── val/
    ├── ProfA/
    └── Room1/
```

### From Configuration

`params.yaml`:
```yaml
model_name: mobilenet_v3_small  # or efficientnet_b0
epochs: 3
batch_size: 16
lr: 0.0005
freeze_ratio: 0.7
seed: 42
img_size: 224
classes: ["ProfA", "Room1"]
```

## Outputs

### Model Checkpoints

**Location:** `artifacts/checkpoints/`

Files created:
- `best_model.pth` - Best model based on validation accuracy
- `final_model.pth` - Model from final epoch

**Checkpoint format:** PyTorch state dict containing:
- Model weights
- Optimizer state
- Learning rate scheduler state
- Epoch number
- Best validation accuracy

### Training Logs

Console output with epoch-wise metrics:
```
[train] Epoch 1/3: train_loss=0.652, train_acc=0.724, val_loss=0.432, val_acc=0.852
[train] Epoch 2/3: train_loss=0.401, train_acc=0.865, val_loss=0.389, val_acc=0.870
[train] Epoch 3/3: train_loss=0.321, train_acc=0.892, val_loss=0.367, val_acc=0.889
[train] Best model saved: artifacts/checkpoints/best_model.pth (val_acc=0.889)
```

## Model Architecture

### MobileNetV3-Small (Default)

**Advantages:**
- Fast CPU training (~3-5 min/epoch for 500 images)
- Small model size (14MB)
- Efficient inference (12-15ms on CPU)
- Good accuracy (85-90% on validation)

**Architecture:**
- Input: 224×224×3 RGB image
- Backbone: MobileNetV3-Small (pretrained on ImageNet)
- Classifier: Custom linear layer for target classes
- Output: Class logits (softmax applied during inference)

**Layer freezing:**
```python
freeze_ratio = 0.7  # Freeze 70% of layers
# Freezes: Early convolutional layers
# Trainable: Top 30% + classifier head
```

### EfficientNet-B0 (Alternative)

**Advantages:**
- Higher accuracy (88-92% on validation)
- State-of-art efficiency

**Trade-offs:**
- Slower training (~6-10 min/epoch)
- Larger model size (21MB)
- Slower inference (23-28ms on CPU)

**Configuration:**
```yaml
model_name: efficientnet_b0
epochs: 5       # Needs more epochs
batch_size: 8   # Reduce for memory
lr: 0.0003
freeze_ratio: 0.8
```

## Training Strategy

### Transfer Learning

**Pretrained weights:** ImageNet1K_V1

**Rationale:**
- Small dataset (500-1000 images)
- Limited training time (CPU-only)
- Face features share low-level patterns with ImageNet

### Layer Freezing

**Default:** Freeze 70% of early layers

**Why freeze:**
- Prevents overfitting on small datasets
- Speeds up training (fewer parameters to update)
- Preserves low-level features (edges, textures)

**Trainable parameters:**
- Top 30% of backbone layers
- Classifier head (always trainable)

### Data Augmentation

Applied during training (torchvision transforms):

```python
train_transforms = Compose([
    Resize((224, 224)),
    RandomHorizontalFlip(p=0.5),
    RandomRotation(degrees=10),
    ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    ToTensor(),
    Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
```

**Validation transforms:** Only resize + normalize (no augmentation)

### Optimization

- **Optimizer:** Adam with weight decay (0.0001)
- **Learning rate:** 0.0005 (default)
- **LR Scheduler:** ReduceLROnPlateau
  - Factor: 0.5 (halve LR on plateau)
  - Patience: 3 epochs
  - Min LR: 1e-7
- **Loss:** CrossEntropyLoss
- **Early stopping:** Patience of 5 epochs (stops if no improvement)

## Configuration

### Default Configuration (CPU)

```yaml
model_name: mobilenet_v3_small
epochs: 3
batch_size: 16
lr: 0.0005
freeze_ratio: 0.7
seed: 42
img_size: 224
```

**Expected performance:**
- Training time: 2-3 minutes per epoch (500 images, CPU)
- Validation accuracy: 85-90%
- Model size: 14MB

### High-Accuracy Configuration

```yaml
model_name: efficientnet_b0
epochs: 10
batch_size: 8
lr: 0.0003
freeze_ratio: 0.8
```

**Expected performance:**
- Training time: 6-8 minutes per epoch
- Validation accuracy: 88-92%
- Model size: 21MB

### Fast Training (Testing)

```yaml
model_name: mobilenet_v3_small
epochs: 1
batch_size: 32
lr: 0.001
freeze_ratio: 0.9
```

**For quick smoke tests only** (accuracy will be lower)

## How to Run

### Docker (Recommended)

```bash
# From repository root
docker compose run train
```

### Standalone Docker

```bash
cd train/
docker build -t harv-train .
docker run -v $(pwd)/../data:/app/data \
           -v $(pwd)/../artifacts:/app/artifacts \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-train
```

### Local Development (CPU)

```bash
cd train/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run
python -m src.train
```

### GPU Training (Optional)

```bash
# Modify params.yaml (no change needed, auto-detects)
docker run --gpus all \
           -v $(pwd)/../data:/app/data \
           -v $(pwd)/../artifacts:/app/artifacts \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-train
```

## Expected Output

### Console Logs

```
[train] Found 2 classes: ['ProfA', 'Room1']
[train] Training samples: 507, Validation samples: 108
[train] Model: mobilenet_v3_small, Parameters: 2.5M (0.6M trainable)
[train] Using device: cpu
[train] Optimizer: Adam, LR: 0.0005
[train] Starting training for 3 epochs...

[train] Epoch 1/3
[train]   Train: loss=0.6524, accuracy=0.7241 (10 batches, 45.2s)
[train]   Val:   loss=0.4318, accuracy=0.8519 (7 batches, 8.1s)
[train]   Saved best model (val_acc=0.8519)

[train] Epoch 2/3
[train]   Train: loss=0.4012, accuracy=0.8649 (10 batches, 44.8s)
[train]   Val:   loss=0.3893, accuracy=0.8704 (7 batches, 8.0s)
[train]   Saved best model (val_acc=0.8704)

[train] Epoch 3/3
[train]   Train: loss=0.3214, accuracy=0.8921 (10 batches, 45.1s)
[train]   Val:   loss=0.3671, accuracy=0.8889 (7 batches, 8.2s)
[train]   Saved best model (val_acc=0.8889)

[train] Training complete!
[train] Best validation accuracy: 0.8889 (epoch 3)
[train] Total training time: 2m 31s
[train] Model saved: artifacts/checkpoints/best_model.pth
```

### Artifacts Created

- `artifacts/checkpoints/best_model.pth` (14-21MB depending on model)
- `artifacts/checkpoints/final_model.pth` (14-21MB)

## Implementation Details

**File:** `src/train.py`

**Key functions:**
- `load_model()`: Initialize model with pretrained weights
- `freeze_layers()`: Freeze specified percentage of layers
- `train_epoch()`: Single training epoch with backpropagation
- `validate()`: Validation loop without gradient computation
- `save_checkpoint()`: Save model state dict

**Dependencies:**
- Python 3.11
- `torch==2.3.0` - Deep learning framework
- `torchvision==0.18.0` - Pretrained models & transforms
- `pyyaml==6.0.1` - Configuration
- `tqdm` - Progress bars (optional)

## Testing

**Tests:** `tests/unit/test_train_smoke.py`

```bash
# Smoke test (1 epoch on tiny dataset)
pytest tests/unit/test_train_smoke.py -v
```

Tests cover:
- Model loading
- Forward pass correctness
- Loss computation
- Backward pass (gradients)
- Checkpoint saving/loading

## Integration with Pipeline

**Upstream:** Requires `data/processed/` from preprocess

**Downstream:** Outputs consumed by evaluate and export components

**Workflow:**
```bash
docker compose run preprocess  # Create processed data
docker compose run train       # Train model
docker compose run evaluate    # Evaluate on test set
docker compose run export      # Export to TorchScript
```

## Troubleshooting

### Issue: CUDA Out of Memory

**Symptom:** `RuntimeError: CUDA out of memory`

**Fixes:**
```yaml
# Reduce batch size
batch_size: 8  # or 4

# Reduce image size
img_size: 160

# Increase layer freezing
freeze_ratio: 0.9
```

### Issue: Low Accuracy (<50%)

**Causes:**
- Insufficient training data
- Too few epochs
- Learning rate too high/low
- Random seed causing bad split

**Fixes:**
```yaml
# Increase epochs
epochs: 10

# Adjust learning rate
lr: 0.0003  # Lower if loss oscillates

# Try different seed
seed: 123

# Use more data or augmentation
```

### Issue: Overfitting

**Symptom:** High train accuracy, low validation accuracy

**Example:** Train=0.95, Val=0.75

**Fixes:**
```yaml
# Increase layer freezing
freeze_ratio: 0.8

# Add regularization (in code: weight_decay)

# Enable more augmentation

# Reduce epochs (use early stopping)
```

### Issue: Slow Training

**Symptom:** >10 minutes per epoch on CPU

**Optimizations:**
```yaml
# Use smaller model
model_name: mobilenet_v3_small

# Reduce batch size (counter-intuitive but can help on CPU)
batch_size: 8

# Reduce image size
img_size: 160

# Increase layer freezing
freeze_ratio: 0.9
```

## Performance Benchmarks

### MobileNetV3-Small (CPU)

| Dataset Size | Epoch Time | Total Time (3 epochs) | Val Accuracy |
|--------------|------------|----------------------|--------------|
| 100 images | 15s | 45s | 85% |
| 500 images | 45s | 2m 15s | 88% |
| 1000 images | 3m | 9m | 89% |
| 5000 images | 15m | 45m | 91% |

### EfficientNet-B0 (CPU)

| Dataset Size | Epoch Time | Total Time (5 epochs) | Val Accuracy |
|--------------|------------|----------------------|--------------|
| 500 images | 1m 30s | 7m 30s | 90% |
| 1000 images | 6m | 30m | 91% |

### GPU (V100)

| Model | Dataset Size | Epoch Time | Total Time (3 epochs) |
|-------|--------------|------------|-----------------------|
| MobileNetV3 | 1000 images | 12s | 36s |
| EfficientNet | 1000 images | 25s | 1m 15s |

## Future Enhancements

- [ ] Mixed precision training (FP16) for faster GPU training
- [ ] Gradient accumulation for larger effective batch sizes
- [ ] Model ensembling
- [ ] AutoML hyperparameter tuning
- [ ] Distributed training support
- [ ] W&B integration for experiment tracking

## Related Documentation

- [Pipeline Overview](../docs/PIPELINE.md#component-3-train)
- [Model Selection Rationale](../docs/DECISIONS.md#model-selection-mobilenetv3-on-cpu)
- [Architecture](../docs/ARCHITECTURE.md)

## Contact

For issues or questions, see main repository README.
