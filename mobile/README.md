# HARV Mobile App

React Native mobile application for HARV (Harvard Attendance Recognition and Verification) with Professor and Student modes.

## Features

### Professor Mode
- **Class Creation**: Set up new classes with geolocation parameters
- **Room Photo Attachments**: Capture 5 reference photos from different angles:
  - Front Left Corner
  - Front Right Corner
  - Back Left Corner
  - Back Right Corner
  - Center (facing lecture screen)
- **Secret Word Generation**: Auto-generated secret word for manual attendance override
- **Class Management**: View all created classes

### Student Mode
- **Class Enrollment**: Browse and enroll in available classes
- **Camera-Based Check-In**: Scan classroom using device camera
- **Dual Verification**:
  1. GPS/Location verification (must be within acceptable radius)
  2. Visual verification (ML model recognizes classroom)
- **Manual Override**: Use professor's secret word if automatic check-in fails
- **Check-In History**: View attendance record

## Prerequisites

- Node.js 18+ and npm
- Expo CLI: `npm install -g expo-cli`
- iOS Simulator (Mac) or Android Emulator
- Physical device for testing camera and GPS features

## Quick Start

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure Backend URL

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```
API_URL=http://your-backend-url:8000
# For local development on iOS Simulator:
# API_URL=http://localhost:8000
# For Android Emulator:
# API_URL=http://10.0.2.2:8000
```

### 3. Start Development Server

```bash
npm start
```

This opens Expo Developer Tools. Choose your platform:
- Press `i` for iOS Simulator
- Press `a` for Android Emulator
- Scan QR code with Expo Go app on physical device

## Development

### Project Structure

```
mobile/
├── app/                      # Expo Router pages
│   ├── _layout.tsx          # Root layout with navigation
│   ├── index.tsx            # Home screen (mode selection)
│   ├── professor/           # Professor mode screens
│   │   ├── index.tsx       # Professor dashboard
│   │   └── create-class.tsx # Class creation with photos
│   └── student/             # Student mode screens
│       ├── index.tsx        # Student dashboard
│       ├── class-list.tsx   # Browse/enroll in classes
│       └── check-in.tsx     # Camera-based check-in
├── utils/
│   ├── api.ts               # Backend API client
│   └── store.ts             # Global state management (Zustand)
├── app.json                 # Expo configuration
├── package.json             # Dependencies
└── tsconfig.json            # TypeScript config
```

### Key Technologies

- **Expo**: React Native framework with managed workflow
- **Expo Router**: File-based navigation
- **Expo Camera**: Camera access for check-in
- **Expo Location**: GPS coordinates
- **Expo Image Picker**: Photo capture for room photos
- **Zustand**: Lightweight state management
- **Axios**: HTTP client for API calls

### Testing on Physical Device

Camera and GPS features require physical devices:

#### iOS
1. Install Expo Go from App Store
2. Ensure iPhone and Mac are on same network
3. Scan QR code from terminal

#### Android
1. Install Expo Go from Play Store
2. Scan QR code from terminal
3. Or use `npx expo start --tunnel` for remote access

## API Integration

The mobile app communicates with the HARV backend API:

### Professor Endpoints
- `POST /professor/classes` - Create new class
- `GET /professor/classes/{professor_id}` - Get professor's classes

### Student Endpoints
- `GET /student/classes` - Browse available classes
- `POST /student/enroll` - Enroll in class
- `GET /student/classes/{student_id}` - Get enrolled classes
- `POST /student/checkin` - Check in with photo + GPS
- `POST /student/manual-override` - Manual check-in with secret word

### Geolocation
- `POST /geo/calibrate` - Set classroom location
- `GET /geo/status` - Get current calibration
- `POST /geo/verify` - Verify location

## Workflows

### Professor: Create a Class

1. Tap "Professor Mode" on home screen
2. Tap "+ Create New Class"
3. Enter class name (e.g., "CS50 - Introduction to Computer Science")
4. Auto-generated class code and secret word are displayed
5. Tap "Get Current Location" to set classroom coordinates
6. Set acceptable distance radius (default 60m)
7. Take 5 photos from different angles in the classroom
8. Tap "Create Class"

### Student: Check In

1. Tap "Student Mode" on home screen
2. Browse available classes or view "My Classes"
3. Enroll in a class (if not already enrolled)
4. When in classroom, tap "📸 Check In"
5. Grant camera and location permissions
6. Point camera at classroom (lecture screen or distinctive feature)
7. Tap capture button
8. App verifies:
   - GPS location (must be within radius)
   - Visual recognition (ML model confirms classroom)
9. Success: ✅ Check-in complete
10. Failure: Option to use manual override with secret word

## Building for Production

### iOS

```bash
# Create iOS build
npx expo build:ios

# Or use EAS Build (recommended)
npx eas build --platform ios
```

### Android

```bash
# Create Android APK
npx expo build:android

# Or use EAS Build (recommended)
npx eas build --platform android
```

## Configuration

### Permissions

The app requires:
- **Camera**: Take photos for check-in and room documentation
- **Location**: Verify student is in classroom

Permissions are requested at runtime with explanatory dialogs.

### Environment Variables

- `API_URL`: Backend API endpoint

## Troubleshooting

### "Cannot connect to backend"

**iOS Simulator:**
- Use `http://localhost:8000` if backend is on same machine
- Ensure backend is running: `docker compose up serve`

**Android Emulator:**
- Use `http://10.0.2.2:8000` (Android's localhost alias)

**Physical Device:**
- Use your computer's IP address: `http://192.168.x.x:8000`
- Ensure device and computer are on same network
- Backend must allow connections from local network

### Camera not working

- Camera only works on physical devices, not simulators/emulators
- Use Expo Go app on real phone for testing
- Ensure camera permissions are granted

### Location inaccurate

- GPS accuracy varies (5-50m typically)
- Works better outdoors
- iOS Simulator can simulate locations
- Android Emulator requires manual location setting

## Development Tips

1. **Fast Refresh**: Code changes update instantly
2. **Logs**: Shake device → "Show Developer Menu" → "Debug JS Remotely"
3. **Network Debugging**: Use React Native Debugger or Reactotron
4. **State Inspection**: Install Flipper for advanced debugging

## Backend Setup

Ensure the HARV backend is running with mobile app support:

```bash
cd ..  # Back to root directory
docker compose up serve
```

The backend must be accessible from your mobile device.

## Contributing

When adding new features:
1. Create new screens in `app/` directory
2. Add API endpoints to `utils/api.ts`
3. Update navigation in `app/_layout.tsx`
4. Test on both iOS and Android
5. Document new workflows

## License

MIT License - See main project LICENSE file

## Support

For issues specific to the mobile app, check:
- Expo documentation: https://docs.expo.dev/
- React Native docs: https://reactnative.dev/
- Main HARV documentation: `../docs/`
