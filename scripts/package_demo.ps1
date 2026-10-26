param([string]$Python = "$PSScriptRoot/../.venv/Scripts/python.exe")
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $projectRoot 'dist/demo-offline'
New-Item -ItemType Directory -Force "$outputRoot/wheels" | Out-Null
# Solo se empaqueta la distribución del proyecto y dependencias; jamás bóvedas del usuario.
& $Python -m pip wheel $projectRoot --wheel-dir "$outputRoot/wheels"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo construir el paquete offline.' }
Copy-Item -LiteralPath "$projectRoot/scripts/install_demo.ps1" -Destination $outputRoot
Copy-Item -LiteralPath "$projectRoot/docs/DEMO_GUIDE.md" -Destination $outputRoot
Get-ChildItem "$outputRoot/wheels" -File | Get-FileHash -Algorithm SHA256 |
    Select-Object Hash, @{Name='File';Expression={Split-Path -Leaf $_.Path}} |
    Export-Csv "$outputRoot/SHA256.csv" -NoTypeInformation -Encoding UTF8
Compress-Archive -Path "$outputRoot/wheels", "$outputRoot/install_demo.ps1", "$outputRoot/DEMO_GUIDE.md", "$outputRoot/SHA256.csv" -DestinationPath "$projectRoot/dist/VaultLab-demo-offline.zip" -Force
Write-Output 'Creado dist/VaultLab-demo-offline.zip. Requiere Python con Tk compatible en destino.'
