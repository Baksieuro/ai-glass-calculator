# Создание .venv и установка зависимостей (запускать из корня проекта)
# Usage: .\scripts\install_venv.ps1   или   pwsh -File scripts\install_venv.ps1

# Корень проекта (родитель папки scripts)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Создаю виртуальное окружение .venv ..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Обновляю pip ..."
.\.venv\Scripts\pip install --upgrade pip

Write-Host "Устанавливаю пакеты из requirements.txt ..."
.\.venv\Scripts\pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Готово. Активация: .\.venv\Scripts\Activate.ps1"
} else {
    exit $LASTEXITCODE
}
