[app]
title = X9 Sovereign Vault
package.name = x9vault
package.domain = org.x9.mesh
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,css,js,pem
version = 1.0.0

requirements = python3,kivy,pyjnius,openssl,cryptography==38.0.4,requests,urllib3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.wakelock = True

[buildozer]
log_level = 2
warn_on_build_tools_version = 1
android.accept_sdk_license = True

android.sdk_build_tools_version = 33.0.2
