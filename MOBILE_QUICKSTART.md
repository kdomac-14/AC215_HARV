# HARV Mobile App - Quick Start Guide

## What's New?

The HARV mobile app brings attendance verification to iOS and Android with enhanced features:

### ✨ Professor Mode
- 📍 GPS-based classroom location setup
- 📸 5-angle room photo capture (corners + center)
- 🔑 Auto-generated secret word for manual overrides
- 📝 Easy class profile creation

### ✨ Student Mode
- 📱 Camera-based check-in (no uploads, real-time capture)
- 🌍 Dual verification: GPS + Visual recognition
- ✅ Instant feedback on attendance status
- 🔓 Manual override option with professor's secret word

## Installation

### 1. Backend Setup

Ensure HARV backend is running with mobile support:

```bash
# From project root
docker compose up --build serve
```

The backend now includes new endpoints for mobile app features.

### 2. Mobile App Setup

```bash
# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your backend URL
# For local development:
#   iOS: API_URL=http://localhost:8000
#   Android: API_URL=http://10.0.2.2:8000
#   Physical device: API_URL=http://YOUR_IP:8000

# Start development server
npm start
```

### 3. Run on Device

**Option A: iOS Simulator (Mac only)**
```bash
npm run ios
```

**Option B: Android Emulator**
```bash
npm run android
```

**Option C: Physical Device (Recommended for camera/GPS)**
1. Install Expo Go app from App Store / Play Store
2. Scan QR code from terminal
3. App launches on your device

## Usage

### For Professors

1. **Open App** → Tap "Professor Mode"
2. **Create Class**:
   - Tap "+ Create New Class"
   - Enter class name (e.g., "CS50 - Intro to CS")
   - Auto-generated code (share with students)
   - Auto-generated secret word (keep private)
3. **Set Location**:
   - Tap "Get Current Location" (or enter manually)
   - Set acceptable radius (default 60m)
4. **Take Room Photos**:
   - Take photo from front-left corner
   - Take photo from front-right corner
   - Take photo from back-left corner
   - Take photo from back-right corner
   - Take photo from center facing screen
5. **Submit** → Class created!

### For Students

1. **Open App** → Tap "Student Mode"
2. **Enroll**:
   - Tap "+ Browse & Enroll in Classes"
   - Enter your student ID
   - Find your class and tap "Enroll"
3. **Check In** (when in classroom):
   - Go to "My Classes"
   - Tap class name
   - Tap "📸 Check In"
   - Grant camera and location permissions
   - Point camera at lecture screen or distinctive feature
   - Tap capture button
   - Wait for verification...
   
4. **Result**:
   - ✅ **Success**: Attendance recorded!
   - ❌ **Failed**: 
     - Check GPS accuracy
     - Ensure you're in correct room
     - Option: Request manual override from professor

5. **Manual Override** (if needed):
   - Approach professor after class
   - Professor gives you the secret word verbally
   - In app, enter secret word
   - Attendance marked

## Verification Process

The app uses **dual verification**:

```
Student taps "Check In"
         ↓
1. GPS Verification
   - Device gets current location
   - Calculates distance to classroom
   - ✓ Pass if within epsilon (e.g., 60m)
   - ✗ Fail if too far
         ↓
2. Visual Verification
   - Camera captures classroom photo
   - ML model analyzes image
   - Compares to reference photos
   - ✓ Pass if confidence > 50%
   - ✗ Fail if wrong room/low confidence
         ↓
✅ BOTH PASS → Attendance recorded
❌ EITHER FAILS → Manual override option
```

## Architecture

```
Mobile App (React Native + Expo)
         ↓
    API Client (Axios)
         ↓
Backend API (FastAPI)
    ├── /professor/classes (POST, GET)
    ├── /student/classes (GET)
    ├── /student/enroll (POST)
    ├── /student/checkin (POST)
    └── /student/manual-override (POST)
         ↓
   Database (JSON files)
    ├── classes.json
    ├── enrollments.json
    └── checkins.json
```

## Features Comparison

| Feature | Web Dashboard | Mobile App |
|---------|--------------|------------|
| Image Upload | ✅ | ❌ (Camera only) |
| Real-time Camera | ❌ | ✅ |
| GPS Verification | ⚠️ (IP-based) | ✅ (Native GPS) |
| Class Management | ✅ | ✅ |
| Room Photos | ❌ | ✅ (5 angles) |
| Manual Override | ❌ | ✅ (Secret word) |
| Student Enrollment | ❌ | ✅ |
| Check-in History | ⚠️ Limited | ✅ Full history |

## Troubleshooting

### "Cannot connect to backend"

**Problem**: Mobile app can't reach API

**Solutions**:
1. Ensure backend is running: `docker compose up serve`
2. Check API_URL in `.env`:
   - iOS Simulator: `http://localhost:8000`
   - Android Emulator: `http://10.0.2.2:8000`
   - Physical device: `http://YOUR_COMPUTER_IP:8000`
3. Verify firewall allows connections on port 8000

### "Camera not working"

**Problem**: Camera doesn't open or shows black screen

**Solutions**:
1. Use physical device (camera doesn't work on simulators)
2. Grant camera permissions when prompted
3. Check Settings → HARV → Permissions → Camera = Enabled

### "Location verification failed"

**Problem**: GPS shows incorrect location or "too far"

**Solutions**:
1. Enable location services (Settings → Privacy → Location)
2. Ensure high accuracy mode enabled
3. Wait for GPS to acquire satellites (works better near windows)
4. Use manual override if GPS unavailable

### "Recognition failed"

**Problem**: ML model doesn't recognize classroom

**Solutions**:
1. Point camera at distinctive features (projection screen, whiteboard)
2. Ensure good lighting
3. Hold camera steady for clear photo
4. If persistent, use manual override

## Next Steps

### Production Deployment

**Mobile App:**
```bash
# iOS
npx eas build --platform ios --profile production

# Android
npx eas build --platform android --profile production
```

**Backend:**
- Deploy to Cloud Run (see `../DEPLOYMENT.md`)
- Update API_URL in mobile app to production URL
- Configure CORS for mobile app domain

### Database Migration

For production, replace JSON files with PostgreSQL:
1. Create PostgreSQL database
2. Define schema (see `docs/MOBILE_APP.md`)
3. Update `serve/src/database.py` with SQL queries
4. Migrate existing data

## Documentation

- **Mobile App README**: `frontend/README.md` - Detailed mobile app docs
- **Mobile Features**: `docs/MOBILE_APP.md` - Architecture and API reference
- **Main README**: `README.md` - Full HARV documentation
- **Backend API**: `serve/src/app.py` - API endpoint definitions

## Support

For issues:
1. Check `frontend/README.md` troubleshooting section
2. Review logs: Shake device → "Show Developer Menu" → "Debug"
3. Backend logs: `docker compose logs serve`
4. Open GitHub issue with:
   - Platform (iOS/Android)
   - Error message
   - Steps to reproduce

---

**Built with:**
- React Native + Expo
- TypeScript
- Expo Camera, Location, Image Picker
- Zustand (state management)
- Axios (HTTP client)

**Backend powered by:**
- FastAPI
- PyTorch (ML inference)
- OpenCV (image processing)
- Custom geolocation verification
