# Google Geolocation API - Setup Complete ✅

## Summary

The dashboard and geolocation system have been updated to:

1. **Simplified student UI** - One-click "Verify My Location" button (no manual coordinates needed)
2. **Google API support** - Better accuracy when configured
3. **Comprehensive tests** - Unit and integration tests for all providers
4. **Clear provider feedback** - Dashboard shows which provider is active

---

## Quick Start

### 1. Add Google API Key (Optional but Recommended)

**Without API key:** Uses ip-api.com (city-level accuracy, ~1-50km off)  
**With API key:** Uses Google API (better accuracy, ~1-5km with IP only)

```bash
# Copy example env file if you haven't already
cp .env.example .env

# Edit .env and add your Google API key:
# GOOGLE_API_KEY=AIzaSyD...your-key-here

# Test the API key works
./scripts/test_google_api.sh
```

**Get an API key:**
1. Visit https://console.cloud.google.com/apis/credentials
2. Create a new project
3. Enable "Geolocation API"
4. Create credentials → API Key
5. Add to `.env`

### 2. Restart Services

```bash
docker-compose restart serve dashboard
```

### 3. Test It

```bash
# Run all geo tests
pytest tests/unit/test_geo.py -v

# Run integration tests (requires API running)
pytest tests/integration/test_google_api.py -v
```

Or test manually in dashboard: http://localhost:8501

---

## How It Works Now

### Student Experience (Simplified)

1. Open dashboard → Toggle to **Student Mode**
2. See provider status:
   - ✅ "Using **Google Geolocation API**" - accurate
   - ⚠️ "Using **IP-based geolocation**" - less accurate (add API key)
3. Click **"Verify My Location"** button
4. System auto-detects location and verifies distance

**No manual coordinate entry needed!**

### Provider Selection Logic

The system automatically picks the best provider:

```python
if GOOGLE_API_KEY is set:
    → Use GoogleGeo (most accurate)
else:
    → Fallback to IpApi (free but less accurate)
```

Set `GEO_PROVIDER=mock` in `.env` for testing (returns Harvard Yard coordinates).

---

## Understanding `source: ip_geo`

**Q: Does `source: ip_geo` mean I'm using Google API?**

**A: No.** The `source` field tells you **what data was used**, not which provider:

| Source | Meaning | Provider |
|--------|---------|----------|
| `ip_geo` | Server used IP address | GoogleGeo OR IpApi |
| `client_gps` | Client sent GPS coords | N/A (direct from device) |

To see **which provider** is active, check:
```bash
curl http://localhost:8000/healthz
# Returns: "geo_provider": "GoogleGeo" or "IpApi"
```

Or look at the dashboard - it shows the provider name.

---

## Accuracy Explained

### Current Implementation (IP-based)

| Provider | Data Used | Accuracy | Cost |
|----------|-----------|----------|------|
| **ip-api.com** | IP address | 1-50km | Free |
| **Google API** | IP address | 1-5km | Free (40k/mo) |

**Both are still IP-based!** Even Google API needs WiFi/cell data for better accuracy.

### Production Implementation (GPS-based)

For **room-level accuracy** (20-100m), you need a mobile app that sends:
- GPS coordinates
- WiFi access points
- Cell tower IDs

```javascript
// Example mobile app code
navigator.geolocation.getCurrentPosition((pos) => {
  fetch('/geo/verify', {
    method: 'POST',
    body: JSON.stringify({
      client_gps_lat: pos.coords.latitude,
      client_gps_lon: pos.coords.longitude,
      client_gps_accuracy_m: pos.coords.accuracy
    })
  });
});
```

This backend **already supports** client GPS via the `client_gps_*` parameters!

---

## Adjusting Tolerance

Edit `GEO_EPSILON_M` in `.env` based on your provider:

```bash
# For IP-based geolocation (current)
GEO_EPSILON_M=5000  # 5km tolerance

# For future GPS-based (with mobile app)
GEO_EPSILON_M=100   # 100m tolerance
```

Professor can also adjust this in the dashboard calibration UI.

---

## Testing

### Unit Tests (All Passing ✅)

```bash
pytest tests/unit/test_geo.py -v

# Tests:
# ✓ Haversine distance calculation
# ✓ Google API response handling
# ✓ IP-API fallback
# ✓ Provider selection logic
# ✓ Mock provider for testing
```

### Integration Tests (Requires Services Running)

```bash
# Start services
docker-compose up -d

# Test Google API (requires GOOGLE_API_KEY)
pytest tests/integration/test_google_api.py -v

# Tests:
# ✓ Google API key configuration
# ✓ Real API calls
# ✓ Provider endpoint verification
# ✓ Full geo verify flow
```

### Manual Testing

```bash
# Test Google API directly
./scripts/test_google_api.sh

# Check provider status
curl http://localhost:8000/healthz | jq .geo_provider

# Calibrate classroom
curl -X POST http://localhost:8000/geo/calibrate \
  -H "Content-Type: application/json" \
  -d '{"lat": 42.3770, "lon": -71.1167, "epsilon_m": 5000}'

# Verify location
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Files Changed

### Dashboard
- `dashboard/app/app.py` - Simplified UI, auto-detect provider, better feedback

### Backend
- `serve/src/geo.py` - Fixed directory creation for testing outside Docker

### Tests
- `tests/unit/test_geo.py` - Added comprehensive provider tests
- `tests/integration/test_google_api.py` - New integration tests

### Documentation
- `.env.example` - Better comments and defaults
- `docs/google_geolocation_setup.md` - Full setup guide
- `scripts/test_google_api.sh` - Quick API verification script

---

## Next Steps

### For Testing (Now)
1. ✅ Set `GOOGLE_API_KEY` in `.env`
2. ✅ Run `./scripts/test_google_api.sh`
3. ✅ Set `GEO_EPSILON_M=5000` for IP-based tolerance
4. ✅ Test in dashboard

### For Production (Future)
1. Build mobile app (React Native/Flutter)
2. Implement HTML5 Geolocation API
3. Send GPS + WiFi data to `/geo/verify` endpoint
4. Reduce `GEO_EPSILON_M` to 50-200m
5. Set up billing alerts in Google Cloud

---

## Troubleshooting

### Still seeing IP-based warnings?

1. Check API key is in `.env`:
   ```bash
   grep GOOGLE_API_KEY .env
   ```

2. Restart services:
   ```bash
   docker-compose restart serve
   ```

3. Verify inside container:
   ```bash
   docker-compose exec serve env | grep GOOGLE_API_KEY
   ```

### Verification always fails?

**Increase tolerance:** Set `GEO_EPSILON_M=5000` (5km) for IP-based testing

### API key invalid?

Run `./scripts/test_google_api.sh` to see detailed error message

---

## Reference

- **Setup Guide:** `docs/google_geolocation_setup.md`
- **Test Script:** `scripts/test_google_api.sh`
- **Unit Tests:** `tests/unit/test_geo.py`
- **Integration Tests:** `tests/integration/test_google_api.py`
