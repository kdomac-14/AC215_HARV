"""
Simple JSON-based database for HARV mobile app.
In production, this should be replaced with PostgreSQL or similar.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

DB_PATH = Path("/app/artifacts/db")
DB_PATH.mkdir(parents=True, exist_ok=True)

CLASSES_FILE = DB_PATH / "classes.json"
ENROLLMENTS_FILE = DB_PATH / "enrollments.json"
CHECKINS_FILE = DB_PATH / "checkins.json"


def load_json(file_path: Path) -> List[Dict]:
    """Load JSON data from file."""
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return []


def save_json(file_path: Path, data: List[Dict]):
    """Save JSON data to file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


# Class Management
def create_class(class_data: Dict) -> Dict:
    """Create a new class."""
    classes = load_json(CLASSES_FILE)
    
    # Generate unique ID
    class_id = hashlib.md5(f"{class_data['code']}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    new_class = {
        "id": class_id,
        "name": class_data["name"],
        "code": class_data["code"],
        "lat": class_data["lat"],
        "lon": class_data["lon"],
        "epsilon_m": class_data["epsilon_m"],
        "secret_word": class_data["secret_word"],
        "room_photos": class_data.get("room_photos", []),
        "professor_id": class_data.get("professor_id", "unknown"),
        "professor_name": class_data.get("professor_name", "Unknown"),
        "created_at": datetime.now().isoformat(),
    }
    
    classes.append(new_class)
    save_json(CLASSES_FILE, classes)
    
    return new_class


def get_class_by_code(code: str) -> Optional[Dict]:
    """Get class by code."""
    classes = load_json(CLASSES_FILE)
    for cls in classes:
        if cls["code"] == code:
            return cls
    return None


def get_classes_by_professor(professor_id: str) -> List[Dict]:
    """Get all classes for a professor."""
    classes = load_json(CLASSES_FILE)
    return [cls for cls in classes if cls.get("professor_id") == professor_id]


def get_all_classes() -> List[Dict]:
    """Get all classes."""
    return load_json(CLASSES_FILE)


# Enrollment Management
def enroll_student(class_code: str, student_id: str) -> Dict:
    """Enroll a student in a class."""
    enrollments = load_json(ENROLLMENTS_FILE)
    
    # Check if already enrolled
    for enrollment in enrollments:
        if enrollment["class_code"] == class_code and enrollment["student_id"] == student_id:
            return {"ok": False, "reason": "already_enrolled"}
    
    enrollment = {
        "id": hashlib.md5(f"{class_code}{student_id}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        "class_code": class_code,
        "student_id": student_id,
        "enrolled_at": datetime.now().isoformat(),
    }
    
    enrollments.append(enrollment)
    save_json(ENROLLMENTS_FILE, enrollments)
    
    return {"ok": True, "enrollment": enrollment}


def get_student_classes(student_id: str) -> List[Dict]:
    """Get all classes a student is enrolled in."""
    enrollments = load_json(ENROLLMENTS_FILE)
    classes = load_json(CLASSES_FILE)
    
    enrolled_codes = [e["class_code"] for e in enrollments if e["student_id"] == student_id]
    return [cls for cls in classes if cls["code"] in enrolled_codes]


def is_student_enrolled(class_code: str, student_id: str) -> bool:
    """Check if student is enrolled in class."""
    enrollments = load_json(ENROLLMENTS_FILE)
    for enrollment in enrollments:
        if enrollment["class_code"] == class_code and enrollment["student_id"] == student_id:
            return True
    return False


# Check-in Management
def record_checkin(checkin_data: Dict) -> Dict:
    """Record a check-in attempt."""
    checkins = load_json(CHECKINS_FILE)
    
    checkin = {
        "id": hashlib.md5(f"{checkin_data['class_code']}{checkin_data['student_id']}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        "class_code": checkin_data["class_code"],
        "student_id": checkin_data["student_id"],
        "success": checkin_data["success"],
        "method": checkin_data.get("method", "auto"),  # auto or manual_override
        "geo_verified": checkin_data.get("geo_verified", False),
        "vision_verified": checkin_data.get("vision_verified", False),
        "distance_m": checkin_data.get("distance_m"),
        "label": checkin_data.get("label"),
        "confidence": checkin_data.get("confidence"),
        "reason": checkin_data.get("reason"),
        "timestamp": datetime.now().isoformat(),
    }
    
    checkins.append(checkin)
    save_json(CHECKINS_FILE, checkins)
    
    return checkin


def get_student_checkins(student_id: str, class_code: Optional[str] = None) -> List[Dict]:
    """Get check-in history for a student."""
    checkins = load_json(CHECKINS_FILE)
    result = [c for c in checkins if c["student_id"] == student_id]
    
    if class_code:
        result = [c for c in result if c["class_code"] == class_code]
    
    return sorted(result, key=lambda x: x["timestamp"], reverse=True)


def get_class_checkins(class_code: str) -> List[Dict]:
    """Get all check-ins for a class."""
    checkins = load_json(CHECKINS_FILE)
    return [c for c in checkins if c["class_code"] == class_code]
