# Ingestion Component

Creates a manifest CSV file that indexes available training data for the HARV pipeline.

## Purpose

The ingestion component scans input data and creates a structured manifest file that maps image paths to class labels. This manifest serves as the input to the preprocessing stage.

**Key responsibilities:**
- Scan raw image directories
- Detect class labels from folder structure
- Generate CSV manifest with `relpath` and `label` columns
- Handle fallback to placeholder data when real data unavailable

## Inputs

### Real Data Mode (`use_real_faces=true` in `params.yaml`)

**Expected directory structure:**
```
data/raw/
├── ProfA/
│   ├── img001.jpg
│   ├── img002.jpg
│   └── ...
├── Room1/
│   ├── img001.jpg
│   ├── img002.jpg
│   └── ...
└── ...
```

Each subdirectory represents a class label. Images can be in JPG, PNG, or other common formats.

### Synthetic Mode (`use_real_faces=false`)

No input required. Creates a placeholder manifest for synthetic data generation in the preprocess stage.

## Outputs

### Manifest File

**Location:** `data/interim/manifest.csv`

**Format:**
```csv
relpath,label
ProfA/img001.jpg,ProfA
ProfA/img002.jpg,ProfA
Room1/img001.jpg,Room1
Room1/img002.jpg,Room1
```

**Schema:**
- `relpath`: Relative path to image from `data/raw/`
- `label`: Class label (typically person name or room identifier)

## Configuration

Configured via `params.yaml` at repository root:

```yaml
use_real_faces: false  # Set to true for real datasets
```

## How to Run

### Docker (Recommended)

```bash
# From repository root
docker compose run ingestion
```

### Standalone Docker

```bash
cd ingestion/
docker build -t harv-ingestion .
docker run -v $(pwd)/../data:/app/data \
           -v $(pwd)/../params.yaml:/app/params.yaml \
           harv-ingestion
```

### Local Development

```bash
cd ingestion/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run
python -m src.ingest
```

## Expected Output

### Console Logs

**Synthetic mode:**
```
[ingestion] Using synthetic dataset
[ingestion] Wrote manifest: /app/data/interim/manifest.csv
```

**Real data mode:**
```
[ingestion] Using real face dataset
[ingestion] Found existing face manifest
[ingestion] Copied face manifest to main manifest
```

### Artifacts Created

- `data/interim/manifest.csv` - Manifest file
- `data/interim/` directory created if doesn't exist

## Error Handling

### No Real Data Found

If `use_real_faces=true` but no images exist in `data/raw/`:

```
[ingestion] No face manifest found, creating placeholder
[ingestion] Wrote manifest: /app/data/interim/manifest.csv
```

Falls back to placeholder manifest automatically.

### Missing params.yaml

```
[ingestion] params.yaml not found, using default settings
[ingestion] Using synthetic dataset
```

Defaults to synthetic mode.

## Implementation Details

**File:** `src/ingest.py`

**Key logic:**
1. Load configuration from `params.yaml`
2. Check `use_real_faces` flag
3. If true, attempt to load pre-generated face manifest
4. If false or no manifest found, create placeholder manifest
5. Ensure `data/interim/` directory exists
6. Write manifest CSV

**Dependencies:**
- Python 3.11
- `pyyaml` - YAML parsing
- Standard library: `csv`, `pathlib`, `os`

## Testing

**Unit tests:** `tests/unit/test_ingestion.py`

```bash
# Run unit tests
pytest tests/unit/test_ingestion.py -v
```

Tests cover:
- Manifest creation with synthetic data
- CSV format validation
- Directory creation
- Error handling

## Integration with Pipeline

**Upstream:** No dependencies (first stage)

**Downstream:** `preprocess` component reads `data/interim/manifest.csv`

**Typical workflow:**
```bash
docker compose run ingestion      # Creates manifest
docker compose run preprocess     # Reads manifest, processes images
```

## Troubleshooting

### Issue: Manifest Empty

**Symptom:** `manifest.csv` has only header row

**Cause:** No images in `data/raw/` and `use_real_faces=true`

**Fix:** Add images to `data/raw/` or set `use_real_faces=false`

### Issue: Permission Denied

**Symptom:** `PermissionError: [Errno 13] Permission denied: 'data/interim'`

**Cause:** Docker volume mount permissions

**Fix:**
```bash
# Create directory with correct permissions
mkdir -p data/interim
chmod 755 data/interim
```

### Issue: Missing params.yaml

**Symptom:** Warning about missing params.yaml

**Fix:**
```bash
# Copy from example
cp params.yaml.example params.yaml

# Or create minimal params.yaml
echo "use_real_faces: false" > params.yaml
```

## Performance

- **Execution time:** <1 second (synthetic mode)
- **Execution time:** 1-5 seconds (real data mode with 100-1000 images)
- **Memory usage:** <100MB
- **Disk usage:** <1MB (manifest file)

## Future Enhancements

- [ ] Support multiple data sources (URLs, S3, GCS)
- [ ] Automatic class balancing recommendations
- [ ] Data quality checks (corrupt images, duplicates)
- [ ] Metadata extraction (image dimensions, file sizes)
- [ ] Incremental manifest updates

## Related Documentation

- [Pipeline Overview](../docs/PIPELINE.md#component-1-ingestion)
- [Architecture](../docs/ARCHITECTURE.md)
- [Runbook](../docs/RUNBOOK.md)

## Contact

For issues or questions, see main repository README.
