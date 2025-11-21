import os, base64, json, time, yaml
from pathlib import Path
import numpy as np
import cv2, torch
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from .geo import (
    save_calibration, load_calibration, haversine_m, get_client_ip, PROVIDER, log_attempt
)
from . import database as db
from .pretrained_classrooms import list_classrooms, get_classroom

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

app = FastAPI(title="HARV API", version="0.2.0")

# Optional CORS for development (disabled by default since we use NGINX proxy)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")
if FRONTEND_ORIGIN:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

class VerifyIn(BaseModel):
    image_b64: str

class CalibrateIn(BaseModel):
    lat: float
    lon: float
    epsilon_m: float | None = None

class GeoVerifyIn(BaseModel):
    # Optional: client can pass its own GPS if available (HTML5), else server uses IP.
    client_gps_lat: float | None = None
    client_gps_lon: float | None = None
    client_gps_accuracy_m: float | None = None

class ClassCreate(BaseModel):
    name: str
    code: str
    lat: float
    lon: float
    epsilon_m: float
    secret_word: str
    classroom_id: Optional[str] = None
    room_photos: List[str] = []  # base64 encoded images
    professor_id: str = "demo_prof"
    professor_name: str = "Demo Professor"

class EnrollmentCreate(BaseModel):
    class_code: str
    student_id: str


class UnenrollRequest(BaseModel):
    class_code: str
    student_id: str


class CheckInRequest(BaseModel):
    class_code: str
    student_id: str
    image_b64: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy_m: Optional[float] = None

class ManualOverrideRequest(BaseModel):
    class_code: str
    student_id: str
    secret_word: str

@app.get("/professor/classrooms")
def get_classroom_catalog():
    """Expose available pre-trained classroom templates to clients."""
    return {"classrooms": list_classrooms(include_photos=False)}

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
            provider_name = type(PROVIDER).__name__
            log_attempt({"ok": False, "ip": ip, "provider": provider_name, "reason":"geo_lookup_failed"})
            return {"ok": False, "reason": "geo_lookup_failed", "provider": provider_name, "ip": ip}
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
    # Lecture hall recognition endpoint; photo step happens AFTER geo in the app flow
    t0 = time.time()
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

# ============================================================================
# PROFESSOR ENDPOINTS
# ============================================================================

@app.post("/professor/classes")
def create_class(class_data: ClassCreate):
    """Professor creates a new class with location and room photos."""
    try:
        payload = class_data.dict()
        template_id = payload.get("classroom_id")
        if template_id:
            template = get_classroom(template_id)
            if not template:
                return {"ok": False, "reason": "classroom_not_found"}
            payload["room_photos"] = template.get("photos", [])
            payload["classroom_label"] = template.get("name")
        elif not payload.get("room_photos"):
            # Legacy path for manual upload is gone, but keep guard in case client is outdated.
            return {"ok": False, "reason": "room_photos_required"}

        new_class = db.create_class(payload)
        return {"ok": True, "class": new_class}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

@app.get("/professor/classes/{professor_id}")
def get_professor_classes(professor_id: str):
    """Get all classes for a professor."""
    classes = db.get_classes_by_professor(professor_id)
    return classes


@app.get("/professor/classes/{class_code}/students")
def get_class_students(class_code: str):
    """Return roster of students enrolled in a class with attendance stats."""
    class_obj = db.get_class_by_code(class_code)
    if not class_obj:
        # Instead of erroring out, return empty roster so the UI can still render.
        return []
    return db.get_students_by_class(class_code)


@app.get("/professor/attendance/{student_id}/{class_code}")
def get_student_attendance(student_id: str, class_code: str):
    """Return attendance history for a student inside a class."""
    class_obj = db.get_class_by_code(class_code)
    if not class_obj:
        raise HTTPException(status_code=404, detail="class_not_found")

    if not db.is_student_enrolled(class_code, student_id):
        return {"records": [], "summary": {"total": 0, "present": 0, "late": 0, "absent": 0, "rate": 0}}

    checkins = db.get_student_checkins(student_id, class_code)
    records = []
    for checkin in checkins:
        status = "present" if checkin.get("success") else "absent"
        if not checkin.get("success") and checkin.get("reason") == "recognition_failed":
            status = "late"

        records.append({
            "date": checkin.get("timestamp"),
            "status": status,
            "check_in_time": checkin.get("timestamp") if checkin.get("success") else None,
            "confidence": checkin.get("confidence"),
            "distance_m": checkin.get("distance_m"),
        })

    summary = {
        "total": len(records),
        "present": sum(1 for r in records if r["status"] == "present"),
        "late": sum(1 for r in records if r["status"] == "late"),
        "absent": sum(1 for r in records if r["status"] == "absent"),
    }
    summary["rate"] = ((summary["present"] + summary["late"]) / summary["total"] * 100.0) if summary["total"] > 0 else 0

    return {"records": records, "summary": summary}

# ============================================================================
# STUDENT ENDPOINTS
# ============================================================================

@app.get("/student/classes")
def get_available_classes():
    """Get all available classes for enrollment."""
    classes = db.get_all_classes()
    # Remove sensitive data (secret_word, room_photos)
    for cls in classes:
        cls.pop("secret_word", None)
        cls.pop("room_photos", None)
    return classes

@app.post("/student/enroll")
def enroll_in_class(enrollment: EnrollmentCreate):
    """Student enrolls in a class."""
    # Check if class exists
    class_obj = db.get_class_by_code(enrollment.class_code)
    if not class_obj:
        return {"ok": False, "reason": "class_not_found"}
    
    result = db.enroll_student(enrollment.class_code, enrollment.student_id)
    return result


@app.post("/student/unenroll")
def unenroll_from_class(unenrollment: UnenrollRequest):
    """Student unenrolls from a class."""
    class_obj = db.get_class_by_code(unenrollment.class_code)
    if not class_obj:
        return {"ok": False, "reason": "class_not_found"}

    return db.unenroll_student(unenrollment.class_code, unenrollment.student_id)

@app.get("/student/classes/{student_id}")
def get_student_classes(student_id: str):
    """Get all classes a student is enrolled in."""
    classes = db.get_student_classes(student_id)
    # Remove sensitive data
    for cls in classes:
        cls.pop("secret_word", None)
        cls.pop("room_photos", None)
    return classes

@app.post("/student/checkin")
async def student_checkin(req: Request, checkin: CheckInRequest):
    """Integrated check-in: geolocation + vision verification."""
    # 1. Check if class exists
    class_obj = db.get_class_by_code(checkin.class_code)
    if not class_obj:
        return {"ok": False, "reason": "class_not_found"}
    
    # 2. Check if student is enrolled
    if not db.is_student_enrolled(checkin.class_code, checkin.student_id):
        return {"ok": False, "reason": "not_enrolled"}
    
    # 3. Geolocation verification
    geo_ok = False
    distance_m = None
    
    if checkin.lat is not None and checkin.lon is not None:
        # Use provided GPS coordinates
        distance_m = haversine_m(class_obj["lat"], class_obj["lon"], checkin.lat, checkin.lon)
        geo_ok = distance_m <= class_obj["epsilon_m"]
    else:
        # Try IP-based geolocation
        client = req.client.host if req.client else ""
        ip = get_client_ip(req.headers, client)
        loc = PROVIDER.locate(ip)
        if loc:
            lat, lon, _ = loc
            distance_m = haversine_m(class_obj["lat"], class_obj["lon"], lat, lon)
            geo_ok = distance_m <= class_obj["epsilon_m"]
    
    if not geo_ok:
        # Record failed check-in
        db.record_checkin({
            "class_code": checkin.class_code,
            "student_id": checkin.student_id,
            "success": False,
            "geo_verified": False,
            "vision_verified": False,
            "distance_m": distance_m,
            "reason": "location_failed",
        })
        return {
            "ok": False,
            "reason": "location_failed",
            "distance_m": distance_m,
            "epsilon_m": class_obj["epsilon_m"],
            "needs_manual_override": True,
        }
    
    # 4. Vision verification (lecture hall recognition)
    vision_ok = False
    label = None
    confidence = 0.0
    
    if model is not None:
        try:
            img_bytes = base64.b64decode(checkin.image_b64)
            img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if img is not None:
                x = preprocess(img)
                with torch.no_grad():
                    logits = model(x)
                    pred = int(torch.argmax(logits, dim=1).item())
                    confidence = float(torch.softmax(logits, dim=1)[0, pred].item())
                    label = CLASSES[pred]
                
                # Check if predicted label matches expected class
                # For now, accept any prediction with confidence > 0.5
                vision_ok = confidence > 0.5
        except:
            pass
    
    if not vision_ok:
        # Record failed check-in
        db.record_checkin({
            "class_code": checkin.class_code,
            "student_id": checkin.student_id,
            "success": False,
            "geo_verified": True,
            "vision_verified": False,
            "distance_m": distance_m,
            "label": label,
            "confidence": confidence,
            "reason": "recognition_failed",
        })
        return {
            "ok": False,
            "reason": "recognition_failed",
            "distance_m": distance_m,
            "label": label,
            "confidence": confidence,
            "needs_manual_override": True,
        }
    
    # 5. Success - record check-in
    db.record_checkin({
        "class_code": checkin.class_code,
        "student_id": checkin.student_id,
        "success": True,
        "geo_verified": True,
        "vision_verified": True,
        "distance_m": distance_m,
        "label": label,
        "confidence": confidence,
    })
    
    return {
        "ok": True,
        "distance_m": distance_m,
        "label": label,
        "confidence": confidence,
    }

@app.post("/student/manual-override")
def manual_override(override: ManualOverrideRequest):
    """Manual check-in using secret word from professor."""
    # 1. Check if class exists
    class_obj = db.get_class_by_code(override.class_code)
    if not class_obj:
        return {"ok": False, "reason": "class_not_found"}
    
    # 2. Check if student is enrolled
    if not db.is_student_enrolled(override.class_code, override.student_id):
        return {"ok": False, "reason": "not_enrolled"}
    
    # 3. Verify secret word
    if override.secret_word != class_obj["secret_word"]:
        return {"ok": False, "reason": "invalid_secret_word"}
    
    # 4. Record successful manual check-in
    db.record_checkin({
        "class_code": override.class_code,
        "student_id": override.student_id,
        "success": True,
        "method": "manual_override",
        "geo_verified": False,
        "vision_verified": False,
    })
    
    return {"ok": True, "method": "manual_override"}
