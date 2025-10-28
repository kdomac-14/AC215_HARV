#!/usr/bin/env python3
"""
Generate tiny synthetic images for testing the HARV pipeline.

Creates colored squares to simulate a minimal dataset without requiring real photos.
Useful for quick smoke tests and documentation examples.

Usage:
    python scripts/make_tiny_images.py
    python scripts/make_tiny_images.py --output data/sample_input/imgs --count 5
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def generate_image(label: str, index: int, size: int = 224) -> np.ndarray:
    """
    Generate a synthetic colored image for a given label.
    
    Args:
        label: Class label (ProfA, Room1, etc.)
        index: Image index for variation
        size: Image size in pixels (square)
    
    Returns:
        RGB image array
    """
    # Color mapping for different labels
    colors = {
        "ProfA": (50, 100, 200),   # Blue-ish
        "Room1": (200, 100, 50),    # Orange-ish
        "ProfB": (50, 200, 100),    # Green-ish
        "Room2": (200, 50, 100),    # Purple-ish
    }
    
    # Get base color or use random
    base_color = colors.get(label, (128, 128, 128))
    
    # Add variation based on index
    variation = (index * 20) % 100 - 50
    color = tuple(max(0, min(255, c + variation)) for c in base_color)
    
    # Create image
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Fill with color
    img[:, :] = color
    
    # Add simple pattern based on label
    if label == "ProfA":
        # Circle
        center = (size // 2, size // 2)
        radius = size // 3
        cv2.circle(img, center, radius, (255, 255, 255), -1)
    elif label == "Room1":
        # Rectangle
        pt1 = (size // 4, size // 4)
        pt2 = (3 * size // 4, 3 * size // 4)
        cv2.rectangle(img, pt1, pt2, (255, 255, 255), -1)
    
    # Add some noise for realism
    noise = np.random.randint(-10, 10, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return img


def main():
    """Generate tiny test images."""
    parser = argparse.ArgumentParser(description="Generate synthetic test images")
    parser.add_argument(
        "--output",
        type=str,
        default="data/sample_input/imgs",
        help="Output directory for images",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of images per class",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=224,
        help="Image size in pixels",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=["ProfA", "Room1"],
        help="Class labels to generate",
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.count} images per class...")
    print(f"Output directory: {output_dir}")
    print(f"Labels: {args.labels}")
    print()
    
    manifest_rows = ["relpath,label"]
    
    for label in args.labels:
        label_dir = output_dir / label
        label_dir.mkdir(exist_ok=True)
        
        for i in range(args.count):
            img = generate_image(label, i, args.size)
            filename = f"sample_{i:03d}.jpg"
            filepath = label_dir / filename
            
            cv2.imwrite(str(filepath), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            
            # Add to manifest
            relpath = f"{label}/{filename}"
            manifest_rows.append(f"{relpath},{label}")
            
            print(f"  Created: {filepath}")
    
    # Write manifest
    manifest_path = output_dir.parent / "manifest.csv"
    with open(manifest_path, "w") as f:
        f.write("\n".join(manifest_rows) + "\n")
    
    print()
    print(f"✓ Generated {args.count * len(args.labels)} images")
    print(f"✓ Manifest saved: {manifest_path}")
    print()
    print("To use these images:")
    print("  1. Set use_real_faces: true in params.yaml")
    print("  2. Run: make run")


if __name__ == "__main__":
    main()
