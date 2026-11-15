<#
.SYNOPSIS
    Registra as labels oficiais (rust, android, linux, emulator, ci) no GitHub via gh CLI.
#>
$ErrorActionPreference = "Stop"

gh label create "rust" --color "dea584" --description "Alteracoes no servidor Axum e crates Rust" --force
gh label create "android" --color "3ddc84" --description "App nativo Android, JNI, Services e TV Box" --force
gh label create "linux" --color "fcc624" --description "Builds estaticos musl, Chromebook Crostini e instalador" --force
gh label create "emulator" --color "7057ff" --description "Integracao e mapeamento de emuladores" --force
gh label create "ci" --color "0e8a16" --description "Workflows GitHub Actions e empacotamento" --force

Write-Host "Labels registradas com sucesso!" -ForegroundColor Green