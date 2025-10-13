import os, json, yaml, torch
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report
from pathlib import Path

with open("/app/params.yaml") as f:
    P = yaml.safe_load(f)
data_dir = "/app/data/processed"
test_tf = transforms.Compose([transforms.Resize((P["img_size"], P["img_size"])), transforms.ToTensor()])
test_ds = datasets.ImageFolder(os.path.join(data_dir,"test"), transform=test_tf)
test_dl = torch.utils.data.DataLoader(test_ds, batch_size=32)

if P["model_name"] == "mobilenet_v3_small":
    model = models.mobilenet_v3_small(weights=None)
    in_feats = model.classifier[3].in_features
    model.classifier[3] = torch.nn.Linear(in_feats, len(test_ds.classes))
else:
    model = models.efficientnet_b0(weights=None)
    in_feats = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(in_feats, len(test_ds.classes))

ckpt = "/app/artifacts/checkpoints/best.pt"
model.load_state_dict(torch.load(ckpt, map_location="cpu"))
model.eval()

y_true, y_pred = [], []
with torch.no_grad():
    for x,y in test_dl:
        p = model(x).argmax(1)
        y_true += y.tolist()
        y_pred += p.tolist()

report = classification_report(y_true, y_pred, target_names=test_ds.classes, output_dict=True)
Path("/app/artifacts").mkdir(parents=True, exist_ok=True)
with open("/app/artifacts/metrics.json","w") as f:
    json.dump({"test_report":report}, f, indent=2)
print("[evaluate] wrote /app/artifacts/metrics.json")
