[app]

# App identity
title = PaceRing
package.name = pacering
package.domain = com.ryanmcg

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = *.py,*.json

# Version
version = 1.0.0

# Requirements — keep only what's needed, avoids bloat/crash
requirements = python3,kivy==2.3.0,android

# Orientation
orientation = portrait

# Android API targets
android.minapi = 26
android.api = 34
android.ndk = 25b
android.sdk = 34

# Permissions
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,VIBRATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Architecture — arm64-v8a is primary modern Android; armeabi-v7a for older devices
android.archs = arm64-v8a, armeabi-v7a

# Entry point
entrypoint = main

# Fullscreen (hides status bar for cleaner look)
fullscreen = 0

# Android features
android.allow_backup = True
android.wakelock = True

# Icon/presplash (create these files or remove these lines)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png
presplash.color = #100d1a

# Gradle / Java config
android.gradle_dependencies =
android.enable_androidx = True
android.add_compile_options = sourceCompatibility = JavaVersion.VERSION_11\ntargetCompatibility = JavaVersion.VERSION_11

# Logcat filter (useful for debugging)
android.logcat_filters = *:S python:D

# Build backend
p4a.branch = master

[buildozer]

# Build log verbosity: 0 = quiet, 1 = normal, 2 = verbose
log_level = 2

# Warn on root build (safety check)
warn_on_root = 1
