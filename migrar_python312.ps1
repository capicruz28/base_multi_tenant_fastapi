# Script de migración a Python 3.12 para Windows
# Ejecutar en PowerShell como Administrador (opcional, pero recomendado)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "MIGRACION A PYTHON 3.12" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar Python 3.12
Write-Host "[1/6] Verificando Python 3.12..." -ForegroundColor Yellow
$python312 = Get-Command python3.12 -ErrorAction SilentlyContinue
if (-not $python312) {
    Write-Host "  [INFO] Python 3.12 no encontrado en PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  OPCIONES:" -ForegroundColor Cyan
    Write-Host "  1. Descargar e instalar Python 3.12 manualmente:" -ForegroundColor White
    Write-Host "     https://www.python.org/downloads/release/python-3127/" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. Usar winget (si está disponible):" -ForegroundColor White
    Write-Host "     winget install Python.Python.3.12" -ForegroundColor Green
    Write-Host ""
    Write-Host "  3. Usar chocolatey (si está instalado):" -ForegroundColor White
    Write-Host "     choco install python312" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Después de instalar, ejecuta este script nuevamente." -ForegroundColor Yellow
    Write-Host ""
    $continuar = Read-Host "  ¿Ya instalaste Python 3.12? (s/n)"
    if ($continuar -ne "s" -and $continuar -ne "S") {
        Write-Host "  Migración cancelada. Instala Python 3.12 primero." -ForegroundColor Red
        exit 1
    }
}

# Verificar nuevamente después de la instalación
$python312 = Get-Command python3.12 -ErrorAction SilentlyContinue
if (-not $python312) {
    # Intentar con py launcher
    $py312 = py -3.12 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Python 3.12 encontrado via py launcher" -ForegroundColor Green
        $pythonCmd = "py -3.12"
    } else {
        Write-Host "  [ERROR] Python 3.12 no encontrado" -ForegroundColor Red
        Write-Host "  Por favor, instala Python 3.12 primero." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [OK] Python 3.12 encontrado: $($python312.Source)" -ForegroundColor Green
    $pythonCmd = "python3.12"
}

# Paso 2: Backup del entorno actual
Write-Host ""
Write-Host "[2/6] Creando backup del entorno actual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    $backupName = "venv_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "  [INFO] Creando backup: $backupName" -ForegroundColor Yellow
    Copy-Item -Path "venv" -Destination $backupName -Recurse -ErrorAction SilentlyContinue
    if (Test-Path $backupName) {
        Write-Host "  [OK] Backup creado: $backupName" -ForegroundColor Green
    } else {
        Write-Host "  [ADVERTENCIA] No se pudo crear backup (puede ser por tamaño)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [INFO] No hay entorno virtual existente" -ForegroundColor Yellow
}

# Paso 3: Eliminar entorno antiguo
Write-Host ""
Write-Host "[3/6] Eliminando entorno virtual antiguo..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  [INFO] Eliminando venv/..." -ForegroundColor Yellow
    Remove-Item -Path "venv" -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path "venv")) {
        Write-Host "  [OK] Entorno antiguo eliminado" -ForegroundColor Green
    } else {
        Write-Host "  [ADVERTENCIA] No se pudo eliminar completamente (puede estar en uso)" -ForegroundColor Yellow
        Write-Host "  Cierra todas las terminales y procesos Python, luego ejecuta:" -ForegroundColor Yellow
        Write-Host "  Remove-Item -Path 'venv' -Recurse -Force" -ForegroundColor White
    }
} else {
    Write-Host "  [INFO] No hay entorno virtual para eliminar" -ForegroundColor Yellow
}

# Paso 4: Crear nuevo entorno con Python 3.12
Write-Host ""
Write-Host "[4/6] Creando nuevo entorno virtual con Python 3.12..." -ForegroundColor Yellow
if ($pythonCmd -eq "py -3.12") {
    & py -3.12 -m venv venv
} else {
    & python3.12 -m venv venv
}

if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "  [OK] Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] No se pudo crear el entorno virtual" -ForegroundColor Red
    exit 1
}

# Paso 5: Activar y actualizar pip
Write-Host ""
Write-Host "[5/6] Actualizando pip..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
& python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] pip actualizado" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Error al actualizar pip" -ForegroundColor Red
    exit 1
}

# Paso 6: Instalar dependencias
Write-Host ""
Write-Host "[6/6] Instalando dependencias..." -ForegroundColor Yellow
& pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Dependencias instaladas" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Error al instalar dependencias" -ForegroundColor Red
    exit 1
}

# Verificación final
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VERIFICACION FINAL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$version = & python --version
Write-Host "Python: $version" -ForegroundColor White

$sqlalchemy = & python -c "import sqlalchemy; print(sqlalchemy.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SQLAlchemy: $sqlalchemy" -ForegroundColor White
} else {
    Write-Host "SQLAlchemy: Error al verificar" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[OK] MIGRACION COMPLETADA" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor Yellow
Write-Host "  1. Activa el entorno: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Verifica: python verificar_python.py" -ForegroundColor White
Write-Host "  3. Inicia el servidor: uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""

