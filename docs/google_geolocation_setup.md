# Google Geolocation API Setup Guide

This guide explains how to configure Google's Geolocation API for more accurate location verification in the HLAB system.

## Why Use Google Geolocation API?

| Provider | Method | Accuracy | Cost |
|----------|--------|----------|------|
| **ip-api.com** (default) | IP address lookup | City-level (1-50km) | Free |
| **Google Geolocation API** | IP + WiFi/cell towers | 20m - 1km | $5 per 1000 requests |

**IMPORTANT:** Even with Google API, accuracy depends on what data the client sends:
- **Server-side (current):** Uses only IP address (~1-5km accuracy)
- **Client-side (production):** Mobile app sends WiFi/cell data (20-100m accuracy)

## Setup Steps

### 1. Get a Google Cloud API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Geolocation API**:
   - Navigate to **APIs & Services** → **Library**
   - Search for "Geolocation API"
   - Click **Enable**

4. Create API credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **API Key**
   - Copy the generated key

5. **(Recommended)** Restrict the API key:
   - Click **Edit API Key**
   - Under **API restrictions**, select "Restrict key"
   - Choose "Geolocation API"
   - Under **Application restrictions**, add your server IP or domain

### 2. Configure Your `.env` File

Add your API key to `.env`:

```bash
# Geolocation-first Auth (Phase 0)
GOOGLE_API_KEY=AIzaSyD...your-key-here
GEO_PROVIDER=google
GEO_EPSILON_M=60
TRUST_X_FORWARDED_FOR=true
```

**Environment Variables:**
- `GOOGLE_API_KEY`: Your Google Cloud API key
- `GEO_PROVIDER`: `google` (use Google), `ipapi` (fallback), `mock` (testing), or `auto` (use Google if key exists)
- `GEO_EPSILON_M`: Allowed radius in meters from classroom center
- `TRUST_X_FORWARDED_FOR`: Trust `X-Forwarded-For` header (needed for Docker/proxies)

### 3. Restart Services

```bash
docker-compose down
docker-compose up -d
```

### 4. Verify Setup

Run the integration tests:

```bash
# Test unit tests (mocked)
pytest tests/unit/test_geo.py -v

# Test Google API integration (requires real key)
pytest tests/integration/test_google_api.py -v
```

Or check manually:

```bash
# Check which provider is active
curl http://localhost:8000/healthz

# Should show: "geo_provider": "GoogleGeo"
```

## Testing the Setup

### Quick Test in Dashboard

1. Open dashboard: http://localhost:8501
2. Toggle to **Student Mode**
3. Look for the provider message:
   - ✅ "Using **Google Geolocation API**" - configured correctly
   - ⚠️ "Using **IP-based geolocation**" - API key missing/invalid

4. Click **Verify My Location**
5. Check the response `source` field:
   - `"source": "ip_geo"` = Using geolocation (Google or ip-api)

### Manual API Test

Test Google API directly:

```bash
# Replace YOUR_API_KEY with your actual key
curl -X POST \
  "https://www.googleapis.com/geolocation/v1/geolocate?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"considerIp": true}'
```

Expected response:
```json
{
  "location": {
    "lat": 42.3601,
    "lng": -71.0942
  },
  "accuracy": 1500.0
}
```

## Troubleshooting

### Error: "API key not valid"

**Cause:** Invalid API key or Geolocation API not enabled

**Fix:**
1. Verify the API key in Google Cloud Console
2. Check that Geolocation API is enabled
3. Wait a few minutes for changes to propagate

### Still Using IpApi Despite Setting Key

**Cause:** Environment variable not loaded or service not restarted

**Fix:**
```bash
# Check environment inside container
docker-compose exec serve env | grep GOOGLE_API_KEY

# Restart services
docker-compose restart serve
```

### Location Still Inaccurate with Google API

**Expected:** Google API with only IP address is still city-level accuracy (1-5km)

**Why:** The server doesn't have access to WiFi/cell tower data

**Solutions:**
1. **For testing:** Use `GEO_EPSILON_M=5000` (5km tolerance)
2. **For production:** Build a mobile app that sends WiFi/cell data to the API

**How production works:**
```javascript
// Mobile app collects WiFi data
navigator.geolocation.getCurrentPosition((position) => {
  // Send to backend
  fetch('/geo/verify', {
    method: 'POST',
    body: JSON.stringify({
      client_gps_lat: position.coords.latitude,
      client_gps_lon: position.coords.longitude,
      client_gps_accuracy_m: position.coords.accuracy
    })
  });
});
```

## Cost Management

- **Free tier:** First 40,000 requests/month are free
- **After free tier:** $5 per 1,000 requests
- **Average classroom:** ~30 students × 2 checks/day × 30 days = 1,800 requests/month (well within free tier)

**Set up billing alerts:**
1. Go to Google Cloud Console → Billing
2. Create a budget alert for $5
3. Set up quota limits in APIs & Services

## Limitations

### Current Implementation (Server-side)
- **Accuracy:** 1-5km (IP-based)
- **Use case:** Verify student is in the same city/campus
- **Not suitable for:** Room-level verification

### Production Implementation (Client-side)
- **Accuracy:** 20-100m (WiFi/cell towers)
- **Use case:** Verify student is in the same building
- **Requires:** Mobile app or browser with location permissions

## Next Steps

1. ✅ Set up Google API key
2. ✅ Run integration tests
3. ⚠️ Adjust `GEO_EPSILON_M` based on your accuracy needs:
   - Testing with IP-based: 3000-5000m
   - Production with GPS: 50-200m
4. 🚀 For production: Build mobile app that sends GPS/WiFi data

## Resources

- [Google Geolocation API Docs](https://developers.google.com/maps/documentation/geolocation/overview)
- [API Pricing](https://developers.google.com/maps/billing-and-pricing/pricing#geolocation)
- [Best Practices](https://developers.google.com/maps/documentation/geolocation/best-practices)
