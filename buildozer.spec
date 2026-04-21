[app]
# (str) Title of your application
title = PaceRing

# (str) Package name
package.name = pacering

# (str) Package domain (needed for android packaging)
package.domain = com.ryanmcg

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let's keep your inclusions)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# CRITICAL FIX: Switched 'android' to specific BLE-compatible libraries
requirements = python3, kivy, bleak, async_gui, android

# (str) Supported orientation
orientation = portrait

# (list) Permissions
# REQUIRED FOR XIAOMI BAND & BLE
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, INTERNET, ACCESS_FINE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 26

# (str) Android NDK version to use
android.ndk_version = 25b

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) Allow backup
android.allow_backup = True

# (bool) Keep screen on
android.wakelock = True

# (str) Presplash color
presplash.color = #100d1a

# (str) python-for-android branch to use
p4a.branch = master

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
