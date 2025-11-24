# HARV Mobile App - Troubleshooting

## EMFILE: Too Many Open Files Error

### Problem
```
Error: EMFILE: too many open files, watch
```

This is a macOS system limitation where the default number of file descriptors is too low for Metro bundler.

### Solutions

#### Option 1: Use Updated Start Script (Recommended)
The `package.json` has been updated to automatically handle this:
```bash
npm start
```

#### Option 2: Use Shell Script
```bash
./start-expo.sh
```

#### Option 3: Manual Terminal Command
Run this in your terminal before starting Expo:
```bash
ulimit -n 10240
npm start
```

#### Option 4: Permanent System-Wide Fix
Add to your `~/.zshrc` or `~/.bash_profile`:
```bash
ulimit -n 10240
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

### Verify Current Limit
```bash
ulimit -n
# Should show 10240 or higher
```

## Package Version Warnings

If you see warnings about package versions:
```
expo-image-picker@15.0.7 - expected version: ~15.1.0
```

These have been fixed in `package.json`. Run:
```bash
npm install
```

## Common Issues

### 1. "Cannot connect to backend"

**Cause**: Mobile app can't reach API server

**Solutions**:
- Ensure backend is running: `cd .. && docker compose up serve`
- Check `frontend/.env` file:
  ```
  API_URL=http://localhost:8000  # iOS Simulator
  API_URL=http://10.0.2.2:8000   # Android Emulator
  API_URL=http://YOUR_IP:8000    # Physical device
  ```
- Find your IP: `ifconfig | grep "inet " | grep -v 127.0.0.1`

### 2. Camera Not Working

**Cause**: Camera doesn't work on simulators/emulators

**Solution**: Use a physical device with Expo Go app

### 3. Location Permissions Denied

**Cause**: iOS/Android permissions not granted

**Solution**: 
- iOS: Settings → Privacy → Location Services → HARV → Always/While Using
- Android: Settings → Apps → HARV → Permissions → Location

### 4. Metro Bundler Stuck

**Cause**: Cache issues

**Solution**:
```bash
# Clear Metro cache
npx expo start -c

# Or clear all caches
rm -rf node_modules
npm install
npx expo start -c
```

### 5. TypeScript Errors

**Cause**: Missing type definitions

**Solution**:
```bash
npm install --save-dev @types/react @types/react-native
```

### 6. Build Fails

**Cause**: Various reasons

**Solutions**:
- Clear watchman: `watchman watch-del-all`
- Clear Xcode derived data (iOS): `rm -rf ~/Library/Developer/Xcode/DerivedData`
- Clean Android build (Android): `cd android && ./gradlew clean`

## Platform-Specific Issues

### iOS

**Simulator doesn't open**:
```bash
# Install iOS Simulator
xcode-select --install

# Open manually
open -a Simulator
```

**Code signing issues**:
- Requires paid Apple Developer account for physical devices
- Use Expo Go app to avoid code signing

### Android

**Emulator not found**:
```bash
# List available emulators
emulator -list-avds

# Start specific emulator
emulator -avd Pixel_5_API_31
```

**ADB connection issues**:
```bash
adb kill-server
adb start-server
adb devices
```

## Performance Issues

### Slow Development Server

**Solution**: Increase Node.js memory:
```bash
export NODE_OPTIONS=--max_old_space_size=4096
npm start
```

### App Crashes on Device

**Solution**: Check logs:
```bash
# iOS
npx react-native log-ios

# Android
npx react-native log-android
```

## Network Debugging

### View Network Requests

**React Native Debugger**:
```bash
brew install --cask react-native-debugger
```

**Reactotron**:
```bash
brew install --cask reactotron
```

### Enable Remote Debugging

1. Shake device (or Cmd+D on simulator)
2. Select "Debug"
3. Open Chrome DevTools

## Getting Help

1. Check logs: Device shake → "Show Developer Menu" → "Debug"
2. Backend logs: `cd .. && docker compose logs serve`
3. Expo forums: https://forums.expo.dev/
4. GitHub Issues: Create issue with:
   - Platform (iOS/Android)
   - Device/Simulator version
   - Error message
   - Steps to reproduce

## Useful Commands

```bash
# Check Expo CLI version
npx expo --version

# Doctor (diagnose issues)
npx expo-doctor

# Clear all caches and restart
rm -rf node_modules
npm install
npx expo start -c

# Update Expo SDK
npx expo upgrade

# View environment info
npx react-native info
```

## Environment Verification

Run this to verify your setup:
```bash
node --version    # Should be 18+
npm --version     # Should be 9+
npx expo --version  # Should be 51+
ulimit -n         # Should be 10240+
```

## Still Having Issues?

1. Delete `node_modules` and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Reset Expo:
   ```bash
   npx expo start -c --reset-cache
   ```

3. Check system resources:
   - Disk space: `df -h`
   - Memory: Activity Monitor
   - CPU: Activity Monitor

4. Update system tools:
   ```bash
   npm install -g npm@latest
   npm install -g expo-cli@latest
   ```
