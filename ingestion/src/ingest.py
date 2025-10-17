import os, csv, pathlib, yaml
from pathlib import Path

RAW = Path("/app/data/raw")
INTERIM = Path("/app/data/interim")
INTERIM.mkdir(parents=True, exist_ok=True)

# Load parameters
try:
    with open("/app/params.yaml") as f:
        params = yaml.safe_load(f)
    use_real_faces = params.get("use_real_faces", False)
except FileNotFoundError:
    print("[ingestion] params.yaml not found, using default settings")
    params = {}
    use_real_faces = False

if use_real_faces:
    print("[ingestion] Using real face dataset")
    
    # Check if face dataset exists
    face_manifest = INTERIM / "face_manifest.csv"
    if face_manifest.exists():
        print("[ingestion] Found existing face manifest")
        # Copy face manifest to main manifest
        manifest = INTERIM / "manifest.csv"
        with open(face_manifest, 'r') as src, open(manifest, 'w') as dst:
            dst.write(src.read())
        print("[ingestion] Copied face manifest to main manifest")
    else:
        print("[ingestion] No face manifest found, creating placeholder")
        # Create placeholder manifest
        manifest = INTERIM / "manifest.csv"
        with manifest.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["relpath","label"])
            w.writeheader()
            w.writerow({"relpath":"placeholder_1.jpg","label":"ProfA"})
            w.writerow({"relpath":"placeholder_2.jpg","label":"Room1"})
else:
    print("[ingestion] Using synthetic dataset")
    # Minimal: ensure a manifest exists even without real images
    manifest = INTERIM / "manifest.csv"
    with manifest.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["relpath","label"])
        w.writeheader()
        # placeholder rows (preprocess will synthesize images anyway)
        w.writerow({"relpath":"placeholder_1.jpg","label":"ProfA"})
        w.writerow({"relpath":"placeholder_2.jpg","label":"Room1"})

print("[ingestion] Wrote manifest:", manifest)
