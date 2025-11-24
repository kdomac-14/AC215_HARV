# Data Versioning Strategy

## Overview
- **Tooling**: DVC orchestrates the ingestion → preprocess → train → evaluate → export stages defined in `dvc.yaml`.
- **Storage**: By default the repo expects local folders (`data/interim`, `data/processed`, `artifacts/*`). Connect a remote (S3/GCS) by running `dvc remote add -d gcs gs://<bucket>` if desired.
- **Model Artifacts**: Logged to `models/harv_cnn_v1` with metrics in `artifacts/metrics/`. Each version folder contains `metadata.json` + weights, making rollbacks trivial.

## Workflow
1. **Pull existing data**
   ```bash
   dvc pull data/interim
   dvc pull data/processed
   ```
2. **Update raw data**
   - Drop new classroom captures into `data/raw/vision/<room>/<images>.jpg`.
   - Commit large files with `dvc add data/raw/vision`.
3. **Re-run pipeline**
   ```bash
   dvc repro train  # will trigger ingest + preprocess upstream if needed
   ```
4. **Register artifacts**
   - Copy the exported model to `models/harv_cnn_v1` (or bump to v2/v3).
   - Commit the updated `.dvc` files and `artifacts/metrics/*.json`.

## Snapshot Alternative
If DVC is unavailable, use the snapshot convention already checked in:
```
data/
  raw/
  interim/
  processed/
models/
  harv_cnn_v1/
  harv_cnn_v2/   # create when hyperparameters change
```
Document each snapshot in `docs/model_results.md` and tag Git commits (e.g., `git tag data-v1`).

## Generated/Synthetic Data
- Synthetic prompts or data augmentations belong in `data/generated/` with a JSONL file capturing prompt + response + timestamp.
- Update this doc whenever a new augmentation source is introduced so graders know how to reproduce the dataset.
