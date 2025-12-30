# app/modules/modulos/application/services/modulo_service.py
"""
Servicio para la gestión del catálogo de módulos ERP del sistema.

Este servicio implementa la lógica de negocio para operaciones sobre la entidad `modulo`,
incluyendo la gestión del catálogo de módulos disponibles, validación de códigos únicos,
validación de dependencias entre módulos, y consultas optimizadas.

Características clave:
- Gestión centralizada del catálogo de módulos del sistema
- Validación de códigos de módulo únicos
- Validación de dependencias entre módulos (JSON)
- Consultas optimizadas para activación por cliente
- Soporte para módulos core y módulos opcionales con licencia
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import List, Optional, Dict, Any
import logging
import json
from sqlalchemy import select, update, delete, and_, or_, func as sql_func
from sqlalchemy import text
from uuid import UUID

from app.infrastructure.database.tables_modulos import ModuloTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.modulos.presentation.schemas import ModuloCreate, ModuloUpdate, ModuloRead
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


class ModuloService(BaseService):
    """
    Servicio central para la administración del catálogo de módulos del sistema.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos(
        skip: int = 0, 
        limit: int = 100,
        solo_activos: bool = True,
        categoria: Optional[str] = None
    ) -> List[ModuloRead]:
        """
        Obtiene la lista de módulos del sistema con paginación.
        """
        logger.info(f"Obteniendo catálogo de módulos - skip: {skip}, limit: {limit}")

        query = select(ModuloTable)
        
        # Filtros
        conditions = []
        if solo_activos:
            conditions.append(ModuloTable.c.es_activo == True)
        if categoria:
            conditions.append(ModuloTable.c.categoria == categoria)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Ordenamiento y paginación
        query = query.order_by(ModuloTable.c.orden, ModuloTable.c.nombre)
        query = query.offset(skip).limit(limit)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        return [ModuloRead(**modulo) for modulo in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_por_id(modulo_id: UUID) -> Optional[ModuloRead]:
        """
        Obtiene un módulo específico por su ID.
        """
        query = select(ModuloTable).where(ModuloTable.c.modulo_id == modulo_id)
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            return None
        return ModuloRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_por_codigo(codigo: str) -> Optional[ModuloRead]:
        """
        Obtiene un módulo específico por su código único.
        """
        if not codigo:
            raise ValidationError(
                detail="El código de módulo es obligatorio.",
                internal_code="MODULE_CODE_REQUIRED"
            )

        query = select(ModuloTable).where(ModuloTable.c.codigo == codigo.upper())
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            return None
        return ModuloRead(**resultado[0])

    @staticmethod
    async def _validar_codigo_modulo_unico(codigo: str, modulo_id: Optional[UUID] = None) -> None:
        """
        Valida que el código de módulo sea único en el sistema.
        
        Nota: Este método es privado y se llama desde métodos que ya tienen @handle_service_errors,
        por lo que no necesita el decorador para evitar doble manejo de errores.
        """
        if not codigo:
            raise ValidationError(
                detail="El código de módulo no puede estar vacío.",
                internal_code="MODULE_CODE_EMPTY"
            )
        
        # Usar query RAW SQL para evitar problemas con SQLAlchemy
        from sqlalchemy import text
        
        try:
            if modulo_id:
                query_raw = text("""
                    SELECT modulo_id 
                    FROM modulo 
                    WHERE codigo = :codigo AND modulo_id != :modulo_id
                """).bindparams(codigo=codigo.upper(), modulo_id=str(modulo_id))
            else:
                query_raw = text("""
                    SELECT modulo_id 
                    FROM modulo 
                    WHERE codigo = :codigo
                """).bindparams(codigo=codigo.upper())
            
            resultado = await execute_query(
                query_raw,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )
            
            if resultado:
                raise ConflictError(
                    detail=f"El código de módulo '{codigo}' ya está en uso.",
                    internal_code="MODULE_CODE_CONFLICT"
                )
        except ConflictError:
            # Re-lanzar ConflictError sin modificar
            raise
        except Exception as e:
            logger.error(f"Error en _validar_codigo_modulo_unico: {str(e)}", exc_info=True)
            raise ServiceError(
                status_code=500,
                detail=f"Error al validar código de módulo: {str(e)}",
                internal_code="MODULE_CODE_VALIDATION_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_dependencias_modulos(modulos_requeridos_json: Optional[str]) -> None:
        """
        Valida que los módulos requeridos existan y estén activos.
        """
        if not modulos_requeridos_json:
            return
        
        try:
            modulos_requeridos = json.loads(modulos_requeridos_json)
            if not isinstance(modulos_requeridos, list):
                raise ValidationError(
                    detail="modulos_requeridos debe ser un array JSON",
                    internal_code="INVALID_MODULOS_REQUERIDOS_FORMAT"
                )
            
            # Verificar que cada módulo requerido exista y esté activo
            for codigo_modulo in modulos_requeridos:
                if not isinstance(codigo_modulo, str):
                    raise ValidationError(
                        detail="Todos los elementos de modulos_requeridos deben ser strings",
                        internal_code="INVALID_MODULOS_REQUERIDOS_FORMAT"
                    )
                
                modulo = await ModuloService.obtener_modulo_por_codigo(codigo_modulo)
                if not modulo:
                    raise ValidationError(
                        detail=f"Módulo requerido '{codigo_modulo}' no existe",
                        internal_code="MODULE_REQUIRED_NOT_FOUND"
                    )
                if not modulo.es_activo:
                    raise ValidationError(
                        detail=f"Módulo requerido '{codigo_modulo}' no está activo",
                        internal_code="MODULE_REQUIRED_NOT_ACTIVE"
                    )
        except json.JSONDecodeError:
            raise ValidationError(
                detail="modulos_requeridos debe ser un JSON válido",
                internal_code="INVALID_MODULOS_REQUERIDOS_JSON"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_modulo(modulo_data: ModuloCreate) -> ModuloRead:
        """
        Crea un nuevo módulo en el catálogo del sistema.
        """
        logger.info(f"Creando nuevo módulo: {modulo_data.nombre}")

        # Validaciones de unicidad
        await ModuloService._validar_codigo_modulo_unico(modulo_data.codigo)
        
        # Validar dependencias si se proporcionan
        if modulo_data.modulos_requeridos:
            await ModuloService._validar_dependencias_modulos(modulo_data.modulos_requeridos)

        # Preparar datos para inserción
        insert_data = {
            'codigo': modulo_data.codigo.upper(),
            'nombre': modulo_data.nombre,
            'descripcion': modulo_data.descripcion,
            'icono': modulo_data.icono,
            'color': modulo_data.color,
            'categoria': modulo_data.categoria,
            'es_core': modulo_data.es_core,
            'requiere_licencia': modulo_data.requiere_licencia,
            'precio_mensual': modulo_data.precio_mensual,
            'modulos_requeridos': modulo_data.modulos_requeridos,
            'orden': modulo_data.orden,
            'es_activo': modulo_data.es_activo,
            'configuracion_defecto': modulo_data.configuracion_defecto,
        }

        # Insertar usando SQLAlchemy Core
        from sqlalchemy import insert
        stmt = insert(ModuloTable).values(**insert_data).returning(ModuloTable)
        
        resultado = await execute_insert(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear el módulo en la base de datos.",
                internal_code="MODULE_CREATION_FAILED"
            )

        logger.info(f"Módulo creado exitosamente con ID: {resultado['modulo_id']}")
        return ModuloRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_modulo(modulo_id: UUID, modulo_data: ModuloUpdate) -> ModuloRead:
        """
        Actualiza un módulo existente en el catálogo del sistema.
        """
        logger.info(f"Actualizando módulo ID: {modulo_id}")

        # Verificar que el módulo existe
        modulo_existente = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo_existente:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar unicidad si se está actualizando el código
        update_dict = modulo_data.model_dump(exclude_unset=True)
        
        # Solo validar código si se está actualizando y es diferente
        if 'codigo' in update_dict and update_dict['codigo']:
            if update_dict['codigo'].upper() != modulo_existente.codigo.upper():
                logger.info(f"Validando código único: {update_dict['codigo']} (excluyendo módulo {modulo_id})")
                await ModuloService._validar_codigo_modulo_unico(update_dict['codigo'], modulo_id)
                update_dict['codigo'] = update_dict['codigo'].upper()
            else:
                # Si el código es el mismo, no actualizarlo
                update_dict.pop('codigo', None)

        # Validar dependencias si se actualizan
        if 'modulos_requeridos' in update_dict:
            await ModuloService._validar_dependencias_modulos(update_dict['modulos_requeridos'])

        # Agregar fecha de actualización
        update_dict['fecha_actualizacion'] = sql_func.getdate()

        if not update_dict:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )

        # Actualizar usando SQLAlchemy Core
        stmt = (
            update(ModuloTable)
            .where(ModuloTable.c.modulo_id == modulo_id)
            .values(**update_dict)
            .returning(ModuloTable)
        )

        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar el módulo.",
                internal_code="MODULE_UPDATE_FAILED"
            )

        logger.info(f"Módulo ID {modulo_id} actualizado exitosamente.")
        return ModuloRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_modulo(modulo_id: UUID) -> bool:
        """
        Elimina (desactiva) un módulo del catálogo del sistema.
        Implementa eliminación lógica (soft delete) para mantener integridad referencial.
        
        Validaciones:
        - No se puede eliminar un módulo core
        - No se puede eliminar un módulo que esté activo para algún cliente
        """
        logger.info(f"Intentando eliminar módulo ID: {modulo_id}")

        # Verificar que el módulo existe
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar que no sea un módulo core
        if modulo.es_core:
            raise ValidationError(
                detail="No se puede eliminar un módulo core del sistema.",
                internal_code="CANNOT_DELETE_CORE_MODULE"
            )

        # Verificar que no esté activo para ningún cliente
        from app.infrastructure.database.tables_modulos import ClienteModuloTable
        query_check = select(sql_func.count()).select_from(
            ClienteModuloTable
        ).where(
            and_(
                ClienteModuloTable.c.modulo_id == modulo_id,
                ClienteModuloTable.c.esta_activo == True
            )
        )
        
        resultado_check = await execute_query(
            query_check,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        clientes_activos = resultado_check[0]['count_1'] if resultado_check else 0

        if clientes_activos > 0:
            raise ValidationError(
                detail=f"No se puede eliminar el módulo. Está activo para {clientes_activos} cliente(s).",
                internal_code="MODULE_IN_USE"
            )

        # Realizar eliminación lógica (desactivar)
        stmt = (
            update(ModuloTable)
            .where(ModuloTable.c.modulo_id == modulo_id)
            .values(es_activo=False, fecha_actualizacion=sql_func.getdate())
        )
        
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        logger.info(f"Módulo ID {modulo_id} desactivado exitosamente.")
        return True

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_modulo(modulo_id: UUID) -> ModuloRead:
        """Activa un módulo del catálogo."""
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloTable)
            .where(ModuloTable.c.modulo_id == modulo_id)
            .values(es_activo=True, fecha_actualizacion=sql_func.getdate())
            .returning(ModuloTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo activar el módulo.",
                internal_code="MODULE_ACTIVATION_FAILED"
            )
        return ModuloRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_modulo(modulo_id: UUID) -> ModuloRead:
        """Desactiva un módulo del catálogo."""
        return await ModuloService.eliminar_modulo(modulo_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def validar_dependencias(modulo_id: UUID) -> Dict[str, Any]:
        """
        Valida las dependencias de un módulo.
        Retorna información sobre módulos requeridos y su estado.
        """
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )
        
        if not modulo.modulos_requeridos:
            return {
                "modulo_id": modulo_id,
                "tiene_dependencias": False,
                "modulos_requeridos": []
            }
        
        try:
            modulos_requeridos = json.loads(modulo.modulos_requeridos)
            dependencias_info = []
            
            for codigo in modulos_requeridos:
                modulo_req = await ModuloService.obtener_modulo_por_codigo(codigo)
                dependencias_info.append({
                    "codigo": codigo,
                    "existe": modulo_req is not None,
                    "esta_activo": modulo_req.es_activo if modulo_req else False,
                    "nombre": modulo_req.nombre if modulo_req else None
                })
            
            return {
                "modulo_id": modulo_id,
                "tiene_dependencias": True,
                "modulos_requeridos": dependencias_info
            }
        except json.JSONDecodeError:
            raise ValidationError(
                detail="El formato de modulos_requeridos no es válido",
                internal_code="INVALID_MODULOS_REQUERIDOS_JSON"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos_disponibles_cliente(cliente_id: UUID) -> List[ModuloRead]:
        """
        Obtiene módulos disponibles para un cliente (no activados aún).
        Usa SQLAlchemy Core, no stored procedures.
        """
        from app.infrastructure.database.tables_modulos import ClienteModuloTable
        
        # Obtener módulos activos del cliente
        query_modulos_activos = select(ClienteModuloTable.c.modulo_id).where(
            and_(
                ClienteModuloTable.c.cliente_id == cliente_id,
                ClienteModuloTable.c.esta_activo == True
            )
        )
        
        modulos_activos_result = await execute_query(
            query_modulos_activos,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        modulos_activos_ids = [row['modulo_id'] for row in modulos_activos_result]
        
        # Obtener módulos disponibles (activos y no activados por el cliente)
        query = select(ModuloTable).where(
            and_(
                ModuloTable.c.es_activo == True,
                ~ModuloTable.c.modulo_id.in_(modulos_activos_ids) if modulos_activos_ids else True
            )
        ).order_by(ModuloTable.c.orden, ModuloTable.c.nombre)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        return [ModuloRead(**modulo) for modulo in resultados]

