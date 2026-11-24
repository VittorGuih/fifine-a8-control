param([switch]$ListOnly)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -Path (Join-Path $PSScriptRoot 'AudioControl.cs')
function Reply($value) { [Console]::WriteLine(($value | ConvertTo-Json -Depth 4 -Compress)) }
function Status {
    $s = [FifineA8Control.AudioControl]::Status()
    return @{ok=$true;muted=$s.Muted;level=$s.Level}
}
if ($ListOnly) {
    try {
        $devices = @([FifineA8Control.AudioControl]::Discover())
        Reply @{ok=$true;count=$devices.Count;devices=$devices}
    } catch { Reply @{ok=$false;error=$_.Exception.Message} }
    exit
}
try { Reply (Status) } catch { Reply @{ok=$false;error=$_.Exception.Message} }
while ($null -ne ($command = [Console]::ReadLine())) {
    if ($command -eq 'quit') { break }
    try {
        switch ($command) {
            'mute' { $s = [FifineA8Control.AudioControl]::Apply($true); Reply @{ok=$true;muted=$s.Muted;level=$s.Level} }
            'unmute' { $s = [FifineA8Control.AudioControl]::Apply($false); Reply @{ok=$true;muted=$s.Muted;level=$s.Level} }
            'status' { Reply (Status) }
            default { throw 'Unknown audio command.' }
        }
    } catch { Reply @{ok=$false;error=$_.Exception.Message} }
}
