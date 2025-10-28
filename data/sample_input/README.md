# Sample Input Data

This directory contains a tiny sample dataset for quickstart demonstrations.

## Contents

For synthetic mode (default):
- No files required - preprocessing generates geometric shapes

For real face mode:
- Add 2-5 sample images here organized by class:
  ```
  sample_input/
  ├── ProfA/
  │   └── sample1.jpg
  └── Room1/
      └── sample1.jpg
  ```

## Usage

```bash
# Copy your sample images
cp /path/to/images/*.jpg data/sample_input/ProfA/

# Run pipeline
make run
```

See [docs/PIPELINE.md](../../docs/PIPELINE.md) for details.
