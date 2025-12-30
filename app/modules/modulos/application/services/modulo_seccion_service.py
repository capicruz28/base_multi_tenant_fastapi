# app/modules/modulos/application/services/modulo_seccion_service.py
"""
Servicio para la gestión de secciones de módulos.

Este servicio implementa la lógica de negocio para operaciones sobre la entidad `modulo_seccion`,
incluyendo CRUD completo, reordenamiento y validaciones de integridad.

Características clave:
- CRUD completo de secciones por módulo
- Validación de códigos únicos dentro del módulo
- Reordenamiento de secciones
- Validación de menús asociados antes de eliminar
"""
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy import select, update, delete, and_, func as sql_func
from uuid import UUID

from app.infrastructure.database.tables_modulos import ModuloSeccionTable, ModuloTable
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
    ModuloSeccionCreate, ModuloSeccionUpdate, ModuloSeccionRead
)
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


class ModuloSeccionService(BaseService):
    """
    Servicio central para la administración de secciones de módulos.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_seccion(seccion_data: ModuloSeccionCreate) -> ModuloSeccionRead:
        """
        Crea una nueva sección en un módulo.
        """
        logger.info(f"Creando nueva sección: {seccion_data.nombre} para módulo {seccion_data.modulo_id}")

        # Validar que el módulo existe
        from app.modules.modulos.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(seccion_data.modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {seccion_data.modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar código único dentro del módulo
        await ModuloSeccionService._validar_codigo_unico_modulo(
            seccion_data.modulo_id, 
            seccion_data.codigo
        )

        # Preparar datos para inserción
        insert_data = {
            'modulo_id': seccion_data.modulo_id,
            'codigo': seccion_data.codigo.upper(),
            'nombre': seccion_data.nombre,
            'descripcion': seccion_data.descripcion,
            'icono': seccion_data.icono,
            'orden': seccion_data.orden,
            'es_seccion_sistema': seccion_data.es_seccion_sistema,
            'es_activo': seccion_data.es_activo,
        }

        from sqlalchemy import insert
        stmt = insert(ModuloSeccionTable).values(**insert_data).returning(ModuloSeccionTable)
        
        resultado = await execute_insert(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear la sección en la base de datos.",
                internal_code="SECTION_CREATION_FAILED"
            )

        logger.info(f"Sección creada exitosamente con ID: {resultado['seccion_id']}")
        return ModuloSeccionRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_codigo_unico_modulo(modulo_id: UUID, codigo: str, excluir_seccion_id: Optional[UUID] = None) -> None:
        """
        Valida que el código sea único dentro del módulo.
        """
        query = select(ModuloSeccionTable.c.seccion_id).where(
            and_(
                ModuloSeccionTable.c.modulo_id == modulo_id,
                ModuloSeccionTable.c.codigo == codigo.upper()
            )
        )
        
        if excluir_seccion_id:
            query = query.where(ModuloSeccionTable.c.seccion_id != excluir_seccion_id)
            
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if resultado:
            raise ConflictError(
                detail=f"Ya existe una sección con el código '{codigo}' en este módulo.",
                internal_code="SECTION_CODE_CONFLICT"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_secciones_modulo(
        modulo_id: UUID,
        solo_activas: bool = True
    ) -> List[ModuloSeccionRead]:
        """
        Obtiene todas las secciones de un módulo.
        """
        query = select(ModuloSeccionTable).where(ModuloSeccionTable.c.modulo_id == modulo_id)
        
        if solo_activas:
            query = query.where(ModuloSeccionTable.c.es_activo == True)
        
        query = query.order_by(ModuloSeccionTable.c.orden, ModuloSeccionTable.c.nombre)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        return [ModuloSeccionRead(**seccion) for seccion in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_seccion_por_id(seccion_id: UUID) -> Optional[ModuloSeccionRead]:
        """
        Obtiene una sección específica por su ID.
        """
        query = select(ModuloSeccionTable).where(ModuloSeccionTable.c.seccion_id == seccion_id)
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            return None
        return ModuloSeccionRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_seccion(seccion_id: UUID, seccion_data: ModuloSeccionUpdate) -> ModuloSeccionRead:
        """
        Actualiza una sección existente.
        """
        logger.info(f"Actualizando sección ID: {seccion_id}")

        # Verificar que la sección existe
        seccion_existente = await ModuloSeccionService.obtener_seccion_por_id(seccion_id)
        if not seccion_existente:
            raise NotFoundError(
                detail=f"Sección con ID {seccion_id} no encontrada.",
                internal_code="SECTION_NOT_FOUND"
            )

        update_dict = seccion_data.model_dump(exclude_unset=True)
        
        # Validar código único si se está actualizando
        if 'codigo' in update_dict:
            if update_dict['codigo'].upper() != seccion_existente.codigo:
                await ModuloSeccionService._validar_codigo_unico_modulo(
                    seccion_existente.modulo_id,
                    update_dict['codigo'],
                    seccion_id
                )
                update_dict['codigo'] = update_dict['codigo'].upper()

        if not update_dict:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )

        stmt = (
            update(ModuloSeccionTable)
            .where(ModuloSeccionTable.c.seccion_id == seccion_id)
            .values(**update_dict)
            .returning(ModuloSeccionTable)
        )

        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la sección.",
                internal_code="SECTION_UPDATE_FAILED"
            )

        logger.info(f"Sección ID {seccion_id} actualizada exitosamente.")
        return ModuloSeccionRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_seccion(seccion_id: UUID) -> bool:
        """
        Elimina una sección (validando que no tenga menús asociados).
        """
        logger.info(f"Intentando eliminar sección ID: {seccion_id}")

        # Verificar que la sección existe
        seccion = await ModuloSeccionService.obtener_seccion_por_id(seccion_id)
        if not seccion:
            raise NotFoundError(
                detail=f"Sección con ID {seccion_id} no encontrada.",
                internal_code="SECTION_NOT_FOUND"
            )

        # Validar que no tenga menús asociados
        from app.infrastructure.database.tables_modulos import ModuloMenuTable
        query_check = select(sql_func.count()).select_from(ModuloMenuTable).where(
            ModuloMenuTable.c.seccion_id == seccion_id
        )
        
        resultado_check = await execute_query(
            query_check,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        menus_asociados = resultado_check[0]['count_1'] if resultado_check else 0

        if menus_asociados > 0:
            raise ValidationError(
                detail=f"No se puede eliminar la sección. Tiene {menus_asociados} menú(s) asociado(s).",
                internal_code="SECTION_HAS_MENUS"
            )

        # Eliminar físicamente (no soft delete para secciones)
        stmt = delete(ModuloSeccionTable).where(ModuloSeccionTable.c.seccion_id == seccion_id)
        
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        logger.info(f"Sección ID {seccion_id} eliminada exitosamente.")
        return True

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_seccion(seccion_id: UUID) -> ModuloSeccionRead:
        """Activa una sección."""
        seccion = await ModuloSeccionService.obtener_seccion_por_id(seccion_id)
        if not seccion:
            raise NotFoundError(
                detail=f"Sección con ID {seccion_id} no encontrada.",
                internal_code="SECTION_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloSeccionTable)
            .where(ModuloSeccionTable.c.seccion_id == seccion_id)
            .values(es_activo=True)
            .returning(ModuloSeccionTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo activar la sección.",
                internal_code="SECTION_ACTIVATION_FAILED"
            )
        return ModuloSeccionRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_seccion(seccion_id: UUID) -> ModuloSeccionRead:
        """Desactiva una sección."""
        seccion = await ModuloSeccionService.obtener_seccion_por_id(seccion_id)
        if not seccion:
            raise NotFoundError(
                detail=f"Sección con ID {seccion_id} no encontrada.",
                internal_code="SECTION_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloSeccionTable)
            .where(ModuloSeccionTable.c.seccion_id == seccion_id)
            .values(es_activo=False)
            .returning(ModuloSeccionTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo desactivar la sección.",
                internal_code="SECTION_DEACTIVATION_FAILED"
            )
        return ModuloSeccionRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def reordenar_secciones(modulo_id: UUID, ordenes: Dict[UUID, int]) -> List[ModuloSeccionRead]:
        """
        Reordena las secciones de un módulo.
        
        Args:
            modulo_id: ID del módulo
            ordenes: Diccionario {seccion_id: nuevo_orden}
        """
        logger.info(f"Reordenando secciones del módulo {modulo_id}")

        # Validar que todas las secciones pertenecen al módulo
        secciones = await ModuloSeccionService.obtener_secciones_modulo(modulo_id, solo_activas=False)
        secciones_ids = {s.seccion_id for s in secciones}
        
        for seccion_id in ordenes.keys():
            if seccion_id not in secciones_ids:
                raise ValidationError(
                    detail=f"Sección {seccion_id} no pertenece al módulo {modulo_id}.",
                    internal_code="SECTION_WRONG_MODULE"
                )

        # Actualizar órdenes
        for seccion_id, nuevo_orden in ordenes.items():
            stmt = (
                update(ModuloSeccionTable)
                .where(ModuloSeccionTable.c.seccion_id == seccion_id)
                .values(orden=nuevo_orden)
            )
            await execute_update(
                stmt,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )

        # Retornar secciones actualizadas
        return await ModuloSeccionService.obtener_secciones_modulo(modulo_id, solo_activas=False)

