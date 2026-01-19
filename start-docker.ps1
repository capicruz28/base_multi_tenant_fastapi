# Script de inicio rápido para Docker (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FastAPI Multi-Tenant - Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker esté corriendo
Write-Host "[1/4] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "[OK] Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker no está instalado o no está corriendo" -ForegroundColor Red
    exit 1
}

# Verificar que docker-compose esté disponible
Write-Host "[2/4] Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "[OK] Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Compose no está disponible" -ForegroundColor Red
    exit 1
}

# Verificar archivo .env.docker
Write-Host "[3/4] Verificando configuración..." -ForegroundColor Yellow
if (Test-Path .env.docker) {
    Write-Host "[OK] Archivo .env.docker encontrado" -ForegroundColor Green
} else {
    Write-Host "[ADVERTENCIA] Archivo .env.docker no existe" -ForegroundColor Yellow
    Write-Host "  Creando desde .env.docker.example..." -ForegroundColor Yellow
    if (Test-Path .env.docker.example) {
        Copy-Item .env.docker.example .env.docker
        Write-Host "[OK] Archivo .env.docker creado. Por favor, edítalo con tus valores." -ForegroundColor Green
    } else {
        Write-Host "[ERROR] .env.docker.example no existe" -ForegroundColor Red
        exit 1
    }
}

# Preguntar qué compose file usar
Write-Host ""
Write-Host "[4/4] Seleccionando configuración..." -ForegroundColor Yellow
Write-Host "  1) docker-compose.yml (solo backend + redis, BD externa)" -ForegroundColor Cyan
Write-Host "  2) docker-compose.dev.yml (backend + redis + SQL Server)" -ForegroundColor Cyan
$choice = Read-Host "Selecciona opción (1 o 2)"

$composeFile = if ($choice -eq "2") { "docker-compose.dev.yml" } else { "docker-compose.yml" }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando servicios con $composeFile..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Construir e iniciar
if ($choice -eq "2") {
    docker-compose -f $composeFile up -d --build
} else {
    docker-compose -f $composeFile up -d --build
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Servicios iniciados!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Health:   http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para ver logs:" -ForegroundColor Yellow
Write-Host "  docker-compose -f $composeFile logs -f backend" -ForegroundColor White
Write-Host ""
Write-Host "Para detener:" -ForegroundColor Yellow
Write-Host "  docker-compose -f $composeFile down" -ForegroundColor White
Write-Host ""


