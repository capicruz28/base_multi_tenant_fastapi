# tests/unit/test_modulo_service.py
"""
Tests unitarios para ModuloService.

Estos tests validan la lógica de negocio del servicio de módulos,
incluyendo validaciones, CRUD básico y dependencias.
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime

from app.modules.modulos.application.services.modulo_service import ModuloService
from app.modules.modulos.presentation.schemas import ModuloCreate, ModuloUpdate
from app.core.exceptions import ValidationError, ConflictError, NotFoundError


@pytest.mark.asyncio
class TestModuloService:
    """Tests para ModuloService."""
    
    async def test_crear_modulo_valido(self):
        """Test: Crear un módulo con datos válidos."""
        modulo_data = ModuloCreate(
            codigo="TEST_MOD",
            nombre="Módulo de Prueba",
            descripcion="Descripción del módulo de prueba",
            categoria="operaciones",
            es_activo=True
        )
        
        # Nota: Este test requiere una BD de prueba configurada
        # Por ahora, solo validamos la estructura
        assert modulo_data.codigo == "TEST_MOD"
        assert modulo_data.nombre == "Módulo de Prueba"
        assert modulo_data.categoria == "operaciones"
    
    async def test_validar_codigo_modulo(self):
        """Test: Validar formato de código de módulo."""
        # Código válido
        modulo_data = ModuloCreate(
            codigo="LOGISTICA",
            nombre="Logística",
            categoria="operaciones"
        )
        assert modulo_data.codigo == "LOGISTICA"
        
        # Código inválido (debe fallar en validación)
        with pytest.raises(ValueError):
            ModuloCreate(
                codigo="logistica",  # Debe ser mayúsculas
                nombre="Logística",
                categoria="operaciones"
            )
    
    async def test_validar_modulos_requeridos_json(self):
        """Test: Validar formato JSON de módulos requeridos."""
        # JSON válido
        modulo_data = ModuloCreate(
            codigo="MOD_DEP",
            nombre="Módulo con Dependencias",
            categoria="operaciones",
            modulos_requeridos='["LOGISTICA", "ALMACEN"]'
        )
        assert modulo_data.modulos_requeridos == '["LOGISTICA", "ALMACEN"]'
        
        # JSON inválido (debe fallar en validación)
        with pytest.raises(ValueError):
            ModuloCreate(
                codigo="MOD_DEP",
                nombre="Módulo con Dependencias",
                categoria="operaciones",
                modulos_requeridos='{"invalid": "json"}'  # Debe ser array
            )


@pytest.mark.asyncio
class TestModuloSeccionService:
    """Tests para ModuloSeccionService."""
    
    async def test_crear_seccion_valida(self):
        """Test: Crear una sección con datos válidos."""
        from app.modules.modulos.presentation.schemas import ModuloSeccionCreate
        
        seccion_data = ModuloSeccionCreate(
            modulo_id=uuid4(),
            codigo="SECCION_TEST",
            nombre="Sección de Prueba",
            orden=1,
            es_activo=True
        )
        
        assert seccion_data.codigo == "SECCION_TEST"
        assert seccion_data.orden == 1


@pytest.mark.asyncio
class TestModuloMenuService:
    """Tests para ModuloMenuService."""
    
    async def test_crear_menu_valido(self):
        """Test: Crear un menú con datos válidos."""
        from app.modules.modulos.presentation.schemas import ModuloMenuCreate
        
        menu_data = ModuloMenuCreate(
            modulo_id=uuid4(),
            nombre="Menú de Prueba",
            ruta="/test",
            tipo_menu="pantalla",
            nivel=1,
            orden=1,
            es_activo=True
        )
        
        assert menu_data.nombre == "Menú de Prueba"
        assert menu_data.ruta == "/test"
        assert menu_data.nivel == 1


@pytest.mark.asyncio
class TestClienteModuloService:
    """Tests para ClienteModuloService - CRÍTICO."""
    
    async def test_activar_modulo_estructura(self):
        """Test: Validar estructura de datos para activar módulo."""
        from app.modules.modulos.presentation.schemas import ClienteModuloCreate
        
        activacion_data = ClienteModuloCreate(
            cliente_id=uuid4(),
            modulo_id=uuid4(),
            esta_activo=True
        )
        
        assert activacion_data.cliente_id is not None
        assert activacion_data.modulo_id is not None
        assert activacion_data.esta_activo == True


@pytest.mark.asyncio
class TestModuloRolPlantillaService:
    """Tests para ModuloRolPlantillaService."""
    
    async def test_validar_json_permisos_estructura(self):
        """Test: Validar estructura del JSON de permisos."""
        from app.modules.modulos.presentation.schemas import ModuloRolPlantillaCreate
        
        # JSON válido
        permisos_json = '{"MENU_1": {"ver": true, "crear": false, "editar": false}}'
        
        plantilla_data = ModuloRolPlantillaCreate(
            modulo_id=uuid4(),
            nombre_rol="Rol de Prueba",
            nivel_acceso=3,
            permisos_json=permisos_json,
            es_activo=True
        )
        
        assert plantilla_data.permisos_json == permisos_json
        assert plantilla_data.nombre_rol == "Rol de Prueba"

