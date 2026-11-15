#!/usr/bin/env bash
set -e

PKG="${1:-com.arena.console}"
APK="${2:-android/app/build/outputs/apk/debug/app-debug.apk}"

if [ -f "$APK" ]; then
  adb install -r "$APK"
fi
adb shell am start -n "${PKG}/.MainActivity"
sleep 2

echo "=== 1. Permissões MANAGE_EXTERNAL_STORAGE e POST_NOTIFICATIONS ==="
adb shell appops get "$PKG" MANAGE_EXTERNAL_STORAGE
adb shell appops set --uid "$PKG" MANAGE_EXTERNAL_STORAGE allow
adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS

echo "=== 2. Binário libarena_web.so, variáveis ARENA_* e ForegroundService (specialUse) ==="
adb shell dumpsys package "$PKG" | grep legacyNativeLibraryDir
adb shell ps -A | grep libarena_web
adb shell "tr '\0' '\n' < /proc/\$(pidof libarena_web.so)/environ | grep ARENA_" || true
adb shell dumpsys activity services "${PKG}/.ArenaWebService" | grep -E "isForeground|foregroundServiceType"

echo "=== 3. Launcher HOME e Modo Imersivo ==="
adb shell cmd package set-home-activity "${PKG}/.MainActivity"
adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME
adb shell input keyevent KEYCODE_HOME
adb shell dumpsys window windows | grep -E "mCurrentFocus|RequestedVisibilities"

echo "=== 4. BootReceiver (BOOT_COMPLETED) ==="
adb logcat -c
adb shell am kill "$PKG"
adb shell am broadcast -a android.intent.action.BOOT_COMPLETED -p "$PKG"
sleep 2
adb logcat -d -s ARENA-BOOT ARENA-RUST

echo "=== 5. MediaMountReceiver (Hotplug USB/SD) ==="
adb shell "cat /proc/mounts | grep -E '/storage/|/mnt/media_rw'" || true
adb logcat -c
adb shell am broadcast -a android.intent.action.MEDIA_MOUNTED -d "file:///storage/emulated/0" -p "$PKG"
sleep 2
adb logcat -d -s ARENA-STORAGE