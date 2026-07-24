param([ValidateSet("format", "lint", "type-check", "test")][string]$Task = "test")
$backend = Join-Path $PSScriptRoot "..\backend"
Push-Location $backend
try {
    switch ($Task) {
        "format" { python -m ruff format . }
        "lint" { python -m ruff check . }
        "type-check" { python -m mypy app }
        "test" { python -m pytest }
    }
} finally { Pop-Location }

