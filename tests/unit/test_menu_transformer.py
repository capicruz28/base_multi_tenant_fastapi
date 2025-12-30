# tests/unit/test_menu_transformer.py
"""
Tests unitarios para el transformador de menú del usuario.

Estos tests validan la transformación del resultado del SP
a estructura jerárquica JSON.
"""
import pytest
from uuid import UUID, uuid4

from app.modules.modulos.application.helpers.menu_transformer import transformar_sp_menu_usuario


@pytest.mark.asyncio
class TestMenuTransformer:
    """Tests para el transformador de menú."""
    
    async def test_transformar_sp_resultado_vacio(self):
        """Test: Transformar resultado vacío del SP."""
        resultado_sp = []
        menu_response = transformar_sp_menu_usuario(resultado_sp)
        
        assert menu_response.modulos == []
    
    async def test_transformar_sp_resultado_simple(self):
        """Test: Transformar resultado simple del SP."""
        modulo_id = uuid4()
        seccion_id = uuid4()
        menu_id = uuid4()
        
        resultado_sp = [
            {
                'modulo_id': modulo_id,
                'modulo_codigo': 'LOGISTICA',
                'modulo_nombre': 'Logística',
                'modulo_icono': 'local_shipping',
                'modulo_color': '#FF9800',
                'modulo_categoria': 'operaciones',
                'modulo_orden': 1,
                'seccion_id': seccion_id,
                'seccion_codigo': 'RUTAS',
                'seccion_nombre': 'Gestión de Rutas',
                'seccion_icono': 'route',
                'seccion_orden': 1,
                'menu_id': menu_id,
                'menu_codigo': 'LOGISTICA_RUTAS_LISTA',
                'menu_nombre': 'Lista de Rutas',
                'menu_icono': 'route',
                'menu_ruta': '/logistica/rutas',
                'menu_nivel': 1,
                'menu_tipo': 'pantalla',
                'menu_orden': 1,
                'menu_padre_id': None,
                'puede_ver': True,
                'puede_crear': True,
                'puede_editar': False,
                'puede_eliminar': False,
                'puede_exportar': False,
                'puede_imprimir': False,
                'puede_aprobar': False,
            }
        ]
        
        menu_response = transformar_sp_menu_usuario(resultado_sp)
        
        assert len(menu_response.modulos) == 1
        assert menu_response.modulos[0].codigo == 'LOGISTICA'
        assert len(menu_response.modulos[0].secciones) == 1
        assert len(menu_response.modulos[0].secciones[0].menus) == 1
        assert menu_response.modulos[0].secciones[0].menus[0].nombre == 'Lista de Rutas'
        assert menu_response.modulos[0].secciones[0].menus[0].permisos.ver == True
    
    async def test_transformar_sp_resultado_jerarquico(self):
        """Test: Transformar resultado con submenús."""
        modulo_id = uuid4()
        seccion_id = uuid4()
        menu_padre_id = uuid4()
        menu_hijo_id = uuid4()
        
        resultado_sp = [
            {
                'modulo_id': modulo_id,
                'modulo_codigo': 'TEST',
                'modulo_nombre': 'Test',
                'modulo_icono': None,
                'modulo_color': '#1976D2',
                'modulo_categoria': 'operaciones',
                'modulo_orden': 1,
                'seccion_id': seccion_id,
                'seccion_codigo': 'SECCION',
                'seccion_nombre': 'Sección',
                'seccion_icono': None,
                'seccion_orden': 1,
                'menu_id': menu_padre_id,
                'menu_codigo': 'MENU_PADRE',
                'menu_nombre': 'Menú Padre',
                'menu_icono': None,
                'menu_ruta': '/padre',
                'menu_nivel': 1,
                'menu_tipo': 'pantalla',
                'menu_orden': 1,
                'menu_padre_id': None,
                'puede_ver': True,
                'puede_crear': False,
                'puede_editar': False,
                'puede_eliminar': False,
                'puede_exportar': False,
                'puede_imprimir': False,
                'puede_aprobar': False,
            },
            {
                'modulo_id': modulo_id,
                'modulo_codigo': 'TEST',
                'modulo_nombre': 'Test',
                'modulo_icono': None,
                'modulo_color': '#1976D2',
                'modulo_categoria': 'operaciones',
                'modulo_orden': 1,
                'seccion_id': seccion_id,
                'seccion_codigo': 'SECCION',
                'seccion_nombre': 'Sección',
                'seccion_icono': None,
                'seccion_orden': 1,
                'menu_id': menu_hijo_id,
                'menu_codigo': 'MENU_HIJO',
                'menu_nombre': 'Menú Hijo',
                'menu_icono': None,
                'menu_ruta': '/padre/hijo',
                'menu_nivel': 2,
                'menu_tipo': 'pantalla',
                'menu_orden': 1,
                'menu_padre_id': menu_padre_id,
                'puede_ver': True,
                'puede_crear': False,
                'puede_editar': False,
                'puede_eliminar': False,
                'puede_exportar': False,
                'puede_imprimir': False,
                'puede_aprobar': False,
            }
        ]
        
        menu_response = transformar_sp_menu_usuario(resultado_sp)
        
        assert len(menu_response.modulos) == 1
        assert len(menu_response.modulos[0].secciones) == 1
        assert len(menu_response.modulos[0].secciones[0].menus) == 1
        # El menú padre debe tener un submenú
        assert len(menu_response.modulos[0].secciones[0].menus[0].submenus) == 1
        assert menu_response.modulos[0].secciones[0].menus[0].submenus[0].nombre == 'Menú Hijo'

