import os, json, random, csv
from pathlib import Path
import numpy as np
import cv2
import yaml

DATA = Path("/app/data")
INTERIM = DATA/"interim"
PROCESSED = DATA/"processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

with open("/app/params.yaml") as f:
    params = yaml.safe_load(f)

img_size = params["img_size"]
use_real_faces = params.get("use_real_faces", False)
blur_augmentation = params.get("blur_augmentation", False)
blur_strength = params.get("blur_strength", 0.3)

def create_blur_augmentation(image, blur_levels):
    """Create blur augmentations to simulate distance effects."""
    augmented_images = []
    
    for blur_level in blur_levels:
        if blur_level == 0:
            augmented_images.append(image)
        else:
            kernel_size = int(blur_level * 3) * 2 + 1
            blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), blur_level)
            augmented_images.append(blurred)
    
    return augmented_images

def process_real_faces():
    """Process real face dataset with blur augmentation."""
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
        relpath = row["relpath"]
        label = row["label"]
        
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

def create_synthetic_dataset():
    """Create synthetic dataset as fallback."""
    print("[preprocess] Creating synthetic dataset...")
    
    splits = ["train","val","test"]
    counts = {"train":30,"val":10,"test":6}
    classes = params["classes"]

    for split in splits:
        outdir = PROCESSED/split
        outdir.mkdir(parents=True, exist_ok=True)
        for cls in classes:
            (outdir/cls).mkdir(parents=True, exist_ok=True)
        for i in range(counts[split]):
            for cls in classes:
                img = np.zeros((img_size, img_size, 3), np.uint8)
                # draw class-specific primitive for separability
                if cls == "ProfA":
                    cv2.circle(img,(img_size//2,img_size//2),img_size//4,(255,255,255),-1)
                else:
                    cv2.rectangle(img,(img_size//4,img_size//4),(3*img_size//4,3*img_size//4),(255,255,255),-1)
                path = outdir/cls/f"{cls}_{i:03d}.jpg"
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
