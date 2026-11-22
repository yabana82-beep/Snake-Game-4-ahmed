
[app]

title = Snake Game 4.6 Neon Ultimate
package.name = snakegame
package.domain = org.yabana82

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,wav,ogg,atlas,json,ttf

version = 4.6

requirements = python3,kivy

orientation = portrait
fullscreen = 1

android.permissions = INTERNET,VIBRATE

android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
