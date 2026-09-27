[app]
title = Taller Lutheria
package.name = tallerlutheria
package.domain = org.tallerlutheria
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy==2.3.0,reportlab,pyjnius

orientation = portrait
fullscreen = 0

# Permisos necesarios: guardar PDFs/DB y abrir WhatsApp
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
