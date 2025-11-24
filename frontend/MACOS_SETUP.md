# macOS Setup for HARV Mobile App

## The EMFILE Problem

Metro bundler (Expo's file watcher) needs to monitor many files. macOS has a default limit of only 256 open files, causing the error:
```
Error: EMFILE: too many open files, watch
```

## Complete Solution (Do All Steps)

### Step 1: Install Watchman (Highly Recommended)

Watchman is Facebook's professional file watching service, much better than Node's default fs.watch:

```bash
brew install watchman
```

**Why Watchman?**
- More efficient file watching
- Better performance
- Solves EMFILE issues
- Required for React Native development

### Step 2: Increase System File Limits (Permanent Fix)

Create system configuration files:

```bash
# Create limits configuration
sudo nano /Library/LaunchDaemons/limit.maxfiles.plist
```

Paste this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>limit.maxfiles</string>
    <key>ProgramArguments</key>
    <array>
      <string>launchctl</string>
      <string>limit</string>
      <string>maxfiles</string>
      <string>65536</string>
      <string>200000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ServiceIPC</key>
    <false/>
  </dict>
</plist>
```

Set permissions and load:
```bash
sudo chown root:wheel /Library/LaunchDaemons/limit.maxfiles.plist
sudo chmod 644 /Library/LaunchDaemons/limit.maxfiles.plist
sudo launchctl load -w /Library/LaunchDaemons/limit.maxfiles.plist
```

### Step 3: Set Shell Limits

Add to `~/.zshrc` (or `~/.bash_profile` if using bash):
```bash
ulimit -n 65536
ulimit -u 2048
```

Reload shell:
```bash
source ~/.zshrc
```

### Step 4: Reboot

For system-wide limits to take effect:
```bash
sudo reboot
```

### Step 5: Verify

After reboot:
```bash
ulimit -n
# Should show: 65536

launchctl limit maxfiles
# Should show: maxfiles 65536 200000

watchman version
# Should show version number
```

## Quick Start (After Setup)

```bash
cd mobile
npm start
```

The app should now start without EMFILE errors!

## Alternative: Exclude Large Directories

If you still have issues, Metro may be watching too many files. Create/update `.watchmanconfig`:

```json
{
  "ignore_dirs": [
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "artifacts",
    ".DS_Store"
  ]
}
```

## Troubleshooting

### Still Getting EMFILE?

1. **Check current limits:**
   ```bash
   ulimit -n
   launchctl limit maxfiles
   ```

2. **Reset watchman:**
   ```bash
   watchman watch-del-all
   ```

3. **Clear all caches:**
   ```bash
   rm -rf node_modules
   npm install
   watchman watch-del-all
   npx expo start -c
   ```

4. **Check for other watchers:**
   ```bash
   # List all processes watching files
   lsof | grep node | wc -l
   ```

### Watchman Issues

```bash
# View watchman logs
watchman --log-level debug watch-project /path/to/mobile

# Reset watchman completely
watchman shutdown-server
rm -rf /usr/local/var/run/watchman
watchman watch-del-all
```

### Verify Installation

Run this diagnostic script:

```bash
#!/bin/bash
echo "=== File Limit Diagnostic ==="
echo ""
echo "ulimit -n: $(ulimit -n)"
echo "launchctl maxfiles: $(launchctl limit maxfiles)"
echo ""
echo "Watchman installed: $(which watchman || echo 'NO')"
echo "Watchman version: $(watchman version 2>/dev/null || echo 'N/A')"
echo ""
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"
echo ""
echo "Expo CLI: $(npx expo --version 2>/dev/null || echo 'N/A')"
```

## Why This Happens

1. **Metro Bundler** watches all project files for hot reload
2. **Large Project** may have thousands of files:
   - node_modules
   - All source files
   - All parent directory files
3. **macOS Default** limit is only 256 files
4. **Solution**: Increase limit + use Watchman

## Production Note

This setup is only needed for **development**. Production builds (EAS Build, Xcode, Android Studio) don't have this issue.

## Resources

- [Watchman Documentation](https://facebook.github.io/watchman/)
- [Node.js File Watching](https://nodejs.org/api/fs.html#fs_fs_watch_filename_options_listener)
- [macOS File Limits](https://unix.stackexchange.com/questions/108174/how-to-persistently-control-maximum-system-resource-consumption-on-mac)
- [Expo Troubleshooting](https://docs.expo.dev/troubleshooting/clear-cache-mac-linux/)
