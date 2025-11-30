#!/bin/bash
# Script de migración a Python 3.12 para Linux/Mac

echo "============================================================"
echo "MIGRACION A PYTHON 3.12"
echo "============================================================"
echo ""

# Paso 1: Verificar Python 3.12
echo "[1/6] Verificando Python 3.12..."
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "  [OK] Python 3.12 encontrado: $(which python3.12)"
elif command -v pyenv &> /dev/null; then
    echo "  [INFO] pyenv detectado, instalando Python 3.12..."
    pyenv install 3.12.7
    pyenv local 3.12.7
    PYTHON_CMD="python"
    echo "  [OK] Python 3.12 instalado via pyenv"
else
    echo "  [ERROR] Python 3.12 no encontrado"
    echo ""
    echo "  OPCIONES:"
    echo "  1. Instalar con pyenv:"
    echo "     pyenv install 3.12.7"
    echo "     pyenv local 3.12.7"
    echo ""
    echo "  2. Instalar con package manager:"
    echo "     # Ubuntu/Debian:"
    echo "     sudo apt install python3.12 python3.12-venv"
    echo ""
    echo "     # macOS (Homebrew):"
    echo "     brew install python@3.12"
    echo ""
    exit 1
fi

# Paso 2: Backup del entorno actual
echo ""
echo "[2/6] Creando backup del entorno actual..."
if [ -d "venv" ]; then
    BACKUP_NAME="venv_backup_$(date +%Y%m%d_%H%M%S)"
    echo "  [INFO] Creando backup: $BACKUP_NAME"
    cp -r venv "$BACKUP_NAME" 2>/dev/null
    if [ -d "$BACKUP_NAME" ]; then
        echo "  [OK] Backup creado: $BACKUP_NAME"
    else
        echo "  [ADVERTENCIA] No se pudo crear backup"
    fi
else
    echo "  [INFO] No hay entorno virtual existente"
fi

# Paso 3: Eliminar entorno antiguo
echo ""
echo "[3/6] Eliminando entorno virtual antiguo..."
if [ -d "venv" ]; then
    echo "  [INFO] Eliminando venv/..."
    rm -rf venv
    if [ ! -d "venv" ]; then
        echo "  [OK] Entorno antiguo eliminado"
    else
        echo "  [ERROR] No se pudo eliminar completamente"
        exit 1
    fi
else
    echo "  [INFO] No hay entorno virtual para eliminar"
fi

# Paso 4: Crear nuevo entorno con Python 3.12
echo ""
echo "[4/6] Creando nuevo entorno virtual con Python 3.12..."
$PYTHON_CMD -m venv venv

if [ -f "venv/bin/python" ] || [ -f "venv/Scripts/python.exe" ]; then
    echo "  [OK] Entorno virtual creado"
else
    echo "  [ERROR] No se pudo crear el entorno virtual"
    exit 1
fi

# Paso 5: Activar y actualizar pip
echo ""
echo "[5/6] Actualizando pip..."
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

if [ $? -eq 0 ]; then
    echo "  [OK] pip actualizado"
else
    echo "  [ERROR] Error al actualizar pip"
    exit 1
fi

# Paso 6: Instalar dependencias
echo ""
echo "[6/6] Instalando dependencias..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "  [OK] Dependencias instaladas"
else
    echo "  [ERROR] Error al instalar dependencias"
    exit 1
fi

# Verificación final
echo ""
echo "============================================================"
echo "VERIFICACION FINAL"
echo "============================================================"
echo ""

VERSION=$(python --version)
echo "Python: $VERSION"

SQLALCHEMY=$(python -c "import sqlalchemy; print(sqlalchemy.__version__)" 2>&1)
if [ $? -eq 0 ]; then
    echo "SQLAlchemy: $SQLALCHEMY"
else
    echo "SQLAlchemy: Error al verificar"
fi

echo ""
echo "============================================================"
echo "[OK] MIGRACION COMPLETADA"
echo "============================================================"
echo ""
echo "Siguiente paso:"
echo "  1. Activa el entorno: source venv/bin/activate"
echo "  2. Verifica: python verificar_python.py"
echo "  3. Inicia el servidor: uvicorn app.main:app --reload"
echo ""

