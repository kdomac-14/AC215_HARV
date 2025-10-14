# GPS-Based Location Verification

## TL;DR - Yes, GPS is Supported! ✅

Your backend **already supports GPS-based location** verification. The dashboard now offers two methods:

1. **📱 GPS Mode** - Uses device's actual GPS (5-50m accuracy)
2. **🌐 IP Mode** - Uses internet connection (1-5km accuracy)

---

## How It Works

### Backend Support (Already Built)

`serve/src/app.py` lines 66-68:

```python
if inp.client_gps_lat is not None and inp.client_gps_lon is not None:
    lat, lon, acc = float(inp.client_gps_lat), float(inp.client_gps_lon), ...
    source = "client_gps"  # ← GPS mode!
```

**The API accepts GPS coordinates via these parameters:**
- `client_gps_lat` - Device latitude
- `client_gps_lon` - Device longitude  
- `client_gps_accuracy_m` - GPS accuracy in meters

### Frontend (Just Added)

The dashboard now has **GPS collection built-in**:

1. Student selects "📱 GPS (Accurate 5-50m)"
2. Clicks "Get GPS Location"
3. Browser requests permission
4. JavaScript collects coordinates using HTML5 Geolocation API
5. Streamlit sends coordinates to backend
6. Backend verifies distance with GPS precision

---

## Using GPS Verification

### In the Dashboard

1. Start services:
   ```bash
   docker-compose up -d
   ```

2. Open dashboard: http://localhost:8501

3. Toggle to **Student Mode**

4. Select **"📱 GPS (Accurate 5-50m)"**

5. Click **"📍 Get GPS Location"**
   - Browser will ask for permission
   - Allow location access

6. Click **"✅ Verify with GPS"**

### Via API Directly

```bash
# Verify with GPS coordinates
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{
    "client_gps_lat": 42.3770,
    "client_gps_lon": -71.1167,
    "client_gps_accuracy_m": 15.0
  }'

# Response shows source: "client_gps"
{
  "ok": true,
  "source": "client_gps",
  "distance_m": 12.5,
  "epsilon_m": 60.0,
  "estimated_lat": 42.3770,
  "estimated_lon": -71.1167
}
```

---

## GPS vs Google Geolocation API

### Important Distinction

| Method | What It Uses | When to Use |
|--------|-------------|-------------|
| **Device GPS** | Satellite signals | Student verification (most accurate) |
| **Google Geolocation API** | IP, WiFi, cell towers | Server-side estimation (fallback) |

### GPS (What You Asked About) ✅

- **Source:** Device's GPS hardware
- **Accuracy:** 5-50m outdoors, 50-500m indoors
- **Requires:** User permission, location-enabled device
- **Cost:** Free (uses device GPS)
- **Implementation:** `client_gps_lat/lon` parameters
- **Best for:** Verifying students are in the classroom

### Google Geolocation API (Different Thing)

- **Source:** Network data (IP, WiFi access points, cell towers)
- **Accuracy:** 1-5km (IP only) or 20-500m (with WiFi/cell data)
- **Requires:** Google API key, network connection
- **Cost:** Free tier: 40k requests/month
- **Implementation:** Server-side, no GPS needed
- **Best for:** Approximate location when GPS unavailable

---

## Which Should You Use?

### For Student Attendance Verification

**Use GPS Mode** (now available in dashboard):
- ✅ Most accurate (5-50m)
- ✅ Works on mobile devices
- ✅ Room-level precision
- ✅ Already implemented
- ⚠️ Requires student permission
- ⚠️ May not work indoors in some buildings

### For Testing/Fallback

**Use IP Mode**:
- ✅ No user permission needed
- ✅ Works everywhere
- ✅ Quick setup
- ⚠️ City-level accuracy only (1-5km)
- ⚠️ Not suitable for classroom verification

---

## Accuracy Comparison

### GPS Mode (Device Location)
```
📍 GPS Signal
└── Device
    └── Satellites (5-50m accuracy)
    └── Backend receives: client_gps_lat, client_gps_lon
    └── Result: "source": "client_gps"
```

**Typical Accuracy:**
- Outdoors: ±5-20m
- Indoors near windows: ±20-50m
- Indoors deep: ±50-500m
- With WiFi assist: ±10-30m

### IP Mode (Network-based)
```
🌐 Network Signal
└── Server
    ├── IP address → City location (1-5km)
    ├── WiFi APs → Neighborhood (100-500m) [requires Google API]
    └── Cell towers → Block (50-200m) [requires Google API]
    └── Backend receives: IP address only
    └── Result: "source": "ip_geo"
```

**Typical Accuracy:**
- IP-only (ip-api.com): ±1-50km
- IP-only (Google API): ±1-5km
- WiFi-based (Google API): ±100-500m*
- Cell-based (Google API): ±50-200m*

*Requires client to send WiFi/cell data to Google API (not just IP)

---

## Production Deployment

### For Best Accuracy (Recommended)

Build a **mobile app** that automatically collects GPS:

```javascript
// React Native / Flutter example
import Geolocation from '@react-native-community/geolocation';

Geolocation.getCurrentPosition(
  (position) => {
    fetch('https://your-api.com/geo/verify', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        client_gps_lat: position.coords.latitude,
        client_gps_lon: position.coords.longitude,
        client_gps_accuracy_m: position.coords.accuracy
      })
    });
  },
  (error) => console.error(error),
  {enableHighAccuracy: true, timeout: 10000}
);
```

### Web Browser (Current Dashboard)

The dashboard uses HTML5 Geolocation API:
- ✅ Works on modern browsers
- ✅ Works on mobile web browsers
- ⚠️ Requires HTTPS in production
- ⚠️ User must grant permission each time (unless remembered)

---

## Troubleshooting GPS

### Browser Doesn't Ask for Permission

**Cause:** Site served over HTTP (not HTTPS)

**Fix:** 
- For local testing: Use `localhost` (browser allows HTTP for localhost)
- For production: Deploy with HTTPS (required for geolocation)

### GPS Always Fails

**Possible causes:**
1. **No GPS hardware** - Desktop computers without GPS chips
2. **Location disabled** - Check device settings
3. **Indoor location** - Move near a window
4. **Permission denied** - Check browser settings

**Solutions:**
- Use the "enter coordinates manually" fallback
- Test on a mobile device
- Check browser console for errors

### Inaccurate GPS

**Cause:** Weak GPS signal or indoor location

**Fix:**
- Adjust `GEO_EPSILON_M` to account for indoor GPS drift
- For indoors: Set epsilon to 100-200m
- For outdoors: Set epsilon to 50-100m

---

## Configuration

### Adjust Tolerance for GPS

```bash
# .env file
GEO_EPSILON_M=100  # 100m radius for GPS mode
```

**Recommended values:**
- **Outdoor classroom:** 50m
- **Indoor classroom:** 100-200m
- **Campus-wide:** 500-1000m
- **Testing:** 5000m

### Force GPS-Only Mode

Modify dashboard to hide IP option if desired (already supports both).

---

## Testing GPS

### Quick Test

1. Open dashboard on your phone
2. Connect to same network as server (or use public IP)
3. Select GPS mode
4. Click "Get GPS Location"
5. Allow permission
6. Verify

### API Test

```bash
# Get your current GPS coordinates
# On Mac: Safari → Develop → Show JavaScript Console
# Run: navigator.geolocation.getCurrentPosition(p => console.log(p.coords))

# Then test API
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{
    "client_gps_lat": YOUR_LAT,
    "client_gps_lon": YOUR_LON,
    "client_gps_accuracy_m": 20
  }'
```

---

## Summary

✅ **GPS-based location IS supported and working**

✅ **Dashboard has GPS collection built-in**

✅ **Backend accepts GPS coordinates via API**

✅ **Much more accurate than IP-based (5-50m vs 1-5km)**

⚠️ **Requires user permission and location-enabled device**

📱 **For production: Build mobile app for seamless GPS collection**

---

## Files

- **Backend API:** `serve/src/app.py` (already supports GPS)
- **Dashboard:** `dashboard/app/app.py` (GPS collection added)
- **Standalone HTML:** `dashboard/app/gps_verify.html` (alternative GPS page)
- **This guide:** `docs/gps_location_guide.md`
