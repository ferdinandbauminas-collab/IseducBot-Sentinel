$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop")
$ShortcutPath = [System.IO.Path]::Combine($DesktopPath, "Assistente ISEDUC.lnk")

# Localiza o Chrome
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $ChromePath)) {
    $ChromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}

if (Test-Path $ChromePath) {
    # Remove o antigo se existir
    if (Test-Path $ShortcutPath) { Remove-Item $ShortcutPath }

    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $ChromePath
    $Shortcut.Arguments = "https://portal.seduc.pi.gov.br/"
    $Shortcut.Description = "Assistente ISEDUC"
    $Shortcut.IconLocation = "$ChromePath, 0"
    $Shortcut.Save()
    Write-Host "✅ Atalho atualizado: agora abre exatamente https://portal.seduc.pi.gov.br/" -ForegroundColor Cyan
} else {
    Write-Host "❌ Erro: Chrome não localizado." -ForegroundColor Red
}
