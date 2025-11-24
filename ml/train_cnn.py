"""Training script for the HARV visual fallback model."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import torch
import torch.nn.functional as F
import yaml
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, models, transforms


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


@dataclass
class Config:
    experiment_name: str
    seed: int
    train_dir: Path
    val_dir: Path
    image_size: int
    batch_size: int
    epochs: int
    learning_rate: float
    weight_decay: float
    output_dir: Path
    metrics_path: Path
    augmentations: dict

    @classmethod
    def from_yaml(cls, path: Path) -> Config:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        data["train_dir"] = Path(data["train_dir"])
        data["val_dir"] = Path(data["val_dir"])
        data["output_dir"] = Path(data["output_dir"])
        data["metrics_path"] = Path(data["metrics_path"])
        return cls(**data)


class SyntheticVisionDataset(Dataset):
    """Fallback dataset when image folders are not available."""

    def __init__(self, size: int, image_size: int, num_classes: int = 2):
        self.size = size
        self.image_size = image_size
        self.num_classes = num_classes

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, idx: int):
        torch.manual_seed(idx)
        image = torch.rand(3, self.image_size, self.image_size)
        label = torch.tensor(idx % self.num_classes, dtype=torch.long)
        return image, label


def build_dataloaders(cfg: Config) -> tuple[DataLoader, DataLoader, int]:
    augment_list = [
        transforms.Resize((cfg.image_size, cfg.image_size)),
        transforms.ToTensor(),
    ]

    if cfg.augmentations.get("horizontal_flip"):
        augment_list.insert(1, transforms.RandomHorizontalFlip())
    if cfg.augmentations.get("random_rotation_degrees"):
        augment_list.insert(
            1, transforms.RandomRotation(cfg.augmentations["random_rotation_degrees"])
        )
    if cfg.augmentations.get("color_jitter"):
        augment_list.insert(1, transforms.ColorJitter(brightness=0.1, contrast=0.1))

    transform_pipeline = transforms.Compose(augment_list)
    eval_pipeline = transforms.Compose(
        [
            transforms.Resize((cfg.image_size, cfg.image_size)),
            transforms.ToTensor(),
        ]
    )

    if cfg.train_dir.exists():
        train_dataset = datasets.ImageFolder(cfg.train_dir, transform_pipeline)
        val_dataset = datasets.ImageFolder(cfg.val_dir, eval_pipeline)
    else:
        print(
            f"[train_cnn] {cfg.train_dir} not found. Using synthetic samples to keep the pipeline reproducible."
        )
        train_dataset = SyntheticVisionDataset(size=200, image_size=cfg.image_size)
        val_dataset = SyntheticVisionDataset(size=40, image_size=cfg.image_size)

    num_classes = len(getattr(train_dataset, "classes", [])) or 2
    train_loader = DataLoader(train_dataset, batch_size=cfg.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=cfg.batch_size)
    return train_loader, val_loader, num_classes


def train(cfg: Config) -> dict:
    set_seed(cfg.seed)
    train_loader, val_loader, num_classes = build_dataloaders(cfg)

    model = models.mobilenet_v3_small(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay
    )
    best_accuracy = 0.0

    for epoch in range(cfg.epochs):
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad()
            logits = model(images)
            loss = F.cross_entropy(logits, labels)
            loss.backward()
            optimizer.step()

        accuracy, precision, recall, fpr = evaluate(model, val_loader, num_classes)
        print(
            f"[train_cnn] epoch={epoch+1}/{cfg.epochs} acc={accuracy:.3f} precision={precision:.3f}"
        )
        best_accuracy = max(best_accuracy, accuracy)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = cfg.output_dir / "weights.pt"
    torch.save(model.state_dict(), model_path)

    latency_ms = benchmark_latency(model, cfg.image_size)

    metrics = {
        "accuracy": best_accuracy,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": fpr,
        "latency_ms": latency_ms,
    }
    cfg.metrics_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    metadata = {
        "model_name": cfg.experiment_name,
        "architecture": "mobilenet_v3_small",
        "classes": num_classes,
        "threshold": 0.65,
        "metrics": metrics,
    }
    metadata_path = cfg.output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[train_cnn] saved weights to {model_path}")
    return metrics


def evaluate(
    model: nn.Module, loader: DataLoader, num_classes: int
) -> tuple[float, float, float, float]:
    model.eval()
    correct = 0
    total = 0
    true_positive = 0
    false_positive = 0
    false_negative = 0

    with torch.no_grad():
        for images, labels in loader:
            logits = model(images)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            true_positive += ((preds == 1) & (labels == 1)).sum().item()
            false_positive += ((preds == 1) & (labels == 0)).sum().item()
            false_negative += ((preds == 0) & (labels == 1)).sum().item()

    accuracy = correct / max(total, 1)
    precision = true_positive / max((true_positive + false_positive), 1)
    recall = true_positive / max((true_positive + false_negative), 1)
    fpr = false_positive / max((false_positive + true_positive), 1)
    return accuracy, precision, recall, fpr


def benchmark_latency(model: nn.Module, image_size: int) -> float:
    dummy = torch.rand(1, 3, image_size, image_size)
    start = perf_counter()
    for _ in range(20):
        _ = model(dummy)
    end = perf_counter()
    avg = (end - start) / 20
    return avg * 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the HARV MobileNet fallback.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("ml/configs/harv_vision_v1.yaml"),
        help="Path to YAML config.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = Config.from_yaml(args.config)
    train(cfg)
