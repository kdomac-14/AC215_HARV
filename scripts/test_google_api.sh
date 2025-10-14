#!/bin/bash
# Test script to verify Google Geolocation API setup

set -e

echo "=========================================="
echo "Google Geolocation API Test"
echo "=========================================="
echo ""

# Load .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and add your GOOGLE_API_KEY"
    exit 1
fi

# Check if API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY is not set in .env"
    echo ""
    echo "To fix:"
    echo "  1. Go to https://console.cloud.google.com/apis/credentials"
    echo "  2. Create an API key with Geolocation API enabled"
    echo "  3. Add it to your .env file: GOOGLE_API_KEY=your-key-here"
    echo ""
    echo "Currently using fallback IP provider (less accurate)"
    exit 1
fi

echo "✓ API key found: ${GOOGLE_API_KEY:0:10}...${GOOGLE_API_KEY: -4}"
echo ""

# Test the API
echo "Testing Google Geolocation API..."
echo ""

response=$(curl -s -X POST \
    "https://www.googleapis.com/geolocation/v1/geolocate?key=$GOOGLE_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"considerIp": true}')

# Check for errors
if echo "$response" | grep -q "error"; then
    echo "❌ API Error:"
    echo "$response" | python3 -m json.tool
    echo ""
    
    error_code=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['error']['code'])" 2>/dev/null || echo "unknown")
    
    if [ "$error_code" = "403" ]; then
        echo "Possible causes:"
        echo "  - API key is invalid"
        echo "  - Geolocation API is not enabled"
        echo "  - Billing is not enabled on your Google Cloud project"
    elif [ "$error_code" = "429" ]; then
        echo "Rate limit exceeded. Try again later."
    fi
    
    exit 1
fi

# Parse and display location
lat=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['location']['lat'])" 2>/dev/null)
lng=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['location']['lng'])" 2>/dev/null)
acc=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('accuracy', 'N/A'))" 2>/dev/null)

if [ -n "$lat" ] && [ -n "$lng" ]; then
    echo "✅ Google Geolocation API is working!"
    echo ""
    echo "Your estimated location:"
    echo "  Latitude:  $lat"
    echo "  Longitude: $lng"
    echo "  Accuracy:  ±${acc}m"
    echo ""
    echo "🗺️  View on map: https://www.google.com/maps?q=${lat},${lng}"
    echo ""
    echo "Next steps:"
    echo "  1. Restart services: docker-compose restart serve"
    echo "  2. Check dashboard: http://localhost:8501"
    echo "  3. Run tests: pytest tests/unit/test_geo.py -v"
else
    echo "❌ Unexpected response format:"
    echo "$response" | python3 -m json.tool
    exit 1
fi
