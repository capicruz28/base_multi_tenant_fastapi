# app/modules/modulos/application/helpers/rol_plantilla_applier.py
"""
Helper para aplicar plantillas de roles al activar un módulo para un cliente.

Cuando el SUPER ADMIN activa un módulo, este helper:
1. Obtiene todas las plantillas activas del módulo
2. Crea roles para el cliente basados en las plantillas
3. Asigna permisos a los roles según el JSON de permisos de cada plantilla
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json

from app.modules.modulos.presentation.schemas import ModuloRolPlantillaRead
# Importaciones lazy para evitar circular imports
# from app.modules.rbac.application.services.rol_service import RolService
# from app.modules.rbac.application.services.permiso_service import PermisoService
# from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService

logger = logging.getLogger(__name__)


async def aplicar_plantillas_roles(
    cliente_id: UUID,
    modulo_id: UUID,
    activado_por_usuario_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Aplica todas las plantillas de roles activas de un módulo al activar el módulo para un cliente.
    
    Args:
        cliente_id: ID del cliente
        modulo_id: ID del módulo que se está activando
        activado_por_usuario_id: ID del usuario que activa (para auditoría)
        
    Returns:
        Lista de diccionarios con información de los roles creados
    """
    logger.info(f"Aplicando plantillas de roles para módulo {modulo_id} en cliente {cliente_id}")
    
    # Obtener todas las plantillas activas del módulo
    from app.modules.modulos.application.services.modulo_rol_plantilla_service import ModuloRolPlantillaService
    plantillas = await ModuloRolPlantillaService.obtener_plantillas_modulo(modulo_id, solo_activas=True)
    
    if not plantillas:
        logger.info(f"No hay plantillas de roles para el módulo {modulo_id}")
        return []
    
    roles_creados = []
    
    for plantilla in plantillas:
        try:
            # Importación lazy para evitar circular imports
            from app.modules.rbac.application.services.rol_service import RolService
            
            # Crear el rol para el cliente
            rol_data = {
                'nombre': plantilla.nombre_rol,
                'descripcion': plantilla.descripcion or f"Rol creado automáticamente desde plantilla {plantilla.plantilla_id}",
                'es_activo': True
            }
            
            # Crear rol usando el servicio de roles
            rol_creado = await RolService.crear_rol(cliente_id, rol_data)
            logger.info(f"Rol '{rol_creado['nombre']}' creado con ID {rol_creado['rol_id']}")
            
            # Aplicar permisos si hay permisos_json
            permisos_aplicados = 0
            if plantilla.permisos_json:
                permisos_aplicados = await _aplicar_permisos_desde_json(
                    cliente_id,
                    rol_creado['rol_id'],
                    modulo_id,
                    plantilla.permisos_json
                )
            
            roles_creados.append({
                'rol_id': rol_creado['rol_id'],
                'rol_nombre': rol_creado['nombre'],
                'plantilla_id': plantilla.plantilla_id,
                'permisos_aplicados': permisos_aplicados
            })
            
        except Exception as e:
            logger.error(f"Error aplicando plantilla {plantilla.plantilla_id}: {str(e)}", exc_info=True)
            # Continuar con las demás plantillas aunque una falle
            continue
    
    logger.info(f"Plantillas aplicadas: {len(roles_creados)} roles creados para cliente {cliente_id}")
    return roles_creados


async def _aplicar_permisos_desde_json(
    cliente_id: UUID,
    rol_id: UUID,
    modulo_id: UUID,
    permisos_json: str
) -> int:
    """
    Aplica permisos a un rol desde el JSON de permisos de una plantilla.
    
    El JSON tiene la estructura:
    {
      "MENU_CODIGO_1": {"ver": true, "crear": true, "editar": false, ...},
      "MENU_CODIGO_2": {"ver": true, "crear": false, ...}
    }
    
    Returns:
        Número de permisos aplicados
    """
    try:
        permisos_dict = json.loads(permisos_json)
        if not isinstance(permisos_dict, dict):
            logger.error(f"permisos_json no es un objeto válido: {permisos_json}")
            return 0
        
        # Importación lazy para evitar circular imports
        from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
        from app.modules.rbac.application.services.permiso_service import PermisoService
        
        permisos_aplicados = 0
        
        # Obtener todos los menús del módulo para mapear códigos a IDs
        menus = await ModuloMenuService.obtener_menus_modulo(modulo_id, solo_activos=True)
        menus_por_codigo = {m.codigo: m for m in menus if m.codigo}
        
        # Aplicar permisos para cada código de menú
        for menu_codigo, permisos_menu in permisos_dict.items():
            if menu_codigo not in menus_por_codigo:
                logger.warning(f"Código de menú '{menu_codigo}' no encontrado en módulo {modulo_id}")
                continue
            
            menu = menus_por_codigo[menu_codigo]
            
            # Aplicar permisos usando el servicio de permisos
            try:
                await PermisoService.asignar_o_actualizar_permiso(
                    cliente_id=cliente_id,
                    rol_id=rol_id,
                    menu_id=menu.menu_id,
                    puede_ver=permisos_menu.get('ver', False),
                    puede_crear=permisos_menu.get('crear', False),
                    puede_editar=permisos_menu.get('editar', False),
                    puede_eliminar=permisos_menu.get('eliminar', False),
                    puede_exportar=permisos_menu.get('exportar', False),
                    puede_imprimir=permisos_menu.get('imprimir', False)
                    # Nota: puede_aprobar no está en la firma del servicio actual
                )
                permisos_aplicados += 1
            except Exception as e:
                logger.error(f"Error aplicando permisos para menú {menu_codigo}: {str(e)}")
                continue
        
        logger.info(f"Aplicados {permisos_aplicados} permisos al rol {rol_id}")
        return permisos_aplicados
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando permisos_json: {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"Error aplicando permisos desde JSON: {str(e)}", exc_info=True)
        return 0

