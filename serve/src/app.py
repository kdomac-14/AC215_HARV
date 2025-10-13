import os, base64, json, time, yaml
from pathlib import Path
import numpy as np
import cv2, torch
from fastapi import FastAPI, Request
from pydantic import BaseModel
from .geo import (
    save_calibration, load_calibration, haversine_m, get_client_ip, PROVIDER, log_attempt
)

# Load model metadata (if present) for /verify demo
META_PATH = Path("/app/artifacts/model/metadata.json")
if META_PATH.exists():
    META = json.loads(META_PATH.read_text())
    model = torch.jit.load("/app/artifacts/model/model.torchscript.pt", map_location="cpu")
    model.eval()
    IMG_SIZE = META["img_size"]
    CLASSES = META["classes"]
else:
    META, model, IMG_SIZE, CLASSES = {}, None, 224, ["ProfA","Room1"]

CHALLENGE_WORD = os.getenv("CHALLENGE_WORD","orchid")

app = FastAPI(title="HLAB API", version="0.2.0")

class VerifyIn(BaseModel):
    image_b64: str
    challenge_word: str | None = None

class CalibrateIn(BaseModel):
    lat: float
    lon: float
    epsilon_m: float | None = None

class GeoVerifyIn(BaseModel):
    # Optional: client can pass its own GPS if available (HTML5), else server uses IP.
    client_gps_lat: float | None = None
    client_gps_lon: float | None = None
    client_gps_accuracy_m: float | None = None

@app.get("/healthz")
def healthz():
    return {"ok": True, "model": META.get("model"), "geo_provider": type(PROVIDER).__name__}

@app.post("/geo/calibrate")
def geo_calibrate(inp: CalibrateIn):
    eps = float(inp.epsilon_m) if inp.epsilon_m is not None else load_calibration().get("epsilon_m", 60.0)
    cfg = save_calibration(inp.lat, inp.lon, eps)
    return {"ok": True, "calibration": cfg}

@app.get("/geo/status")
def geo_status():
    cfg = load_calibration()
    return {"ok": True, "calibration": cfg}

@app.post("/geo/verify")
async def geo_verify(req: Request, inp: GeoVerifyIn):
    cfg = load_calibration()
    if cfg["lat"] is None or cfg["lon"] is None:
        return {"ok": False, "reason": "not_calibrated"}

    client = req.client.host if req.client else ""
    ip = get_client_ip(req.headers, client)

    # Prefer client-provided GPS if present; else use IP geolocation provider.
    if inp.client_gps_lat is not None and inp.client_gps_lon is not None:
        lat, lon, acc = float(inp.client_gps_lat), float(inp.client_gps_lon), float(inp.client_gps_accuracy_m or 50.0)
        source = "client_gps"
    else:
        loc = PROVIDER.locate(ip)
        if not loc:
            log_attempt({"ok": False, "ip": ip, "reason":"geo_lookup_failed"})
            return {"ok": False, "reason": "geo_lookup_failed"}
        lat, lon, acc = loc
        source = "ip_geo"

    dist_m = haversine_m(cfg["lat"], cfg["lon"], lat, lon)
    ok = dist_m <= float(cfg["epsilon_m"])
    rec = {"ok": ok, "ip": ip, "source": source, "lat": lat, "lon": lon, "acc_m": acc, "dist_m": dist_m, "eps_m": cfg["epsilon_m"]}
    log_attempt(rec)

    return {
        "ok": ok,
        "source": source,
        "client_ip": ip,
        "distance_m": round(dist_m, 3),
        "epsilon_m": float(cfg["epsilon_m"]),
        "estimated_lat": lat,
        "estimated_lon": lon,
        "estimated_accuracy_m": acc
    }

def preprocess(img):
    img = cv2.resize(img,(IMG_SIZE,IMG_SIZE))
    t = torch.from_numpy(img.transpose(2,0,1)).float().unsqueeze(0)/255.0
    return t

@app.post("/verify")
def verify(inp: VerifyIn):
    # (unchanged MS2 demo classifier; photo step happens AFTER geo in the app flow)
    t0 = time.time()
    if (inp.challenge_word or "").strip().lower() != CHALLENGE_WORD.lower():
        return {"ok": False, "reason":"challenge_failed","latency_ms": int((time.time()-t0)*1000)}
    if model is None:
        return {"ok": False, "reason":"model_missing"}

    img_bytes = base64.b64decode(inp.image_b64)
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "reason":"bad_image"}

    x = preprocess(img)
    with torch.no_grad():
        logits = model(x)
        pred = int(torch.argmax(logits, dim=1).item())
        conf = float(torch.softmax(logits, dim=1)[0, pred].item())

    result = {
        "ok": True,
        "label": CLASSES[pred],
        "confidence": round(conf, 4),
        "latency_ms": int((time.time()-t0)*1000)
    }
    Path("/app/artifacts/samples").mkdir(parents=True, exist_ok=True)
    with open("/app/artifacts/samples/sample_response.json","w") as f:
        json.dump(result, f, indent=2)
    return result
