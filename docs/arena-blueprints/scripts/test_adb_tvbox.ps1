<#
.SYNOPSIS
    Checklist automatizado de validação ADB na TV Box / Dispositivo Android
    (MANAGE_EXTERNAL_STORAGE, ForegroundService specialUse, Launcher HOME,
     BootReceiver e MediaMountReceiver).
#>
param(
    [string]$PackageName = "com.arena.console",
    [string]$ApkPath = "android\app\build\outputs\apk\debug\app-debug.apk"
)

$ErrorActionPreference = "Continue"

Write-Host "=== 1. Verificando dispositivo ADB conectado ===" -ForegroundColor Cyan
adb devices

if (Test-Path $ApkPath) {
    Write-Host "`n=== 2. Instalando APK e abrindo MainActivity ===" -ForegroundColor Cyan
    adb install -r $ApkPath
    adb shell am start -n "$PackageName/.MainActivity"
    Start-Sleep -Seconds 2
}

Write-Host "`n=== 3. Validando e concedendo MANAGE_EXTERNAL_STORAGE e POST_NOTIFICATIONS ===" -ForegroundColor Cyan
adb shell appops get $PackageName MANAGE_EXTERNAL_STORAGE
adb shell appops set --uid $PackageName MANAGE_EXTERNAL_STORAGE allow
adb shell pm grant $PackageName android.permission.POST_NOTIFICATIONS

Write-Host "`n=== 4. Validando libarena_web.so e ForegroundService (specialUse) ===" -ForegroundColor Cyan
adb shell dumpsys package $PackageName | Select-String "legacyNativeLibraryDir"
adb shell ps -A | Select-String "libarena_web"
adb shell dumpsys activity services "$PackageName/.ArenaWebService" | Select-String -Pattern "isForeground|foregroundServiceType"

Write-Host "`n=== 5. Configurando Launcher HOME e testando KEYCODE_HOME ===" -ForegroundColor Cyan
adb shell cmd package set-home-activity "$PackageName/.MainActivity"
adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME
adb shell input keyevent KEYCODE_HOME
adb shell dumpsys window windows | Select-String -Pattern "mCurrentFocus|RequestedVisibilities"

Write-Host "`n=== 6. Testando BootReceiver (BOOT_COMPLETED) ===" -ForegroundColor Cyan
adb logcat -c
adb shell am kill $PackageName
adb shell am broadcast -a android.intent.action.BOOT_COMPLETED -p $PackageName
Start-Sleep -Seconds 2
adb logcat -d -s ARENA-BOOT ARENA-RUST

Write-Host "`n=== 7. Testando MediaMountReceiver (Hotplug USB/SD) ===" -ForegroundColor Cyan
adb shell "cat /proc/mounts | grep -E '/storage/|/mnt/media_rw'"
adb logcat -c
adb shell am broadcast -a android.intent.action.MEDIA_MOUNTED -d "file:///storage/emulated/0" -p $PackageName
Start-Sleep -Seconds 2
adb logcat -d -s ARENA-STORAGE

Write-Host "`n=== 8. Testando resposta HTTP local via adb forward ===" -ForegroundColor Cyan
adb forward tcp:8080 tcp:8080
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/storage" -Method Get | ConvertTo-Json -Depth 4
} catch {
    Write-Warning "Nao foi possivel consultar http://127.0.0.1:8080/api/storage: $_"
}