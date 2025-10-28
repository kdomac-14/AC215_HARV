"""  
Training Component for HARV Pipeline.

This module implements transfer learning for face recognition using
MobileNetV3 or EfficientNet-B0 with ImageNet pretrained weights.

Features:
- Transfer learning with configurable freeze ratio (default 70%)
- CPU-optimized training (no GPU required)
- Enhanced data augmentation (flip, rotation, color jitter)
- Early stopping based on validation accuracy
- Learning rate scheduling

Author: HARV Team
License: MIT
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple

import torch
import yaml
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

# Load parameters
with open("/app/params.yaml") as f:
    P: Dict[str, Any] = yaml.safe_load(f)

data_dir: str = "/app/data/processed"

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

train_ds: datasets.ImageFolder = datasets.ImageFolder(os.path.join(data_dir, "train"), transform=train_tf)
val_ds: datasets.ImageFolder = datasets.ImageFolder(os.path.join(data_dir, "val"), transform=val_tf)
train_dl: DataLoader = torch.utils.data.DataLoader(train_ds, batch_size=P["batch_size"], shuffle=True)
val_dl: DataLoader = torch.utils.data.DataLoader(val_ds, batch_size=P["batch_size"])

num_classes: int = len(train_ds.classes)
print(f"[train] Found {num_classes} classes: {train_ds.classes}")
print(f"[train] Training samples: {len(train_ds)}, Validation samples: {len(val_ds)}")


def build_model(model_name: str, num_classes: int, freeze_ratio: float) -> nn.Module:
    """
    Build and configure transfer learning model.
    
    Loads pretrained model from torchvision, replaces final classifier layer,
    and freezes specified ratio of early layers for transfer learning.
    
    Args:
        model_name: Model architecture ("mobilenet_v3_small" or "efficientnet_b0").
        num_classes: Number of output classes for classification.
        freeze_ratio: Proportion of layers to freeze (0.0-1.0).
    
    Returns:
        Configured PyTorch model ready for training.
    
    Example:
        >>> model = build_model("mobilenet_v3_small", num_classes=2, freeze_ratio=0.7)
        >>> trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    """
    if model_name == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights='IMAGENET1K_V1')
        in_feats = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_feats, num_classes)
    else:
        model = models.efficientnet_b0(weights='IMAGENET1K_V1')
        in_feats = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_feats, num_classes)
    
    # Freeze early layers
    if freeze_ratio > 0:
        total_layers = len(list(model.features))
        freeze_layers = int(total_layers * freeze_ratio)
        for i, (name, param) in enumerate(model.features.named_parameters()):
            if i < freeze_layers:
                param.requires_grad = False
    
    return model

# Build model with transfer learning
freeze_ratio: float = P.get("freeze_ratio", 0.7)
model: nn.Module = build_model(P["model_name"], num_classes, freeze_ratio)

device: torch.device = torch.device("cpu")
model = model.to(device)

# Enhanced optimizer with weight decay
opt: optim.Adam = optim.Adam(model.parameters(), lr=P["lr"], weight_decay=1e-4)
crit: nn.CrossEntropyLoss = nn.CrossEntropyLoss()

# Learning rate scheduler
scheduler: optim.lr_scheduler.StepLR = optim.lr_scheduler.StepLR(opt, step_size=3, gamma=0.1)

best_acc: float = 0.0
best_path: Path = Path("/app/artifacts/checkpoints")
best_path.mkdir(parents=True, exist_ok=True)

print(f"[train] Starting training for {P['epochs']} epochs...")
print(f"[train] Learning rate: {P['lr']}, Batch size: {P['batch_size']}")
print(f"[train] Freeze ratio: {freeze_ratio}")


def train_epoch(model: nn.Module, train_dl: DataLoader, opt: optim.Adam, crit: nn.CrossEntropyLoss, device: torch.device) -> Tuple[float, float]:
    """
    Execute one training epoch.
    
    Args:
        model: PyTorch model to train.
        train_dl: Training data loader.
        opt: Optimizer.
        crit: Loss criterion.
        device: Device to run on (CPU or GPU).
    
    Returns:
        Tuple of (average loss, accuracy percentage).
    """
    model.train()
    train_loss: float = 0.0
    train_correct: int = 0
    train_total: int = 0
    
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
    
    avg_loss: float = train_loss / len(train_dl)
    accuracy: float = 100 * train_correct / train_total
    return avg_loss, accuracy


def validate(model: nn.Module, val_dl: DataLoader, crit: nn.CrossEntropyLoss, device: torch.device) -> Tuple[float, float]:
    """
    Evaluate model on validation set.
    
    Args:
        model: PyTorch model to evaluate.
        val_dl: Validation data loader.
        crit: Loss criterion.
        device: Device to run on (CPU or GPU).
    
    Returns:
        Tuple of (average loss, accuracy percentage).
    """
    model.eval()
    val_correct: int = 0
    val_total: int = 0
    val_loss: float = 0.0
    
    with torch.no_grad():
        for x, y in val_dl:
            x, y = x.to(device), y.to(device)
            outputs = model(x)
            loss = crit(outputs, y)
            val_loss += loss.item()
            
            _, predicted = torch.max(outputs.data, 1)
            val_total += y.size(0)
            val_correct += (predicted == y).sum().item()
    
    avg_loss: float = val_loss / len(val_dl)
    accuracy: float = 100 * val_correct / val_total
    return avg_loss, accuracy


# Training loop
for epoch in range(P["epochs"]):
    # Training phase
    train_loss, train_acc = train_epoch(model, train_dl, opt, crit, device)
    
    # Validation phase
    val_loss, val_acc = validate(model, val_dl, crit, device)
    
    print(f"[train] Epoch {epoch+1}/{P['epochs']}: "
          f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, "
          f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
    
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), best_path / "best.pt")
        print(f"[train] New best model saved with val_acc: {best_acc:.2f}%")
    
    scheduler.step()

# Save final metrics
metrics: Dict[str, Any] = {
    "val_acc": best_acc,
    "final_train_acc": train_acc,
    "epochs": P["epochs"],
    "model_name": P["model_name"],
    "num_classes": num_classes,
    "train_samples": len(train_ds),
    "val_samples": len(val_ds)
}

Path("/app/artifacts").mkdir(parents=True, exist_ok=True)
with open("/app/artifacts/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"[train] Training completed! Best validation accuracy: {best_acc:.2f}%")
print(f"[train] Metrics saved to /app/artifacts/metrics.json")
