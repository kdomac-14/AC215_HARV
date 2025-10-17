#!/usr/bin/env python3
"""
Quick script to download real face data from Kaggle.
This script provides multiple options for getting real face data.
"""

import os
import sys
import subprocess
from pathlib import Path
import requests
import zipfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_kaggle_api():
    """Check if Kaggle API is available."""
    try:
        result = subprocess.run(['kaggle', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_kaggle():
    """Install Kaggle API."""
    print("📦 Installing Kaggle API...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'kaggle'], check=True)
        print("✅ Kaggle API installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Kaggle API: {e}")
        return False

def download_with_kaggle_api():
    """Download dataset using Kaggle API."""
    print("📥 Downloading with Kaggle API...")
    
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = ['kaggle', 'datasets', 'download', '-d', 'ashwingupta3012/human-faces', '-p', str(raw_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dataset downloaded successfully")
            return True
        else:
            print(f"❌ Download failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def extract_dataset():
    """Extract downloaded dataset."""
    print("📦 Extracting dataset...")
    
    raw_dir = project_root / "data" / "raw"
    zip_files = list(raw_dir.glob("*.zip"))
    
    if not zip_files:
        print("❌ No zip files found")
        return False
    
    zip_path = zip_files[0]
    faces_dir = raw_dir / "human_faces"
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(faces_dir)
        print("✅ Dataset extracted successfully")
        
        # Remove zip file
        zip_path.unlink()
        return True
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def create_sample_dataset():
    """Create a small sample dataset for testing."""
    print("🎭 Creating sample dataset...")
    
    raw_dir = project_root / "data" / "raw"
    faces_dir = raw_dir / "human_faces"
    faces_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple sample structure
    sample_dir = faces_dir / "images"
    sample_dir.mkdir(exist_ok=True)
    
    # Create some placeholder files
    for i in range(10):
        sample_file = sample_dir / f"face_{i:03d}.jpg"
        sample_file.touch()
    
    print("✅ Sample dataset created")
    print("⚠️  Note: This is a placeholder dataset")
    print("   For real faces, download from Kaggle manually")
    return True

def manual_download_instructions():
    """Provide manual download instructions."""
    print("📋 Manual Download Instructions:")
    print("=" * 40)
    print("1. Go to: https://www.kaggle.com/datasets/ashwingupta3012/human-faces")
    print("2. Click 'Download' button")
    print("3. Extract the downloaded zip file")
    print("4. Copy contents to: data/raw/human_faces/")
    print("5. Run: python scripts/simple_face_setup.py")

def main():
    """Main function."""
    print("🎭 Real Face Data Downloader")
    print("=" * 40)
    
    # Check current status
    raw_dir = project_root / "data" / "raw"
    faces_dir = raw_dir / "human_faces"
    
    if faces_dir.exists() and any(faces_dir.iterdir()):
        print("✅ Face dataset already exists")
        print(f"📁 Location: {faces_dir}")
        return
    
    print("❌ No face dataset found")
    print("\n🔧 Attempting to download...")
    
    # Try Kaggle API
    if check_kaggle_api():
        print("✅ Kaggle API found")
        if download_with_kaggle_api():
            if extract_dataset():
                print("✅ Real face dataset downloaded and extracted!")
                return
    else:
        print("⚠️  Kaggle API not found")
        if input("Install Kaggle API? (y/n): ").lower() == 'y':
            if install_kaggle():
                if download_with_kaggle_api():
                    if extract_dataset():
                        print("✅ Real face dataset downloaded and extracted!")
                        return
    
    # Fallback options
    print("\n🔄 Kaggle API not available, trying alternatives...")
    
    print("\nOption 1: Manual Download")
    manual_download_instructions()
    
    print("\nOption 2: Create Sample Dataset")
    if input("Create sample dataset for testing? (y/n): ").lower() == 'y':
        create_sample_dataset()
        print("✅ Sample dataset created")
        print("⚠️  This is for testing only - not real faces")
    
    print("\nOption 3: Use Docker")
    print("Run: docker compose run --rm ingestion python scripts/simple_face_setup.py")

if __name__ == "__main__":
    main()
