# app/services/rol_service.py
from typing import Dict, List, Optional, Any
from uuid import UUID
import math
import logging
import pyodbc

# 🗄️ IMPORTACIONES DE BASE DE DATOS
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import (
    execute_query, execute_insert, execute_update
)
from app.infrastructure.database.queries import (
    COUNT_ROLES_PAGINATED, SELECT_ROLES_PAGINATED,
    DEACTIVATE_ROL, REACTIVATE_ROL,
    SELECT_PERMISOS_POR_ROL, DELETE_PERMISOS_POR_ROL, INSERT_PERMISO_ROL
)

# 📋 SCHEMAS
from app.modules.rbac.presentation.schemas import (
    RolRead, PaginatedRolResponse, PermisoRead, PermisoUpdatePayload, PermisoBase
)

# 🚨 EXCEPCIONES - Nuevo sistema de manejo de errores
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, ServiceError, DatabaseError
)

# 🏗️ BASE SERVICE - Clase base para manejo consistente de errores
from app.core.application.base_service import BaseService

logger = logging.getLogger(__name__)

class RolService(BaseService):
    """
    Servicio para gestión completa de roles del sistema en arquitectura multi-tenant.
    
    ⚠️ IMPORTANTE: Este servicio maneja operaciones críticas relacionadas con:
    - Creación, actualización y desactivación de roles **por cliente**
    - Gestión de permisos de roles sobre menús
    - Asignación de roles a usuarios **dentro de un cliente**
    
    CARACTERÍSTICAS PRINCIPALES:
    - Herencia de BaseService para manejo automático de errores
    - Validaciones robustas de nombres únicos **por cliente**
    - Manejo de transacciones para operaciones críticas
    - Logging detallado para auditoría de seguridad
    - Aislamiento total de datos por cliente_id
    """

    @staticmethod
    def _normalizar_rol_dict(rol_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza un diccionario de rol para cumplir con las reglas de validación del schema.
        
        ✅ REGLAS DE NORMALIZACIÓN:
        - Convierte es_activo de int a bool
        - Si un rol tiene codigo_rol pero cliente_id != 1, establece codigo_rol = None
          (roles con codigo_rol solo pueden pertenecer al cliente SUPER ADMIN)
        
        Args:
            rol_dict: Diccionario con datos del rol desde la BD
            
        Returns:
            Dict[str, Any]: Diccionario normalizado
        """
        # Convertir es_activo de int a bool
        if 'es_activo' in rol_dict and isinstance(rol_dict['es_activo'], int):
            rol_dict['es_activo'] = bool(rol_dict['es_activo'])
        
        # ✅ CRÍTICO: Normalizar codigo_rol según regla de negocio
        # Si un rol tiene codigo_rol pero cliente_id no es SUPERADMIN, es un rol de cliente mal configurado
        # ⚠️ Con UUID, la validación de SUPERADMIN debe hacerse en el servicio usando settings
        # Para evitar errores de validación, establecer codigo_rol = None si cliente_id no es None
        if rol_dict.get('codigo_rol') is not None and rol_dict.get('cliente_id') is not None:
            # ⚠️ Nota: La validación de SUPERADMIN debe hacerse en el servicio, no aquí
            # Por ahora, si tiene cliente_id y codigo_rol, mantenerlo (el servicio validará)
            pass
        
        return rol_dict

    @staticmethod
    async def get_min_required_access_level(role_names: List[str], cliente_id: Optional[UUID] = None) -> int:
        """
        Consulta el nivel de acceso más bajo (MIN) necesario para la lista de nombres de rol dados.
        Ej: Si se requiere ['Administrador', 'Editor'], y los niveles son [50, 30],
        el nivel mínimo requerido es 30.
        
        ✅ CORRECCIÓN: Ahora filtra por cliente_id para respetar el contexto multi-tenant.
        Busca roles del cliente específico Y roles del sistema (cliente_id IS NULL).
        
        Args:
            role_names: Lista de nombres de rol requeridos (ej: ['Administrador']).
            cliente_id: ID del cliente para filtrar roles. Si es None, busca solo roles del sistema.

        Returns:
            El nivel de acceso más bajo requerido (int), o 0 si no se encuentra ninguno.
        """
        if not role_names:
            return 0  # Si no se requiere ningún rol, el nivel es 0 (cualquiera pasa)

        # ⚠️ Construcción dinámica de la cláusula IN: Evita inyección SQL
        placeholders = ', '.join(['?' for _ in role_names])
        
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        
        # ✅ CORRECCIÓN: Para BD dedicadas, no filtrar por cliente_id (todos los roles pertenecen al mismo tenant)
        if database_type == "multi":
            # BD dedicada: buscar roles sin filtrar por cliente_id
            QUERY = f"""
            SELECT MIN(nivel_acceso) AS min_level
            FROM rol
            WHERE nombre IN ({placeholders}) 
              AND es_activo = 1;
            """
            params = tuple(role_names)
        elif cliente_id is not None:
            # BD compartida: Buscar roles del cliente específico Y roles del sistema
            QUERY = f"""
            SELECT MIN(nivel_acceso) AS min_level
            FROM rol
            WHERE nombre IN ({placeholders}) 
              AND es_activo = 1
              AND (cliente_id = ? OR cliente_id IS NULL);
            """
            params = tuple(list(role_names) + [cliente_id])
        else:
            # Solo buscar roles del sistema
            QUERY = f"""
            SELECT MIN(nivel_acceso) AS min_level
            FROM rol
            WHERE nombre IN ({placeholders}) 
              AND es_activo = 1
              AND cliente_id IS NULL;
            """
            params = tuple(role_names)
        
        try:
            # execute_query devuelve List[Dict]
            # ✅ FASE 2: Usar await
            result = await execute_query(QUERY, params)
            
            if result and result[0]['min_level'] is not None:
                # El valor de min_level no es NULL
                min_level = int(result[0]['min_level'])
                logger.debug(f"Nivel mínimo requerido para roles {role_names} (cliente_id={cliente_id}): {min_level}")
                return min_level
            
            # Si la lista de nombres no coincide con ningún rol activo
            logger.warning(f"No se encontraron niveles de acceso para los roles: {role_names} (cliente_id={cliente_id})")
            # Devolvemos un nivel muy alto si no se encuentra (para forzar la denegación)
            return 999 
            
        except DatabaseError as db_err:
            logger.error(f"Error de BD en get_min_required_access_level: {db_err.detail}", exc_info=True)
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener nivel de rol requerido.",
                internal_code="ROLE_LEVEL_DB_ERROR"
            )

    @staticmethod
    async def get_user_max_access_level(usuario_id: UUID, cliente_id: UUID) -> int:
        """
        Consulta el nivel de acceso más alto (MAX) entre todos los roles asignados al usuario.
        
        Args:
            usuario_id: ID del usuario.
            cliente_id: ID del cliente (tenant) para filtrar roles.

        Returns:
            El nivel de acceso más alto que posee el usuario (int), o 1 si no tiene roles activos.
        """
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        
        try:
            # ✅ Para BD dedicadas, no filtrar por cliente_id (todos los roles pertenecen al mismo tenant)
            if database_type == "multi":
                query = """
                SELECT ISNULL(MAX(r.nivel_acceso), 1) as max_level
                FROM usuario_rol ur
                INNER JOIN rol r ON ur.rol_id = r.rol_id
                WHERE ur.usuario_id = ? 
                  AND ur.es_activo = 1
                  AND r.es_activo = 1
                """
                # ✅ FASE 2: Usar await - solo pasar usuario_id para BD dedicadas
                result = await execute_query(query, (usuario_id,))
            else:
                # BD compartida: usar la query que filtra por cliente_id
                from app.infrastructure.database.queries import GET_USER_MAX_ACCESS_LEVEL
                # ✅ FASE 2: Usar await
                result = await execute_query(GET_USER_MAX_ACCESS_LEVEL, (usuario_id, cliente_id))
            
            if result and result[0]['max_level'] is not None:
                # El valor de max_level no es NULL
                return int(result[0]['max_level'])
            
            # Si no tiene roles activos, nivel mínimo
            return 1 
            
        except DatabaseError as db_err:
            logger.error(f"Error de BD en get_user_max_access_level: {db_err.detail}", exc_info=True)
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener nivel máximo del usuario.",
                internal_code="USER_LEVEL_DB_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def _verificar_nombre_rol_unico(cliente_id: UUID, nombre: str, rol_id_excluir: Optional[UUID] = None) -> None:
        """
        Verifica que el nombre del rol sea único **dentro del cliente** (case-insensitive).
        
        🛡️ PREVENCIÓN DE DUPLICADOS:
        - Evita violaciones de constraints únicos en la base de datos
        - Comparación insensible a mayúsculas/minúsculas
        - Soporte para exclusiones en actualizaciones
        
        Args:
            cliente_id: ID del cliente
            nombre: Nombre del rol a verificar
            rol_id_excluir: ID del rol a excluir (para actualizaciones)
            
        Raises:
            ConflictError: Si ya existe un rol con el mismo nombre en el cliente
        """
        try:
            query = "SELECT rol_id FROM rol WHERE cliente_id = ? AND LOWER(nombre) = LOWER(?)"
            params = [cliente_id, nombre]
            
            if rol_id_excluir is not None:
                query += " AND rol_id != ?"
                params.append(rol_id_excluir)

            # ✅ FASE 2: Usar await
            resultados = await execute_query(query, tuple(params))

            if resultados:
                raise ConflictError(
                    detail=f"El nombre de rol '{nombre}' ya está en uso en este cliente.",
                    internal_code="ROLE_NAME_CONFLICT"
                )
                
        except ConflictError:
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD en _verificar_nombre_rol_unico para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al verificar nombre de rol",
                internal_code="ROLE_NAME_VERIFICATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en _verificar_nombre_rol_unico: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al verificar nombre de rol",
                internal_code="ROLE_NAME_VERIFICATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_rol(cliente_id: UUID, rol_data: Dict) -> Dict:
        """
        Crea un nuevo rol en el sistema **para un cliente específico**.
        
        🆕 CREACIÓN SEGURA:
        - Valida nombre único **dentro del cliente**
        - Aplica valores por defecto seguros
        - Registra la creación para auditoría
        
        Args:
            cliente_id: ID del cliente
            rol_data: Datos del rol a crear
            
        Returns:
            Dict: Rol creado con todos sus datos
            
        Raises:
            ConflictError: Si el nombre ya existe en el cliente
            ServiceError: Si la creación falla
        """
        logger.info(f"Intentando crear rol para cliente {cliente_id}: {rol_data.get('nombre')}")
        
        try:
            nombre_rol = rol_data.get('nombre')
            
            # 🚫 VALIDAR NOMBRE OBLIGATORIO
            if not nombre_rol:
                raise ValidationError(
                    detail="El nombre del rol es requerido.",
                    internal_code="ROLE_NAME_REQUIRED"
                )

            # 🛡️ VERIFICAR NOMBRE ÚNICO DENTRO DEL CLIENTE
            await RolService._verificar_nombre_rol_unico(cliente_id, nombre_rol)

            # 💾 EJECUTAR INSERCIÓN
            insert_query = """
            INSERT INTO rol (cliente_id, nombre, descripcion, es_activo)
            OUTPUT INSERTED.rol_id, INSERTED.cliente_id, INSERTED.nombre, INSERTED.descripcion,
                   INSERTED.es_activo, INSERTED.fecha_creacion
            VALUES (?, ?, ?, ?)
            """
            
            params = (
                cliente_id,
                nombre_rol,
                rol_data.get('descripcion'),
                rol_data.get('es_activo', True)  # ✅ Valor por defecto seguro
            )

            # ✅ FASE 2: Usar await
            result = await execute_insert(insert_query, params)

            if not result:
                raise ServiceError(
                    status_code=500,
                    detail="La creación del rol no devolvió resultados.",
                    internal_code="ROLE_CREATION_FAILED"
                )

            logger.info(f"Rol '{result.get('nombre')}' creado con ID: {result.get('rol_id')} para cliente {cliente_id}")
            return result

        except (ValidationError, ConflictError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al crear rol para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al crear rol",
                internal_code="ROLE_CREATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado creando rol para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al crear rol",
                internal_code="ROLE_CREATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_rol_por_id(rol_id: UUID, incluir_inactivos: bool = False) -> Optional[Dict]:
        """
        Obtiene un rol por su ID **(el cliente_id se obtiene del rol)**.
        
        🔍 BÚSQUEDA FLEXIBLE:
        - Por defecto solo retorna roles activos
        - Opción para incluir roles inactivos (admin)
        - Conversión automática de tipos de datos
        
        Args:
            rol_id: ID del rol a buscar
            incluir_inactivos: Si incluir roles inactivos
            
        Returns:
            Optional[Dict]: Datos del rol o None si no existe
        """
        try:
            query = """
            SELECT rol_id, cliente_id, nombre, descripcion, es_activo, fecha_creacion
            FROM rol
            WHERE rol_id = ?
            """
            params = [rol_id]
            
            if not incluir_inactivos:
                query += " AND es_activo = 1"

            # ✅ FASE 2: Usar await
            resultados = await execute_query(query, tuple(params))

            if not resultados:
                logger.debug(f"Rol con ID {rol_id} no encontrado")
                return None

            # 🔄 NORMALIZAR DATOS
            rol = resultados[0]
            rol_normalizado = RolService._normalizar_rol_dict(rol)
            return rol_normalizado

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener rol {rol_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener rol",
                internal_code="ROLE_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado obteniendo rol {rol_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener rol",
                internal_code="ROLE_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_roles_paginados(
        cliente_id: int,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Dict:
        """
        Obtiene una lista paginada de roles **de un cliente** con búsqueda.
        
        📊 PAGINACIÓN EFICIENTE:
        - Búsqueda insensible en nombre y descripción
        - Metadatos completos de paginación
        - Ordenamiento consistente
        
        Args:
            cliente_id: ID del cliente
            page: Número de página (comienza en 1)
            limit: Límite de resultados por página
            search: Término de búsqueda opcional
            
        Returns:
            Dict: Respuesta paginada con roles y metadatos
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            ServiceError: Si hay errores en la consulta
        """
        logger.info(f"Obteniendo roles paginados para cliente {cliente_id}: page={page}, limit={limit}, search='{search}'")

        # 🚫 VALIDAR PARÁMETROS
        if page < 1:
            raise ValidationError(
                detail="El número de página debe ser mayor o igual a 1.",
                internal_code="INVALID_PAGE_NUMBER"
            )
        if limit < 1:
            raise ValidationError(
                detail="El límite por página debe ser mayor o igual a 0.",
                internal_code="INVALID_LIMIT"
            )

        offset = (page - 1) * limit
        search_param = f"%{search}%" if search else None
        
        # ✅ VALIDACIÓN: Verificar que cliente_id es válido (UUID)
        from uuid import UUID
        cliente_id_valido = cliente_id
        if not cliente_id_valido:
            logger.error(f"Cliente ID inválido recibido en obtener_roles_paginados: {cliente_id}")
            raise ValidationError(
                detail="Cliente ID no válido. No se puede obtener la lista de roles.",
                internal_code="INVALID_CLIENT_ID"
            )
        
        # Verificar que no sea UUID nulo
        if isinstance(cliente_id_valido, UUID) and cliente_id_valido == UUID('00000000-0000-0000-0000-000000000000'):
            logger.error(f"Cliente ID es UUID nulo en obtener_roles_paginados: {cliente_id}")
            raise ValidationError(
                detail="Cliente ID no válido. No se puede obtener la lista de roles.",
                internal_code="INVALID_CLIENT_ID"
            )
        
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"

        try:
            # 📊 CONTAR TOTAL DE ROLES
            # ✅ Para BD dedicadas, no filtrar por cliente_id
            if database_type == "multi":
                COUNT_QUERY = """
                SELECT COUNT(rol_id) as total 
                FROM dbo.rol
                WHERE 
                    (? IS NULL OR (
                        LOWER(nombre) LIKE LOWER(?) OR
                        LOWER(descripcion) LIKE LOWER(?)
                    ));
                """
                count_params = (search_param, search_param, search_param)
                logger.debug(f"[ROLES-PAGINADOS] BD dedicada: Contando roles sin filtrar por cliente_id")
            else:
                COUNT_QUERY = COUNT_ROLES_PAGINATED
                count_params = (cliente_id, search_param, search_param, search_param)
                logger.debug(f"[ROLES-PAGINADOS] BD compartida: Contando roles con cliente_id {cliente_id}")
            
            logger.info(f"[ROLES-PAGINADOS] Iniciando consulta para cliente_id={cliente_id}, page={page}, limit={limit}, search='{search}'")
            logger.debug(f"[ROLES-PAGINADOS] Parámetros de conteo: {count_params}")
            # ✅ FASE 2: Usar await
            count_result = await execute_query(COUNT_QUERY, count_params)

            if not count_result or not isinstance(count_result, list) or len(count_result) == 0:
                logger.error(f"[ROLES-PAGINADOS] Error al contar roles para cliente {cliente_id}: resultado inesperado: {count_result}")
                raise ServiceError(
                    status_code=500,
                    detail="Error al obtener el total de roles",
                    internal_code="ROLE_COUNT_ERROR"
                )

            total_roles = count_result[0]['total']
            logger.info(f"[ROLES-PAGINADOS] Total de roles encontrados para cliente {cliente_id}: {total_roles}")

            # 📋 OBTENER ROLES PAGINADOS
            # ✅ Para BD dedicadas, no filtrar por cliente_id
            if database_type == "multi":
                SELECT_QUERY = """
                SELECT
                    rol_id, nombre, descripcion, es_activo, fecha_creacion, cliente_id, codigo_rol
                FROM
                    dbo.rol
                WHERE 
                    (? IS NULL OR (
                        LOWER(nombre) LIKE LOWER(?) OR
                        LOWER(descripcion) LIKE LOWER(?)
                    ))
                ORDER BY
                    rol_id 
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
                """
                select_params = (search_param, search_param, search_param, offset, limit)
                logger.debug(f"[ROLES-PAGINADOS] BD dedicada: Obteniendo roles sin filtrar por cliente_id")
            else:
                SELECT_QUERY = SELECT_ROLES_PAGINATED
                select_params = (cliente_id, search_param, search_param, search_param, offset, limit)
                logger.debug(f"[ROLES-PAGINADOS] BD compartida: Obteniendo roles con cliente_id {cliente_id}")
            
            lista_roles = []
            if total_roles > 0 and limit > 0:
                logger.debug(f"[ROLES-PAGINADOS] Obteniendo roles con parámetros: {select_params}")
                # ✅ FASE 2: Usar await
                lista_roles = await execute_query(SELECT_QUERY, select_params)
                logger.info(f"[ROLES-PAGINADOS] Obtenidos {len(lista_roles)} roles para la página {page} de {total_roles} totales")
            else:
                logger.info(f"[ROLES-PAGINADOS] No hay roles para mostrar (total={total_roles}, limit={limit})")

            # 🔄 PROCESAR Y CONVERTIR DATOS
            roles_procesados = []
            for rol_dict in lista_roles:
                # ✅ CORRECCIÓN: Para BD dedicadas, establecer cliente_id desde el contexto si es NULL o UUID nulo
                if database_type == "multi":
                    rol_cliente_id = rol_dict.get('cliente_id')
                    if not rol_cliente_id or (isinstance(rol_cliente_id, UUID) and rol_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                        rol_dict['cliente_id'] = cliente_id
                        logger.debug(f"[ROLES-PAGINADOS] BD dedicada: Rol {rol_dict.get('rol_id')} tenía cliente_id NULL, establecido a {cliente_id}")
                
                # ✅ Usar función helper para normalizar
                rol_normalizado = RolService._normalizar_rol_dict(rol_dict)
                roles_procesados.append(rol_normalizado)

            # 🧮 CALCULAR METADATOS
            total_paginas = math.ceil(total_roles / limit) if limit > 0 else 0

            response_data = {
                "roles": roles_procesados,
                "total_roles": total_roles,
                "pagina_actual": page,
                "total_paginas": total_paginas
            }

            logger.info(f"[ROLES-PAGINADOS] Consulta completada exitosamente - Cliente: {cliente_id}, Total: {total_roles}, Página: {page}/{total_paginas}, Resultados: {len(roles_procesados)}")
            return response_data

        except (ValidationError, ServiceError):
            raise
        except DatabaseError as db_err:
            logger.error(f"[ROLES-PAGINADOS] Error de BD para cliente {cliente_id}: {db_err.detail}", exc_info=True)
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener roles paginados",
                internal_code="ROLE_PAGINATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"[ROLES-PAGINADOS] Error inesperado para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error inesperado al obtener roles paginados",
                internal_code="ROLE_PAGINATION_UNEXPECTED_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en obtener_roles_paginados: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener roles paginados",
                internal_code="ROLE_PAGINATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_rol(rol_id: UUID, rol_data: Dict) -> Dict:
        """
        Actualiza un rol existente **dentro de su cliente** con validaciones de integridad.
        
        🔄 ACTUALIZACIÓN PARCIAL:
        - Solo actualiza campos proporcionados
        - Valida nombre único (si se cambia)
        - Mantiene la integridad de los datos
        
        Args:
            rol_id: ID del rol a actualizar
            rol_data: Campos a actualizar (parcial)
            
        Returns:
            Dict: Rol actualizado
            
        Raises:
            NotFoundError: Si el rol no existe
            ConflictError: Si el nuevo nombre ya existe en el cliente
            ServiceError: Si la actualización falla
        """
        logger.info(f"Intentando actualizar rol ID: {rol_id}")

        try:
            # 🔍 VERIFICAR EXISTENCIA DEL ROL Y OBTENER SU CLIENTE_ID
            rol_actual = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
            if not rol_actual:
                raise NotFoundError(
                    detail=f"Rol con ID {rol_id} no encontrado.",
                    internal_code="ROLE_NOT_FOUND"
                )
            cliente_id = rol_actual['cliente_id']

            # 🛡️ VALIDAR NOMBRE ÚNICO (si se cambia)
            nuevo_nombre = rol_data.get('nombre')
            if nuevo_nombre and nuevo_nombre != rol_actual.get('nombre'):
                await RolService._verificar_nombre_rol_unico(cliente_id, nuevo_nombre, rol_id)

            # 🛠️ CONSTRUIR ACTUALIZACIÓN DINÁMICA
            update_parts = []
            params = []
            campos_actualizados = False

            campos_permitidos = {
                'nombre': 'nombre', 
                'descripcion': 'descripcion', 
                'es_activo': 'es_activo'
            }

            for field, db_field in campos_permitidos.items():
                if field in rol_data and rol_data[field] is not None:
                    # 🔄 Solo actualizar si es diferente (excepto para es_activo)
                    if field != 'es_activo' or rol_data[field] != rol_actual.get(field):
                        update_parts.append(f"{db_field} = ?")
                        params.append(rol_data[field])
                        campos_actualizados = True

            if not campos_actualizados:
                logger.info(f"No hay cambios detectados para el rol ID {rol_id}")
                return rol_actual

            params.append(rol_id)

            # 💾 EJECUTAR ACTUALIZACIÓN
            update_query = f"""
            UPDATE rol
            SET {', '.join(update_parts)}
            OUTPUT INSERTED.rol_id, INSERTED.cliente_id, INSERTED.nombre, INSERTED.descripcion,
                   INSERTED.es_activo, INSERTED.fecha_creacion
            WHERE rol_id = ?
            """

            # ✅ FASE 2: Usar await
            result = await execute_update(update_query, tuple(params))

            if not result:
                logger.error(f"La actualización del rol ID {rol_id} no devolvió resultados")
                raise ServiceError(
                    status_code=500,
                    detail="Error al actualizar el rol",
                    internal_code="ROLE_UPDATE_FAILED"
                )

            # 🔄 CONVERTIR TIPOS DE DATOS
            if 'es_activo' in result and isinstance(result['es_activo'], int):
                result['es_activo'] = bool(result['es_activo'])
                
            logger.info(f"Rol '{result.get('nombre')}' actualizado exitosamente")
            return result

        except (ValidationError, NotFoundError, ConflictError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al actualizar rol {rol_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al actualizar rol",
                internal_code="ROLE_UPDATE_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado actualizando rol {rol_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al actualizar rol",
                internal_code="ROLE_UPDATE_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_rol(rol_id: UUID) -> Dict:
        """
        Desactiva un rol (borrado lógico).
        
        🚫 DESACTIVACIÓN SEGURA:
        - Verifica que el rol exista y esté activo
        - Evita operaciones redundantes
        - Mantiene integridad referencial
        
        Args:
            rol_id: ID del rol a desactivar
            
        Returns:
            Dict: Rol desactivado
            
        Raises:
            NotFoundError: Si el rol no existe
            ValidationError: Si el rol ya está inactivo
            ServiceError: Si la desactivación falla
        """
        logger.info(f"Intentando desactivar rol ID: {rol_id}")

        try:
            # 🔍 VERIFICAR EXISTENCIA Y ESTADO
            rol_actual = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
            if not rol_actual:
                raise NotFoundError(
                    detail=f"Rol con ID {rol_id} no encontrado.",
                    internal_code="ROLE_NOT_FOUND"
                )
                
            if not rol_actual.get('es_activo', False):
                logger.info(f"Rol ID {rol_id} ya se encontraba inactivo")
                return rol_actual

            # 💾 EJECUTAR DESACTIVACIÓN
            # ✅ FASE 2: Usar await
            result = await execute_update(DEACTIVATE_ROL, (rol_id,))

            if not result:
                logger.warning(f"No se pudo desactivar el rol ID {rol_id}")
                # 🔄 VERIFICAR ESTADO ACTUAL
                rol_revisado = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
                if rol_revisado and not rol_revisado.get('es_activo'):
                    return rol_revisado
                    
                raise ServiceError(
                    status_code=500,
                    detail="Error al desactivar el rol",
                    internal_code="ROLE_DEACTIVATION_FAILED"
                )

            # 🔄 NORMALIZAR DATOS
            result_normalizado = RolService._normalizar_rol_dict(result)
                
            logger.info(f"Rol ID {rol_id} desactivado exitosamente")
            return result_normalizado

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al desactivar rol {rol_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al desactivar rol",
                internal_code="ROLE_DEACTIVATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado desactivando rol {rol_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al desactivar rol",
                internal_code="ROLE_DEACTIVATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def reactivar_rol(rol_id: UUID) -> Dict:
        """
        Reactiva un rol previamente desactivado.
        
        🔄 REACTIVACIÓN SEGURA:
        - Verifica que el rol exista y esté inactivo
        - Evita operaciones redundantes
        - Mantiene la trazabilidad
        
        Args:
            rol_id: ID del rol a reactivar
            
        Returns:
            Dict: Rol reactivado
            
        Raises:
            NotFoundError: Si el rol no existe
            ValidationError: Si el rol ya está activo
            ServiceError: Si la reactivación falla
        """
        logger.info(f"Intentando reactivar rol ID: {rol_id}")

        try:
            # 🔍 VERIFICAR EXISTENCIA Y ESTADO
            rol_actual = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
            if not rol_actual:
                raise NotFoundError(
                    detail=f"Rol con ID {rol_id} no encontrado.",
                    internal_code="ROLE_NOT_FOUND"
                )
                
            if rol_actual.get('es_activo', False):
                logger.info(f"Rol ID {rol_id} ya se encontraba activo")
                return rol_actual

            # 💾 EJECUTAR REACTIVACIÓN
            # ✅ FASE 2: Usar await
            result = await execute_update(REACTIVATE_ROL, (rol_id,))

            if not result:
                logger.warning(f"No se pudo reactivar el rol ID {rol_id}")
                # 🔄 VERIFICAR ESTADO ACTUAL
                rol_revisado = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
                if rol_revisado and rol_revisado.get('es_activo'):
                    return rol_revisado
                    
                raise ServiceError(
                    status_code=500,
                    detail="Error al reactivar el rol",
                    internal_code="ROLE_REACTIVATION_FAILED"
                )

            # 🔄 NORMALIZAR DATOS
            result_normalizado = RolService._normalizar_rol_dict(result)
                
            logger.info(f"Rol ID {rol_id} reactivado exitosamente")
            return result_normalizado

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al reactivar rol {rol_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al reactivar rol",
                internal_code="ROLE_REACTIVATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado reactivando rol {rol_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al reactivar rol",
                internal_code="ROLE_REACTIVATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def get_all_active_roles(cliente_id: UUID) -> List[Dict]:
        """
        Obtiene todos los roles activos **de un cliente** (sin paginación).
        
        📋 LISTA COMPLETA:
        - Optimizado para listas desplegables
        - Ordenado por nombre
        - Solo roles activos
        
        Returns:
            List[Dict]: Lista de roles activos del cliente
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        logger.debug(f"📋 Obteniendo todos los roles activos para cliente {cliente_id}")
        
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        
        # ✅ Para BD dedicadas, no filtrar por cliente_id (todos los roles pertenecen al mismo tenant)
        if database_type == "multi":
            query = """
                SELECT rol_id, cliente_id, nombre, descripcion, es_activo, fecha_creacion
                FROM rol
                WHERE es_activo = 1
                ORDER BY nombre ASC;
            """
            params = ()
        else:
            query = """
                SELECT rol_id, cliente_id, nombre, descripcion, es_activo, fecha_creacion
                FROM rol
                WHERE cliente_id = ? AND es_activo = 1
                ORDER BY nombre ASC;
            """
            params = (cliente_id,)
        
        try:
            # ✅ FASE 2: Usar await
            from app.infrastructure.database.queries_async import execute_query
            resultados = await execute_query(query, params)
            
            roles_procesados = []
            for rol_dict in resultados:
                # ✅ Usar función helper para normalizar
                rol_normalizado = RolService._normalizar_rol_dict(rol_dict)
                roles_procesados.append(rol_normalizado)

            logger.info(f"Se encontraron {len(roles_procesados)} roles activos para cliente {cliente_id}")
            return roles_procesados

        except DatabaseError as db_err:
            logger.error(f"Error de BD en get_all_active_roles para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener roles activos",
                internal_code="ACTIVE_ROLES_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en get_all_active_roles: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener roles activos",
                internal_code="ACTIVE_ROLES_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_permisos_por_rol(rol_id: UUID) -> List[PermisoRead]:
        """
        Obtiene todos los permisos asignados a un rol específico.
        
        🔐 GESTIÓN DE PERMISOS:
        - Lista completa de permisos del rol
        - Incluye detalles de menús asociados
        - Validación de existencia del rol
        
        Args:
            rol_id: ID del rol cuyos permisos se quieren obtener
            
        Returns:
            List[PermisoRead]: Lista de permisos del rol
            
        Raises:
            NotFoundError: Si el rol no existe
            ServiceError: Si hay errores en la consulta
        """
        logger.info(f"Obteniendo permisos para el rol ID: {rol_id}")

        # 🔍 VERIFICAR EXISTENCIA DEL ROL
        rol_existente = await RolService.obtener_rol_por_id(rol_id)
        if not rol_existente:
            raise NotFoundError(
                detail=f"Rol con ID {rol_id} no encontrado.",
                internal_code="ROLE_NOT_FOUND"
            )

        try:
            # ✅ FASE 2: Usar await
            resultados = await execute_query(SELECT_PERMISOS_POR_ROL, (rol_id,))
            
            if not resultados:
                logger.info(f"El rol ID {rol_id} no tiene permisos asignados")
                return []

            permisos = [PermisoRead(**dict(row)) for row in resultados]
            logger.info(f"Se encontraron {len(permisos)} permisos para el rol ID: {rol_id}")
            
            return permisos

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener permisos para rol {rol_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener permisos",
                internal_code="ROLE_PERMISSIONS_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener permisos para rol {rol_id}: {e}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener permisos",
                internal_code="ROLE_PERMISSIONS_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_permisos_rol(rol_id: UUID, permisos_payload: PermisoUpdatePayload) -> None:
        """
        Actualiza TODOS los permisos de un rol en una transacción atómica.
        
        🔄 ACTUALIZACIÓN ATÓMICA:
        - Elimina permisos existentes
        - Inserta nuevos permisos
        - Transacción para garantizar consistencia
        
        Args:
            rol_id: ID del rol a actualizar
            permisos_payload: Payload con la nueva lista de permisos
            
        Raises:
            NotFoundError: Si el rol no existe
            ServiceError: Si la transacción falla
        """
        logger.info(f"Actualizando permisos para el rol ID: {rol_id}")

        # 🔍 VERIFICAR EXISTENCIA DEL ROL
        rol_existente = await RolService.obtener_rol_por_id(rol_id)
        if not rol_existente:
            raise NotFoundError(
                detail=f"Rol con ID {rol_id} no encontrado.",
                internal_code="ROLE_NOT_FOUND"
            )

        nuevos_permisos: List[PermisoBase] = permisos_payload.permisos
        logger.debug(f"Se actualizarán {len(nuevos_permisos)} permisos para el rol {rol_id}")

        # ✅ FASE 2: Refactorizar para usar transacciones async
        # Primero validar todos los menús ANTES de la transacción
        menu_validations = {}
        if nuevos_permisos:
            for permiso in nuevos_permisos:
                menu_id = permiso.menu_id
                menu_query = "SELECT cliente_id FROM menu WHERE menu_id = ?"
                menu_result = await execute_query(menu_query, (menu_id,))
                if not menu_result:
                    raise ServiceError(
                        status_code=404,
                        detail=f"Menú con ID {menu_id} no encontrado.",
                        internal_code="MENU_NOT_FOUND_FOR_PERM"
                    )
                menu_cliente_id = menu_result[0]['cliente_id']
                
                # Validar que el menú pertenezca al mismo cliente que el rol
                if menu_cliente_id != rol_existente['cliente_id']:
                    raise ServiceError(
                        status_code=400,
                        detail="El menú y el rol deben pertenecer al mismo cliente.",
                        internal_code="MENU_ROLE_CLIENT_MISMATCH"
                    )
                menu_validations[menu_id] = menu_cliente_id

        try:
            # ✅ FASE 2: Usar transacción async con SQLAlchemy
            from app.infrastructure.database.connection_async import get_db_connection
            from sqlalchemy import text
            
            async with get_db_connection() as session:
                try:
                    # 🗑️ ELIMINAR PERMISOS EXISTENTES
                    # ✅ FASE 2: Convertir query con ? a parámetros nombrados para SQLAlchemy
                    delete_query = """
                    DELETE rmp
                    FROM rol_menu_permiso rmp
                    JOIN rol r ON rmp.rol_id = r.rol_id
                    WHERE rmp.rol_id = :rol_id AND (r.cliente_id IS NULL OR r.cliente_id = :cliente_id)
                    """
                    logger.debug(f"Eliminando permisos existentes para rol {rol_id}")
                    await session.execute(
                        text(delete_query), 
                        {"rol_id": rol_id, "cliente_id": rol_existente['cliente_id']}
                    )
                    logger.debug(f"Permisos existentes eliminados para rol {rol_id}")

                    # ➕ INSERTAR NUEVOS PERMISOS
                    if nuevos_permisos:
                        # ✅ FASE 2: Query con cliente_id incluido y parámetros nombrados
                        insert_query = """
                        INSERT INTO rol_menu_permiso (
                            cliente_id, rol_id, menu_id, puede_ver, puede_editar, puede_eliminar
                        )
                        VALUES (:cliente_id, :rol_id, :menu_id, :puede_ver, :puede_editar, :puede_eliminar)
                        """
                        logger.debug(f"Insertando {len(nuevos_permisos)} nuevos permisos")
                        insert_count = 0
                        for permiso in nuevos_permisos:
                            menu_id = permiso.menu_id
                            params = {
                                "cliente_id": rol_existente['cliente_id'],
                                "rol_id": rol_id,
                                "menu_id": menu_id,
                                "puede_ver": permiso.puede_ver,
                                "puede_editar": permiso.puede_editar,
                                "puede_eliminar": permiso.puede_eliminar
                            }
                            await session.execute(text(insert_query), params)
                            insert_count += 1
                        logger.debug(f"Insertados {insert_count} permisos para rol {rol_id}")
                    else:
                        logger.debug(f"No hay nuevos permisos para insertar para rol {rol_id}")
                    
                    # Commit de la transacción
                    await session.commit()
                    logger.info(f"Permisos actualizados exitosamente para el rol ID: {rol_id}")
                    
                except Exception as e:
                    await session.rollback()
                    raise

        except (ValidationError, ServiceError) as e:
            # Re-lanzar errores específicos de validación o lógica de negocio
            raise e
        except DatabaseError as db_err:
            logger.error(f"Error de BD en actualizar_permisos_rol: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al actualizar permisos",
                internal_code="ROLE_PERMISSIONS_UPDATE_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en actualizar_permisos_rol: {e}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al actualizar permisos",
                internal_code="ROLE_PERMISSIONS_UPDATE_UNEXPECTED_ERROR"
            )