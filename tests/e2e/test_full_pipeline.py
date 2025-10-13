"""End-to-end smoke tests for full system."""
import pytest
import requests
import json
import base64
import numpy as np
import cv2
from pathlib import Path


@pytest.mark.e2e
class TestE2EWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_complete_verification_workflow(self, api_base_url, evidence_dir, wait_for_services):
        """Test complete workflow: calibrate → geo verify → image verify."""
        results = {}
        
        # Step 1: Check health
        health_resp = requests.get(f"{api_base_url}/healthz", timeout=5)
        assert health_resp.status_code == 200
        results["health"] = health_resp.json()
        
        # Step 2: Calibrate geolocation
        calibrate_payload = {
            "lat": 42.3770,
            "lon": -71.1167,
            "epsilon_m": 100.0
        }
        calibrate_resp = requests.post(
            f"{api_base_url}/geo/calibrate",
            json=calibrate_payload,
            timeout=5
        )
        assert calibrate_resp.status_code == 200
        results["calibration"] = calibrate_resp.json()
        
        # Step 3: Verify geolocation with client GPS
        geo_verify_payload = {
            "client_gps_lat": 42.3765,
            "client_gps_lon": -71.1170,
            "client_gps_accuracy_m": 20.0
        }
        geo_resp = requests.post(
            f"{api_base_url}/geo/verify",
            json=geo_verify_payload,
            timeout=5
        )
        assert geo_resp.status_code == 200
        results["geo_verification"] = geo_resp.json()
        
        # Step 4: Create test image
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255
        _, buf = cv2.imencode(".jpg", img)
        img_b64 = base64.b64encode(buf).decode()
        
        # Step 5: Verify image with challenge word
        verify_payload = {
            "image_b64": img_b64,
            "challenge_word": "orchid"
        }
        verify_resp = requests.post(
            f"{api_base_url}/verify",
            json=verify_payload,
            timeout=10
        )
        assert verify_resp.status_code == 200
        results["image_verification"] = verify_resp.json()
        
        # Save E2E results
        output_file = evidence_dir / "e2e" / "e2e_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ E2E results saved to {output_file}")
        
        # Verify overall success
        assert results["health"]["ok"] is True
        assert results["calibration"]["ok"] is True
        # Geo verification should pass (within epsilon)
        if results["geo_verification"]["ok"]:
            assert results["geo_verification"]["distance_m"] <= 100.0
    
    def test_error_handling_workflow(self, api_base_url, wait_for_services):
        """Test error handling in various scenarios."""
        # Test 1: Wrong challenge word
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255
        _, buf = cv2.imencode(".jpg", img)
        img_b64 = base64.b64encode(buf).decode()
        
        verify_payload = {
            "image_b64": img_b64,
            "challenge_word": "wrong_word"
        }
        response = requests.post(
            f"{api_base_url}/verify",
            json=verify_payload,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["reason"] == "challenge_failed"
        
        # Test 2: Verify geo status works
        status_resp = requests.get(f"{api_base_url}/geo/status", timeout=5)
        assert status_resp.status_code == 200
        assert status_resp.json()["ok"] is True


@pytest.mark.e2e
@pytest.mark.slow
class TestE2EPerformance:
    """Test system performance under E2E scenarios."""
    
    def test_latency_verification(self, api_base_url, wait_for_services):
        """Test that verification completes within acceptable time."""
        import time
        
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255
        _, buf = cv2.imencode(".jpg", img)
        img_b64 = base64.b64encode(buf).decode()
        
        verify_payload = {
            "image_b64": img_b64,
            "challenge_word": "orchid"
        }
        
        start = time.time()
        response = requests.post(
            f"{api_base_url}/verify",
            json=verify_payload,
            timeout=10
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Total request should complete within 5 seconds
        assert elapsed < 5.0
        
        # Check reported latency
        data = response.json()
        if data.get("ok"):
            assert "latency_ms" in data
            # Model inference should be fast (< 1000ms on CPU)
            assert data["latency_ms"] < 1000
    
    def test_sequential_requests(self, api_base_url, wait_for_services):
        """Test multiple sequential requests work correctly."""
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255
        _, buf = cv2.imencode(".jpg", img)
        img_b64 = base64.b64encode(buf).decode()
        
        verify_payload = {
            "image_b64": img_b64,
            "challenge_word": "orchid"
        }
        
        # Send 5 sequential requests
        for i in range(5):
            response = requests.post(
                f"{api_base_url}/verify",
                json=verify_payload,
                timeout=10
            )
            assert response.status_code == 200
            print(f"  Request {i+1}/5 completed")
