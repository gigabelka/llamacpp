$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\MyProjecs\llamacpp\strata' }
Set-Location -LiteralPath $here
& 'C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd' launch --preset 'IQ3_S 200K'
if ($LASTEXITCODE -ne 0) { Read-Host 'Press Enter to close' | Out-Null }
