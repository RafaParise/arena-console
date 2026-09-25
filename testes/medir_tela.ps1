# Revisao pos-auditoria: RAM da tela do ARENA e custo do fundo animado.
#
# As duas medicoes que a auditoria nao conseguiu (Fases 0 e 2). A tela abre
# num Edge SEPARADO, com perfil proprio numa pasta temporaria: vira um grupo
# de processos so dele, com a janela visivel (a animacao roda de verdade).
# Mede por 20 s com o modo modesto DESLIGADO (fundo animando) e LIGADO
# (fundo parado), e devolve o modo modesto ao valor que estava.
#
# Precisa do servidor do ARENA ja no ar (ARENA.bat). E' PowerShell, nao
# Python, porque neste Windows o Edge aberto a partir do Python fecha sem
# abrir janela.
#
# Uso:  powershell -ExecutionPolicy Bypass -File testes\medir_tela.ps1

$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" }
$url = "http://127.0.0.1:8777"
$original = (Invoke-RestMethod "$url/api/estado").config.modo_modesto
$nucleos = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$resultados = @()

function Processos($marca) {
    Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'msedge.exe' -and $_.CommandLine -like "*$marca*" } |
        ForEach-Object { Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
}

foreach ($modesto in @($false, $true)) {
    Invoke-RestMethod -Method Post -Uri "$url/api/config" -ContentType "application/json" `
        -Body (@{ modo_modesto = $modesto } | ConvertTo-Json) | Out-Null
    $marca = "arena_medir_tela_" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    $perfil = Join-Path $env:TEMP $marca
    Start-Process -FilePath $edge -ArgumentList "--app=$url/", "--window-size=1180,760", "--no-first-run", "--user-data-dir=$perfil"
    Start-Sleep 15
    $antes = @{}; Processos $marca | ForEach-Object { $antes[$_.Id] = $_.CPU }
    $t0 = Get-Date
    Start-Sleep 20
    $depois = @(Processos $marca)
    $seg = ((Get-Date) - $t0).TotalSeconds
    $cpu = 0; foreach ($p in $depois) { $cpu += $p.CPU - $(if ($antes.ContainsKey($p.Id)) { $antes[$p.Id] } else { $p.CPU }) }
    $r = [pscustomobject]@{
        modo_modesto = $modesto
        processos = $depois.Count
        ram_mb = [math]::Round(($depois | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 1)
        cpu_pct_da_maquina = [math]::Round(100 * $cpu / $seg / $nucleos, 2)
        cpu_pct_de_um_nucleo = [math]::Round(100 * $cpu / $seg, 1)
    }
    $r
    $resultados += $r
    $depois | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
    Remove-Item -Recurse -Force $perfil -ErrorAction SilentlyContinue
}

Invoke-RestMethod -Method Post -Uri "$url/api/config" -ContentType "application/json" `
    -Body (@{ modo_modesto = [bool]$original } | ConvertTo-Json) | Out-Null
"Modo modesto devolvido para: $original"
$resultados | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $PSScriptRoot "..\docs\medir_tela_bruto.json")
