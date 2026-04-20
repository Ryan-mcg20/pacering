[app]
title = POTS Monitor
package.name = potsmonitor
package.domain = org.neil.pots
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav
version = 0.1
requirements = python3, kivy, plyer, bleak, aiosqlite

orientation = portrait
fullscreen = 0

android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 26
android.archs = arm64-v8a
android.allow_backup = True
android.ndk_version = 25b
android.skip_update = True
android.accept_sdk_license = True

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
