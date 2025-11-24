"""Integration tests hitting FastAPI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_gps_checkin(client: TestClient):
    payload = {
        "student_id": "student-1",
        "course_id": 1,
        "instructor_id": "instructor-harv",
        "device_id": "ios",
        "latitude": 42.3765,
        "longitude": -71.1168,
    }
    response = client.post("/api/checkin/gps", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "record_id" in body
    assert body["status"] in {"present", "pending"}


def test_vision_checkin(client: TestClient, sample_image_b64: str):
    payload = {
        "student_id": "student-2",
        "course_id": 1,
        "instructor_id": "instructor-harv",
        "image_b64": sample_image_b64,
    }
    response = client.post("/api/checkin/vision", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "record_id" in body
    assert body["confidence"] is not None


def test_instructor_endpoints(client: TestClient):
    courses = client.get("/api/instructor/courses", params={"instructor_id": "instructor-harv"})
    assert courses.status_code == 200
    data = courses.json()
    assert data
    course_id = data[0]["id"]

    attendance = client.get(f"/api/instructor/attendance?course_id={course_id}")
    assert attendance.status_code == 200

    override_payload = {
        "status": "present",
        "notes": "Instructor confirmed manually",
    }
    # Create an event first via GPS
    gps_payload = {
        "student_id": "student-override",
        "course_id": course_id,
        "instructor_id": "instructor-harv",
        "device_id": "ios-1",
        "latitude": 42.3765,
        "longitude": -71.1168,
    }
    gps_response = client.post("/api/checkin/gps", json=gps_payload)
    event_id = gps_response.json()["record_id"]
    override = client.post(f"/api/instructor/attendance/{event_id}/override", json=override_payload)
    assert override.status_code == 200
    assert override.json()["status"] == "present"
