param([string]$Foto, [int]$Espera = 30)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$raiz = "C:\Projetos\Criador De Apps Pedagógicos\ARENA\ARENA-unificado"
$p = Start-Process -FilePath "$raiz\emuladores\PCSX2\PCSX2\pcsx2-qt.exe" -ArgumentList "`"$raiz\jogos\pessoais\PS2\Crash Nitro Kart (USA).chd`"" -PassThru
Start-Sleep $Espera
$p.Refresh()
$cpu1 = $p.TotalProcessorTime.TotalSeconds
Start-Sleep 5
$p.Refresh()
$cpu2 = $p.TotalProcessorTime.TotalSeconds
$tela = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $tela.Width, $tela.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($tela.Location, [System.Drawing.Point]::Empty, $tela.Size)
$bmp.Save($Foto, [System.Drawing.Imaging.ImageFormat]::Png)
"janela='{0}' respondendo={1} cpu_em_5s={2:N1}s" -f $p.MainWindowTitle, $p.Responding, ($cpu2 - $cpu1)
Stop-Process -Id $p.Id -Force

