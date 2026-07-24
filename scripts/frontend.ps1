param([ValidateSet("format", "lint", "type-check", "test", "build")][string]$Task = "test")
$frontend = Join-Path $PSScriptRoot "..\frontend"
Push-Location $frontend
try { & npm.cmd run $Task } finally { Pop-Location }

