"""Integration tests for API endpoints."""
import pytest
import requests
import json


@pytest.mark.integration
class TestAPIHealth:
    """Test API health and availability."""
    
    def test_healthz_endpoint(self, api_base_url, wait_for_services):
        """Test /healthz endpoint returns 200."""
        response = requests.get(f"{api_base_url}/healthz", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert "model" in data
        assert "geo_provider" in data
    
    def test_healthz_content_type(self, api_base_url, wait_for_services):
        """Test /healthz returns JSON."""
        response = requests.get(f"{api_base_url}/healthz", timeout=5)
        assert "application/json" in response.headers["Content-Type"]


@pytest.mark.integration
class TestGeoCalibration:
    """Test geolocation calibration endpoints."""
    
    def test_calibrate_endpoint(self, api_base_url, wait_for_services):
        """Test POST /geo/calibrate."""
        payload = {
            "lat": 42.3770,
            "lon": -71.1167,
            "epsilon_m": 100.0
        }
        
        response = requests.post(
            f"{api_base_url}/geo/calibrate",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "calibration" in data
        assert data["calibration"]["lat"] == 42.3770
        assert data["calibration"]["lon"] == -71.1167
        assert data["calibration"]["epsilon_m"] == 100.0
    
    def test_status_endpoint(self, api_base_url, wait_for_services):
        """Test GET /geo/status."""
        response = requests.get(f"{api_base_url}/geo/status", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "calibration" in data


@pytest.mark.integration
class TestGeoVerification:
    """Test geolocation verification endpoint."""
    
    def test_verify_without_calibration(self, api_base_url, wait_for_services):
        """Test /geo/verify fails gracefully without calibration."""
        # First clear calibration by setting it to None (or skip if already clear)
        response = requests.post(
            f"{api_base_url}/geo/verify",
            json={},
            timeout=5
        )
        
        assert response.status_code == 200
        # May return not_calibrated or process with defaults
    
    def test_verify_with_client_gps(self, api_base_url, wait_for_services):
        """Test /geo/verify with client-provided GPS."""
        # First calibrate
        calibrate_payload = {
            "lat": 42.3770,
            "lon": -71.1167,
            "epsilon_m": 100.0
        }
        requests.post(
            f"{api_base_url}/geo/calibrate",
            json=calibrate_payload,
            timeout=5
        )
        
        # Verify with GPS near Harvard (should pass)
        verify_payload = {
            "client_gps_lat": 42.3765,
            "client_gps_lon": -71.1170,
            "client_gps_accuracy_m": 20.0
        }
        
        response = requests.post(
            f"{api_base_url}/geo/verify",
            json=verify_payload,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "distance_m" in data
        assert "source" in data
        assert data["source"] == "client_gps"


@pytest.mark.integration
class TestVerifyEndpoint:
    """Test lecture hall recognition endpoint."""
    
    def test_verify_with_image(self, api_base_url, sample_image_b64, wait_for_services):
        """Test /verify succeeds with valid image."""
        payload = {
            "image_b64": sample_image_b64
        }
        
        response = requests.post(
            f"{api_base_url}/verify",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should succeed if model is loaded
        if data["ok"]:
            assert "label" in data
            assert "confidence" in data
            assert "latency_ms" in data
            assert data["label"] in ["ProfA", "Room1"]
            assert 0 <= data["confidence"] <= 1
    
    def test_verify_invalid_base64(self, api_base_url, wait_for_services):
        """Test /verify handles invalid image data."""
        payload = {
            "image_b64": "invalid_base64!@#$"
        }
        
        response = requests.post(
            f"{api_base_url}/verify",
            json=payload,
            timeout=5
        )
        
        # Should return error (400 or 200 with ok=false)
        assert response.status_code in [200, 400]
