# Tira uma foto da tela principal. Uso (pwsh): -File testesoto_tela.ps1 -Foto <arquivo.png>
param([string]$Foto)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$tela = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $tela.Width, $tela.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($tela.Location, [System.Drawing.Point]::Empty, $tela.Size)
$bmp.Save($Foto, [System.Drawing.Imaging.ImageFormat]::Png)
"ok"
