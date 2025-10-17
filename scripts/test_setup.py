#!/usr/bin/env python3
"""
Test script to verify the face setup works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import yaml
        print("✅ yaml imported successfully")
    except ImportError as e:
        print(f"❌ yaml import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL imported successfully")
    except ImportError as e:
        print(f"⚠️  PIL import failed: {e} (optional)")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"⚠️  OpenCV import failed: {e} (optional)")
    
    return True

def test_params_file():
    """Test that params.yaml exists and is readable."""
    print("🧪 Testing params.yaml...")
    
    params_path = project_root / "params.yaml"
    if not params_path.exists():
        print("❌ params.yaml not found")
        return False
    
    try:
        import yaml
        with open(params_path) as f:
            params = yaml.safe_load(f)
        print("✅ params.yaml loaded successfully")
        print(f"   use_real_faces: {params.get('use_real_faces', False)}")
        return True
    except Exception as e:
        print(f"❌ Error loading params.yaml: {e}")
        return False

def test_directories():
    """Test that required directories exist or can be created."""
    print("🧪 Testing directories...")
    
    data_dir = project_root / "data"
    artifacts_dir = project_root / "artifacts"
    
    # Create directories if they don't exist
    data_dir.mkdir(exist_ok=True)
    artifacts_dir.mkdir(exist_ok=True)
    
    print("✅ Directories created/verified")
    return True

def main():
    """Run all tests."""
    print("🧪 Face Setup Test Suite")
    print("=" * 30)
    
    tests = [
        test_imports,
        test_params_file,
        test_directories
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Setup should work correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
