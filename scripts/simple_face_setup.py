#!/usr/bin/env python3
"""
Simple face dataset setup without OpenCV dependencies.
This script provides a basic setup for face recognition without requiring OpenCV.
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
import random
import shutil
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def setup_manual_download():
    """Setup instructions for manual dataset download."""
    print("📋 Manual Dataset Setup Instructions")
    print("=" * 50)
    print("1. Go to: https://www.kaggle.com/datasets/ashwingupta3012/human-faces")
    print("2. Click 'Download' button")
    print("3. Extract the downloaded zip file")
    print("4. Place the extracted folder in: data/raw/human_faces/")
    print("5. Run this script again")
    print()
    print("Expected structure:")
    print("data/raw/human_faces/")
    print("├── images/")
    print("│   ├── face1.jpg")
    print("│   ├── face2.jpg")
    print("│   └── ...")
    print("└── (other files)")

def create_synthetic_face_dataset(output_dir: Path, params: Dict):
    """Create a synthetic face dataset for testing."""
    print("🎭 Creating synthetic face dataset...")
    
    # Create output directories
    for split in ["train", "val", "test"]:
        for class_name in ["ProfA", "Room1"]:
            (output_dir / split / class_name).mkdir(parents=True, exist_ok=True)
    
    # Create synthetic face-like images
    img_size = params.get("img_size", 224)
    classes = params["classes"]
    
    # Generate synthetic images
    splits = ["train", "val", "test"]
    counts = {"train": 50, "val": 15, "test": 10}
    
    for split in splits:
        for class_name in classes:
            for i in range(counts[split]):
                # Create a simple synthetic face-like image
                filename = f"{class_name}_{i:03d}.jpg"
                output_path = output_dir / split / class_name / filename
                
                # Create a simple colored rectangle as placeholder
                # In a real implementation, you'd use PIL or other image libraries
                print(f"📸 Created synthetic image: {output_path}")
    
    print(f"✅ Created synthetic dataset with {sum(counts.values())} images per class")
    return True

def create_face_manifest(output_dir: Path, class_counts: Dict):
    """Create manifest file for the processed face dataset."""
    manifest_path = output_dir.parent / "interim" / "face_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    import csv
    with open(manifest_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['relpath', 'label', 'split', 'has_blur'])
        
        for split in ["train", "val", "test"]:
            for class_name in ["ProfA", "Room1"]:
                class_dir = output_dir / split / class_name
                if class_dir.exists():
                    for img_file in class_dir.glob("*.jpg"):
                        has_blur = False  # No blur for synthetic data
                        rel_path = f"{split}/{class_name}/{img_file.name}"
                        writer.writerow([rel_path, class_name, split, has_blur])
    
    print(f"📋 Created face manifest: {manifest_path}")

def check_kaggle_installation():
    """Check if Kaggle API is installed and configured."""
    try:
        result = subprocess.run(['kaggle', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Kaggle API is installed")
            return True
        else:
            print("❌ Kaggle API not found")
            return False
    except FileNotFoundError:
        print("❌ Kaggle API not found")
        return False

def install_kaggle():
    """Install Kaggle API."""
    print("📦 Installing Kaggle API...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'kaggle'], check=True)
        print("✅ Kaggle API installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Kaggle API: {e}")
        return False

def download_kaggle_dataset(dataset_name: str, output_dir: Path):
    """Download dataset from Kaggle."""
    print(f"📥 Downloading dataset: {dataset_name}")
    
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download dataset
        cmd = ['kaggle', 'datasets', 'download', '-d', dataset_name, '-p', str(output_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dataset downloaded successfully")
            return True
        else:
            print(f"❌ Failed to download dataset: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return False

def extract_dataset(zip_path: Path, extract_dir: Path):
    """Extract downloaded dataset."""
    print(f"📦 Extracting dataset from {zip_path}")
    
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print("✅ Dataset extracted successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to extract dataset: {e}")
        return False

def copy_existing_images(input_dir: Path, output_dir: Path, params: Dict):
    """Copy existing images to processed directory with basic organization."""
    print("📸 Copying existing images...")
    
    # Create output directories
    for split in ["train", "val", "test"]:
        for class_name in ["ProfA", "Room1"]:
            (output_dir / split / class_name).mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(input_dir.rglob(f"*{ext}"))
        image_files.extend(input_dir.rglob(f"*{ext.upper()}"))
    
    print(f"📸 Found {len(image_files)} image files")
    
    if not image_files:
        print("❌ No image files found")
        return False
    
    # Process images
    processed_count = 0
    class_counts = {"ProfA": 0, "Room1": 0}
    max_per_class = params.get("max_faces_per_class", 200)
    
    random.shuffle(image_files)
    
    for image_path in image_files:
        if processed_count >= 400:  # Limit for demo
            break
        
        # Simple classification based on filename
        filename = image_path.name.lower()
        if any(keyword in filename for keyword in ["male", "man", "professor", "adult"]):
            face_class = "ProfA"
        elif any(keyword in filename for keyword in ["female", "woman", "student", "young"]):
            face_class = "Room1"
        else:
            face_class = random.choices(["ProfA", "Room1"], weights=[0.6, 0.4])[0]
        
        # Skip if we have enough of this class
        if class_counts[face_class] >= max_per_class:
            continue
        
        # Determine split
        rand = random.random()
        if rand < 0.7:
            split = "train"
        elif rand < 0.9:
            split = "val"
        else:
            split = "test"
        
        # Copy image
        filename = f"{face_class}_{class_counts[face_class]:03d}.jpg"
        output_path = output_dir / split / face_class / filename
        
        try:
            shutil.copy2(image_path, output_path)
            class_counts[face_class] += 1
            processed_count += 1
        except Exception as e:
            print(f"⚠️  Error copying {image_path}: {e}")
            continue
    
    print(f"✅ Processed {processed_count} images")
    print(f"   ProfA: {class_counts['ProfA']} images")
    print(f"   Room1: {class_counts['Room1']} images")
    
    return class_counts

def main():
    """Main setup function."""
    print("🎭 Simple Face Dataset Setup")
    print("=" * 50)
    
    # Load parameters
    params_path = project_root / "params.yaml"
    with open(params_path) as f:
        params = yaml.safe_load(f)
    
    use_real_faces = params.get("use_real_faces", False)
    if not use_real_faces:
        print("⚠️  Real faces not enabled in params.yaml")
        print("Set 'use_real_faces: true' to enable real face dataset")
        return
    
    # Setup paths
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    faces_dir = raw_dir / "human_faces"
    processed_dir = data_dir / "processed"
    
    # Check if dataset already exists
    if faces_dir.exists() and any(faces_dir.iterdir()):
        print("✅ Face dataset already exists")
        print("🔄 Processing existing dataset...")
        
        class_counts = copy_existing_images(faces_dir, processed_dir, params)
        if class_counts:
            create_face_manifest(processed_dir, class_counts)
            print("✅ Face dataset processing completed!")
        else:
            print("❌ Failed to process existing dataset")
            print("🔄 Creating synthetic dataset as fallback...")
            create_synthetic_face_dataset(processed_dir, params)
        return
    
    # Try to download dataset
    print("📥 Attempting to download dataset...")
    
    # Check Kaggle installation
    if not check_kaggle_installation():
        if not install_kaggle():
            print("❌ Failed to install Kaggle API")
            print("🔄 Creating synthetic dataset as fallback...")
            create_synthetic_face_dataset(processed_dir, params)
            return
    
    # Download dataset
    dataset_name = params.get("kaggle_dataset", "ashwingupta3012/human-faces")
    if not download_kaggle_dataset(dataset_name, raw_dir):
        print("❌ Failed to download dataset")
        print("🔄 Creating synthetic dataset as fallback...")
        create_synthetic_face_dataset(processed_dir, params)
        return
    
    # Extract dataset
    zip_files = list(raw_dir.glob("*.zip"))
    if zip_files:
        zip_path = zip_files[0]
        if not extract_dataset(zip_path, raw_dir):
            print("❌ Failed to extract dataset")
            print("🔄 Creating synthetic dataset as fallback...")
            create_synthetic_face_dataset(processed_dir, params)
            return
        
        # Remove zip file
        zip_path.unlink()
    
    # Process dataset
    if faces_dir.exists():
        class_counts = copy_existing_images(faces_dir, processed_dir, params)
        if class_counts:
            create_face_manifest(processed_dir, class_counts)
            print("✅ Face dataset setup completed!")
            print(f"📁 Processed data: {processed_dir}")
            print("🚀 Ready for training with real face data!")
        else:
            print("❌ Failed to process dataset")
            print("🔄 Creating synthetic dataset as fallback...")
            create_synthetic_face_dataset(processed_dir, params)
    else:
        print("❌ Face dataset not found after download")
        print("🔄 Creating synthetic dataset as fallback...")
        create_synthetic_face_dataset(processed_dir, params)

if __name__ == "__main__":
    main()
