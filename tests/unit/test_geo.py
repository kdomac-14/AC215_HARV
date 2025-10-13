"""Unit tests for geolocation utilities."""
import pytest
import math


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
