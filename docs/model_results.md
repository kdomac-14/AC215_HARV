# Model Results (Milestone 4)

| Experiment | Accuracy | Precision | Recall | FPR | Latency (ms) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `harv_vision_v1` | 0.962 | 0.955 | 0.968 | 0.010 | 38.2 | Synthetic run for reproducibility; retrain with campus captures for production. Metrics stored in `artifacts/metrics/harv_cnn_v1.json`. |

Artifacts:
- Weights: `models/harv_cnn_v1/weights.pt`
- Metadata: `models/harv_cnn_v1/metadata.json`
- Logs: `ml/train_cnn.py` output + metrics JSON
