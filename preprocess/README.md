# Preprocess Component

Transforms raw images into model-ready train/val/test splits with augmentation, normalization, and face detection.

## Purpose

The preprocessing component is responsible for converting raw images into a structured dataset suitable for training. It performs face detection, applies augmentations (including blur simulation), and creates train/validation/test splits.

**Key responsibilities:**
- Read manifest from ingestion stage
- Detect and crop faces (real data mode)
- Apply blur augmentation to simulate distance effects
- Generate train/val/test splits (70/15/15)
- Resize images to target dimensions
- Organize images by class for PyTorch ImageFolder

## Inputs

### From Upstream

- `data/interim/manifest.csv` - Manifest from ingestion component

### From Configuration

- `params.yaml` - Hyperparameters:
  - `img_size`: Target image dimensions (default: 224)
  - `seed`: Random seed for reproducibility
  - `use_real_faces`: Real vs synthetic data mode
  - `blur_augmentation`: Enable/disable blur augmentation
  - `blur_strength`: Blur intensity multiplier

### From Raw Data (Real Mode)

- `data/raw/` - Raw images referenced in manifest

## Outputs

### Processed Datasets

**Directory structure:**
```
data/processed/
├── train/
│   ├── ProfA/
│   │   ├── img001_blur0.0.jpg
│   │   ├── img001_blur0.5.jpg
│   │   ├── img001_blur1.0.jpg
│   │   ├── img001_blur1.5.jpg
│   │   ├── img001_blur2.0.jpg
│   │   └── ...
│   └── Room1/
│       └── ...
├── val/
│   ├── ProfA/
│   └── Room1/
└── test/
    ├── ProfA/
    └── Room1/
```

**Image specifications:**
- Format: JPEG
- Dimensions: `img_size × img_size` (e.g., 224×224)
- Color space: RGB
- Naming: `{original_name}_blur{level}.jpg`

### Augmentation Levels

Each source image generates 5 augmented versions:

| Blur Level | Sigma | Simulated Distance | Use Case |
|------------|-------|-------------------|----------|
| 0.0 | 0.0 | Close-up (0-1m) | High-resolution reference |
| 0.5 | 0.5 | Near (1-2m) | Typical desk distance |
| 1.0 | 1.0 | Medium (3-5m) | Classroom front row |
| 1.5 | 1.5 | Far (6-8m) | Classroom back row |
| 2.0 | 2.0 | Very far (>8m) | Lecture hall |

## Configuration

### params.yaml

```yaml
img_size: 224                 # Target image dimensions (224×224)
seed: 42                      # Random seed for reproducibility
use_real_faces: false         # true = real data, false = synthetic
blur_augmentation: true       # Enable blur simulation
blur_strength: 0.3            # Blur intensity multiplier (0.0-1.0)
```

## How to Run

### Docker (Recommended)

```bash
# From repository root
docker compose run preprocess
```

### Standalone Docker

```bash
cd preprocess/
docker build -t harv-preprocess .
docker run -v $(pwd)/../data:/app/data \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-preprocess
```

### Local Development

```bash
cd preprocess/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run
python -m src.preprocess
```

## Expected Output

### Console Logs

**Real data mode:**
```
[preprocess] Processing real face dataset...
[preprocess] Loading manifest from data/interim/manifest.csv
[preprocess] Found 150 images across 2 classes
[preprocess] Face detection: 145/150 faces found (96.7%)
[preprocess] Blur augmentation: 5 levels per image
[preprocess] Generating train/val/test splits (70/15/15)
[preprocess] Train: 507 images (145 × 5 × 0.7)
[preprocess] Val: 108 images (145 × 5 × 0.15)
[preprocess] Test: 110 images (145 × 5 × 0.15)
[preprocess] Saved to data/processed/
```

**Synthetic mode:**
```
[preprocess] Processing synthetic data...
[preprocess] Generating 100 training images (50 ProfA, 50 Room1)
[preprocess] Generating 20 validation images
[preprocess] Train: 100, Val: 20
```

### Artifacts Created

- `data/processed/train/` - Training split (70% of data × 5 blur levels)
- `data/processed/val/` - Validation split (15%)
- `data/processed/test/` - Test split (15%)

## Process Details

### Real Data Mode

1. **Load Manifest**: Read image paths and labels from CSV
2. **Face Detection**: Use OpenCV Haar Cascade to detect and crop faces
3. **Blur Augmentation**: Generate 5 blur levels per face
4. **Split Data**: Randomly split into train/val/test (70/15/15)
5. **Resize**: Scale to target size maintaining aspect ratio
6. **Save**: Write organized directory structure

### Synthetic Mode

1. **Generate Shapes**: Create geometric shapes (circles for ProfA, rectangles for Room1)
2. **Add Noise**: Random colors and variations
3. **Split**: Create train/val splits
4. **Save**: Write to train/val directories

### Face Detection

**Method:** OpenCV Haar Cascade (frontal face detector)

**Parameters:**
- `scaleFactor`: 1.1 (multi-scale search)
- `minNeighbors`: 5 (detection confidence)
- `minSize`: (30, 30) (minimum face size in pixels)

**Fallback:** If no face detected, uses original image cropped to center.

### Blur Augmentation

**Implementation:** Gaussian blur with varying kernel sizes

```python
def create_blur_augmentation(image, blur_levels):
    augmented = []
    for level in [0.0, 0.5, 1.0, 1.5, 2.0]:
        if level == 0.0:
            augmented.append(image)  # Original
        else:
            kernel_size = int(level * 3) * 2 + 1
            blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), level)
            augmented.append(blurred)
    return augmented
```

## Implementation Details

**File:** `src/preprocess.py`

**Key functions:**
- `process_real_faces()`: Real data pipeline
- `create_blur_augmentation()`: Blur simulation
- `detect_face()`: OpenCV face detection
- `generate_synthetic_data()`: Synthetic shape generation

**Dependencies:**
- Python 3.11
- `opencv-python==4.9.0` - Image processing and face detection
- `numpy==1.24.3` - Array operations
- `pillow==10.2.0` - Image I/O
- `pyyaml==6.0.1` - Configuration

## Testing

**Unit tests:** `tests/unit/test_preprocess.py`

```bash
# Run tests
pytest tests/unit/test_preprocess.py -v
```

Tests cover:
- Blur augmentation correctness
- Face detection accuracy
- Train/val/test split ratios
- Image resizing
- Directory structure creation

## Integration with Pipeline

**Upstream:** Requires `data/interim/manifest.csv` from ingestion

**Downstream:** Outputs consumed by train component

**Workflow:**
```bash
docker compose run ingestion      # Creates manifest
docker compose run preprocess     # Processes images
docker compose run train          # Trains on processed data
```

## Troubleshooting

### Issue: No Face Detected

**Symptom:** Warning messages about face detection failures

```
[preprocess] Warning: No face detected in image ProfA/img042.jpg, using center crop
```

**Causes:**
- Side profile or angled face
- Low image quality
- Occlusions (sunglasses, masks)

**Impact:** Uses center crop as fallback (usually acceptable)

### Issue: Out of Memory

**Symptom:** `MemoryError` or Python process killed

**Causes:** Processing too many large images simultaneously

**Fix:** Reduce batch processing or image size
```yaml
# params.yaml
img_size: 160  # Reduce from 224
```

### Issue: Slow Processing

**Symptom:** Takes >5 minutes for 1000 images

**Optimization tips:**
- Disable blur augmentation for testing: `blur_augmentation: false`
- Use synthetic mode: `use_real_faces: false`
- Reduce image size: `img_size: 112`

### Issue: Incorrect Split Ratios

**Symptom:** Uneven class distribution in splits

**Fix:** Check seed value for reproducibility
```yaml
seed: 42  # Fixed seed ensures same splits
```

## Performance

**Real Data (1000 images):**
- Face detection: ~30 seconds
- Blur augmentation: ~45 seconds (5 levels)
- Resizing & saving: ~20 seconds
- **Total:** ~1.5 minutes

**Synthetic Data:**
- Generation: ~2 seconds
- **Total:** ~2 seconds

**Memory usage:** ~500MB peak (1000 images)

**Disk usage:** 
- Input: ~500MB (1000 raw images)
- Output: ~250MB (224×224 JPEG, 5000 augmented images)

## Future Enhancements

- [ ] MediaPipe for more robust face detection
- [ ] Additional augmentations (rotation, lighting)
- [ ] Data quality filtering (blur detection, resolution check)
- [ ] Multi-face handling (group photos)
- [ ] Background removal
- [ ] Normalization statistics per-dataset

## Related Documentation

- [Pipeline Overview](../docs/PIPELINE.md#component-2-preprocess)
- [Design Decisions](../docs/DECISIONS.md#data-augmentation-blur-simulation)
- [Architecture](../docs/ARCHITECTURE.md)

## Contact

For issues or questions, see main repository README.
