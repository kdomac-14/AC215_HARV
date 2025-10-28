"""
Ingestion Component for HARV Pipeline.

This module creates a manifest CSV file that indexes available training data.
Supports both real face datasets and synthetic data generation.

The manifest serves as the input to the preprocessing component, providing
relative paths to images and their corresponding labels.

Features:
- Real face dataset indexing from pre-split directories
- Synthetic dataset placeholder generation for testing
- CSV manifest format: relpath, label

Author: HARV Team
License: MIT
"""

import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

# Directory paths
RAW: Path = Path("/app/data/raw")
INTERIM: Path = Path("/app/data/interim")
INTERIM.mkdir(parents=True, exist_ok=True)

# Load parameters
try:
    with open("/app/params.yaml") as f:
        params: Dict[str, Any] = yaml.safe_load(f) or {}
    use_real_faces: bool = params.get("use_real_faces", False)
except FileNotFoundError:
    print("[ingestion] params.yaml not found, using default settings")
    params = {}
    use_real_faces = False


def create_manifest_from_real_faces(face_manifest_path: Path, output_manifest_path: Path) -> bool:
    """
    Copy existing face manifest to main manifest.
    
    Args:
        face_manifest_path: Path to pre-existing face dataset manifest.
        output_manifest_path: Path where main manifest should be written.
    
    Returns:
        True if manifest was successfully copied, False otherwise.
    
    Side Effects:
        Writes to output_manifest_path if source exists.
    """
    if face_manifest_path.exists():
        print("[ingestion] Found existing face manifest")
        with open(face_manifest_path, 'r') as src, open(output_manifest_path, 'w') as dst:
            dst.write(src.read())
        print("[ingestion] Copied face manifest to main manifest")
        return True
    return False


def create_placeholder_manifest(output_manifest_path: Path, classes: Optional[list] = None) -> None:
    """
    Create placeholder manifest for synthetic dataset or testing.
    
    Generates a minimal 2-row manifest with placeholder entries. Used when
    real face data is unavailable or for quick testing.
    
    Args:
        output_manifest_path: Path where manifest CSV should be written.
        classes: Optional list of class names. Defaults to ["ProfA", "Room1"].
    
    Side Effects:
        Writes CSV file with header (relpath, label) and placeholder rows.
    
    Example Output:
        relpath,label
        placeholder_1.jpg,ProfA
        placeholder_2.jpg,Room1
    """
    if classes is None:
        classes = ["ProfA", "Room1"]
    
    with output_manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["relpath", "label"])
        writer.writeheader()
        writer.writerow({"relpath": "placeholder_1.jpg", "label": classes[0]})
        writer.writerow({"relpath": "placeholder_2.jpg", "label": classes[1]})

# Main ingestion logic
manifest: Path = INTERIM / "manifest.csv"

if use_real_faces:
    print("[ingestion] Using real face dataset")
    face_manifest = INTERIM / "face_manifest.csv"
    
    if not create_manifest_from_real_faces(face_manifest, manifest):
        print("[ingestion] No face manifest found, creating placeholder")
        create_placeholder_manifest(manifest)
else:
    print("[ingestion] Using synthetic dataset")
    create_placeholder_manifest(manifest)

print("[ingestion] Wrote manifest:", manifest)
