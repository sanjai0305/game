[app]
title = NEO DODGE
package.name = neododge
package.domain = org.sanjai

source.dir = .
source.include_exts = py,json,png,jpg,ogg,wav,ttf

version = 0.1

requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.ndk = 25b
android.arch = armeabi-v7a,arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
