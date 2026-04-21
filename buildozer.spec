[app]
# (str) Title of your application
title = PacePoint

# (str) Package name
package.name = pacepoint

# (str) Package domain (needed for android packaging)
package.domain = com.ryanmcg

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = python3, kivy, bleak, async_gui, android

# (str) Supported orientation
orientation = portrait

# (list) Permissions REQUIRED FOR XIAOMI BAND & BLE
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, INTERNET, ACCESS_FINE_LOCATION

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 26

# (str) Android NDK version to use
android.ndk_version = 25b

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) Allow backup
android.allow_backup = True

# (bool) Keep screen on
android.wakelock = True

# (str) Presplash color
presplash.color = #121411

# (str) python-for-android branch to use
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
