# app/services/area_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID
import math
import logging

# 🗄️ IMPORTACIONES DE BASE DE DATOS
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import (
    execute_query, execute_insert, execute_update
)
from app.infrastructure.database.sql_constants import (
    GET_AREAS_PAGINATED_QUERY, COUNT_AREAS_QUERY, GET_AREA_BY_ID_QUERY,
    CHECK_AREA_EXISTS_BY_NAME_QUERY, CREATE_AREA_QUERY,
    UPDATE_AREA_BASE_QUERY_TEMPLATE, TOGGLE_AREA_STATUS_QUERY, 
    GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY
)

# 📋 SCHEMAS - Mantener estructura de datos existente
from app.modules.menus.presentation.schemas import AreaCreate, AreaUpdate, AreaRead, PaginatedAreaResponse, AreaSimpleList

# 🚨 EXCEPCIONES - Nuevo sistema de manejo de errores
from app.core.exceptions import ValidationError, NotFoundError, ConflictError, DatabaseError, ServiceError

# 🏗️ BASE SERVICE - Nueva clase base para manejo consistente de errores
from app.core.application.base_service import BaseService

logger = logging.getLogger(__name__)

class AreaService(BaseService):
    """
    Servicio para gestión de áreas del sistema en arquitectura multi-tenant.
    
    ⚠️ IMPORTANTE: Esta clase maneja todas las operaciones relacionadas con áreas
    manteniendo la integridad de los datos y aplicando las reglas de negocio **por cliente**.
    
    CARACTERÍSTICAS PRINCIPALES:
    - Herencia de BaseService para manejo automático de errores
    - Validaciones consistentes usando el nuevo sistema de excepciones
    - Logging detallado para auditoría y debugging
    - Aislamiento total de datos por cliente_id
    - Soporte para áreas del sistema (cliente_id IS NULL) y áreas custom del cliente
    """

    @staticmethod
    async def _verificar_nombre_existente(cliente_id: UUID, nombre: str, excluir_id: Optional[UUID] = None) -> bool:
        """
        Verifica si ya existe un área con el mismo nombre **dentro del cliente** (case-insensitive).
        
        🔍 PROPÓSITO: Prevenir duplicados en la base de datos que violarían
        constraints únicos y causarían errores de integridad **por cliente**.
        
        Args:
            cliente_id: ID del cliente
            nombre: Nombre del área a verificar
            excluir_id: ID de área a excluir (útil en actualizaciones)
            
        Returns:
            bool: True si ya existe un área con ese nombre en el cliente, False en caso contrario
            
        🛡️ SEGURIDAD: Este método es interno y no expone detalles de errores de BD
        """
        # ⚠️ UUID: Manejar None correctamente en la query
        if excluir_id is not None:
            params = (cliente_id, nombre.lower(), excluir_id, cliente_id)
        else:
            params = (cliente_id, nombre.lower(), cliente_id)
        
        try:
            # 🗃️ CONSULTA A BD: Verificar existencia **dentro del cliente**
            # Construir query dinámica para manejar UUID None
            if excluir_id is not None:
                query = """
                SELECT COUNT(*) as count 
                FROM area_menu 
                WHERE LOWER(nombre) = LOWER(?) AND area_id != ? AND (cliente_id IS NULL OR cliente_id = ?);
                """
            else:
                query = """
                SELECT COUNT(*) as count 
                FROM area_menu 
                WHERE LOWER(nombre) = LOWER(?) AND (cliente_id IS NULL OR cliente_id = ?);
                """
            # ✅ FASE 2: Usar await
            resultado_lista = await execute_query(query, params)
            
            if resultado_lista:
                return resultado_lista[0].get('count', 0) > 0
            return False
            
        except KeyError:
            # 🔧 ERROR DE ESTRUCTURA: La consulta no devolvió el campo esperado
            logger.error("Error al acceder a la clave 'count' en CHECK_AREA_EXISTS_BY_NAME_QUERY")
            raise DatabaseError(
                detail="Error interno al verificar nombre de área",
                internal_code="DB_QUERY_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_area(cliente_id: UUID, area_data: AreaCreate) -> AreaRead:
        """
        Crea una nueva área en el sistema **para un cliente específico**.
        
        📝 FLUJO PRINCIPAL:
        1. Validar que el nombre no exista en el cliente (prevenir duplicados)
        2. Insertar en base de datos con el cliente_id
        3. Retornar el área creada
        
        Args:
            cliente_id: ID del cliente
            area_data: Datos validados del área a crear
            
        Returns:
            AreaRead: El área creada con todos sus datos
            
        Raises:
            ConflictError: Si ya existe un área con el mismo nombre en el cliente
            ServiceError: Si la inserción falla por razones internas
        """
        logger.debug(f"Iniciando creación de área para cliente {cliente_id}: {area_data.nombre}")
        
        # 🚫 VALIDACIÓN DE NEGOCIO: Prevenir nombres duplicados en el cliente
        if await AreaService._verificar_nombre_existente(cliente_id, area_data.nombre):
            raise ConflictError(
                detail=f"Ya existe un área con el nombre '{area_data.nombre}' en este cliente.",
                internal_code="AREA_NAME_CONFLICT"
            )

        # 🗃️ PREPARAR DATOS PARA INSERCIÓN
        params = (
            cliente_id,
            area_data.nombre,
            area_data.descripcion,
            area_data.icono,
            area_data.es_activo
        )
        
        # 💾 EJECUTAR INSERCIÓN EN BD
        # ✅ FASE 2: Usar await
        resultado_insert = await execute_insert(CREATE_AREA_QUERY, params)
        
        # 🔍 VERIFICAR RESULTADO DE INSERCIÓN
        if not resultado_insert:
            raise ServiceError(
                status_code=500,
                detail="La inserción del área no devolvió el registro creado.",
                internal_code="AREA_CREATION_FAILED"
            )

        # ✅ CONVERSIÓN Y LOG DE ÉXITO
        created_area = AreaRead(**resultado_insert)
        logger.debug(f"Área '{created_area.nombre}' creada para cliente {cliente_id} con ID: {created_area.area_id}")
        return created_area

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_area_por_id(area_id: UUID) -> Optional[AreaRead]:
        """
        Obtiene un área específica por su ID **(cliente_id se obtiene del área)**.
        
        🔍 CARACTERÍSTICAS:
        - Retorna None si el área no existe (no lanza excepción)
        - Útil para verificaciones de existencia sin interrumpir flujo
        
        Args:
            area_id: ID del área a buscar
            
        Returns:
            Optional[AreaRead]: El área encontrada o None si no existe
        """
        logger.debug(f"Buscando área con ID: {area_id}")
        
        # 🗃️ CONSULTA SIMPLE POR ID (incluye cliente_id en el resultado)
        # ✅ FASE 2: Usar await
        resultado_lista = await execute_query(GET_AREA_BY_ID_QUERY, (area_id,))
        
        if not resultado_lista:
            logger.debug(f"Área con ID {area_id} no encontrada.")
            return None
            
        # ✅ CONVERSIÓN A SCHEMA PYDANTIC
        return AreaRead(**resultado_lista[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_areas_paginadas(
        cliente_id: UUID,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None
    ) -> PaginatedAreaResponse:
        """
        Obtiene una lista paginada y filtrada de áreas **de un cliente**.
        
        📊 PAGINACIÓN EFICIENTE:
        - Realiza 2 consultas: conteo total y datos paginados **dentro del cliente**
        - Calcula metadatos de paginación automáticamente
        - Soporte para búsqueda por nombre o descripción
        
        Args:
            cliente_id: ID del cliente
            skip: Número de registros a saltar (offset)
            limit: Número máximo de registros por página
            search: Término de búsqueda opcional
            
        Returns:
            PaginatedAreaResponse: Respuesta con datos paginados y metadatos
        """
        logger.debug(f"Obteniendo áreas paginadas para cliente {cliente_id}: skip={skip}, limit={limit}, search='{search}'")
        
        # 🔍 PREPARAR PARÁMETROS DE BÚSQUEDA
        search_param = f"%{search}%" if search else None
        where_params = (cliente_id, search, search_param, search_param)
        
        # 1. 📊 OBTENER CONTEO TOTAL (para calcular páginas)
        # ✅ FASE 2: Usar await
        count_result_list = await execute_query(COUNT_AREAS_QUERY, where_params)
        total_count = count_result_list[0].get('total_count', 0) if count_result_list else 0

        # 2. 📋 OBTENER DATOS PAGINADOS (solo si hay resultados)
        areas_lista: List[AreaRead] = []
        if total_count > 0 and limit > 0:
            pagination_params = where_params + (skip, limit)
            # ✅ FASE 2: Usar await
            rows = await execute_query(GET_AREAS_PAGINATED_QUERY, pagination_params)
            
            # 🎯 MAPEAR RESULTADOS CON MANEJO DE ERRORES INDIVIDUALES
            for row_dict in rows:
                try:
                    areas_lista.append(AreaRead(**row_dict))
                except Exception as map_err:
                    logger.error(f"Error mapeando área: {map_err}")
                    # 🔄 CONTINUAR: No fallar toda la operación por un registro corrupto
                    continue

        # 3. 🧮 CALCULAR METADATOS DE PAGINACIÓN
        total_pages = math.ceil(total_count / limit) if limit > 0 else 0
        current_page = (skip // limit) + 1 if limit > 0 else 1

        logger.debug(f"Paginación completada para cliente {cliente_id}: {len(areas_lista)} áreas de {total_count} totales")
        
        return PaginatedAreaResponse(
            areas=areas_lista,
            total_areas=total_count,
            pagina_actual=current_page,
            total_paginas=total_pages
        )

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_area(area_id: UUID, area_data: AreaUpdate) -> AreaRead:
        """
        Actualiza un área existente con validaciones de negocio **por cliente**.
        
        🔄 FLUJO DE ACTUALIZACIÓN:
        1. Verificar que el área existe y obtener su cliente_id
        2. Validar que el nuevo nombre no cause conflictos en el cliente
        3. Aplicar actualización parcial (solo campos proporcionados)
        4. Retornar área actualizada
        
        Args:
            area_id: ID del área a actualizar
            area_ Campos a actualizar (parcial)
            
        Returns:
            AreaRead: El área actualizada
            
        Raises:
            NotFoundError: Si el área no existe
            ConflictError: Si el nuevo nombre ya está en uso en el cliente
            ValidationError: Si no se proporcionan datos para actualizar
        """
        logger.debug(f"Intentando actualizar área ID: {area_id}")

        # 🚫 VALIDACIÓN: Debe haber datos para actualizar
        update_payload = area_data.model_dump(exclude_unset=True)
        if not update_payload:
            raise ValidationError(
                detail="No se proporcionaron datos para actualizar el área.",
                internal_code="NO_UPDATE_DATA"
            )

        # 🔍 VERIFICAR EXISTENCIA DEL ÁREA Y OBTENER SU CLIENTE_ID
        area_existente = await AreaService.obtener_area_por_id(area_id)
        if not area_existente:
            raise NotFoundError(
                detail=f"Área con ID {area_id} no encontrada para actualizar.",
                internal_code="AREA_NOT_FOUND"
            )
        cliente_id = area_existente.cliente_id

        # 🚫 VALIDACIÓN DE NOMBRE ÚNICO (si se está cambiando)
        if 'nombre' in update_payload and update_payload['nombre'].lower() != area_existente.nombre.lower():
            if await AreaService._verificar_nombre_existente(cliente_id, update_payload['nombre'], excluir_id=area_id):
                raise ConflictError(
                    detail=f"Ya existe otra área con el nombre '{update_payload['nombre']}' en este cliente.",
                    internal_code="AREA_NAME_CONFLICT"
                )

        # 🛠️ CONSTRUIR QUERY DINÁMICA (solo campos proporcionados)
        fields_to_update = []
        params_list = []
        for key, value in update_payload.items():
            fields_to_update.append(f"{key} = ?")
            params_list.append(value)
        params_list.append(cliente_id)
        params_list.append(area_id)

        # 💾 EJECUTAR ACTUALIZACIÓN
        update_query = UPDATE_AREA_BASE_QUERY_TEMPLATE.format(fields=", ".join(fields_to_update))
        # ✅ FASE 2: Usar await
        resultado_update = await execute_update(update_query, tuple(params_list))
        
        # 🔄 FALLBACK: Si no retorna datos, obtener el área actualizada
        if not resultado_update:
            logger.warning(f"execute_update no devolvió datos para área {area_id}. Usando fallback.")
            updated_area = await AreaService.obtener_area_por_id(area_id)
            if not updated_area:
                raise ServiceError(
                    status_code=500,
                    detail="Error crítico: Área actualizada pero no se pudo recuperar.",
                    internal_code="AREA_UPDATE_RETRIEVAL_FAILED"
                )
            logger.debug(f"Área ID: {area_id} del cliente {cliente_id} actualizada (verificada post-actualización)")
            return updated_area
            
        # ✅ ÉXITO: Retornar datos de la actualización
        logger.debug(f"Área ID: {area_id} del cliente {cliente_id} actualizada exitosamente")
        return AreaRead(**resultado_update)

    @staticmethod
    @BaseService.handle_service_errors
    async def cambiar_estado_area(area_id: UUID, activar: bool) -> AreaRead:
        """
        Activa o desactiva un área (borrado lógico).
        
        🔄 CAMBIO DE ESTADO:
        - activar=True: Reactiva un área desactivada
        - activar=False: Desactiva un área activa
        
        Args:
            area_id: ID del área a modificar
            activar: True para activar, False para desactivar
            
        Returns:
            AreaRead: El área con el nuevo estado
            
        Raises:
            NotFoundError: Si el área no existe
            ValidationError: Si el área ya está en el estado deseado
        """
        accion = "reactivar" if activar else "desactivar"
        logger.debug(f"Intentando {accion} área ID: {area_id}")

        # 🔍 VERIFICAR EXISTENCIA Y ESTADO ACTUAL
        area_existente = await AreaService.obtener_area_por_id(area_id)
        if not area_existente:
            raise NotFoundError(
                detail=f"Área con ID {area_id} no encontrada para {accion}.",
                internal_code="AREA_NOT_FOUND"
            )
            
        # 🚫 VALIDACIÓN: No realizar operación redundante
        if area_existente.es_activo == activar:
            estado_str = "activa" if activar else "inactiva"
            raise ValidationError(
                detail=f"Área con ID {area_id} ya está {estado_str}.",
                internal_code="AREA_ALREADY_IN_STATE"
            )

        # 💾 EJECUTAR CAMBIO DE ESTADO **(el cliente_id ya está en el área)**
        # ✅ FASE 2: Usar await
        resultado_toggle = await execute_update(TOGGLE_AREA_STATUS_QUERY, (activar, area_id))
        
        # 🔄 FALLBACK: Verificar cambio si no retorna datos
        if not resultado_toggle:
            logger.warning(f"execute_update no devolvió datos al {accion} área {area_id}")
            toggled_area = await AreaService.obtener_area_por_id(area_id)
            if not toggled_area or toggled_area.es_activo != activar:
                raise ServiceError(
                    status_code=500,
                    detail=f"Error crítico: Área {accion}da pero no se pudo verificar el estado.",
                    internal_code="AREA_STATE_VERIFICATION_FAILED"
                )
            logger.debug(f"Área ID: {area_id} {accion}da (verificada post-actualización)")
            return toggled_area
            
        # ✅ ÉXITO: Retornar datos del cambio
        logger.debug(f"Área ID: {area_id} {accion}da exitosamente")
        return AreaRead(**resultado_toggle)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_lista_simple_areas_activas(cliente_id: UUID) -> List[AreaSimpleList]:
        """
        Obtiene una lista simplificada de áreas activas **de un cliente**.
        
        🎯 PROPÓSITO: Optimizado para listas desplegables y selectores
        donde solo se necesitan ID y nombre.
        
        Returns:
            List[AreaSimpleList]: Lista de áreas activas simplificadas del cliente
        """
        logger.debug(f"Obteniendo lista simple de áreas activas para cliente {cliente_id}")
        
        params = (cliente_id,)
        # ✅ FASE 2: Usar await
        rows = await execute_query(GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY, params)
        if not rows:
            logger.debug(f"No se encontraron áreas activas para el cliente {cliente_id} en la lista simple")
            return []

        # 🎯 MAPEO SEGURO: Continuar incluso si algún registro falla
        areas_list = []
        for row in rows:
            try:
                areas_list.append(AreaSimpleList(**row))
            except Exception as map_err:
                logger.error(f"Error mapeando área simple para cliente {cliente_id}: {map_err}")
                continue

        logger.debug(f"Lista simple obtenida para cliente {cliente_id}: {len(areas_list)} áreas activas")
        return areas_list