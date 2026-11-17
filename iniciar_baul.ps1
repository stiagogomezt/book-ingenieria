$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Stop-WithMessage([string]$Message) {
    Write-Host ""
    Write-Host $Message -ForegroundColor Red
    exit 1
}

$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
$PythonArgs = @("-3")
if (-not $PythonCommand) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $PythonArgs = @()
}
if (-not $PythonCommand) {
    Stop-WithMessage "Instala Python 3.10 o posterior y vuelve a ejecutar este archivo."
}

$PythonVersion = & $PythonCommand.Source @PythonArgs -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or [version]$PythonVersion -lt [version]"3.10") {
    Stop-WithMessage "Se requiere Python 3.10 o posterior."
}

$OllamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $OllamaCommand) {
    Stop-WithMessage "Instala Ollama desde https://ollama.com/download y vuelve a ejecutar este archivo."
}

$OpenCodeCommand = Get-Command opencode -ErrorAction SilentlyContinue
if (-not $OpenCodeCommand) {
    Stop-WithMessage "Instala OpenCode desde https://opencode.ai/download y vuelve a ejecutar este archivo."
}

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Preparando el entorno de Python..."
    & $PythonCommand.Source @PythonArgs -m venv (Join-Path $ProjectRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "No se pudo crear el entorno de Python."
    }
}

Write-Host "Instalando o verificando dependencias..."
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "No se pudieron instalar las dependencias. Revisa tu conexión e inténtalo otra vez."
}

Write-Host "Comprobando Ollama..."
$ModelList = & $OllamaCommand.Source list 2>&1
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Ollama no está iniciado. Abre Ollama desde el menú Inicio y vuelve a ejecutar este archivo."
}

$HasQwen = $false
foreach ($Line in $ModelList) {
    if ("$Line" -match "^qwen3:8b(\s|$)") {
        $HasQwen = $true
        break
    }
}
if (-not $HasQwen) {
    Write-Host "Qwen3 8B requiere descargar varios GB."
    $DownloadModel = Read-Host "¿Descargar qwen3:8b ahora? Escribe S para continuar"
    if ($DownloadModel -notmatch "^[sS]$") {
        Stop-WithMessage "No se descargó Qwen. Ejecuta ollama pull qwen3:8b y vuelve a iniciar Baúl."
    }
    & $OllamaCommand.Source pull qwen3:8b
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "No se pudo descargar qwen3:8b."
    }
}

$PasswordBytes = New-Object byte[] 32
$RandomGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$RandomGenerator.GetBytes($PasswordBytes)
$RandomGenerator.Dispose()
$OpenCodePassword = [Convert]::ToBase64String($PasswordBytes)
$env:OPENCODE_PASSWORD = $OpenCodePassword

$ServerOutput = Join-Path $env:TEMP "baul-opencode-$PID.out.log"
$ServerError = Join-Path $env:TEMP "baul-opencode-$PID.err.log"
$OpenCodeProcess = $null
try {
    Write-Host "Iniciando los dos agentes OpenCode en este equipo..."
    $OpenCodeProcess = Start-Process `
        -FilePath $OpenCodeCommand.Source `
        -ArgumentList @("serve", "--hostname", "127.0.0.1", "--port", "4096") `
        -WorkingDirectory $ProjectRoot `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $ServerOutput `
        -RedirectStandardError $ServerError

    $BasicValue = [Convert]::ToBase64String(
        [Text.Encoding]::ASCII.GetBytes("opencode:$OpenCodePassword")
    )
    $Headers = @{ Authorization = "Basic $BasicValue" }
    $AgentList = $null
    for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
        if ($OpenCodeProcess.HasExited) {
            break
        }
        try {
            $AgentList = Invoke-RestMethod `
                -Uri "http://127.0.0.1:4096/api/agent" `
                -Headers $Headers `
                -TimeoutSec 3
            break
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $AgentList) {
        $LogHint = ""
        if (Test-Path $ServerError) {
            $LogHint = Get-Content $ServerError -Raw
        }
        Stop-WithMessage "OpenCode no inició correctamente. Revisa si el puerto 4096 está ocupado. $LogHint"
    }

    $AgentIds = @($AgentList.data | ForEach-Object { $_.id })
    if (($AgentIds -notcontains "agente_catastro") -or ($AgentIds -notcontains "agente_geodesia")) {
        Stop-WithMessage "OpenCode inició, pero no encuentra los dos agentes. Descarga el ZIP completo del repositorio y ejecuta el iniciador desde su carpeta raíz."
    }

    $env:OPENCODE_BASE_URL = "http://127.0.0.1:4096"
    $env:OPENCODE_API_TOKEN = $OpenCodePassword
    $env:OPENCODE_AUTH_SCHEME = "basic"
    $env:OPENCODE_USERNAME = "opencode"
    $env:OPENCODE_WORKSPACE = $ProjectRoot

    Write-Host "Baúl está listo. Se abrirá en http://localhost:8501."
    Write-Host "No compartas esta dirección para datos privados. Para salir, cierra Streamlit con Ctrl+C."
    & $VenvPython -m streamlit run (Join-Path $ProjectRoot "app_baul.py") `
        --server.headless false `
        --server.address 127.0.0.1
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Streamlit terminó con un error."
    }
}
finally {
    Remove-Item Env:OPENCODE_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_BASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_API_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_AUTH_SCHEME -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_USERNAME -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_WORKSPACE -ErrorAction SilentlyContinue
    if ($OpenCodeProcess -and -not $OpenCodeProcess.HasExited) {
        Stop-Process -Id $OpenCodeProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
