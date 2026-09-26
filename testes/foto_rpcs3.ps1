# Abre um jogo de PS3 no RPCS3 (sem a tela de lista) e tira fotos da tela
# nos segundos pedidos. Uso (pwsh):
#   pwsh -File testes\foto_rpcs3.ps1 -Jogo "<caminho .iso>" -Pasta "<saida>" -Segundos "30,60,90"
param([string]$Jogo, [string]$Pasta, [string]$Segundos = "30,60,90")
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$raiz = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $raiz "emuladores\RPCS3\RPCS3\rpcs3.exe"
$p = Start-Process -FilePath $exe -ArgumentList '--no-gui', "`"$Jogo`"" -PassThru
$passado = 0
foreach ($s in ($Segundos -split "," | ForEach-Object { [int]$_ })) {
    Start-Sleep ($s - $passado)
    $passado = $s
    $tela = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap $tela.Width, $tela.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($tela.Location, [System.Drawing.Point]::Empty, $tela.Size)
    $bmp.Save((Join-Path $Pasta ("rpcs3_{0}s.png" -f $s)), [System.Drawing.Imaging.ImageFormat]::Png)
    $p.Refresh()
    "{0}s: rodando={1} janela='{2}'" -f $s, (-not $p.HasExited), $p.MainWindowTitle
}
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
