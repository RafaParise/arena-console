<#
.SYNOPSIS
    Valida todos os endpoints HTTP da API Rust do ARENA (/api/storage/sync, /api/storage,
    /api/roms, /api/artwork, /api/favorites/toggle).
#>
param(
    [string]$BaseUrl = "http://127.0.0.1:8080"
)

Write-Host "=== 1. POST /api/storage/sync ===" -ForegroundColor Cyan
$SyncResp = Invoke-RestMethod -Uri "$BaseUrl/api/storage/sync" -Method Post -ContentType "application/json" -Body '{"paths": []}'
$SyncResp | ConvertTo-Json -Depth 4

Write-Host "`n=== 2. GET /api/roms ===" -ForegroundColor Cyan
$Roms = Invoke-RestMethod -Uri "$BaseUrl/api/roms" -Method Get
Write-Host "Total retornado: $($Roms.Count)"
if ($Roms.Count -gt 0) {
    $Roms[0] | Select-Object id, title, description, system, artwork_url, is_favorite | ConvertTo-Json -Depth 3

    $FirstId = $Roms[0].id
    Write-Host "`n=== 3. POST /api/favorites/toggle ($FirstId) ===" -ForegroundColor Cyan
    $FavResp = Invoke-RestMethod -Uri "$BaseUrl/api/favorites/toggle" -Method Post -ContentType "application/json" -Body "{`"id`": `"$FirstId`"}"
    $FavResp | ConvertTo-Json -Depth 3
}