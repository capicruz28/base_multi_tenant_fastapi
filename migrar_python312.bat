@echo off
REM Script de migración a Python 3.12 para Windows

echo ============================================================
echo MIGRACION A PYTHON 3.12
echo ============================================================
echo.

REM Paso 1: Verificar Python 3.12
echo [1/6] Verificando Python 3.12...
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.12 --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py -3.12
        echo   [OK] Python 3.12 encontrado via py launcher
    ) else (
        echo   [ERROR] Python 3.12 no encontrado
        echo.
        echo   OPCIONES:
        echo   1. Descargar e instalar Python 3.12 desde:
        echo      https://www.python.org/downloads/
        echo      (Marcar "Add Python to PATH" durante instalacion)
        echo.
        echo   2. O usar py launcher si tienes varias versiones:
        echo      py -3.12 -m venv venv
        echo.
        pause
        exit /b 1
    )
) else (
    python3.12 --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3.12
        echo   [OK] Python 3.12 encontrado
    ) else (
        echo   [ERROR] Python 3.12 no encontrado
        echo.
        echo   OPCIONES:
        echo   1. Descargar e instalar Python 3.12 desde:
        echo      https://www.python.org/downloads/
        echo      (Marcar "Add Python to PATH" durante instalacion)
        echo.
        pause
        exit /b 1
    )
)

REM Paso 2: Backup del entorno actual
echo.
echo [2/6] Creando backup del entorno actual...
if exist venv (
    set BACKUP_NAME=venv_backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    set BACKUP_NAME=!BACKUP_NAME: =0!
    echo   [INFO] Creando backup: %BACKUP_NAME%
    xcopy /E /I /Y venv %BACKUP_NAME% >nul 2>&1
    if exist %BACKUP_NAME% (
        echo   [OK] Backup creado: %BACKUP_NAME%
    ) else (
        echo   [ADVERTENCIA] No se pudo crear backup
    )
) else (
    echo   [INFO] No hay entorno virtual existente
)

REM Paso 3: Eliminar entorno antiguo
echo.
echo [3/6] Eliminando entorno virtual antiguo...
if exist venv (
    echo   [INFO] Eliminando venv\...
    rmdir /S /Q venv
    if not exist venv (
        echo   [OK] Entorno antiguo eliminado
    ) else (
        echo   [ERROR] No se pudo eliminar completamente
        pause
        exit /b 1
    )
) else (
    echo   [INFO] No hay entorno virtual para eliminar
)

REM Paso 4: Crear nuevo entorno con Python 3.12
echo.
echo [4/6] Creando nuevo entorno virtual con Python 3.12...
%PYTHON_CMD% -m venv venv

if exist venv\Scripts\python.exe (
    echo   [OK] Entorno virtual creado
) else (
    echo   [ERROR] No se pudo crear el entorno virtual
    pause
    exit /b 1
)

REM Paso 5: Activar y actualizar pip
echo.
echo [5/6] Actualizando pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel

if %ERRORLEVEL% EQU 0 (
    echo   [OK] pip actualizado
) else (
    echo   [ERROR] Error al actualizar pip
    pause
    exit /b 1
)

REM Paso 6: Instalar dependencias
echo.
echo [6/6] Instalando dependencias...
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo   [OK] Dependencias instaladas
) else (
    echo   [ERROR] Error al instalar dependencias
    pause
    exit /b 1
)

REM Verificación final
echo.
echo ============================================================
echo VERIFICACION FINAL
echo ============================================================
echo.

python --version
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)" 2>nul

echo.
echo ============================================================
echo [OK] MIGRACION COMPLETADA
echo ============================================================
echo.
echo Siguiente paso:
echo   1. Activa el entorno: venv\Scripts\activate.bat
echo   2. Verifica: python verificar_python.py
echo   3. Inicia el servidor: uvicorn app.main:app --reload
echo.
echo IMPORTANTE: Verifica en los logs que aparezca:
echo   "Módulo de connection pooling cargado y activo"
echo.
pause


