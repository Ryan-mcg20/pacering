[app]
title = PaceRing
package.name = pacering
package.domain = com.ryanmcg
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy,android,pyblemulator
orientation = portrait
android.minapi = 26
android.api = 33
android.ndk_version = 25b
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, INTERNET, ACCESS_FINE_LOCATION
android.archs = arm64-v8a
android.allow_backup = True
android.wakelock = True
android.skip_update = True
android.accept_sdk_license = True
presplash.color = #100d1a
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
