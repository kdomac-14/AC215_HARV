"""
Preprocessing Component for HARV Pipeline.

This module handles face detection, image normalization, and blur augmentation
to prepare training data for the face recognition model.

Features:
- Real face dataset processing with train/val/test splits
- Synthetic dataset generation as fallback
- 5-level blur augmentation to simulate distance effects (σ=0.0-2.0)
- Standard 224×224 image normalization

Author: HARV Team
License: MIT
"""

import csv
import random
from pathlib import Path
from typing import Dict, List, Any

import cv2
import numpy as np
import yaml

# Directory paths
DATA = Path("/app/data")
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

# Load parameters
with open("/app/params.yaml") as f:
    params: Dict[str, Any] = yaml.safe_load(f)

img_size: int = params["img_size"]
use_real_faces: bool = params.get("use_real_faces", False)
blur_augmentation: bool = params.get("blur_augmentation", False)
blur_strength: float = params.get("blur_strength", 0.3)


def create_blur_augmentation(image: np.ndarray, blur_levels: List[float]) -> List[np.ndarray]:
    """
    Create blur augmentations to simulate distance effects.
    
    Applies Gaussian blur at multiple sigma levels to simulate faces at
    varying distances from camera (1m to 10m+).
    
    Args:
        image: Input image as numpy array (H, W, C).
        blur_levels: List of Gaussian blur sigma values (e.g., [0.0, 0.5, 1.0, 1.5, 2.0]).
    
    Returns:
        List of augmented images with varying blur levels.
    
    Example:
        >>> img = cv2.imread("face.jpg")
        >>> blurred = create_blur_augmentation(img, [0.0, 1.0, 2.0])
        >>> len(blurred)
        3
    """
    augmented_images: List[np.ndarray] = []
    
    for blur_level in blur_levels:
        if blur_level == 0:
            augmented_images.append(image)
        else:
            kernel_size = int(blur_level * 3) * 2 + 1
            blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), blur_level)
            augmented_images.append(blurred)
    
    return augmented_images


def process_real_faces() -> bool:
    """
    Process real face dataset with blur augmentation.
    
    Reads manifest CSV, loads images, applies normalization and optional
    blur augmentation, and saves to train/val/test splits.
    
    Returns:
        True if processing succeeded, False if manifest missing/empty.
    
    Side Effects:
        Writes processed images to PROCESSED directory organized by split and label.
    """
    print("[preprocess] Processing real face dataset...")
    
    # Read manifest
    manifest_path = INTERIM / "manifest.csv"
    if not manifest_path.exists():
        print("[preprocess] No manifest found, falling back to synthetic data")
        return False
    
    with open(manifest_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("[preprocess] Empty manifest, falling back to synthetic data")
        return False
    
    # Process each image
    processed_count = 0
    for row in rows:
        relpath: str = row["relpath"]
        label: str = row["label"]
        
        # Determine split from path
        if "train/" in relpath:
            split = "train"
        elif "val/" in relpath:
            split = "val"
        elif "test/" in relpath:
            split = "test"
        else:
            split = "train"  # default
        
        # Create output directory
        outdir = PROCESSED / split / label
        outdir.mkdir(parents=True, exist_ok=True)
        
        # Load and process image
        img_path = DATA / "processed" / relpath
        if img_path.exists():
            image = cv2.imread(str(img_path))
            if image is not None:
                # Resize to standard size
                image = cv2.resize(image, (img_size, img_size))
                
                # Create blur augmentations if enabled
                if blur_augmentation and random.random() < 0.3:  # 30% chance
                    blur_levels = [0.0, 0.5, 1.0, 1.5]
                    augmented_images = create_blur_augmentation(image, blur_levels)
                else:
                    augmented_images = [image]
                
                # Save images
                for i, aug_img in enumerate(augmented_images):
                    filename = f"{label}_{processed_count:03d}_{i}.jpg"
                    output_path = outdir / filename
                    cv2.imwrite(str(output_path), aug_img)
                
                processed_count += 1
    
    print(f"[preprocess] Processed {processed_count} real face images")
    return True


def create_synthetic_dataset() -> None:
    """
    Create synthetic dataset as fallback.
    
    Generates simple geometric shapes (circles and rectangles) for quick testing
    when real face data is unavailable. Used primarily for development and CI.
    
    Generates:
        - 30 train images per class
        - 10 val images per class
        - 6 test images per class
    
    Side Effects:
        Writes synthetic images to PROCESSED directory.
    """
    print("[preprocess] Creating synthetic dataset...")
    
    splits = ["train", "val", "test"]
    counts: Dict[str, int] = {"train": 30, "val": 10, "test": 6}
    classes: List[str] = params["classes"]

    for split in splits:
        outdir = PROCESSED / split
        outdir.mkdir(parents=True, exist_ok=True)
        for cls in classes:
            (outdir / cls).mkdir(parents=True, exist_ok=True)
        for i in range(counts[split]):
            for cls in classes:
                img = np.zeros((img_size, img_size, 3), np.uint8)
                # draw class-specific primitive for separability
                if cls == "ProfA":
                    cv2.circle(img, (img_size // 2, img_size // 2), img_size // 4, (255, 255, 255), -1)
                else:
                    cv2.rectangle(img, (img_size // 4, img_size // 4), (3 * img_size // 4, 3 * img_size // 4), (255, 255, 255), -1)
                path = outdir / cls / f"{cls}_{i:03d}.jpg"
                cv2.imwrite(str(path), img)

# Main processing logic
if use_real_faces:
    success = process_real_faces()
    if not success:
        print("[preprocess] Falling back to synthetic dataset")
        create_synthetic_dataset()
else:
    print("[preprocess] Using synthetic dataset")
    create_synthetic_dataset()

print("[preprocess] Dataset created at", PROCESSED)
