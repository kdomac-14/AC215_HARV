# Sample Evidence

This directory contains minimal example outputs for documentation and verification purposes.

## Files

### example_prediction.json

Sample API response from the `/verify` endpoint showing:
- Predicted class label
- Confidence scores
- Inference latency

**Use case:** Demonstrates expected API output format for graders/reviewers.

### example_metrics.json

Sample training metrics showing:
- Epoch number
- Training/validation loss
- Training/validation accuracy

**Use case:** Shows typical training progression on synthetic dataset.

## Generating Your Own

After running the pipeline:

```bash
# Run full pipeline
make run

# Check actual metrics
cat artifacts/metrics.json

# Test API and save response
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d @test_payload.json > outputs/samples/my_prediction.json
```

## Note

These are **example files only** for documentation. Actual runtime outputs are gitignored and generated fresh each pipeline run.

For complete evidence collection, use:
```bash
make evidence
```
