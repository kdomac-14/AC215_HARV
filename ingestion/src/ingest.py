import os, csv, pathlib
from pathlib import Path

RAW = Path("/app/data/raw")
INTERIM = Path("/app/data/interim")
INTERIM.mkdir(parents=True, exist_ok=True)

# Minimal: ensure a manifest exists even without real images
manifest = INTERIM / "manifest.csv"
with manifest.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["relpath","label"])
    w.writeheader()
    # placeholder rows (preprocess will synthesize images anyway)
    w.writerow({"relpath":"placeholder_1.jpg","label":"ProfA"})
    w.writerow({"relpath":"placeholder_2.jpg","label":"Room1"})

print("[ingestion] Wrote manifest:", manifest)
