#!/usr/bin/env python3
"""
Dataset diagnostic script to check if real photos are in the dataset.
This script analyzes the current dataset and provides recommendations.
"""

import os
import sys
from pathlib import Path
import json
import yaml
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_raw_data():
    """Check if raw face dataset exists."""
    print("🔍 Checking raw data directory...")
    
    raw_dir = project_root / "data" / "raw"
    faces_dir = raw_dir / "human_faces"
    
    if not raw_dir.exists():
        print("❌ data/raw directory doesn't exist")
        return False
    
    if not faces_dir.exists():
        print("❌ data/raw/human_faces directory doesn't exist")
        return False
    
    # Check for image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(faces_dir.rglob(f"*{ext}"))
        image_files.extend(faces_dir.rglob(f"*{ext.upper()}"))
    
    if not image_files:
        print("❌ No image files found in data/raw/human_faces/")
        return False
    
    print(f"✅ Found {len(image_files)} image files in raw data")
    return True

def check_processed_data():
    """Check the processed dataset."""
    print("🔍 Checking processed data directory...")
    
    processed_dir = project_root / "data" / "processed"
    
    if not processed_dir.exists():
        print("❌ data/processed directory doesn't exist")
        return False
    
    # Check each split
    splits = ["train", "val", "test"]
    total_images = 0
    
    for split in splits:
        split_dir = processed_dir / split
        if not split_dir.exists():
            print(f"❌ {split} directory doesn't exist")
            continue
        
        for class_name in ["ProfA", "Room1"]:
            class_dir = split_dir / class_name
            if class_dir.exists():
                images = list(class_dir.glob("*.jpg"))
                total_images += len(images)
                print(f"   {split}/{class_name}: {len(images)} images")
            else:
                print(f"   {split}/{class_name}: No directory")
    
    print(f"✅ Total processed images: {total_images}")
    return total_images > 0

def analyze_image_content(image_path: Path) -> Dict:
    """Analyze an image to determine if it's real or synthetic."""
    try:
        # Try to read the image
        from PIL import Image
        img = Image.open(image_path)
        
        # Basic analysis
        width, height = img.size
        mode = img.mode
        
        # Check if it's likely synthetic (very uniform colors)
        if mode == 'RGB':
            # Convert to numpy for analysis
            import numpy as np
            img_array = np.array(img)
            
            # Calculate color variance
            color_variance = np.var(img_array)
            
            # Check for geometric patterns (synthetic images tend to have very low variance)
            is_synthetic = color_variance < 1000  # Threshold for synthetic images
            
            return {
                "size": (width, height),
                "mode": mode,
                "color_variance": color_variance,
                "is_synthetic": is_synthetic,
                "file_size": image_path.stat().st_size
            }
        else:
            return {
                "size": (width, height),
                "mode": mode,
                "is_synthetic": True,  # Assume synthetic if not RGB
                "file_size": image_path.stat().st_size
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "is_synthetic": True
        }

def sample_analysis():
    """Analyze a sample of images to determine if they're real or synthetic."""
    print("🔍 Analyzing sample images...")
    
    processed_dir = project_root / "data" / "processed"
    
    # Sample a few images from each class
    samples = []
    for split in ["train", "val", "test"]:
        for class_name in ["ProfA", "Room1"]:
            class_dir = processed_dir / split / class_name
            if class_dir.exists():
                images = list(class_dir.glob("*.jpg"))
                if images:
                    # Take first image as sample
                    samples.append(images[0])
                    break
    
    if not samples:
        print("❌ No images found for analysis")
        return
    
    print(f"📸 Analyzing {len(samples)} sample images...")
    
    synthetic_count = 0
    real_count = 0
    
    for img_path in samples:
        analysis = analyze_image_content(img_path)
        print(f"   {img_path.name}: {analysis}")
        
        if analysis.get("is_synthetic", True):
            synthetic_count += 1
        else:
            real_count += 1
    
    print(f"📊 Analysis Results:")
    print(f"   Synthetic images: {synthetic_count}")
    print(f"   Real images: {real_count}")
    
    if synthetic_count > real_count:
        print("⚠️  Dataset appears to contain mostly synthetic images")
        return False
    else:
        print("✅ Dataset appears to contain real images")
        return True

def check_manifest():
    """Check the dataset manifest."""
    print("🔍 Checking dataset manifest...")
    
    manifest_path = project_root / "data" / "interim" / "manifest.csv"
    face_manifest_path = project_root / "data" / "interim" / "face_manifest.csv"
    
    if face_manifest_path.exists():
        print("✅ Face manifest found")
        try:
            import csv
            with open(face_manifest_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            print(f"   Face manifest entries: {len(rows)}")
            return True
        except Exception as e:
            print(f"❌ Error reading face manifest: {e}")
            return False
    elif manifest_path.exists():
        print("⚠️  Only basic manifest found (no face manifest)")
        return False
    else:
        print("❌ No manifest found")
        return False

def check_params():
    """Check if real faces are enabled in params.yaml."""
    print("🔍 Checking params.yaml configuration...")
    
    params_path = project_root / "params.yaml"
    if not params_path.exists():
        print("❌ params.yaml not found")
        return False
    
    try:
        with open(params_path) as f:
            params = yaml.safe_load(f)
        
        use_real_faces = params.get("use_real_faces", False)
        print(f"   use_real_faces: {use_real_faces}")
        
        if not use_real_faces:
            print("⚠️  Real faces not enabled in params.yaml")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error reading params.yaml: {e}")
        return False

def provide_recommendations():
    """Provide recommendations for getting real face data."""
    print("\n💡 Recommendations:")
    print("=" * 50)
    
    print("1. **Enable Real Faces in params.yaml:**")
    print("   Set 'use_real_faces: true' in params.yaml")
    
    print("\n2. **Download Real Face Dataset:**")
    print("   Option A - Automatic (requires Kaggle API):")
    print("   - Install: pip install kaggle")
    print("   - Run: make setup-faces")
    
    print("\n   Option B - Manual Download:")
    print("   - Go to: https://www.kaggle.com/datasets/ashwingupta3012/human-faces")
    print("   - Download and extract to: data/raw/human_faces/")
    print("   - Run: python scripts/simple_face_setup.py")
    
    print("\n3. **Verify Dataset:**")
    print("   - Check data/raw/human_faces/ contains image files")
    print("   - Run this script again to verify")
    
    print("\n4. **Alternative - Use Docker:**")
    print("   - docker compose run --rm ingestion python scripts/simple_face_setup.py")

def main():
    """Main diagnostic function."""
    print("🔍 Dataset Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Raw Data", check_raw_data),
        ("Processed Data", check_processed_data),
        ("Sample Analysis", sample_analysis),
        ("Manifest", check_manifest),
        ("Params", check_params)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 30)
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    # Determine overall status
    if not results.get("Raw Data", False):
        print("\n⚠️  ISSUE: No raw face dataset found")
        print("   The current images are synthetic (geometric shapes)")
        print("   You need to download real face data")
        provide_recommendations()
    elif not results.get("Sample Analysis", False):
        print("\n⚠️  ISSUE: Dataset contains synthetic images")
        print("   Real face data may not have been processed correctly")
        provide_recommendations()
    else:
        print("\n✅ Dataset looks good!")
        print("   Real face data appears to be present and processed")

if __name__ == "__main__":
    main()
