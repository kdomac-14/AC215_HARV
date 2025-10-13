import os, time, yaml, torch, json
from torch import nn, optim
from torchvision import datasets, transforms, models
from pathlib import Path

with open("/app/params.yaml") as f:
    P = yaml.safe_load(f)

data_dir = "/app/data/processed"
train_tf = transforms.Compose([
    transforms.Resize((P["img_size"], P["img_size"])),
    transforms.ToTensor(),
])
train_ds = datasets.ImageFolder(os.path.join(data_dir,"train"), transform=train_tf)
val_ds   = datasets.ImageFolder(os.path.join(data_dir,"val"),   transform=train_tf)
train_dl = torch.utils.data.DataLoader(train_ds, batch_size=P["batch_size"], shuffle=True)
val_dl   = torch.utils.data.DataLoader(val_ds,   batch_size=P["batch_size"])

num_classes = len(train_ds.classes)

if P["model_name"] == "mobilenet_v3_small":
    model = models.mobilenet_v3_small(weights=None)
    in_feats = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_feats, num_classes)
else:
    model = models.efficientnet_b0(weights=None)  # lite0 stand-in
    in_feats = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_feats, num_classes)

device = torch.device("cpu")
model = model.to(device)

opt = optim.Adam(model.parameters(), lr=P["lr"])
crit = nn.CrossEntropyLoss()

best_acc, best_path = 0.0, Path("/app/artifacts/checkpoints")
best_path.mkdir(parents=True, exist_ok=True)
for epoch in range(P["epochs"]):
    model.train()
    for x,y in train_dl:
        x,y = x.to(device), y.to(device)
        opt.zero_grad(); loss = crit(model(x), y); loss.backward(); opt.step()

    # val
    model.eval(); correct=total=0
    with torch.no_grad():
        for x,y in val_dl:
            x,y = x.to(device), y.to(device)
            pred = model(x).argmax(1)
            correct += (pred==y).sum().item(); total += y.numel()
    acc = correct/total if total else 0
    print(f"[train] epoch={epoch} val_acc={acc:.3f}")
    if acc > best_acc:
        best_acc = acc
        torch.save(model.state_dict(), best_path/"best.pt")

# minimal metrics
(Path("/app/artifacts").mkdir(parents=True, exist_ok=True))
with open("/app/artifacts/metrics.json","w") as f:
    json.dump({"val_acc":best_acc}, f)
print("[train] saved best checkpoint, val_acc", best_acc)
