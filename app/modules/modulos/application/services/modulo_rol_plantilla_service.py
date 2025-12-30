# app/modules/modulos/application/services/modulo_rol_plantilla_service.py
"""
Servicio para la gestión de plantillas de roles de módulos.

Este servicio implementa la lógica de negocio para operaciones sobre la entidad `modulo_rol_plantilla`,
incluyendo CRUD completo, validación de JSON de permisos, y preview de aplicación.

Características clave:
- CRUD completo de plantillas de roles por módulo
- Validación de estructura JSON de permisos
- Preview de aplicación (mostrar qué se creará sin ejecutar)
- Solo SUPER ADMIN puede crear/editar plantillas globales
"""
from typing import List, Optional, Dict, Any
import logging
import json
from sqlalchemy import select, update, delete, and_, func as sql_func
from uuid import UUID

from app.infrastructure.database.tables_modulos import ModuloRolPlantillaTable, ModuloTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.modulos.presentation.schemas import (
    ModuloRolPlantillaCreate, ModuloRolPlantillaUpdate, ModuloRolPlantillaRead
)
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


class ModuloRolPlantillaService(BaseService):
    """
    Servicio central para la administración de plantillas de roles de módulos.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_plantilla(plantilla_data: ModuloRolPlantillaCreate) -> ModuloRolPlantillaRead:
        """
        Crea una nueva plantilla de rol para un módulo.
        Solo accesible para SUPER ADMIN.
        """
        logger.info(f"Creando nueva plantilla: {plantilla_data.nombre_rol} para módulo {plantilla_data.modulo_id}")

        # Validar que el módulo existe
        from app.modules.modulos.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(plantilla_data.modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {plantilla_data.modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar JSON de permisos si se proporciona
        if plantilla_data.permisos_json:
            await ModuloRolPlantillaService.validar_json_permisos(plantilla_data.permisos_json, plantilla_data.modulo_id)

        # Preparar datos para inserción
        insert_data = {
            'modulo_id': plantilla_data.modulo_id,
            'nombre_rol': plantilla_data.nombre_rol,
            'descripcion': plantilla_data.descripcion,
            'nivel_acceso': plantilla_data.nivel_acceso,
            'permisos_json': plantilla_data.permisos_json,
            'es_activo': plantilla_data.es_activo,
            'orden': plantilla_data.orden,
        }

        from sqlalchemy import insert
        stmt = insert(ModuloRolPlantillaTable).values(**insert_data).returning(ModuloRolPlantillaTable)
        
        resultado = await execute_insert(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear la plantilla en la base de datos.",
                internal_code="PLANTILLA_CREATION_FAILED"
            )

        logger.info(f"Plantilla creada exitosamente con ID: {resultado['plantilla_id']}")
        return ModuloRolPlantillaRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_plantillas_modulo(
        modulo_id: UUID,
        solo_activas: bool = True
    ) -> List[ModuloRolPlantillaRead]:
        """
        Obtiene todas las plantillas de un módulo.
        """
        query = select(ModuloRolPlantillaTable).where(ModuloRolPlantillaTable.c.modulo_id == modulo_id)
        
        if solo_activas:
            query = query.where(ModuloRolPlantillaTable.c.es_activo == True)
        
        query = query.order_by(ModuloRolPlantillaTable.c.orden, ModuloRolPlantillaTable.c.nombre_rol)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        return [ModuloRolPlantillaRead(**plantilla) for plantilla in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_plantilla_por_id(plantilla_id: UUID) -> Optional[ModuloRolPlantillaRead]:
        """
        Obtiene una plantilla específica por su ID.
        """
        query = select(ModuloRolPlantillaTable).where(ModuloRolPlantillaTable.c.plantilla_id == plantilla_id)
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            return None
        return ModuloRolPlantillaRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_plantilla(plantilla_id: UUID, plantilla_data: ModuloRolPlantillaUpdate) -> ModuloRolPlantillaRead:
        """
        Actualiza una plantilla existente.
        Solo accesible para SUPER ADMIN.
        """
        logger.info(f"Actualizando plantilla ID: {plantilla_id}")

        # Verificar que la plantilla existe
        plantilla_existente = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla_existente:
            raise NotFoundError(
                detail=f"Plantilla con ID {plantilla_id} no encontrada.",
                internal_code="PLANTILLA_NOT_FOUND"
            )

        update_dict = plantilla_data.model_dump(exclude_unset=True)
        
        # Validar JSON de permisos si se está actualizando
        if 'permisos_json' in update_dict and update_dict['permisos_json']:
            await ModuloRolPlantillaService.validar_json_permisos(
                update_dict['permisos_json'],
                plantilla_existente.modulo_id
            )

        if not update_dict:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )

        stmt = (
            update(ModuloRolPlantillaTable)
            .where(ModuloRolPlantillaTable.c.plantilla_id == plantilla_id)
            .values(**update_dict)
            .returning(ModuloRolPlantillaTable)
        )

        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la plantilla.",
                internal_code="PLANTILLA_UPDATE_FAILED"
            )

        logger.info(f"Plantilla ID {plantilla_id} actualizada exitosamente.")
        return ModuloRolPlantillaRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_plantilla(plantilla_id: UUID) -> bool:
        """
        Elimina una plantilla.
        """
        logger.info(f"Intentando eliminar plantilla ID: {plantilla_id}")

        # Verificar que la plantilla existe
        plantilla = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla:
            raise NotFoundError(
                detail=f"Plantilla con ID {plantilla_id} no encontrada.",
                internal_code="PLANTILLA_NOT_FOUND"
            )

        # Eliminar físicamente
        stmt = delete(ModuloRolPlantillaTable).where(ModuloRolPlantillaTable.c.plantilla_id == plantilla_id)
        
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        logger.info(f"Plantilla ID {plantilla_id} eliminada exitosamente.")
        return True

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_plantilla(plantilla_id: UUID) -> ModuloRolPlantillaRead:
        """Activa una plantilla."""
        plantilla = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla:
            raise NotFoundError(
                detail=f"Plantilla con ID {plantilla_id} no encontrada.",
                internal_code="PLANTILLA_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloRolPlantillaTable)
            .where(ModuloRolPlantillaTable.c.plantilla_id == plantilla_id)
            .values(es_activo=True)
            .returning(ModuloRolPlantillaTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo activar la plantilla.",
                internal_code="PLANTILLA_ACTIVATION_FAILED"
            )
        return ModuloRolPlantillaRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_plantilla(plantilla_id: UUID) -> ModuloRolPlantillaRead:
        """Desactiva una plantilla."""
        plantilla = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla:
            raise NotFoundError(
                detail=f"Plantilla con ID {plantilla_id} no encontrada.",
                internal_code="PLANTILLA_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloRolPlantillaTable)
            .where(ModuloRolPlantillaTable.c.plantilla_id == plantilla_id)
            .values(es_activo=False)
            .returning(ModuloRolPlantillaTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo desactivar la plantilla.",
                internal_code="PLANTILLA_DEACTIVATION_FAILED"
            )
        return ModuloRolPlantillaRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def reordenar_plantillas(modulo_id: UUID, ordenes: Dict[UUID, int]) -> List[ModuloRolPlantillaRead]:
        """
        Reordena las plantillas de un módulo.
        """
        logger.info(f"Reordenando plantillas del módulo {modulo_id}")

        # Validar que todas las plantillas pertenecen al módulo
        plantillas = await ModuloRolPlantillaService.obtener_plantillas_modulo(modulo_id, solo_activas=False)
        plantillas_ids = {p.plantilla_id for p in plantillas}
        
        for plantilla_id in ordenes.keys():
            if plantilla_id not in plantillas_ids:
                raise ValidationError(
                    detail=f"Plantilla {plantilla_id} no pertenece al módulo {modulo_id}.",
                    internal_code="PLANTILLA_WRONG_MODULE"
                )

        # Actualizar órdenes
        for plantilla_id, nuevo_orden in ordenes.items():
            stmt = (
                update(ModuloRolPlantillaTable)
                .where(ModuloRolPlantillaTable.c.plantilla_id == plantilla_id)
                .values(orden=nuevo_orden)
            )
            await execute_update(
                stmt,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )

        # Retornar plantillas actualizadas
        return await ModuloRolPlantillaService.obtener_plantillas_modulo(modulo_id, solo_activas=False)

    @staticmethod
    @BaseService.handle_service_errors
    async def validar_json_permisos(permisos_json: str, modulo_id: UUID) -> Dict[str, Any]:
        """
        Valida la estructura del JSON de permisos y verifica que los códigos de menú existan.
        
        Returns:
            Diccionario con información de validación
        """
        try:
            permisos_dict = json.loads(permisos_json)
            if not isinstance(permisos_dict, dict):
                raise ValidationError(
                    detail="permisos_json debe ser un objeto JSON",
                    internal_code="INVALID_PERMISOS_JSON_FORMAT"
                )
            
            # Obtener menús del módulo para validar códigos
            from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
            menus = await ModuloMenuService.obtener_menus_modulo(modulo_id, solo_activos=True)
            menus_por_codigo = {m.codigo: m for m in menus if m.codigo}
            
            codigos_invalidos = []
            permisos_validos = ['ver', 'crear', 'editar', 'eliminar', 'exportar', 'imprimir', 'aprobar']
            
            for menu_codigo, permisos_menu in permisos_dict.items():
                # Validar que el código de menú existe
                if menu_codigo not in menus_por_codigo:
                    codigos_invalidos.append(menu_codigo)
                    continue
                
                # Validar estructura de permisos
                if not isinstance(permisos_menu, dict):
                    raise ValidationError(
                        detail=f"Los permisos para '{menu_codigo}' deben ser un objeto",
                        internal_code="INVALID_PERMISOS_STRUCTURE"
                    )
                
                # Validar que todos los permisos sean booleanos
                for permiso, valor in permisos_menu.items():
                    if permiso not in permisos_validos:
                        raise ValidationError(
                            detail=f"Permiso '{permiso}' no válido. Permisos válidos: {', '.join(permisos_validos)}",
                            internal_code="INVALID_PERMISO_NAME"
                        )
                    if not isinstance(valor, bool):
                        raise ValidationError(
                            detail=f"El valor del permiso '{permiso}' para '{menu_codigo}' debe ser booleano",
                            internal_code="INVALID_PERMISO_VALUE"
                        )
            
            if codigos_invalidos:
                raise ValidationError(
                    detail=f"Códigos de menú no encontrados en el módulo: {', '.join(codigos_invalidos)}",
                    internal_code="MENU_CODES_NOT_FOUND"
                )
            
            return {
                "valido": True,
                "total_menus": len(permisos_dict),
                "menus_validados": list(permisos_dict.keys())
            }
            
        except json.JSONDecodeError:
            raise ValidationError(
                detail="permisos_json debe ser un JSON válido",
                internal_code="INVALID_PERMISOS_JSON"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def preview_aplicacion(plantilla_id: UUID, cliente_id: UUID) -> Dict[str, Any]:
        """
        Muestra un preview de qué se creará al aplicar la plantilla (sin ejecutar).
        """
        plantilla = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla:
            raise NotFoundError(
                detail=f"Plantilla con ID {plantilla_id} no encontrada.",
                internal_code="PLANTILLA_NOT_FOUND"
            )
        
        preview = {
            "plantilla_id": plantilla_id,
            "plantilla_nombre": plantilla.nombre_rol,
            "cliente_id": cliente_id,
            "rol_a_crear": {
                "nombre": plantilla.nombre_rol,
                "descripcion": plantilla.descripcion,
                "nivel_acceso": plantilla.nivel_acceso,
                "es_rol_sistema": False
            },
            "permisos_a_aplicar": []
        }
        
        if plantilla.permisos_json:
            try:
                permisos_dict = json.loads(plantilla.permisos_json)
                from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
                menus = await ModuloMenuService.obtener_menus_modulo(plantilla.modulo_id, solo_activos=True)
                menus_por_codigo = {m.codigo: m for m in menus if m.codigo}
                
                for menu_codigo, permisos_menu in permisos_dict.items():
                    if menu_codigo in menus_por_codigo:
                        menu = menus_por_codigo[menu_codigo]
                        preview["permisos_a_aplicar"].append({
                            "menu_id": str(menu.menu_id),
                            "menu_codigo": menu_codigo,
                            "menu_nombre": menu.nombre,
                            "permisos": permisos_menu
                        })
            except Exception as e:
                logger.error(f"Error generando preview: {str(e)}")
                preview["error"] = f"Error procesando permisos_json: {str(e)}"
        
        return preview

