#!/bin/bash
# Script de inicio rápido para Docker (Linux/Mac)

echo "========================================"
echo "FastAPI Multi-Tenant - Docker Setup"
echo "========================================"
echo ""

# Verificar que Docker esté corriendo
echo "[1/4] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker no está instalado"
    exit 1
fi
echo "[OK] Docker encontrado: $(docker --version)"

# Verificar que docker-compose esté disponible
echo "[2/4] Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose no está disponible"
    exit 1
fi
echo "[OK] Docker Compose encontrado: $(docker-compose --version)"

# Verificar archivo .env.docker
echo "[3/4] Verificando configuración..."
if [ -f .env.docker ]; then
    echo "[OK] Archivo .env.docker encontrado"
else
    echo "[ADVERTENCIA] Archivo .env.docker no existe"
    echo "  Creando desde .env.docker.example..."
    if [ -f .env.docker.example ]; then
        cp .env.docker.example .env.docker
        echo "[OK] Archivo .env.docker creado. Por favor, edítalo con tus valores."
    else
        echo "[ERROR] .env.docker.example no existe"
        exit 1
    fi
fi

# Preguntar qué compose file usar
echo ""
echo "[4/4] Seleccionando configuración..."
echo "  1) docker-compose.yml (solo backend + redis, BD externa)"
echo "  2) docker-compose.dev.yml (backend + redis + SQL Server)"
read -p "Selecciona opción (1 o 2): " choice

if [ "$choice" = "2" ]; then
    compose_file="docker-compose.dev.yml"
else
    compose_file="docker-compose.yml"
fi

echo ""
echo "========================================"
echo "Iniciando servicios con $compose_file..."
echo "========================================"
echo ""

# Construir e iniciar
docker-compose -f $compose_file up -d --build

echo ""
echo "========================================"
echo "Servicios iniciados!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Docs:     http://localhost:8000/docs"
echo "Health:   http://localhost:8000/health"
echo ""
echo "Para ver logs:"
echo "  docker-compose -f $compose_file logs -f backend"
echo ""
echo "Para detener:"
echo "  docker-compose -f $compose_file down"
echo ""


