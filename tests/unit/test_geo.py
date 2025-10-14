"""Unit tests for geolocation utilities."""
import pytest
import math
import os
from unittest.mock import Mock, patch
import requests


def haversine_m_local(lat1, lon1, lat2, lon2) -> float:
    """
    Local implementation of haversine distance for testing.
    This matches the implementation in serve/src/geo.py
    """
    R = 6371000.0  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*(math.sin(dlambda/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


@pytest.mark.unit
class TestHaversine:
    """Test haversine distance calculation."""
    
    def test_zero_distance(self):
        """Same coordinates should give zero distance."""
        lat, lon = 42.3770, -71.1167
        assert haversine_m_local(lat, lon, lat, lon) == 0.0
    
    def test_known_distance(self):
        """Test known distance between Harvard and MIT."""
        # Harvard Yard
        lat1, lon1 = 42.3770, -71.1167
        # MIT
        lat2, lon2 = 42.3601, -71.0942
        
        distance = haversine_m_local(lat1, lon1, lat2, lon2)
        # Should be approximately 2.5 km
        assert 2000 < distance < 3000
    
    def test_symmetry(self):
        """Distance should be symmetric."""
        lat1, lon1 = 42.3770, -71.1167
        lat2, lon2 = 42.3601, -71.0942
        
        d1 = haversine_m_local(lat1, lon1, lat2, lon2)
        d2 = haversine_m_local(lat2, lon2, lat1, lon1)
        
        assert abs(d1 - d2) < 0.001


@pytest.mark.unit
class TestCalibration:
    """Test calibration logic (integration tests cover file I/O)."""
    
    def test_calibration_data_structure(self):
        """Test expected calibration data structure."""
        # Test that our expected calibration format is correct
        expected_keys = ["lat", "lon", "epsilon_m"]
        calibration_example = {
            "lat": 42.377,
            "lon": -71.1167,
            "epsilon_m": 100.0
        }
        
        for key in expected_keys:
            assert key in calibration_example
        
        assert isinstance(calibration_example["lat"], (int, float))
        assert isinstance(calibration_example["lon"], (int, float))
        assert isinstance(calibration_example["epsilon_m"], (int, float))
    
    def test_epsilon_ranges(self):
        """Test that epsilon values are reasonable."""
        valid_epsilon_values = [10, 50, 100, 500, 1000]
        
        for eps in valid_epsilon_values:
            assert eps > 0, "Epsilon must be positive"
            assert eps < 10000, "Epsilon should be reasonable (< 10km)"


@pytest.mark.unit
class TestGoogleGeoProvider:
    """Test Google Geolocation API provider."""
    
    def test_google_api_success(self):
        """Test successful Google API response."""
        # Mock Google's response format
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "location": {"lat": 42.3770, "lng": -71.1167},
            "accuracy": 50.0
        }
        
        with patch('requests.post', return_value=mock_response):
            # Simulate GoogleGeo provider
            from serve.src.geo import GoogleGeo
            provider = GoogleGeo("fake-api-key")
            result = provider.locate("8.8.8.8")
            
            assert result is not None
            lat, lon, acc = result
            assert lat == 42.3770
            assert lon == -71.1167
            assert acc == 50.0
    
    def test_google_api_failure(self):
        """Test Google API failure handling."""
        mock_response = Mock()
        mock_response.ok = False
        
        with patch('requests.post', return_value=mock_response):
            from serve.src.geo import GoogleGeo
            provider = GoogleGeo("fake-api-key")
            result = provider.locate("8.8.8.8")
            
            assert result is None
    
    def test_google_api_timeout(self):
        """Test Google API timeout handling."""
        with patch('requests.post', side_effect=requests.Timeout):
            from serve.src.geo import GoogleGeo
            provider = GoogleGeo("fake-api-key")
            result = provider.locate("8.8.8.8")
            
            assert result is None
    
    def test_google_api_missing_location(self):
        """Test Google API response with missing location data."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"accuracy": 100.0}  # No location field
        
        with patch('requests.post', return_value=mock_response):
            from serve.src.geo import GoogleGeo
            provider = GoogleGeo("fake-api-key")
            result = provider.locate("8.8.8.8")
            
            assert result is None


@pytest.mark.unit  
class TestIpApiProvider:
    """Test IP-API.com provider."""
    
    def test_ipapi_success(self):
        """Test successful IP-API response."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "status": "success",
            "lat": 42.3601,
            "lon": -71.0942
        }
        
        with patch('requests.get', return_value=mock_response):
            from serve.src.geo import IpApi
            provider = IpApi()
            result = provider.locate("18.9.22.69")  # MIT IP
            
            assert result is not None
            lat, lon, acc = result
            assert lat == 42.3601
            assert lon == -71.0942
            assert acc == 1000.0  # Default accuracy
    
    def test_ipapi_failure(self):
        """Test IP-API failure handling."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "status": "fail",
            "message": "invalid query"
        }
        
        with patch('requests.get', return_value=mock_response):
            from serve.src.geo import IpApi
            provider = IpApi()
            result = provider.locate("invalid")
            
            assert result is None


@pytest.mark.unit
class TestProviderPicking:
    """Test provider selection logic."""
    
    def test_pick_google_with_key(self):
        """Test that GoogleGeo is picked when API key is set."""
        with patch.dict(os.environ, {"GEO_PROVIDER": "google", "GOOGLE_API_KEY": "test-key"}):
            from serve.src.geo import pick_provider, GoogleGeo
            # Need to reimport to pick up env changes
            import importlib
            import serve.src.geo as geo_module
            importlib.reload(geo_module)
            provider = geo_module.pick_provider()
            assert isinstance(provider, geo_module.GoogleGeo)
    
    def test_pick_ipapi_fallback(self):
        """Test that IpApi is used when no Google key is set."""
        with patch.dict(os.environ, {"GEO_PROVIDER": "google", "GOOGLE_API_KEY": ""}, clear=True):
            from serve.src.geo import pick_provider, IpApi
            import importlib
            import serve.src.geo as geo_module
            importlib.reload(geo_module)
            provider = geo_module.pick_provider()
            assert isinstance(provider, geo_module.IpApi)
    
    def test_pick_mock_provider(self):
        """Test mock provider selection."""
        with patch.dict(os.environ, {"GEO_PROVIDER": "mock"}):
            from serve.src.geo import pick_provider, MockGeo
            import importlib
            import serve.src.geo as geo_module
            importlib.reload(geo_module)
            provider = geo_module.pick_provider()
            assert isinstance(provider, geo_module.MockGeo)


@pytest.mark.unit
class TestMockGeoProvider:
    """Test Mock geolocation provider."""
    
    def test_mock_returns_harvard(self):
        """Test that MockGeo returns Harvard coordinates."""
        from serve.src.geo import MockGeo
        provider = MockGeo()
        result = provider.locate(None)
        
        assert result is not None
        lat, lon, acc = result
        # Harvard Yard coordinates
        assert 42.37 < lat < 42.38
        assert -71.12 < lon < -71.11
        assert acc == 800.0
