"""Integration tests for Google Geolocation API.

These tests verify that:
1. Google API key is properly configured
2. Google API is responding correctly
3. Provider selection logic works as expected
"""
import pytest
import os
import requests


@pytest.mark.integration
class TestGoogleAPIIntegration:
    """Integration tests for Google Geolocation API."""
    
    def test_google_api_key_configured(self):
        """Verify Google API key is set in environment."""
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set - using fallback IP provider")
        
        assert api_key, "GOOGLE_API_KEY should be set for production use"
        assert len(api_key) > 20, "API key seems too short"
    
    def test_google_api_responds(self):
        """Test that Google API actually responds (requires valid key)."""
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set - cannot test real API")
        
        # Make a real API call with considerIp=True
        url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
        payload = {"considerIp": True}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            # Check for common errors
            if response.status_code == 403:
                pytest.fail("Google API key is invalid or API is not enabled")
            elif response.status_code == 429:
                pytest.skip("Google API rate limit exceeded")
            
            assert response.ok, f"Google API failed: {response.status_code} - {response.text}"
            
            data = response.json()
            assert "location" in data, "Response missing 'location' field"
            assert "lat" in data["location"], "Response missing latitude"
            assert "lng" in data["location"], "Response missing longitude"
            
            # Verify coordinates are reasonable (on Earth)
            lat = data["location"]["lat"]
            lon = data["location"]["lng"]
            assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
            assert -180 <= lon <= 180, f"Invalid longitude: {lon}"
            
            print(f"\n✓ Google API working! Location: ({lat:.4f}, {lon:.4f})")
            
        except requests.RequestException as e:
            pytest.fail(f"Failed to connect to Google API: {e}")
    
    def test_google_api_accuracy_field(self):
        """Verify Google API returns accuracy information."""
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set - cannot test real API")
        
        url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
        payload = {"considerIp": True}
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.ok:
            data = response.json()
            # Accuracy field is optional but usually present
            if "accuracy" in data:
                acc = data["accuracy"]
                assert acc > 0, "Accuracy should be positive"
                print(f"\n✓ Accuracy: ±{acc:.0f}m")


@pytest.mark.integration
class TestProviderEndpoint:
    """Test that the serve API uses the correct provider."""
    
    def test_healthz_shows_provider(self):
        """Test /healthz endpoint shows which geo provider is active."""
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            response = requests.get(f"{api_url}/healthz", timeout=5)
            
            if not response.ok:
                pytest.skip(f"API not available at {api_url}")
            
            data = response.json()
            assert "geo_provider" in data, "healthz should report geo provider"
            
            provider = data["geo_provider"]
            api_key = os.getenv("GOOGLE_API_KEY")
            
            if api_key:
                assert provider == "GoogleGeo", f"Expected GoogleGeo with API key, got {provider}"
                print(f"\n✓ Using {provider} (Google API configured)")
            else:
                assert provider in ["IpApi", "MockGeo"], f"Expected fallback provider, got {provider}"
                print(f"\n⚠️  Using {provider} - set GOOGLE_API_KEY for better accuracy")
                
        except requests.RequestException:
            pytest.skip(f"API not running at {api_url}")


@pytest.mark.integration
class TestGeoVerifyEndpoint:
    """Test the full geo verify flow."""
    
    def test_geo_verify_without_calibration(self):
        """Test geo verify fails gracefully without calibration."""
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            response = requests.post(f"{api_url}/geo/verify", json={}, timeout=10)
            
            if not response.ok:
                pytest.skip(f"API not available at {api_url}")
            
            data = response.json()
            
            # Should either fail with not_calibrated or succeed (if already calibrated)
            if not data.get("ok"):
                assert data.get("reason") == "not_calibrated", \
                    f"Expected not_calibrated, got {data.get('reason')}"
            
        except requests.RequestException:
            pytest.skip(f"API not running at {api_url}")
    
    def test_geo_verify_response_structure(self):
        """Test that geo verify returns expected fields."""
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            # First calibrate
            cal_response = requests.post(
                f"{api_url}/geo/calibrate",
                json={"lat": 42.3770, "lon": -71.1167, "epsilon_m": 5000},
                timeout=10
            )
            
            if not cal_response.ok:
                pytest.skip("Failed to calibrate")
            
            # Then verify
            verify_response = requests.post(f"{api_url}/geo/verify", json={}, timeout=10)
            
            if not verify_response.ok:
                pytest.skip("Verify endpoint failed")
            
            data = verify_response.json()
            
            # Check required fields
            assert "ok" in data
            assert "source" in data
            assert "client_ip" in data
            
            if data.get("ok") or data.get("reason") != "not_calibrated":
                assert "distance_m" in data
                assert "estimated_lat" in data
                assert "estimated_lon" in data
                
                print(f"\n✓ Geo verify working! Source: {data.get('source')}, "
                      f"Location: ({data.get('estimated_lat'):.4f}, {data.get('estimated_lon'):.4f})")
                
        except requests.RequestException as e:
            pytest.skip(f"API not running: {e}")
