#!/usr/bin/env python3
"""
Setup script for real face dataset integration.
This script handles downloading, processing, and organizing the Kaggle human faces dataset.
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Try to import OpenCV, fall back to basic image processing if not available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    print("⚠️  OpenCV not available, using basic image processing")
    OPENCV_AVAILABLE = False
    try:
        from PIL import Image
        import numpy as np
        PIL_AVAILABLE = True
    except ImportError:
        print("⚠️  PIL not available, limited image processing")
        PIL_AVAILABLE = False

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

def detect_faces_in_image(image_path: Path) -> List[np.ndarray]:
    """Detect faces in an image using OpenCV or fallback to basic processing."""
    if not OPENCV_AVAILABLE:
        # Fallback: assume the entire image is a face
        print(f"⚠️  OpenCV not available, treating entire image as face: {image_path}")
        if PIL_AVAILABLE:
            try:
                from PIL import Image
                img = Image.open(image_path)
                img_array = np.array(img)
                return [img_array]
            except Exception as e:
                print(f"❌ Error loading image {image_path}: {e}")
                return []
        else:
            print(f"❌ Cannot process image {image_path} without OpenCV or PIL")
            return []
    
    # OpenCV face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    image = cv2.imread(str(image_path))
    if image is None:
        return []
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    detected_faces = []
    for (x, y, w, h) in faces:
        face = image[y:y+h, x:x+w]
        detected_faces.append(face)
    
    return detected_faces

def classify_face_simple(image_path: Path, filename: str) -> str:
    """Simple face classification based on filename heuristics."""
    filename_lower = filename.lower()
    
    # Simple heuristics for classification
    if any(keyword in filename_lower for keyword in ["male", "man", "professor", "adult", "mature"]):
        return "ProfA"
    elif any(keyword in filename_lower for keyword in ["female", "woman", "student", "young", "girl"]):
        return "Room1"
    else:
        # Random assignment with slight bias
        return random.choices(["ProfA", "Room1"], weights=[0.6, 0.4])[0]

def create_blur_augmentations(face_image: np.ndarray, blur_levels: List[float]) -> List[np.ndarray]:
    """Create blur augmentations to simulate distance effects."""
    augmented_faces = []
    
    for blur_level in blur_levels:
        if blur_level == 0:
            augmented_faces.append(face_image)
        else:
            if OPENCV_AVAILABLE:
                kernel_size = int(blur_level * 3) * 2 + 1
                blurred = cv2.GaussianBlur(face_image, (kernel_size, kernel_size), blur_level)
                augmented_faces.append(blurred)
            else:
                # Fallback: simple downsampling and upsampling for blur effect
                if PIL_AVAILABLE:
                    from PIL import Image
                    try:
                        # Convert to PIL, resize down and up for blur effect
                        img = Image.fromarray(face_image)
                        scale_factor = max(0.1, 1.0 - blur_level * 0.3)
                        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                        if new_size[0] > 0 and new_size[1] > 0:
                            img_small = img.resize(new_size, Image.LANCZOS)
                            img_blurred = img_small.resize((img.width, img.height), Image.LANCZOS)
                            blurred_array = np.array(img_blurred)
                            augmented_faces.append(blurred_array)
                        else:
                            augmented_faces.append(face_image)
                    except Exception as e:
                        print(f"⚠️  Error creating blur augmentation: {e}")
                        augmented_faces.append(face_image)
                else:
                    # No blur augmentation possible
                    augmented_faces.append(face_image)
    
    return augmented_faces

def process_face_dataset(input_dir: Path, output_dir: Path, params: Dict):
    """Process the downloaded face dataset."""
    print("🔄 Processing face dataset...")
    
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
    
    # Process images
    processed_count = 0
    class_counts = {"ProfA": 0, "Room1": 0}
    max_per_class = params.get("max_faces_per_class", 200)
    min_per_class = params.get("min_faces_per_class", 50)
    
    random.shuffle(image_files)
    
    for image_path in image_files:
        if processed_count >= 400:  # Limit for demo
            break
        
        # Detect faces in image
        faces = detect_faces_in_image(image_path)
        
        for i, face in enumerate(faces):
            if processed_count >= 400:
                break
            
            # Resize face to standard size
            face_resized = cv2.resize(face, (224, 224))
            
            # Classify face
            face_class = classify_face_simple(image_path, image_path.name)
            
            # Skip if we have enough of this class
            if class_counts[face_class] >= max_per_class:
                continue
            
            # Create blur augmentations
            blur_levels = [0.0, 0.5, 1.0, 1.5] if random.random() < 0.3 else [0.0]
            augmented_faces = create_blur_augmentations(face_resized, blur_levels)
            
            # Save original and augmented versions
            for j, aug_face in enumerate(augmented_faces):
                if class_counts[face_class] >= max_per_class:
                    break
                
                # Determine split
                rand = random.random()
                if rand < 0.7:
                    split = "train"
                elif rand < 0.9:
                    split = "val"
                else:
                    split = "test"
                
                # Save image
                filename = f"{face_class}_{class_counts[face_class]:03d}_{i}_{j}.jpg"
                output_path = output_dir / split / face_class / filename
                
                if OPENCV_AVAILABLE:
                    cv2.imwrite(str(output_path), aug_face)
                elif PIL_AVAILABLE:
                    try:
                        from PIL import Image
                        img = Image.fromarray(aug_face)
                        img.save(str(output_path), 'JPEG')
                    except Exception as e:
                        print(f"⚠️  Error saving image {output_path}: {e}")
                        continue
                else:
                    print(f"⚠️  Cannot save image {output_path} without OpenCV or PIL")
                    continue
                
                class_counts[face_class] += 1
                processed_count += 1
    
    print(f"✅ Processed {processed_count} face images")
    print(f"   ProfA: {class_counts['ProfA']} images")
    print(f"   Room1: {class_counts['Room1']} images")
    
    return class_counts

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
                        has_blur = "_1_" in img_file.name or "_2_" in img_file.name or "_3_" in img_file.name
                        rel_path = f"{split}/{class_name}/{img_file.name}"
                        writer.writerow([rel_path, class_name, split, has_blur])
    
    print(f"📋 Created face manifest: {manifest_path}")

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

def main():
    """Main setup function."""
    print("🎭 Real Face Dataset Setup")
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
        
        class_counts = process_face_dataset(faces_dir, processed_dir, params)
        create_face_manifest(processed_dir, class_counts)
        
        print("✅ Face dataset processing completed!")
        return
    
    # Try to download dataset
    print("📥 Attempting to download dataset...")
    
    # Check Kaggle installation
    if not check_kaggle_installation():
        if not install_kaggle():
            print("❌ Failed to install Kaggle API")
            setup_manual_download()
            return
    
    # Download dataset
    dataset_name = params.get("kaggle_dataset", "ashwingupta3012/human-faces")
    if not download_kaggle_dataset(dataset_name, raw_dir):
        print("❌ Failed to download dataset")
        setup_manual_download()
        return
    
    # Extract dataset
    zip_files = list(raw_dir.glob("*.zip"))
    if zip_files:
        zip_path = zip_files[0]
        if not extract_dataset(zip_path, raw_dir):
            print("❌ Failed to extract dataset")
            return
        
        # Remove zip file
        zip_path.unlink()
    
    # Process dataset
    if faces_dir.exists():
        class_counts = process_face_dataset(faces_dir, processed_dir, params)
        create_face_manifest(processed_dir, class_counts)
        
        print("✅ Face dataset setup completed!")
        print(f"📁 Processed data: {processed_dir}")
        print("🚀 Ready for training with real face data!")
    else:
        print("❌ Face dataset not found after download")
        setup_manual_download()

if __name__ == "__main__":
    main()
