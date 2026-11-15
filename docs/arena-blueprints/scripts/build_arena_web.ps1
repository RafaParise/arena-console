<#
.SYNOPSIS
    Compila o servidor Rust arena-web para Android ARM64 (aarch64-linux-android) no Windows
    e posiciona o binário libarena_web.so em android/app/src/main/jniLibs/arm64-v8a/.
#>
$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$ArenaWebDir = Join-Path $RootDir "arena-web"
$TargetJniDir = Join-Path $RootDir "android\app\src\main\jniLibs\arm64-v8a"

Write-Host "[ARENA-BUILD] Garantindo toolchain aarch64-linux-android..." -ForegroundColor Cyan
rustup target add aarch64-linux-android

Push-Location $ArenaWebDir
try {
    Write-Host "[ARENA-BUILD] Executando cargo build --target aarch64-linux-android --release..." -ForegroundColor Cyan
    cargo build --target aarch64-linux-android --release
}
finally {
    Pop-Location
}

if (-not (Test-Path $TargetJniDir)) {
    New-Item -ItemType Directory -Path $TargetJniDir -Force | Out-Null
}

$SourceSo = Join-Path $ArenaWebDir "target\aarch64-linux-android\release\libarena_web.so"
$DestSo = Join-Path $TargetJniDir "libarena_web.so"
Copy-Item -Path $SourceSo -Destination $DestSo -Force

Write-Host "[ARENA-BUILD] Sucesso! Binário copiado para: $DestSo" -ForegroundColor Green