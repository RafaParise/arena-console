# Traz a janela de um processo para a frente e aperta teclas nela (para
# testes que precisam passar de "PRESS START" sem ninguem no controle).
# Uso (pwsh): -File testes\apertar_teclas.ps1 -Processo xenia_canary -Teclas "x,x" -Intervalo 3
param([string]$Processo, [string]$Teclas, [int]$Intervalo = 3)
$shell = New-Object -ComObject WScript.Shell
$p = Get-Process $Processo -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $p) { "processo nao encontrado"; exit 1 }
foreach ($tecla in ($Teclas -split ",")) {
    [void]$shell.AppActivate($p.Id)
    Start-Sleep -Milliseconds 300
    $shell.SendKeys($tecla)
    Start-Sleep $Intervalo
}
"ok"
