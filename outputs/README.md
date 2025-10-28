# Outputs Directory

This directory stores runtime-generated files from the HARV pipeline.

## Structure

```
outputs/
├── logs/           # Service and training logs (gitignored)
├── samples/        # Sample predictions and metrics
│   ├── example_prediction.json  # Tracked: Sample API response
│   └── example_metrics.json     # Tracked: Sample training metrics
└── [other runtime files]        # Gitignored
```

## Usage

**Training logs:**
```bash
# After running pipeline
ls outputs/logs/train_*.log
```

**Sample predictions:**
```bash
# View example API response
cat outputs/samples/example_prediction.json
```

## What's Tracked?

Only tiny example files are version-controlled for documentation purposes:
- `outputs/.gitkeep` - Directory placeholder
- `outputs/README.md` - This file
- `outputs/samples/README.md` - Sample guide
- `outputs/samples/example_prediction.json` - Sample API response
- `outputs/samples/example_metrics.json` - Sample training metrics

All other files in `outputs/` are gitignored to avoid bloating the repository with runtime artifacts.

## Evidence Collection

For milestone submissions, use:
```bash
make evidence
```

This creates a timestamped archive with all outputs, logs, and coverage reports.
