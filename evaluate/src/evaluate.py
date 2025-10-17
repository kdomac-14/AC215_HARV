import os, json, yaml, torch
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

with open("/app/params.yaml") as f:
    P = yaml.safe_load(f)

data_dir = "/app/data/processed"

# Enhanced test transforms for face recognition
test_tf = transforms.Compose([
    transforms.Resize((P["img_size"], P["img_size"])),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

test_ds = datasets.ImageFolder(os.path.join(data_dir,"test"), transform=test_tf)
test_dl = torch.utils.data.DataLoader(test_ds, batch_size=32)

print(f"[evaluate] Found {len(test_ds)} test samples")
print(f"[evaluate] Classes: {test_ds.classes}")

# Load model
if P["model_name"] == "mobilenet_v3_small":
    model = models.mobilenet_v3_small(weights=None)
    in_feats = model.classifier[3].in_features
    model.classifier[3] = torch.nn.Linear(in_feats, len(test_ds.classes))
else:
    model = models.efficientnet_b0(weights=None)
    in_feats = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(in_feats, len(test_ds.classes))

# Load checkpoint
ckpt_path = "/app/artifacts/checkpoints/best.pt"
if os.path.exists(ckpt_path):
    model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
    print(f"[evaluate] Loaded model from {ckpt_path}")
else:
    print(f"[evaluate] Warning: No checkpoint found at {ckpt_path}")

model.eval()

# Evaluation
y_true, y_pred, y_probs = [], [], []
with torch.no_grad():
    for x, y in test_dl:
        outputs = model(x)
        probs = torch.softmax(outputs, dim=1)
        pred = outputs.argmax(1)
        
        y_true += y.tolist()
        y_pred += pred.tolist()
        y_probs += probs.tolist()

# Calculate metrics
accuracy = sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true)
print(f"[evaluate] Test Accuracy: {accuracy:.4f}")

# Classification report
report = classification_report(y_true, y_pred, target_names=test_ds.classes, output_dict=True)

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)

# ROC AUC (for binary classification)
if len(test_ds.classes) == 2:
    try:
        y_probs_array = np.array(y_probs)
        roc_auc = roc_auc_score(y_true, y_probs_array[:, 1])
        print(f"[evaluate] ROC AUC: {roc_auc:.4f}")
    except:
        roc_auc = None
else:
    roc_auc = None

# Create confusion matrix visualization
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=test_ds.classes, yticklabels=test_ds.classes)
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()
cm_path = "/app/artifacts/confusion_matrix.png"
plt.savefig(cm_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"[evaluate] Confusion matrix saved to {cm_path}")

# Enhanced metrics
metrics = {
    "test_accuracy": accuracy,
    "test_report": report,
    "confusion_matrix": cm.tolist(),
    "num_test_samples": len(test_ds),
    "classes": test_ds.classes,
    "model_name": P["model_name"]
}

if roc_auc is not None:
    metrics["roc_auc"] = roc_auc

# Per-class metrics
for class_name in test_ds.classes:
    if class_name in report:
        class_metrics = report[class_name]
        print(f"[evaluate] {class_name}: Precision={class_metrics['precision']:.3f}, "
              f"Recall={class_metrics['recall']:.3f}, F1={class_metrics['f1-score']:.3f}")

# Save results
Path("/app/artifacts").mkdir(parents=True, exist_ok=True)
with open("/app/artifacts/metrics.json","w") as f:
    json.dump(metrics, f, indent=2)

print("[evaluate] Enhanced evaluation completed!")
print(f"[evaluate] Results saved to /app/artifacts/metrics.json")
