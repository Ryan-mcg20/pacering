[app]

title = PaceRing
package.name = pacering
package.domain = org.pacering

source.dir = .
source.include_exts = py,png,jpg,kv,json

version = 0.1

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION

log_level = 2

[buildozer]
warn_on_root = 1
