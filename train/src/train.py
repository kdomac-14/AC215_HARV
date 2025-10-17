import os, time, yaml, torch, json
from torch import nn, optim
from torchvision import datasets, transforms, models
from pathlib import Path
import torch.nn.functional as F

with open("/app/params.yaml") as f:
    P = yaml.safe_load(f)

data_dir = "/app/data/processed"

# Enhanced data augmentation for face recognition
train_tf = transforms.Compose([
    transforms.Resize((P["img_size"], P["img_size"])),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_tf = transforms.Compose([
    transforms.Resize((P["img_size"], P["img_size"])),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

train_ds = datasets.ImageFolder(os.path.join(data_dir,"train"), transform=train_tf)
val_ds   = datasets.ImageFolder(os.path.join(data_dir,"val"),   transform=val_tf)
train_dl = torch.utils.data.DataLoader(train_ds, batch_size=P["batch_size"], shuffle=True)
val_dl   = torch.utils.data.DataLoader(val_ds,   batch_size=P["batch_size"])

num_classes = len(train_ds.classes)
print(f"[train] Found {num_classes} classes: {train_ds.classes}")
print(f"[train] Training samples: {len(train_ds)}, Validation samples: {len(val_ds)}")

# Enhanced model architecture for face recognition
if P["model_name"] == "mobilenet_v3_small":
    model = models.mobilenet_v3_small(weights='IMAGENET1K_V1')  # Use pretrained weights
    in_feats = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_feats, num_classes)
else:
    model = models.efficientnet_b0(weights='IMAGENET1K_V1')  # Use pretrained weights
    in_feats = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_feats, num_classes)

# Freeze early layers for transfer learning
freeze_ratio = P.get("freeze_ratio", 0.7)
if freeze_ratio > 0:
    if P["model_name"] == "mobilenet_v3_small":
        total_layers = len(list(model.features))
        freeze_layers = int(total_layers * freeze_ratio)
        for i, (name, param) in enumerate(model.features.named_parameters()):
            if i < freeze_layers:
                param.requires_grad = False
    else:
        total_layers = len(list(model.features))
        freeze_layers = int(total_layers * freeze_ratio)
        for i, (name, param) in enumerate(model.features.named_parameters()):
            if i < freeze_layers:
                param.requires_grad = False

device = torch.device("cpu")
model = model.to(device)

# Enhanced optimizer with weight decay
opt = optim.Adam(model.parameters(), lr=P["lr"], weight_decay=1e-4)
crit = nn.CrossEntropyLoss()

# Learning rate scheduler
scheduler = optim.lr_scheduler.StepLR(opt, step_size=3, gamma=0.1)

best_acc, best_path = 0.0, Path("/app/artifacts/checkpoints")
best_path.mkdir(parents=True, exist_ok=True)

print(f"[train] Starting training for {P['epochs']} epochs...")
print(f"[train] Learning rate: {P['lr']}, Batch size: {P['batch_size']}")
print(f"[train] Freeze ratio: {freeze_ratio}")

for epoch in range(P["epochs"]):
    # Training phase
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    
    for x, y in train_dl:
        x, y = x.to(device), y.to(device)
        opt.zero_grad()
        outputs = model(x)
        loss = crit(outputs, y)
        loss.backward()
        opt.step()
        
        train_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        train_total += y.size(0)
        train_correct += (predicted == y).sum().item()
    
    train_acc = 100 * train_correct / train_total
    
    # Validation phase
    model.eval()
    val_correct = 0
    val_total = 0
    val_loss = 0.0
    
    with torch.no_grad():
        for x, y in val_dl:
            x, y = x.to(device), y.to(device)
            outputs = model(x)
            loss = crit(outputs, y)
            val_loss += loss.item()
            
            _, predicted = torch.max(outputs.data, 1)
            val_total += y.size(0)
            val_correct += (predicted == y).sum().item()
    
    val_acc = 100 * val_correct / val_total
    
    print(f"[train] Epoch {epoch+1}/{P['epochs']}: "
          f"Train Loss: {train_loss/len(train_dl):.4f}, Train Acc: {train_acc:.2f}%, "
          f"Val Loss: {val_loss/len(val_dl):.4f}, Val Acc: {val_acc:.2f}%")
    
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), best_path/"best.pt")
        print(f"[train] New best model saved with val_acc: {best_acc:.2f}%")
    
    scheduler.step()

# Save final metrics
metrics = {
    "val_acc": best_acc,
    "final_train_acc": train_acc,
    "epochs": P["epochs"],
    "model_name": P["model_name"],
    "num_classes": num_classes,
    "train_samples": len(train_ds),
    "val_samples": len(val_ds)
}

(Path("/app/artifacts").mkdir(parents=True, exist_ok=True))
with open("/app/artifacts/metrics.json","w") as f:
    json.dump(metrics, f, indent=2)

print(f"[train] Training completed! Best validation accuracy: {best_acc:.2f}%")
print(f"[train] Metrics saved to /app/artifacts/metrics.json")
