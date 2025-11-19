# HARV Mobile App Documentation

## Overview

The HARV mobile app extends the attendance verification system to iOS and Android devices with enhanced Professor and Student modes.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile App (React Native)             │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐              ┌──────────────┐         │
│  │  Professor   │              │   Student    │         │
│  │    Mode      │              │    Mode      │         │
│  │              │              │              │         │
│  │ • Create     │              │ • Browse     │         │
│  │   Classes    │              │   Classes    │         │
│  │ • Take       │              │ • Enroll     │         │
│  │   Photos     │              │ • Check In   │         │
│  │ • Generate   │              │ • Camera     │         │
│  │   Secret     │              │   Scan       │         │
│  └──────┬───────┘              └──────┬───────┘         │
│         │                             │                  │
│         └────────────┬────────────────┘                 │
│                      │                                    │
│              ┌───────▼────────┐                          │
│              │   API Client    │                          │
│              │    (Axios)      │                          │
│              └───────┬────────┘                          │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │     HARV Backend API         │
        │    (FastAPI + Database)      │
        │                               │
        │  • Class Management          │
        │  • Enrollment                │
        │  • Geo Verification          │
        │  • Vision Recognition        │
        │  • Manual Override           │
        └──────────────────────────────┘
```

## Professor Mode Enhancements

### 1. Geolocation Parameters

**Current Implementation:**
- Latitude and longitude input

**New Features:**
- Auto-capture current location via GPS
- Manual coordinate entry option
- Adjustable epsilon (acceptable distance in meters)
- Default: 60m radius

```typescript
interface ClassLocation {
  lat: number;
  lon: number;
  epsilon_m: number;
}
```

### 2. Room Photo Attachments

**Requirements:**
Capture 5 photos from strategic positions:

1. **Front Left Corner** - View of lecture hall from front-left
2. **Front Right Corner** - View of lecture hall from front-right
3. **Back Left Corner** - View from rear of classroom
4. **Back Right Corner** - View from opposite rear corner
5. **Center (Facing Screen)** - Direct view of projection screen/whiteboard

**Purpose:**
- Provides comprehensive visual reference of classroom
- Helps ML model learn room features from multiple angles
- Validates student is actually in correct physical space

**Technical Details:**
- Images captured using `expo-camera` or `expo-image-picker`
- Converted to base64 for API transmission
- Stored with class profile in database
- Quality: 0.7 compression for balance between size and detail

### 3. Class Profile Link

**Implementation:**
Each class has a unique code (e.g., `AB12CD`) that acts as:
- Join/enrollment code
- Reference in check-in process
- Shareable identifier (similar to Gradescope)

**Workflow:**
```
Professor creates class
    ↓
Auto-generated code: "AB12CD"
    ↓
Professor shares code with students
    ↓
Students enroll using code
    ↓
Code links to class profile with:
  - Location coordinates
  - Room photos
  - Secret word
  - Enrolled students
```

### 4. Secret Word Generation

**Purpose:**
Manual override when automatic verification fails

**Features:**
- Auto-generated on class creation
- Format: `{adjective}{number}` (e.g., `crimson842`)
- Displayed only to professor
- Never shown to students unless needed
- Used for emergency check-ins

## Student Mode Enhancements

### 1. Camera Scanning (Not Upload)

**Previous:** Image upload from gallery
**New:** Real-time camera capture

**Implementation:**
```typescript
<CameraView
  ref={cameraRef}
  style={styles.camera}
  facing="back"
>
  {/* Camera controls */}
</CameraView>
```

**Benefits:**
- Prevents photo reuse/fraud
- Ensures student is physically present
- Captures current timestamp
- Better user experience

**Fallback:**
If camera unavailable (permissions denied), force in-app photo capture using `expo-image-picker` with camera option only.

### 2. Check-In Flow

```
1. Student opens app → Student Mode
2. Selects class from "My Classes"
3. Taps "Check In" button
4. Camera opens automatically
5. Point at classroom (lecture screen/distinctive feature)
6. Tap capture button
7. App processes:
   a. GPS location check
   b. Image recognition
8. Result displayed:
   ✅ Success - Attendance recorded
   ❌ Failure - Manual override option
```

### 3. Dual Verification System

**Phase 1: Geolocation**
```typescript
// Get GPS coordinates
const location = await Location.getCurrentPositionAsync();

// Calculate distance from classroom
const distance = haversine(
  classLocation,
  userLocation
);

// Verify within epsilon
if (distance <= class.epsilon_m) {
  // Pass to Phase 2
} else {
  // Fail: Too far from classroom
}
```

**Phase 2: Visual Recognition**
```typescript
// Send photo to ML model
const result = await api.checkIn({
  class_code: "AB12CD",
  student_id: "12345",
  image_b64: base64Photo,
  lat: location.latitude,
  lon: location.longitude,
});

// Model predicts classroom
if (result.confidence > 0.5 && result.label === expectedRoom) {
  // Success!
} else {
  // Fail: Wrong room or low confidence
}
```

### 4. Manual Override Process

**Trigger Conditions:**
- Geolocation fails (GPS inaccurate, wrong location)
- Vision recognition fails (low confidence, wrong room)
- Technical issues (camera malfunction, network error)

**Workflow:**
```
Check-in fails
    ↓
App shows: "Check-in failed. Need manual override?"
    ↓
Student approaches professor after class
    ↓
Professor verbally gives secret word
    ↓
Student enters secret word in app
    ↓
Backend verifies secret word
    ↓
Attendance marked (with "manual_override" flag)
```

**Security:**
- Secret word never displayed in student app
- Changes per class
- Professor can regenerate if compromised
- Manual overrides logged separately for auditing

## API Endpoints

### Professor

```http
POST /professor/classes
Content-Type: application/json

{
  "name": "CS50 - Intro to CS",
  "code": "CS50F23",
  "lat": 42.3770,
  "lon": -71.1167,
  "epsilon_m": 60,
  "secret_word": "crimson842",
  "room_photos": ["base64_1", "base64_2", ...],
  "professor_id": "prof_123"
}

Response: {
  "ok": true,
  "class": { ... }
}
```

### Student

```http
POST /student/enroll
Content-Type: application/json

{
  "class_code": "CS50F23",
  "student_id": "student_456"
}

POST /student/checkin
{
  "class_code": "CS50F23",
  "student_id": "student_456",
  "image_b64": "base64_photo",
  "lat": 42.3771,
  "lon": -71.1168,
  "accuracy_m": 15
}

Response (Success): {
  "ok": true,
  "distance_m": 12.5,
  "label": "Science_Center_B",
  "confidence": 0.87
}

Response (Failure): {
  "ok": false,
  "reason": "location_failed",
  "distance_m": 125.3,
  "needs_manual_override": true
}

POST /student/manual-override
{
  "class_code": "CS50F23",
  "student_id": "student_456",
  "secret_word": "crimson842"
}
```

## Database Schema

### Classes Table
```json
{
  "id": "cls_abc123",
  "name": "CS50 - Intro to CS",
  "code": "CS50F23",
  "lat": 42.3770,
  "lon": -71.1167,
  "epsilon_m": 60,
  "secret_word": "crimson842",
  "room_photos": ["base64_1", ...],
  "professor_id": "prof_123",
  "professor_name": "David Malan",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Enrollments Table
```json
{
  "id": "enr_xyz789",
  "class_code": "CS50F23",
  "student_id": "student_456",
  "enrolled_at": "2024-01-20T14:30:00Z"
}
```

### Check-ins Table
```json
{
  "id": "chk_def456",
  "class_code": "CS50F23",
  "student_id": "student_456",
  "success": true,
  "method": "auto",  // or "manual_override"
  "geo_verified": true,
  "vision_verified": true,
  "distance_m": 12.5,
  "label": "Science_Center_B",
  "confidence": 0.87,
  "timestamp": "2024-01-22T15:45:00Z"
}
```

## Security Considerations

1. **Secret Word Protection**
   - Never exposed in API responses to students
   - Only accessible to professor who created class
   - Hashed storage recommended for production

2. **Photo Privacy**
   - Room photos contain no student faces
   - Only architectural features
   - Stored securely, not publicly accessible

3. **Location Privacy**
   - GPS coordinates only used for verification
   - Not stored long-term
   - Accuracy radius disclosed to students

4. **Fraud Prevention**
   - Camera-only check-in prevents photo reuse
   - Timestamp verification
   - IP address logging
   - Manual overrides audited

## Deployment

### Mobile App

**iOS:**
```bash
cd mobile
npx eas build --platform ios
```

**Android:**
```bash
npx eas build --platform android
```

### Backend Updates

Update `serve/` container to include new endpoints:
```bash
docker compose up --build serve
```

## Testing

### Unit Tests
```bash
cd mobile
npm test
```

### E2E Tests
- Test on physical devices (iOS and Android)
- Verify camera permissions
- Test GPS accuracy
- Validate manual override flow

### Backend Tests
```python
# Test class creation
def test_create_class():
    response = client.post("/professor/classes", json={...})
    assert response.status_code == 200

# Test check-in
def test_student_checkin():
    response = client.post("/student/checkin", json={...})
    assert response.status_code == 200
```

## Future Enhancements

1. **Push Notifications**
   - Remind students to check in
   - Alert professors of check-in issues

2. **Offline Mode**
   - Cache check-ins when network unavailable
   - Sync when connection restored

3. **Analytics Dashboard**
   - Attendance trends
   - Check-in success rates
   - Common failure reasons

4. **Multi-factor Verification**
   - Bluetooth beacon detection
   - WiFi SSID verification
   - Combine with existing geo + vision

## Troubleshooting

See `mobile/README.md` for common issues and solutions.

## References

- Main README: `../README.md`
- Architecture: `./ARCHITECTURE.md`
- API Documentation: `./API.md` (if exists)
- Deployment Guide: `../DEPLOYMENT.md`
