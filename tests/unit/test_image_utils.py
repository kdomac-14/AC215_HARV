"""Unit tests for image utilities."""
import pytest
import numpy as np
import cv2
import base64


@pytest.mark.unit
class TestImageProcessing:
    """Test image processing utilities."""
    
    def test_image_creation(self, sample_image):
        """Test sample image fixture."""
        assert sample_image.shape == (224, 224, 3)
        assert sample_image.dtype == np.uint8
    
    def test_image_encoding(self, sample_image):
        """Test image can be encoded to JPEG."""
        success, buf = cv2.imencode(".jpg", sample_image)
        assert success
        assert len(buf) > 0
    
    def test_base64_encoding(self, sample_image_b64):
        """Test base64 encoding fixture."""
        assert isinstance(sample_image_b64, str)
        assert len(sample_image_b64) > 0
        
        # Verify it can be decoded
        decoded = base64.b64decode(sample_image_b64)
        img = cv2.imdecode(np.frombuffer(decoded, np.uint8), cv2.IMREAD_COLOR)
        assert img is not None
        assert img.shape == (224, 224, 3)
    
    def test_image_resize(self, sample_image):
        """Test image resizing."""
        resized = cv2.resize(sample_image, (112, 112))
        assert resized.shape == (112, 112, 3)
    
    def test_color_channels(self, sample_image):
        """Test image has 3 color channels."""
        assert sample_image.ndim == 3
        assert sample_image.shape[2] == 3
