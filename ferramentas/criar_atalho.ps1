# Cria o atalho do ARENA, com o icone do supercontrole (launcher\arena.ico), na area de
# trabalho ou na pasta que vier no argumento. Nao precisa de administrador e nao mexe no
# registro: e' so um arquivo .lnk. O atalho guarda o caminho desta pasta; se a pasta mudar
# de lugar (ou o pen drive ganhar outra letra), rode de novo.
param([string]$Destino = "")
$ErrorActionPreference = "Stop"
# a pasta do ARENA: a de cima da pasta "ferramentas", onde este arquivo mora
$aqui = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $Destino) { $Destino = [Environment]::GetFolderPath("Desktop") }
if (-not (Test-Path -LiteralPath $Destino)) { throw "A pasta nao existe: $Destino" }
$icone = Join-Path $aqui "launcher\arena.ico"
if (-not (Test-Path -LiteralPath $icone)) { throw "Falta o icone: $icone" }
$atalho = Join-Path $Destino "ARENA.lnk"
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($atalho)
$s.TargetPath = Join-Path $aqui "ARENA.bat"
$s.WorkingDirectory = $aqui
$s.IconLocation = $icone + ",0"
$s.Description = "ARENA: a central de jogos retro da turma"
$s.Save()
Write-Output $atalho
