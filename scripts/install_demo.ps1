param([string]$Python = 'py')
$ErrorActionPreference = 'Stop'
$demoEnvironment = Join-Path $PSScriptRoot '.venv-demo'
& $Python -m venv $demoEnvironment
if ($LASTEXITCODE -ne 0) { throw 'Se requiere Python >=3.12 con Tk instalado.' }
& "$demoEnvironment/Scripts/python.exe" -m pip install --no-index --find-links "$PSScriptRoot/wheels" vaultlab
if ($LASTEXITCODE -ne 0) { throw 'Instalación offline fallida. Verificar versión y arquitectura de Python.' }
Write-Output "Para iniciar: & '$demoEnvironment/Scripts/python.exe' -m vaultlab"
