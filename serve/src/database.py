"""
Simple JSON-based database for HARV mobile app.
In production, this should be replaced with PostgreSQL or similar.
"""
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

DB_BACKEND = os.getenv("DB_BACKEND", "json").lower()
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID") or os.getenv("PROJECT_ID")
FIRESTORE_COLLECTION_PREFIX = os.getenv("FIRESTORE_COLLECTION_PREFIX", "harv")
USE_FIRESTORE = DB_BACKEND == "firestore"

if USE_FIRESTORE:
    try:
        from google.cloud import firestore
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"[database] Failed to import Firestore client ({exc}); falling back to JSON storage.")
        USE_FIRESTORE = False

if USE_FIRESTORE and not FIRESTORE_PROJECT_ID:
    print("[database] FIRESTORE_PROJECT_ID/PROJECT_ID not configured; falling back to JSON storage.")
    USE_FIRESTORE = False

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
        "classroom_id": class_data.get("classroom_id"),
        "classroom_label": class_data.get("classroom_label"),
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


def unenroll_student(class_code: str, student_id: str) -> Dict:
    """Remove a student enrollment from a class."""
    enrollments = load_json(ENROLLMENTS_FILE)
    new_enrollments = [
        e for e in enrollments
        if not (e["class_code"] == class_code and e["student_id"] == student_id)
    ]

    if len(new_enrollments) == len(enrollments):
        return {"ok": False, "reason": "not_enrolled"}

    save_json(ENROLLMENTS_FILE, new_enrollments)
    return {"ok": True}


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


def get_students_by_class(class_code: str) -> List[Dict]:
    """Return roster for a class with lightweight attendance stats."""
    enrollments = load_json(ENROLLMENTS_FILE)
    checkins = load_json(CHECKINS_FILE)

    roster = []
    seen = set()

    for enrollment in enrollments:
        if enrollment["class_code"] != class_code:
            continue

        student_id = enrollment["student_id"]
        if student_id in seen:
            continue
        seen.add(student_id)

        student_checkins = [
            c for c in checkins
            if c["class_code"] == class_code and c["student_id"] == student_id
        ]
        student_checkins.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        total_attempts = len(student_checkins)
        attended = sum(1 for c in student_checkins if c.get("success"))
        attendance_rate = (attended / total_attempts * 100.0) if total_attempts > 0 else 0.0
        last_check_in = student_checkins[0]["timestamp"] if student_checkins else None

        roster.append({
            "id": student_id,
            "name": student_id,
            "email": None,
            "attendance_rate": attendance_rate,
            "last_check_in": last_check_in,
            "attended_classes": attended,
            "total_classes": total_attempts,
        })

    roster.sort(key=lambda s: s["id"])
    return roster


if USE_FIRESTORE:
    class FirestoreBackend:
        """Firestore-backed storage for classes, students, enrollments, and check-ins."""

        def __init__(self):
            self.client = firestore.Client(project=FIRESTORE_PROJECT_ID)
            prefix = FIRESTORE_COLLECTION_PREFIX.rstrip("_")
            self.classes = self.client.collection(f"{prefix}_classes")
            self.students = self.client.collection(f"{prefix}_students")
            self.enrollments = self.client.collection(f"{prefix}_enrollments")
            self.checkins = self.client.collection(f"{prefix}_checkins")

        def _timestamp(self) -> str:
            return datetime.utcnow().isoformat()

        def _class_from_doc(self, doc):
            data = doc.to_dict()
            if not data:
                return None
            data.setdefault("code", doc.id)
            data.setdefault("id", data.get("id", doc.id))
            return data

        def create_class(self, class_data: Dict) -> Dict:
            class_code = class_data["code"]
            class_id = hashlib.md5(f"{class_code}{self._timestamp()}".encode()).hexdigest()[:12]
            new_class = {
                "id": class_id,
                "name": class_data["name"],
                "code": class_code,
                "lat": class_data["lat"],
                "lon": class_data["lon"],
                "epsilon_m": class_data["epsilon_m"],
                "secret_word": class_data["secret_word"],
                "room_photos": class_data.get("room_photos", []),
                "classroom_id": class_data.get("classroom_id"),
                "classroom_label": class_data.get("classroom_label"),
                "professor_id": class_data.get("professor_id", "unknown"),
                "professor_name": class_data.get("professor_name", "Unknown"),
                "created_at": self._timestamp(),
            }
            self.classes.document(class_code).set(new_class)
            return new_class

        def get_class_by_code(self, code: str) -> Optional[Dict]:
            doc = self.classes.document(code).get()
            if not doc.exists:
                return None
            return self._class_from_doc(doc)

        def get_classes_by_professor(self, professor_id: str) -> List[Dict]:
            docs = self.classes.where("professor_id", "==", professor_id).stream()
            return [cls for doc in docs if (cls := self._class_from_doc(doc))]

        def get_all_classes(self) -> List[Dict]:
            return [cls for doc in self.classes.stream() if (cls := self._class_from_doc(doc))]

        def enroll_student(self, class_code: str, student_id: str) -> Dict:
            enrollment_id = f"{class_code}_{student_id}"
            doc_ref = self.enrollments.document(enrollment_id)
            if doc_ref.get().exists:
                return {"ok": False, "reason": "already_enrolled"}

            enrollment = {
                "id": enrollment_id,
                "class_code": class_code,
                "student_id": student_id,
                "enrolled_at": self._timestamp(),
            }
            doc_ref.set(enrollment)

            # Ensure a student profile exists for roster views.
            self.students.document(student_id).set(
                {"id": student_id, "name": student_id, "updated_at": self._timestamp()},
                merge=True,
            )
            return {"ok": True, "enrollment": enrollment}

        def unenroll_student(self, class_code: str, student_id: str) -> Dict:
            enrollment_id = f"{class_code}_{student_id}"
            doc_ref = self.enrollments.document(enrollment_id)
            if not doc_ref.get().exists:
                return {"ok": False, "reason": "not_enrolled"}
            doc_ref.delete()
            return {"ok": True}

        def get_student_classes(self, student_id: str) -> List[Dict]:
            classes = []
            for enrollment_doc in self.enrollments.where("student_id", "==", student_id).stream():
                class_code = enrollment_doc.to_dict().get("class_code")
                if not class_code:
                    continue
                cls = self.get_class_by_code(class_code)
                if cls:
                    classes.append(cls.copy())
            return classes

        def is_student_enrolled(self, class_code: str, student_id: str) -> bool:
            enrollment_id = f"{class_code}_{student_id}"
            return self.enrollments.document(enrollment_id).get().exists

        def record_checkin(self, checkin_data: Dict) -> Dict:
            checkin = {
                "class_code": checkin_data["class_code"],
                "student_id": checkin_data["student_id"],
                "success": checkin_data["success"],
                "method": checkin_data.get("method", "auto"),
                "geo_verified": checkin_data.get("geo_verified", False),
                "vision_verified": checkin_data.get("vision_verified", False),
                "distance_m": checkin_data.get("distance_m"),
                "label": checkin_data.get("label"),
                "confidence": checkin_data.get("confidence"),
                "reason": checkin_data.get("reason"),
                "timestamp": self._timestamp(),
            }
            doc_ref = self.checkins.document()
            checkin["id"] = doc_ref.id
            doc_ref.set(checkin)
            return checkin

        def get_student_checkins(self, student_id: str, class_code: Optional[str] = None) -> List[Dict]:
            query = self.checkins.where("student_id", "==", student_id)
            if class_code:
                query = query.where("class_code", "==", class_code)
            results = [doc.to_dict() for doc in query.stream()]
            return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)

        def get_class_checkins(self, class_code: str) -> List[Dict]:
            return [doc.to_dict() for doc in self.checkins.where("class_code", "==", class_code).stream()]

        def get_students_by_class(self, class_code: str) -> List[Dict]:
            enrollments = [
                doc.to_dict()
                for doc in self.enrollments.where("class_code", "==", class_code).stream()
            ]
            checkins = [
                doc.to_dict()
                for doc in self.checkins.where("class_code", "==", class_code).stream()
            ]
            checkins_by_student = defaultdict(list)
            for checkin in checkins:
                checkins_by_student[checkin.get("student_id")].append(checkin)

            roster = []
            for enrollment in enrollments:
                student_id = enrollment["student_id"]
                student_checkins = checkins_by_student.get(student_id, [])
                total_attempts = len(student_checkins)
                attended = sum(1 for c in student_checkins if c.get("success"))
                attendance_rate = (attended / total_attempts * 100.0) if total_attempts > 0 else 0.0
                last_check_in = None
                if student_checkins:
                    last_check_in = max(
                        (c.get("timestamp") for c in student_checkins if c.get("timestamp")),
                        default=None,
                    )

                student_doc = self.students.document(student_id).get()
                student_name = student_id
                if student_doc.exists:
                    student_data = student_doc.to_dict() or {}
                    student_name = student_data.get("name") or student_id

                roster.append({
                    "id": student_id,
                    "name": student_name,
                    "email": None,
                    "attendance_rate": attendance_rate,
                    "last_check_in": last_check_in,
                    "attended_classes": attended,
                    "total_classes": total_attempts,
                })

            roster.sort(key=lambda s: s["id"])
            return roster

    _firestore_db = FirestoreBackend()

    def create_class(class_data: Dict) -> Dict:
        return _firestore_db.create_class(class_data)

    def get_class_by_code(code: str) -> Optional[Dict]:
        return _firestore_db.get_class_by_code(code)

    def get_classes_by_professor(professor_id: str) -> List[Dict]:
        return _firestore_db.get_classes_by_professor(professor_id)

    def get_all_classes() -> List[Dict]:
        return _firestore_db.get_all_classes()

    def enroll_student(class_code: str, student_id: str) -> Dict:
        return _firestore_db.enroll_student(class_code, student_id)

    def unenroll_student(class_code: str, student_id: str) -> Dict:
        return _firestore_db.unenroll_student(class_code, student_id)

    def get_student_classes(student_id: str) -> List[Dict]:
        return _firestore_db.get_student_classes(student_id)

    def is_student_enrolled(class_code: str, student_id: str) -> bool:
        return _firestore_db.is_student_enrolled(class_code, student_id)

    def record_checkin(checkin_data: Dict) -> Dict:
        return _firestore_db.record_checkin(checkin_data)

    def get_student_checkins(student_id: str, class_code: Optional[str] = None) -> List[Dict]:
        return _firestore_db.get_student_checkins(student_id, class_code)

    def get_class_checkins(class_code: str) -> List[Dict]:
        return _firestore_db.get_class_checkins(class_code)

    def get_students_by_class(class_code: str) -> List[Dict]:
        return _firestore_db.get_students_by_class(class_code)
