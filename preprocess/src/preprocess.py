import os, json, random
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

# synthesize tiny dataset (two classes) so pipeline always runs
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

print("[preprocess] Synthetic dataset created at", PROCESSED)
