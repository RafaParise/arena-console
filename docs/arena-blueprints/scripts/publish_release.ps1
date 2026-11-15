<#
.SYNOPSIS
    Protege o .gitignore, cria commit e envia tag anotada (ex: 2026.11.14) para
    disparar a release automática no GitHub Actions.
#>
param(
    [Parameter(Mandatory=$true)][string]$TagVersion,
    [string]$CommitMessage = "feat: atualiza servidor web Rust (Axum) e integracao nativa Android"
)

$ErrorActionPreference = "Stop"

Write-Host "=== 1. Removendo artefatos temporarios do indice Git (se existirem) ===" -ForegroundColor Cyan
git rm -rf --cached arena-web/target bin dist apk-out 2>$null

Write-Host "=== 2. Conferindo status antes do commit ===" -ForegroundColor Cyan
git status

$Confirm = Read-Host "Deseja continuar com commit e push da tag '$TagVersion'? (S/N)"
if ($Confirm -notin @("S", "s", "Y", "y")) {
    Write-Host "Operacao cancelada pelo usuario." -ForegroundColor Yellow
    exit 0
}

git add .
git commit -m $CommitMessage
git push origin main

git tag -a $TagVersion -m "Release ARENA $TagVersion"
git push origin $TagVersion

Write-Host "Tag $TagVersion enviada! Acompanhe com: gh run watch" -ForegroundColor Green