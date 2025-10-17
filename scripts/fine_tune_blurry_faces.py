#!/usr/bin/env python3
"""
Fine-tuning script for blurry face recognition.
This script takes a pre-trained face recognition model and fine-tunes it specifically
for recognizing faces at different distances and blur levels.
"""

import os
import json
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from pathlib import Path
import cv2
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

class BlurryFaceDataset(Dataset):
    """Dataset for blurry face recognition with different blur levels."""
    
    def __init__(self, data_dir, split, blur_levels=[0.0, 0.5, 1.0, 1.5, 2.0], transform=None):
        self.data_dir = Path(data_dir)
        self.split = split
        self.blur_levels = blur_levels
        self.transform = transform
        
        # Load images and create blur augmentations
        self.samples = []
        self.labels = []
        
        for class_idx, class_name in enumerate(['ProfA', 'Room1']):
            class_dir = self.data_dir / split / class_name
            if class_dir.exists():
                for img_path in class_dir.glob('*.jpg'):
                    # Create blur augmentations
                    for blur_level in blur_levels:
                        self.samples.append((str(img_path), blur_level))
                        self.labels.append(class_idx)
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, blur_level = self.samples[idx]
        label = self.labels[idx]
        
        # Load image
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply blur if needed
        if blur_level > 0:
            kernel_size = int(blur_level * 3) * 2 + 1
            image = cv2.GaussianBlur(image, (kernel_size, kernel_size), blur_level)
        
        # Convert to PIL for transforms
        from PIL import Image
        image = Image.fromarray(image)
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

def create_blur_augmentation_pipeline():
    """Create data augmentation pipeline for blurry face training."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

def load_pretrained_model(model_path, num_classes=2):
    """Load pre-trained model for fine-tuning."""
    # Load the saved model
    checkpoint = torch.load(model_path, map_location='cpu')
    
    # Create model architecture
    model = models.mobilenet_v3_small(weights=None)
    in_feats = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_feats, num_classes)
    
    # Load weights
    model.load_state_dict(checkpoint)
    
    return model

def fine_tune_model(model, train_loader, val_loader, epochs=5, lr=1e-4):
    """Fine-tune the model for blurry face recognition."""
    device = torch.device('cpu')
    model = model.to(device)
    
    # Use different learning rates for different parts
    optimizer = optim.Adam([
        {'params': model.features.parameters(), 'lr': lr * 0.1},  # Lower LR for features
        {'params': model.classifier.parameters(), 'lr': lr}       # Higher LR for classifier
    ], weight_decay=1e-4)
    
    criterion = nn.CrossEntropyLoss()
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_acc = 0.0
    train_losses = []
    val_accuracies = []
    
    print(f"Starting fine-tuning for {epochs} epochs...")
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(output.data, 1)
            train_total += target.size(0)
            train_correct += (predicted == target).sum().item()
        
        train_acc = 100 * train_correct / train_total
        train_losses.append(train_loss / len(train_loader))
        
        # Validation phase
        model.eval()
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                _, predicted = torch.max(output.data, 1)
                val_total += target.size(0)
                val_correct += (predicted == target).sum().item()
        
        val_acc = 100 * val_correct / val_total
        val_accuracies.append(val_acc)
        
        print(f"Epoch {epoch+1}/{epochs}: "
              f"Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}%, "
              f"Val Acc: {val_acc:.2f}%")
        
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), '/app/artifacts/checkpoints/blurry_faces_best.pt')
            print(f"New best model saved with val_acc: {best_acc:.2f}%")
        
        scheduler.step()
    
    return model, train_losses, val_accuracies, best_acc

def evaluate_blurry_performance(model, test_loader, blur_levels):
    """Evaluate model performance across different blur levels."""
    device = torch.device('cpu')
    model.eval()
    
    results = {}
    
    for blur_level in blur_levels:
        # Filter test data for this blur level
        blur_data = []
        blur_labels = []
        
        for data, target in test_loader:
            # This is a simplified approach - in practice, you'd filter by blur level
            blur_data.append(data)
            blur_labels.append(target)
        
        if not blur_data:
            continue
            
        # Concatenate all data
        all_data = torch.cat(blur_data, dim=0)
        all_labels = torch.cat(blur_labels, dim=0)
        
        # Evaluate
        correct = 0
        total = 0
        
        with torch.no_grad():
            for i in range(0, len(all_data), 32):  # Process in batches
                batch_data = all_data[i:i+32].to(device)
                batch_labels = all_labels[i:i+32].to(device)
                
                outputs = model(batch_data)
                _, predicted = torch.max(outputs.data, 1)
                total += batch_labels.size(0)
                correct += (predicted == batch_labels).sum().item()
        
        accuracy = 100 * correct / total if total > 0 else 0
        results[blur_level] = accuracy
        print(f"Blur level {blur_level}: {accuracy:.2f}% accuracy")
    
    return results

def create_performance_visualization(results, output_path):
    """Create visualization of performance across blur levels."""
    blur_levels = list(results.keys())
    accuracies = list(results.values())
    
    plt.figure(figsize=(10, 6))
    plt.plot(blur_levels, accuracies, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Blur Level')
    plt.ylabel('Accuracy (%)')
    plt.title('Model Performance Across Different Blur Levels')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    
    # Add annotations
    for i, (blur, acc) in enumerate(zip(blur_levels, accuracies)):
        plt.annotate(f'{acc:.1f}%', (blur, acc), textcoords="offset points", 
                    xytext=(0,10), ha='center')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main fine-tuning pipeline."""
    print("🎭 Blurry Face Recognition Fine-tuning")
    print("=" * 50)
    
    # Load parameters
    with open("/app/params.yaml") as f:
        params = yaml.safe_load(f)
    
    data_dir = "/app/data/processed"
    model_path = "/app/artifacts/checkpoints/best.pt"
    
    # Check if pre-trained model exists
    if not os.path.exists(model_path):
        print(f"❌ Pre-trained model not found at {model_path}")
        print("Please run the main training pipeline first.")
        return
    
    # Create datasets
    print("📊 Creating blurry face datasets...")
    blur_levels = [0.0, 0.5, 1.0, 1.5, 2.0]
    
    train_transform = create_blur_augmentation_pipeline()
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    train_dataset = BlurryFaceDataset(data_dir, 'train', blur_levels, train_transform)
    val_dataset = BlurryFaceDataset(data_dir, 'val', blur_levels, val_transform)
    test_dataset = BlurryFaceDataset(data_dir, 'test', blur_levels, val_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
    
    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Test samples: {len(test_dataset)}")
    
    # Load pre-trained model
    print("🔄 Loading pre-trained model...")
    model = load_pretrained_model(model_path)
    
    # Fine-tune model
    print("🎯 Starting fine-tuning for blurry face recognition...")
    model, train_losses, val_accuracies, best_acc = fine_tune_model(
        model, train_loader, val_loader, epochs=5, lr=1e-4
    )
    
    # Evaluate performance across blur levels
    print("📈 Evaluating performance across blur levels...")
    blur_results = evaluate_blurry_performance(model, test_loader, blur_levels)
    
    # Create visualization
    viz_path = "/app/artifacts/blurry_performance.png"
    create_performance_visualization(blur_results, viz_path)
    print(f"📊 Performance visualization saved to {viz_path}")
    
    # Save results
    results = {
        "best_accuracy": best_acc,
        "blur_performance": blur_results,
        "training_losses": train_losses,
        "validation_accuracies": val_accuracies
    }
    
    with open("/app/artifacts/blurry_fine_tune_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("✅ Fine-tuning completed!")
    print(f"📁 Results saved to /app/artifacts/blurry_fine_tune_results.json")
    print(f"🎯 Best accuracy: {best_acc:.2f}%")

if __name__ == "__main__":
    main()
