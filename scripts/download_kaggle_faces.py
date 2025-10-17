#!/usr/bin/env python3
"""
Download and prepare Kaggle human faces dataset for face recognition training.
This script downloads the dataset and organizes it for our two-class face recognition task.
"""

import os
import json
import shutil
import random
from pathlib import Path
import requests
import zipfile
from typing import List, Dict
import cv2
import numpy as np

# Configuration
KAGGLE_DATASET = "ashwingupta3012/human-faces"
DATA_DIR = Path("/Users/vilassogaard-srikrishnan/AC215-HLAV/data")
RAW_DIR = DATA_DIR / "raw"
FACES_DIR = RAW_DIR / "human_faces"
PROCESSED_DIR = DATA_DIR / "processed"

# Class mapping for our two-class problem
CLASS_MAPPING = {
    "ProfA": ["male", "professional", "adult"],  # Professor-like faces
    "Room1": ["female", "student", "young"]      # Student-like faces
}

def download_kaggle_dataset():
    """Download the Kaggle dataset using kaggle API or manual download."""
    print("📥 Downloading Kaggle human faces dataset...")
    
    # Create directories
    FACES_DIR.mkdir(parents=True, exist_ok=True)
    
    # For now, we'll create a placeholder structure
    # In production, you would use: kaggle datasets download -d ashwingupta3012/human-faces
    print("⚠️  Manual download required:")
    print(f"1. Go to: https://www.kaggle.com/datasets/{KAGGLE_DATASET}")
    print("2. Download the dataset")
    print(f"3. Extract to: {FACES_DIR}")
    print("4. Run this script again")
    
    # Check if dataset exists
    if not any(FACES_DIR.iterdir()):
        print("❌ Dataset not found. Please download manually first.")
        return False
    
    return True

def detect_faces(image_path: Path) -> List[np.ndarray]:
    """Detect faces in an image using OpenCV Haar cascades."""
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

def classify_face(image_path: Path) -> str:
    """Classify a face image into ProfA or Room1 based on simple heuristics."""
    # This is a simplified classification - in practice, you'd use more sophisticated methods
    # For now, we'll use random assignment with some bias
    filename = image_path.name.lower()
    
    # Simple heuristics (very basic)
    if any(keyword in filename for keyword in ["male", "man", "professor", "adult"]):
        return "ProfA"
    elif any(keyword in filename for keyword in ["female", "woman", "student", "young"]):
        return "Room1"
    else:
        # Random assignment with slight bias
        return random.choices(["ProfA", "Room1"], weights=[0.6, 0.4])[0]

def create_blur_augmentations(face_image: np.ndarray, blur_levels: List[float]) -> List[np.ndarray]:
    """Create blur augmentations to simulate distance/blur effects."""
    augmented_faces = [face_image]  # Original
    
    for blur_level in blur_levels:
        # Gaussian blur
        kernel_size = int(blur_level * 3) * 2 + 1  # Ensure odd number
        blurred = cv2.GaussianBlur(face_image, (kernel_size, kernel_size), blur_level)
        augmented_faces.append(blurred)
    
    return augmented_faces

def process_face_dataset():
    """Process the downloaded face dataset and organize into train/val/test splits."""
    print("🔄 Processing face dataset...")
    
    # Create output directories
    for split in ["train", "val", "test"]:
        for class_name in ["ProfA", "Room1"]:
            (PROCESSED_DIR / split / class_name).mkdir(parents=True, exist_ok=True)
    
    # Process images
    image_files = list(FACES_DIR.rglob("*.jpg")) + list(FACES_DIR.rglob("*.png"))
    random.shuffle(image_files)
    
    processed_count = 0
    class_counts = {"ProfA": 0, "Room1": 0}
    
    for image_path in image_files:
        if processed_count >= 400:  # Limit for demo
            break
            
        # Detect faces in image
        faces = detect_faces(image_path)
        
        for i, face in enumerate(faces):
            if processed_count >= 400:
                break
                
            # Resize face to standard size
            face_resized = cv2.resize(face, (224, 224))
            
            # Classify face
            face_class = classify_face(image_path)
            
            # Skip if we have enough of this class
            if class_counts[face_class] >= 200:
                continue
                
            # Create blur augmentations
            blur_levels = [0.5, 1.0, 1.5] if random.random() < 0.3 else [0.0]  # 30% chance of blur
            augmented_faces = create_blur_augmentations(face_resized, blur_levels)
            
            # Save original and augmented versions
            for j, aug_face in enumerate(augmented_faces):
                if class_counts[face_class] >= 200:
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
                output_path = PROCESSED_DIR / split / face_class / filename
                cv2.imwrite(str(output_path), aug_face)
                
                class_counts[face_class] += 1
                processed_count += 1
    
    print(f"✅ Processed {processed_count} face images")
    print(f"   ProfA: {class_counts['ProfA']} images")
    print(f"   Room1: {class_counts['Room1']} images")
    
    # Create manifest
    create_manifest()

def create_manifest():
    """Create a manifest file for the processed dataset."""
    manifest_path = DATA_DIR / "interim" / "face_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    import csv
    with open(manifest_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['relpath', 'label', 'split', 'has_blur'])
        
        for split in ["train", "val", "test"]:
            for class_name in ["ProfA", "Room1"]:
                class_dir = PROCESSED_DIR / split / class_name
                if class_dir.exists():
                    for img_file in class_dir.glob("*.jpg"):
                        has_blur = "_1_" in img_file.name or "_2_" in img_file.name
                        rel_path = f"{split}/{class_name}/{img_file.name}"
                        writer.writerow([rel_path, class_name, split, has_blur])
    
    print(f"📋 Created manifest: {manifest_path}")

def main():
    """Main function to download and process the face dataset."""
    print("🎭 Human Face Dataset Preparation")
    print("=" * 50)
    
    # Download dataset
    if not download_kaggle_dataset():
        return
    
    # Process dataset
    process_face_dataset()
    
    print("✅ Face dataset preparation complete!")
    print(f"📁 Processed data: {PROCESSED_DIR}")
    print("🚀 Ready for training with real face data!")

if __name__ == "__main__":
    main()
