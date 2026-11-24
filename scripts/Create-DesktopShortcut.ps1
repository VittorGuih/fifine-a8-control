$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$target = Join-Path $repo '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $target)) { throw 'Create .venv and install the app using the README instructions first.' }
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Fifine A8 Control.lnk'))
$shortcut.TargetPath = $target
$shortcut.Arguments = '-m fifine_a8_control'
$shortcut.WorkingDirectory = $repo
$shortcut.Description = 'Control and optionally maintain the FIFINE A8 mute state'
$shortcut.IconLocation = "$env:SystemRoot\System32\mmsys.cpl,0"
$shortcut.Save()
Write-Output 'Created the Fifine A8 Control desktop shortcut.'
