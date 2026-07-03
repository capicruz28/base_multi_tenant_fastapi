# app/services/superadmin_usuario_service.py
"""
Servicio exclusivo para Superadmin - Gestión de Usuarios.

Este servicio proporciona operaciones de Superadmin sobre usuarios,
incluyendo vista global de todos los clientes con filtrado opcional.

Características principales:
- NO modifica servicios existentes en usuario_service.py
- Reutiliza métodos de UsuarioService cuando es posible
- Filtrado opcional por cliente_id
- Incluye información del cliente en respuestas
"""

from datetime import datetime
import math
from typing import Dict, List, Optional, Any
from uuid import UUID
import logging
import json

from sqlalchemy import text

# Importaciones de base de datos
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_query, execute_auth_query
from app.infrastructure.database.query_helpers import qmark_sql_text
from app.infrastructure.database.queries.auth.session.session_store_connection import (
    SESSION_STORE_CONNECTION,
)
from app.modules.superadmin.application.platform_global_query_intent import (
    kwargs_control_plane_read,
    kwargs_platform_global_read,
    kwargs_platform_global_user_lookup,
)
from app.core.tenant.platform_tenant_data_store import (
    resolve_platform_tenant_data_database_type,
    resolve_platform_tenant_data_execute_kwargs,
)
from app.core.tenant.platform_tenant_reachability import (
    ReachabilityResult,
    ReachabilityStatus,
    check_platform_tenant_reachability,
)

# Schemas
from app.modules.superadmin.presentation.schemas import (
    UsuarioSuperadminRead,
    PaginatedUsuarioSuperadminResponse,
    ClienteInfo,
    RolInfo,
    UsuarioActividadResponse,
    UsuarioSesionesResponse,
    RefreshTokenInfo
)

# Servicios existentes (reutilizar)
from app.modules.users.application.services.user_service import UsuarioService
from app.modules.tenant.application.services.cliente_service import ClienteService

# Excepciones
from app.core.exceptions import (
    ValidationError, NotFoundError, ServiceError, DatabaseError
)

# Base Service
from app.core.application.base_service import BaseService

logger = logging.getLogger(__name__)

_DEGRADATION_RESPONSE_KEYS = frozenset({
    "tenant_data_reachability",
    "tenant_data_available",
    "enrichment_degraded",
    "tenant_data_internal_code",
    "tenant_data_message",
})


class SuperadminUsuarioService(BaseService):
    """
    Servicio para operaciones Superadmin sobre usuarios.
    Permite ver usuarios de todos los clientes con filtrado opcional.
    """

    @staticmethod
    async def _fetch_cliente_info_from_admin(usuario_cliente_id: UUID) -> Optional[ClienteInfo]:
        from app.infrastructure.database.connection_async import DatabaseConnection

        query_cliente = """
        SELECT cliente_id, razon_social, subdominio, codigo_cliente,
               nombre_comercial, tipo_instalacion, estado_suscripcion
        FROM dbo.cliente
        WHERE cliente_id = ?
        """
        cliente_raw = await execute_query(
            qmark_sql_text(query_cliente, (usuario_cliente_id,)),
            **kwargs_control_plane_read(),
        )
        if not cliente_raw:
            return None
        cliente_row = cliente_raw[0]
        return ClienteInfo(
            cliente_id=cliente_row["cliente_id"],
            razon_social=cliente_row["razon_social"],
            subdominio=cliente_row["subdominio"],
            codigo_cliente=cliente_row.get("codigo_cliente"),
            nombre_comercial=cliente_row.get("nombre_comercial"),
            tipo_instalacion=cliente_row.get("tipo_instalacion", "cloud"),
            estado_suscripcion=cliente_row.get("estado_suscripcion", "activo"),
        )

    @staticmethod
    async def _resolve_cliente_info_for_usuario(
        usuario_cliente_id: Optional[UUID],
        *,
        filtered_cliente_id: Optional[UUID],
        filtered_cliente_info: Optional[ClienteInfo],
    ) -> ClienteInfo:
        if filtered_cliente_id and filtered_cliente_info:
            return filtered_cliente_info
        if usuario_cliente_id:
            info = await SuperadminUsuarioService._fetch_cliente_info_from_admin(
                usuario_cliente_id
            )
            if info:
                return info
        cliente_id_default = (
            usuario_cliente_id
            or filtered_cliente_id
            or UUID("00000000-0000-0000-0000-000000000000")
        )
        return ClienteInfo(
            cliente_id=cliente_id_default,
            razon_social="N/A",
            subdominio="N/A",
            codigo_cliente=None,
            nombre_comercial=None,
            tipo_instalacion="cloud",
            estado_suscripcion="activo",
        )

    @staticmethod
    async def _get_reachability_for_global_enrichment(
        cliente_id: UUID,
        cache: Dict[UUID, ReachabilityResult],
    ) -> ReachabilityResult:
        if cliente_id not in cache:
            cache[cliente_id] = await check_platform_tenant_reachability(cliente_id)
        return cache[cliente_id]

    @staticmethod
    def _build_usuario_superadmin_read_from_row(
        usuario_row: Dict[str, Any],
        *,
        usuario_cliente_id: UUID,
        row_cliente_info: ClienteInfo,
        roles: List[RolInfo],
        level_info: Dict[str, Any],
        reachability: Optional[ReachabilityResult] = None,
    ) -> UsuarioSuperadminRead:
        if reachability is not None and reachability.status != ReachabilityStatus.REACHABLE:
            return UsuarioSuperadminRead(
                usuario_id=usuario_row["usuario_id"],
                cliente_id=usuario_cliente_id,
                cliente=row_cliente_info,
                nombre_usuario=usuario_row["nombre_usuario"],
                correo=usuario_row.get("correo"),
                nombre=usuario_row.get("nombre"),
                apellido=usuario_row.get("apellido"),
                dni=usuario_row.get("dni"),
                telefono=usuario_row.get("telefono"),
                es_activo=bool(usuario_row["es_activo"]),
                es_eliminado=bool(usuario_row.get("es_eliminado", False)),
                proveedor_autenticacion=usuario_row.get("proveedor_autenticacion", "local"),
                referencia_externa_id=usuario_row.get("referencia_externa_id"),
                referencia_externa_email=usuario_row.get("referencia_externa_email"),
                correo_confirmado=bool(usuario_row.get("correo_confirmado", False)),
                intentos_fallidos=usuario_row.get("intentos_fallidos", 0),
                fecha_bloqueo=usuario_row.get("fecha_bloqueo"),
                ultimo_ip=usuario_row.get("ultimo_ip"),
                fecha_creacion=usuario_row["fecha_creacion"],
                fecha_ultimo_acceso=usuario_row.get("fecha_ultimo_acceso"),
                fecha_actualizacion=usuario_row.get("fecha_actualizacion"),
                sincronizado_desde=usuario_row.get("sincronizado_desde"),
                fecha_ultima_sincronizacion=usuario_row.get("fecha_ultima_sincronizacion"),
                roles=[],
                access_level=None,
                is_super_admin=False,
                user_type="user",
                tenant_data_reachability=reachability.status.value,
                tenant_data_available=False,
                enrichment_degraded=True,
                tenant_data_internal_code=reachability.internal_code,
                tenant_data_message=reachability.message,
            )

        return UsuarioSuperadminRead(
            usuario_id=usuario_row["usuario_id"],
            cliente_id=usuario_cliente_id,
            cliente=row_cliente_info,
            nombre_usuario=usuario_row["nombre_usuario"],
            correo=usuario_row.get("correo"),
            nombre=usuario_row.get("nombre"),
            apellido=usuario_row.get("apellido"),
            dni=usuario_row.get("dni"),
            telefono=usuario_row.get("telefono"),
            es_activo=bool(usuario_row["es_activo"]),
            es_eliminado=bool(usuario_row.get("es_eliminado", False)),
            proveedor_autenticacion=usuario_row.get("proveedor_autenticacion", "local"),
            referencia_externa_id=usuario_row.get("referencia_externa_id"),
            referencia_externa_email=usuario_row.get("referencia_externa_email"),
            correo_confirmado=bool(usuario_row.get("correo_confirmado", False)),
            intentos_fallidos=usuario_row.get("intentos_fallidos", 0),
            fecha_bloqueo=usuario_row.get("fecha_bloqueo"),
            ultimo_ip=usuario_row.get("ultimo_ip"),
            fecha_creacion=usuario_row["fecha_creacion"],
            fecha_ultimo_acceso=usuario_row.get("fecha_ultimo_acceso"),
            fecha_actualizacion=usuario_row.get("fecha_actualizacion"),
            sincronizado_desde=usuario_row.get("sincronizado_desde"),
            fecha_ultima_sincronizacion=usuario_row.get("fecha_ultima_sincronizacion"),
            roles=roles,
            access_level=level_info.get("access_level", 1),
            is_super_admin=level_info.get("is_super_admin", False),
            user_type=level_info.get("user_type", "user"),
        )

    @staticmethod
    def _serialize_usuario_for_global_list(usuario: UsuarioSuperadminRead) -> Dict[str, Any]:
        dump = usuario.model_dump()
        if not dump.get("enrichment_degraded"):
            for key in _DEGRADATION_RESPONSE_KEYS:
                dump.pop(key, None)
        return dump

    @staticmethod
    def _build_usuarios_globales_where(
        *,
        cliente_id: Optional[UUID],
        database_type: str,
        search: Optional[str] = None,
        es_activo: Optional[bool] = None,
        proveedor_autenticacion: Optional[str] = None,
        ordenar_por: str = "fecha_creacion",
        orden: str = "desc",
    ) -> tuple[str, List[Any], str, str]:
        """Construye WHERE, parámetros base, campo y dirección de ordenamiento."""
        search_param = f"%{search}%" if search else None

        where_conditions = ["u.es_eliminado = 0"]
        params: List[Any] = []

        if cliente_id and database_type == "single":
            where_conditions.append("u.cliente_id = ?")
            params.append(cliente_id)
            logger.debug(
                "[SUPERADMIN_USUARIOS] BD compartida: Filtrando usuarios por cliente_id %s",
                cliente_id,
            )
        elif cliente_id and database_type == "multi":
            logger.debug(
                "[SUPERADMIN_USUARIOS] BD dedicada: No filtrando por cliente_id "
                "(todos los usuarios pertenecen al mismo cliente)",
            )

        if search_param:
            where_conditions.append(
                "(? IS NULL OR u.nombre_usuario LIKE ? OR u.correo LIKE ? "
                "OR u.nombre LIKE ? OR u.apellido LIKE ?)"
            )
            params.extend([search_param, search_param, search_param, search_param, search_param])

        if es_activo is not None:
            where_conditions.append("u.es_activo = ?")
            params.append(1 if es_activo else 0)

        if proveedor_autenticacion:
            where_conditions.append("u.proveedor_autenticacion = ?")
            params.append(proveedor_autenticacion)

        where_clause = " AND ".join(where_conditions)

        valid_order_fields = {
            "fecha_creacion": "u.fecha_creacion",
            "fecha_ultimo_acceso": "u.fecha_ultimo_acceso",
            "nombre_usuario": "u.nombre_usuario",
            "nombre": "u.nombre",
            "apellido": "u.apellido",
        }
        order_field = valid_order_fields.get(ordenar_por, "u.fecha_creacion")
        order_dir = "DESC" if orden.lower() == "desc" else "ASC"

        return where_clause, params, order_field, order_dir

    _SEARCH_WHERE_QMARK = (
        "(? IS NULL OR u.nombre_usuario LIKE ? OR u.correo LIKE ? "
        "OR u.nombre LIKE ? OR u.apellido LIKE ?)"
    )
    _SEARCH_WHERE_NAMED = (
        "(:search IS NULL OR u.nombre_usuario LIKE :search OR u.correo LIKE :search "
        "OR u.nombre LIKE :search OR u.apellido LIKE :search)"
    )

    @staticmethod
    def _usuarios_globales_where_to_named(
        where_clause: str,
        params: List[Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Convierte WHERE del builder (? posicionales) a nombres F13-D2 sin alterar semántica."""
        clause = where_clause
        bind: Dict[str, Any] = {}
        idx = 0

        if "u.cliente_id = ?" in clause:
            clause = clause.replace("u.cliente_id = ?", "u.cliente_id = :cliente_id", 1)
            bind["cliente_id"] = params[idx]
            idx += 1

        if SuperadminUsuarioService._SEARCH_WHERE_QMARK in clause:
            clause = clause.replace(
                SuperadminUsuarioService._SEARCH_WHERE_QMARK,
                SuperadminUsuarioService._SEARCH_WHERE_NAMED,
                1,
            )
            bind["search"] = params[idx]
            idx += 5

        if "u.es_activo = ?" in clause:
            clause = clause.replace("u.es_activo = ?", "u.es_activo = :es_activo", 1)
            bind["es_activo"] = params[idx]
            idx += 1

        if "u.proveedor_autenticacion = ?" in clause:
            clause = clause.replace(
                "u.proveedor_autenticacion = ?",
                "u.proveedor_autenticacion = :proveedor_autenticacion",
                1,
            )
            bind["proveedor_autenticacion"] = params[idx]
            idx += 1

        if idx != len(params):
            raise ValueError(
                "Parámetros WHERE usuarios globales no coinciden con el builder posicional"
            )

        return clause, bind

    @staticmethod
    async def _resolve_usuarios_globales_query_kwargs(
        cliente_id: Optional[UUID],
    ) -> Dict[str, Any]:
        """Centraliza kwargs de execute_query para listado/count global de usuarios."""
        if cliente_id:
            return await resolve_platform_tenant_data_execute_kwargs(cliente_id)
        return kwargs_platform_global_read()

    @staticmethod
    async def _resolve_usuarios_globales_cliente_context(
        cliente_id: Optional[UUID],
    ) -> tuple[Optional[ClienteInfo], str]:
        """Resuelve ClienteInfo y database_type cuando hay filtro mono-tenant."""
        if not cliente_id:
            return None, "single"

        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND",
            )

        cliente_info = ClienteInfo(
            cliente_id=cliente.cliente_id,
            razon_social=cliente.razon_social,
            subdominio=cliente.subdominio,
            codigo_cliente=cliente.codigo_cliente,
            nombre_comercial=cliente.nombre_comercial,
            tipo_instalacion=getattr(cliente, "tipo_instalacion", "cloud"),
            estado_suscripcion=getattr(cliente, "estado_suscripcion", "activo"),
        )
        database_type = await resolve_platform_tenant_data_database_type(cliente_id)
        logger.debug(
            "[SUPERADMIN_USUARIOS] Cliente %s database_type=%s (resolver)",
            cliente_id,
            database_type,
        )
        return cliente_info, database_type

    @staticmethod
    @BaseService.handle_service_errors
    async def count_usuarios_globales(
        cliente_id: Optional[UUID] = None,
        search: Optional[str] = None,
        es_activo: Optional[bool] = None,
        proveedor_autenticacion: Optional[str] = None,
        ordenar_por: str = "fecha_creacion",
        orden: str = "desc",
    ) -> int:
        """Cuenta usuarios globales (COUNT only — sin SELECT ni enriquecimiento)."""
        _, database_type = await SuperadminUsuarioService._resolve_usuarios_globales_cliente_context(
            cliente_id
        )

        where_clause, params, _, _ = SuperadminUsuarioService._build_usuarios_globales_where(
            cliente_id=cliente_id,
            database_type=database_type,
            search=search,
            es_activo=es_activo,
            proveedor_autenticacion=proveedor_autenticacion,
            ordenar_por=ordenar_por,
            orden=orden,
        )

        named_where, bind_params = SuperadminUsuarioService._usuarios_globales_where_to_named(
            where_clause,
            params,
        )

        count_query = f"""
        SELECT COUNT(*) as total
        FROM dbo.usuario u
        WHERE {named_where}
        """
        tenant_query_kwargs = await SuperadminUsuarioService._resolve_usuarios_globales_query_kwargs(
            cliente_id
        )
        count_result = await execute_query(
            text(count_query).bindparams(**bind_params),
            **tenant_query_kwargs,
        )
        return count_result[0]["total"] if count_result else 0

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_estadisticas_globales_usuarios(
        cliente_id: Optional[UUID] = None,
        search: Optional[str] = None,
        proveedor_autenticacion: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Estadísticas agregadas de usuarios globales (COUNT-only, sin listado ni enriquecimiento).

        Paridad de filtros con count_usuarios_globales / listado excepto es_activo (desglose interno).
        """
        _, database_type = await SuperadminUsuarioService._resolve_usuarios_globales_cliente_context(
            cliente_id
        )

        where_clause, params, _, _ = SuperadminUsuarioService._build_usuarios_globales_where(
            cliente_id=cliente_id,
            database_type=database_type,
            search=search,
            es_activo=None,
            proveedor_autenticacion=proveedor_autenticacion,
            ordenar_por="fecha_creacion",
            orden="desc",
        )

        named_where, bind_params = SuperadminUsuarioService._usuarios_globales_where_to_named(
            where_clause,
            params,
        )

        stats_query = f"""
        SELECT
            COUNT(*) AS total_usuarios,
            ISNULL(SUM(CASE WHEN u.es_activo = 1 THEN 1 ELSE 0 END), 0) AS usuarios_activos,
            ISNULL(SUM(CASE WHEN u.es_activo = 0 THEN 1 ELSE 0 END), 0) AS usuarios_inactivos,
            ISNULL(SUM(CASE WHEN u.fecha_bloqueo IS NOT NULL THEN 1 ELSE 0 END), 0) AS usuarios_bloqueados
        FROM dbo.usuario u
        WHERE {named_where}
        """

        tenant_query_kwargs = await SuperadminUsuarioService._resolve_usuarios_globales_query_kwargs(
            cliente_id
        )
        stats_result = await execute_query(
            text(stats_query).bindparams(**bind_params),
            **tenant_query_kwargs,
        )

        if not stats_result:
            return {
                "total_usuarios": 0,
                "usuarios_activos": 0,
                "usuarios_inactivos": 0,
                "usuarios_bloqueados": 0,
            }

        row = stats_result[0]
        return {
            "total_usuarios": int(row.get("total_usuarios") or 0),
            "usuarios_activos": int(row.get("usuarios_activos") or 0),
            "usuarios_inactivos": int(row.get("usuarios_inactivos") or 0),
            "usuarios_bloqueados": int(row.get("usuarios_bloqueados") or 0),
        }

    @staticmethod
    @BaseService.handle_service_errors
    async def get_usuarios_globales(
        cliente_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        es_activo: Optional[bool] = None,
        proveedor_autenticacion: Optional[str] = None,
        ordenar_por: str = "fecha_creacion",
        orden: str = "desc"
    ) -> Dict:
        """
        Obtiene usuarios globales con filtro opcional por cliente.
        
        Args:
            cliente_id: ID del cliente para filtrar (opcional)
            page: Número de página
            limit: Registros por página
            search: Término de búsqueda
            es_activo: Filtrar por estado activo
            proveedor_autenticacion: Filtrar por método de autenticación
            ordenar_por: Campo para ordenar
            orden: 'asc' o 'desc'
            
        Returns:
            Dict con usuarios paginados y metadatos
        """
        logger.debug(f"Obteniendo usuarios globales - cliente_id: {cliente_id}, page: {page}, limit: {limit}")

        # Validar parámetros
        if page < 1:
            raise ValidationError(
                detail="El número de página debe ser mayor o igual a 1.",
                internal_code="INVALID_PAGE_NUMBER"
            )
        if limit < 1 or limit > 100:
            raise ValidationError(
                detail="El límite por página debe estar entre 1 y 100.",
                internal_code="INVALID_LIMIT"
            )

        cliente_info, database_type = await SuperadminUsuarioService._resolve_usuarios_globales_cliente_context(
            cliente_id
        )

        total_usuarios = await SuperadminUsuarioService.count_usuarios_globales(
            cliente_id=cliente_id,
            search=search,
            es_activo=es_activo,
            proveedor_autenticacion=proveedor_autenticacion,
            ordenar_por=ordenar_por,
            orden=orden,
        )

        offset = (page - 1) * limit
        where_clause, params, order_field, order_dir = SuperadminUsuarioService._build_usuarios_globales_where(
            cliente_id=cliente_id,
            database_type=database_type,
            search=search,
            es_activo=es_activo,
            proveedor_autenticacion=proveedor_autenticacion,
            ordenar_por=ordenar_por,
            orden=orden,
        )

        named_where, bind_params = SuperadminUsuarioService._usuarios_globales_where_to_named(
            where_clause,
            params,
        )
        bind_params["offset"] = offset
        bind_params["limit"] = limit

        # Query para obtener datos (SIN JOIN con cliente, ya que cliente está en BD centralizada)
        data_query = f"""
        SELECT 
            u.usuario_id,
            u.cliente_id,
            u.nombre_usuario,
            u.correo,
            u.nombre,
            u.apellido,
            u.dni,
            u.telefono,
            u.es_activo,
            u.es_eliminado,
            u.proveedor_autenticacion,
            u.referencia_externa_id,
            u.referencia_externa_email,
            u.correo_confirmado,
            u.intentos_fallidos,
            u.fecha_bloqueo,
            u.ultimo_ip,
            u.fecha_creacion,
            u.fecha_ultimo_acceso,
            u.fecha_actualizacion,
            u.sincronizado_desde,
            u.fecha_ultima_sincronizacion
        FROM dbo.usuario u
        WHERE {named_where}
        ORDER BY {order_field} {order_dir}
        OFFSET :offset ROWS
        FETCH NEXT :limit ROWS ONLY
        """
        tenant_query_kwargs = await SuperadminUsuarioService._resolve_usuarios_globales_query_kwargs(
            cliente_id
        )
        usuarios_raw = await execute_query(
            text(data_query).bindparams(**bind_params),
            **tenant_query_kwargs,
        )

        # Procesar usuarios y obtener roles
        usuarios_procesados = []
        reachability_cache: Dict[UUID, ReachabilityResult] = {}
        use_fail_soft_enrichment = cliente_id is None
        for usuario_row in usuarios_raw:
            # ✅ CORRECCIÓN: Para BD dedicadas, establecer cliente_id desde el contexto si es NULL o UUID nulo
            usuario_cliente_id = usuario_row.get('cliente_id')
            if database_type == "multi":
                from uuid import UUID
                if not usuario_cliente_id or (isinstance(usuario_cliente_id, UUID) and usuario_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                    usuario_cliente_id = cliente_id
                    usuario_row['cliente_id'] = cliente_id
                    logger.debug(f"[SUPERADMIN_USUARIOS] BD dedicada: Usuario {usuario_row.get('usuario_id')} tenía cliente_id NULL, establecido a {cliente_id}")
            
            # Resolver cliente embebido por fila (vista global) o reutilizar filtro tenant
            row_cliente_info = await SuperadminUsuarioService._resolve_cliente_info_for_usuario(
                usuario_cliente_id,
                filtered_cliente_id=cliente_id,
                filtered_cliente_info=cliente_info,
            )

            reachability: Optional[ReachabilityResult] = None
            if use_fail_soft_enrichment and usuario_cliente_id:
                reachability = await SuperadminUsuarioService._get_reachability_for_global_enrichment(
                    usuario_cliente_id,
                    reachability_cache,
                )
                if reachability.status != ReachabilityStatus.REACHABLE:
                    usuarios_procesados.append(
                        SuperadminUsuarioService._build_usuario_superadmin_read_from_row(
                            usuario_row,
                            usuario_cliente_id=usuario_cliente_id,
                            row_cliente_info=row_cliente_info,
                            roles=[],
                            level_info={},
                            reachability=reachability,
                        )
                    )
                    continue

            # Obtener roles del usuario
            roles = await SuperadminUsuarioService._obtener_roles_usuario(
                usuario_row['usuario_id'],
                usuario_cliente_id
            )

            # Obtener niveles de acceso
            level_info = await UsuarioService.get_user_level_info(
                usuario_row['usuario_id'],
                usuario_cliente_id
            )

            usuarios_procesados.append(
                SuperadminUsuarioService._build_usuario_superadmin_read_from_row(
                    usuario_row,
                    usuario_cliente_id=usuario_cliente_id,
                    row_cliente_info=row_cliente_info,
                    roles=roles,
                    level_info=level_info,
                )
            )

        total_paginas = math.ceil(total_usuarios / limit) if limit > 0 else 0

        return {
            "usuarios": [
                SuperadminUsuarioService._serialize_usuario_for_global_list(u)
                for u in usuarios_procesados
            ],
            "total_usuarios": total_usuarios,
            "pagina_actual": page,
            "total_paginas": total_paginas
        }

    @staticmethod
    async def _obtener_roles_usuario(usuario_id: UUID, cliente_id: UUID) -> List[RolInfo]:
        """Obtiene roles activos de un usuario."""
        try:
            query = """
            SELECT 
                r.rol_id,
                r.nombre,
                r.codigo_rol,
                r.nivel_acceso,
                r.es_rol_sistema,
                ur.fecha_asignacion,
                ur.es_activo
            FROM dbo.rol r
            INNER JOIN dbo.usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = :usuario_id
              AND ur.cliente_id = :cliente_id
              AND ur.es_activo = 1
              AND r.es_activo = 1
            ORDER BY r.nombre
            """
            roles_raw = await execute_query(
                text(query).bindparams(
                    usuario_id=str(usuario_id),
                    cliente_id=str(cliente_id),
                ),
                **await resolve_platform_tenant_data_execute_kwargs(cliente_id),
            )
            
            roles = []
            for rol_row in roles_raw:
                rol = RolInfo(
                    rol_id=rol_row['rol_id'],
                    nombre=rol_row['nombre'],
                    codigo_rol=rol_row.get('codigo_rol'),
                    nivel_acceso=rol_row.get('nivel_acceso', 1),
                    es_rol_sistema=bool(rol_row.get('es_rol_sistema', False)),
                    fecha_asignacion=rol_row.get('fecha_asignacion'),
                    es_activo=True
                )
                roles.append(rol)
            
            return roles
        except Exception as e:
            logger.error(f"Error obteniendo roles para usuario {usuario_id}: {e}")
            return []

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_usuario_completo(usuario_id: UUID, cliente_id: Optional[UUID] = None) -> Optional[Dict]:
        """
        Obtiene información completa de un usuario (Superadmin puede ver cualquier usuario).
        
        Args:
            usuario_id: ID del usuario a obtener
            cliente_id: ID del cliente (opcional). Si se proporciona, consulta directamente en la BD de ese tenant.
                       Si no se proporciona, obtiene el cliente_id del usuario desde BD ADMIN.
        """
        logger.debug(f"Obteniendo usuario completo ID {usuario_id} (Superadmin), cliente_id: {cliente_id}")

        # Si se proporciona cliente_id, usarlo directamente
        # Si no, obtener el cliente_id del usuario desde la BD centralizada (ADMIN)
        from app.infrastructure.database.connection_async import DatabaseConnection
        usuario_cliente_id = cliente_id
        
        if not usuario_cliente_id:
            query_cliente = """
            SELECT cliente_id
            FROM dbo.usuario
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            # ✅ CORRECCIÓN: Convertir UUID a string para SQL Server
            # ✅ FASE 2: Usar await
            cliente_info_raw = await execute_query(
                qmark_sql_text(query_cliente, (str(usuario_id),)),
                **kwargs_platform_global_user_lookup(),
            )
            
            if not cliente_info_raw:
                return None
            
            usuario_cliente_id = cliente_info_raw[0]['cliente_id']
            logger.debug(f"[USUARIO] Cliente_id del usuario {usuario_id} obtenido desde BD ADMIN: {usuario_cliente_id}")
        else:
            logger.debug(f"[USUARIO] Usando cliente_id proporcionado: {usuario_cliente_id}")
        
        # Obtener usuario básico usando la conexión del cliente (SIN JOIN con cliente)
        query = """
        SELECT 
            u.*
        FROM dbo.usuario u
        WHERE u.usuario_id = :usuario_id
          AND (u.cliente_id = :cliente_id OR u.cliente_id IS NULL)
          AND u.es_eliminado = 0
        """
        usuario_raw = await execute_query(
            text(query).bindparams(
                usuario_id=str(usuario_id),
                cliente_id=usuario_cliente_id,
            ),
            **await resolve_platform_tenant_data_execute_kwargs(usuario_cliente_id),
        )
        
        if not usuario_raw:
            return None
        
        usuario_row = usuario_raw[0]
        
        # Obtener información del cliente desde BD centralizada (ADMIN)
        from app.infrastructure.database.connection_async import DatabaseConnection
        query_cliente = """
        SELECT cliente_id, razon_social, subdominio, codigo_cliente, 
               nombre_comercial, tipo_instalacion, estado_suscripcion
        FROM dbo.cliente
        WHERE cliente_id = ?
        """
        # ✅ FASE 2: Usar await
        cliente_raw = await execute_query(
            qmark_sql_text(query_cliente, (usuario_cliente_id,)),
            **kwargs_control_plane_read(),
        )
        
        if not cliente_raw:
            return None
        
        cliente_row = cliente_raw[0]

        # Información del cliente
        cliente_info = ClienteInfo(
            cliente_id=cliente_row['cliente_id'],
            razon_social=cliente_row['razon_social'],
            subdominio=cliente_row['subdominio'],
            codigo_cliente=cliente_row.get('codigo_cliente'),
            nombre_comercial=cliente_row.get('nombre_comercial'),
            tipo_instalacion=cliente_row.get('tipo_instalacion', 'cloud'),
            estado_suscripcion=cliente_row.get('estado_suscripcion', 'activo')
        )

        # Obtener roles
        roles = await SuperadminUsuarioService._obtener_roles_usuario(
            usuario_id,
            usuario_row['cliente_id']
        )

        # Obtener niveles de acceso
        level_info = await UsuarioService.get_user_level_info(
            usuario_id,
            usuario_row['cliente_id']
        )

        # Construir respuesta
        usuario = UsuarioSuperadminRead(
            usuario_id=usuario_row['usuario_id'],
            cliente_id=usuario_row['cliente_id'],
            cliente=cliente_info,
            nombre_usuario=usuario_row['nombre_usuario'],
            correo=usuario_row.get('correo'),
            nombre=usuario_row.get('nombre'),
            apellido=usuario_row.get('apellido'),
            dni=usuario_row.get('dni'),
            telefono=usuario_row.get('telefono'),
            es_activo=bool(usuario_row['es_activo']),
            es_eliminado=bool(usuario_row.get('es_eliminado', False)),
            proveedor_autenticacion=usuario_row.get('proveedor_autenticacion', 'local'),
            referencia_externa_id=usuario_row.get('referencia_externa_id'),
            referencia_externa_email=usuario_row.get('referencia_externa_email'),
            correo_confirmado=bool(usuario_row.get('correo_confirmado', False)),
            intentos_fallidos=usuario_row.get('intentos_fallidos', 0),
            fecha_bloqueo=usuario_row.get('fecha_bloqueo'),
            ultimo_ip=usuario_row.get('ultimo_ip'),
            fecha_creacion=usuario_row['fecha_creacion'],
            fecha_ultimo_acceso=usuario_row.get('fecha_ultimo_acceso'),
            fecha_actualizacion=usuario_row.get('fecha_actualizacion'),
            sincronizado_desde=usuario_row.get('sincronizado_desde'),
            fecha_ultima_sincronizacion=usuario_row.get('fecha_ultima_sincronizacion'),
            roles=roles,
            access_level=level_info.get('access_level', 1),
            is_super_admin=level_info.get('is_super_admin', False),
            user_type=level_info.get('user_type', 'user')
        )

        return usuario.model_dump()

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_actividad_usuario(
        usuario_id: UUID,
        cliente_id: Optional[UUID] = None,
        limite: int = 50,
        tipo_evento: Optional[str] = None
    ) -> Dict:
        """
        Obtiene actividad reciente de un usuario.
        
        Args:
            usuario_id: ID del usuario
            cliente_id: ID del cliente (opcional). Si se proporciona, consulta directamente en la BD de ese tenant.
                       Si no se proporciona, obtiene el cliente_id del usuario desde BD ADMIN.
            limite: Número de eventos a retornar
            tipo_evento: Tipo de evento a filtrar (opcional)
        """
        logger.debug(f"Obteniendo actividad para usuario {usuario_id}, cliente_id: {cliente_id}")

        # Validar límite
        if limite < 1 or limite > 200:
            raise ValidationError(
                detail="El límite debe estar entre 1 y 200.",
                internal_code="INVALID_LIMIT"
            )

        # Si se proporciona cliente_id, usarlo directamente
        # Si no, obtener el cliente_id del usuario desde la BD centralizada (ADMIN)
        from app.infrastructure.database.connection_async import DatabaseConnection
        usuario_cliente_id = cliente_id
        
        if not usuario_cliente_id:
            query_cliente = """
            SELECT cliente_id
            FROM dbo.usuario
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            # ✅ CORRECCIÓN: Convertir UUID a string para SQL Server
            # ✅ FASE 2: Usar await
            cliente_info_raw = await execute_query(
                qmark_sql_text(query_cliente, (str(usuario_id),)),
                **kwargs_platform_global_user_lookup(),
            )
            
            if not cliente_info_raw:
                raise NotFoundError(
                    detail=f"Usuario con ID {usuario_id} no encontrado.",
                    internal_code="USER_NOT_FOUND"
                )
            
            usuario_cliente_id = cliente_info_raw[0]['cliente_id']
            logger.debug(f"[ACTIVIDAD] Cliente_id del usuario {usuario_id} obtenido desde BD ADMIN: {usuario_cliente_id}")
        else:
            logger.debug(f"[ACTIVIDAD] Usando cliente_id proporcionado: {usuario_cliente_id}")
        
        # Obtener información básica del usuario usando la conexión del cliente
        query_usuario = """
        SELECT 
            usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido,
            dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
            fecha_creacion, fecha_ultimo_acceso, fecha_actualizacion, ultimo_ip,
            sincronizado_desde, fecha_ultima_sincronizacion, es_eliminado,
            intentos_fallidos, fecha_bloqueo, referencia_externa_id, referencia_externa_email
        FROM dbo.usuario
        WHERE usuario_id = :usuario_id
          AND (cliente_id = :cliente_id OR cliente_id IS NULL)
          AND es_eliminado = 0
        """
        usuario_raw = await execute_query(
            text(query_usuario).bindparams(
                usuario_id=str(usuario_id),
                cliente_id=usuario_cliente_id,
            ),
            **await resolve_platform_tenant_data_execute_kwargs(usuario_cliente_id),
        )
        
        if not usuario_raw:
            raise NotFoundError(
                detail=f"Usuario con ID {usuario_id} no encontrado.",
                internal_code="USER_NOT_FOUND"
            )
        
        usuario = usuario_raw[0]

        audit_bind: Dict[str, Any] = {
            "limite": limite,
            "usuario_id": str(usuario_id),
            "cliente_id": usuario_cliente_id,
        }
        where_conditions = [
            "a.usuario_id = :usuario_id",
            "a.cliente_id = :cliente_id",
        ]

        if tipo_evento:
            where_conditions.append("a.evento = :tipo_evento")
            audit_bind["tipo_evento"] = tipo_evento

        where_clause = " AND ".join(where_conditions)

        query = f"""
        SELECT TOP (:limite)
            a.log_id,
            a.fecha_evento,
            a.evento,
            a.exito,
            a.ip_address,
            a.user_agent,
            a.device_info,
            a.descripcion,
            a.codigo_error,
            a.metadata_json
        FROM dbo.auth_audit_log a
        WHERE {where_clause}
        ORDER BY a.fecha_evento DESC
        """
        eventos_raw = await execute_query(
            text(query).bindparams(**audit_bind),
            **await resolve_platform_tenant_data_execute_kwargs(usuario_cliente_id),
        )

        eventos = []
        for evento_row in eventos_raw:
            metadata = None
            if evento_row.get('metadata_json'):
                try:
                    metadata = json.loads(evento_row['metadata_json'])
                except:
                    pass

            eventos.append({
                "log_id": evento_row['log_id'],
                "fecha_evento": evento_row['fecha_evento'].isoformat() if evento_row['fecha_evento'] else None,
                "evento": evento_row['evento'],
                "exito": bool(evento_row['exito']),
                "ip_address": evento_row.get('ip_address'),
                "user_agent": evento_row.get('user_agent'),
                "device_info": evento_row.get('device_info'),
                "descripcion": evento_row.get('descripcion'),
                "codigo_error": evento_row.get('codigo_error'),
                "metadata": metadata
            })

        # Contar total
        # ✅ CORRECCIÓN: params no incluye el límite, solo los parámetros del WHERE
        count_query = f"""
        SELECT COUNT(*) as total
        FROM dbo.auth_audit_log a
        WHERE {where_clause}
        """
        # Usar la conexión del cliente del usuario
        # ✅ FASE 2: Usar await
        count_bind = {k: v for k, v in audit_bind.items() if k != "limite"}
        count_result = await execute_query(
            text(count_query).bindparams(**count_bind),
            **await resolve_platform_tenant_data_execute_kwargs(usuario_cliente_id),
        )
        total_eventos = count_result[0]['total'] if count_result else 0

        return {
            "usuario_id": usuario_id,
            "ultimo_acceso": usuario.get('fecha_ultimo_acceso'),
            "ultimo_ip": usuario.get('ultimo_ip'),
            "total_eventos": total_eventos,
            "eventos": eventos
        }

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_sesiones_usuario(
        usuario_id: UUID,
        cliente_id: Optional[UUID] = None,
        solo_activas: bool = True
    ) -> Dict:
        """
        Obtiene sesiones (tokens refresh) de un usuario.
        
        Args:
            usuario_id: ID del usuario
            cliente_id: ID del cliente (opcional). Si se proporciona, consulta directamente en la BD de ese tenant.
                       Si no se proporciona, obtiene el cliente_id del usuario desde BD ADMIN.
            solo_activas: Si solo mostrar sesiones activas
        """
        logger.debug(f"Obteniendo sesiones para usuario {usuario_id}, cliente_id: {cliente_id}")

        # Si se proporciona cliente_id, usarlo directamente
        # Si no, obtener el cliente_id del usuario desde la BD centralizada (ADMIN)
        from app.infrastructure.database.connection_async import DatabaseConnection
        usuario_cliente_id = cliente_id
        
        if not usuario_cliente_id:
            query_cliente = """
            SELECT cliente_id
            FROM dbo.usuario
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            # ✅ CORRECCIÓN: Convertir UUID a string para SQL Server
            # ✅ FASE 2: Usar await
            cliente_info_raw = await execute_query(
                qmark_sql_text(query_cliente, (str(usuario_id),)),
                **kwargs_platform_global_user_lookup(),
            )
            
            if not cliente_info_raw:
                raise NotFoundError(
                    detail=f"Usuario con ID {usuario_id} no encontrado.",
                    internal_code="USER_NOT_FOUND"
                )
            
            usuario_cliente_id = cliente_info_raw[0]['cliente_id']
            logger.debug(f"[SESIONES] Cliente_id del usuario {usuario_id} obtenido desde BD ADMIN: {usuario_cliente_id}")
        else:
            logger.debug(f"[SESIONES] Usando cliente_id proporcionado: {usuario_cliente_id}")

        from uuid import UUID as UUIDType

        if not isinstance(usuario_cliente_id, UUIDType):
            usuario_cliente_id = UUIDType(str(usuario_cliente_id))

        from app.modules.auth.application.session.session_v2_feature import (
            is_session_v2_enabled,
        )

        if is_session_v2_enabled(usuario_cliente_id):
            from app.modules.auth.application.services.active_sessions_read_service import (
                ActiveSessionsReadService,
            )

            session_dtos = await ActiveSessionsReadService.list_user_sessions(
                usuario_cliente_id,
                usuario_id,
            )
            sesiones = [
                SuperadminUsuarioService._map_user_session_to_refresh_token_info(dto)
                for dto in session_dtos
            ]
            sesiones_activas = sum(
                1
                for s in sesiones
                if not s.is_revoked and s.expires_at > datetime.now()
            )
            return {
                "usuario_id": usuario_id,
                "total_sesiones": len(sesiones),
                "sesiones_activas": sesiones_activas,
                "sesiones": [s.model_dump() for s in sesiones],
            }

        # V1 — lectura legacy desde refresh_tokens
        where_conditions = ["rt.usuario_id = ?"]
        # ✅ CORRECCIÓN: Convertir UUID a string para SQL Server
        params = [str(usuario_id)]

        if solo_activas:
            where_conditions.append("rt.is_revoked = 0")
            where_conditions.append("rt.expires_at > GETDATE()")

        where_clause = " AND ".join(where_conditions)

        query = f"""
        SELECT 
            rt.token_id,
            rt.client_type,
            rt.device_name,
            rt.device_id,
            rt.ip_address,
            rt.user_agent,
            rt.created_at,
            rt.expires_at,
            rt.is_revoked,
            rt.last_used_at,
            rt.uso_count,
            rt.revoked_at,
            rt.revoked_reason
        FROM dbo.refresh_tokens rt
        WHERE {where_clause}
        ORDER BY rt.created_at DESC
        """
        # Usar la conexión del cliente del usuario
        # ✅ FASE 2: Usar await
        sesiones_raw = await execute_query(
            qmark_sql_text(query, tuple(params)),
            **kwargs_platform_global_read(
                client_id=usuario_cliente_id,
                connection_type=SESSION_STORE_CONNECTION,
            ),
        )

        sesiones = []
        sesiones_activas = 0
        for sesion_row in sesiones_raw:
            is_active = not sesion_row['is_revoked'] and sesion_row['expires_at'] > datetime.now()
            if is_active:
                sesiones_activas += 1

            sesion = RefreshTokenInfo(
                token_id=sesion_row['token_id'],
                client_type=sesion_row['client_type'],
                device_name=sesion_row.get('device_name'),
                device_id=sesion_row.get('device_id'),
                ip_address=sesion_row.get('ip_address'),
                user_agent=sesion_row.get('user_agent'),
                created_at=sesion_row['created_at'],
                expires_at=sesion_row['expires_at'],
                is_revoked=bool(sesion_row['is_revoked']),
                last_used_at=sesion_row.get('last_used_at'),
                uso_count=sesion_row.get('uso_count', 0),
                revoked_at=sesion_row.get('revoked_at'),
                revoked_reason=sesion_row.get('revoked_reason')
            )
            sesiones.append(sesion)

        return {
            "usuario_id": usuario_id,
            "total_sesiones": len(sesiones),
            "sesiones_activas": sesiones_activas,
            "sesiones": [s.model_dump() for s in sesiones]
        }

    @staticmethod
    def _map_user_session_to_refresh_token_info(
        dto: "UserSessionRead",
    ) -> RefreshTokenInfo:
        """Mapea DTO C09 → RefreshTokenInfo (superset compatible V1/V2)."""
        from app.modules.auth.presentation.schemas_sessions import UserSessionRead

        device = dto.device
        return RefreshTokenInfo(
            token_id=dto.token_id,
            session_id=dto.session_id,
            client_type=dto.client_type,
            device_name=dto.device_name or device.device_label,
            device_id=dto.device_id or device.device_id,
            ip_address=dto.ip_address or dto.login_ip or device.ip_address,
            login_ip=dto.login_ip,
            platform=dto.platform,
            user_agent=None,
            created_at=dto.created_at,
            expires_at=dto.expires_at,
            is_revoked=False,
            last_used_at=dto.last_refresh_at or dto.last_used_at,
            uso_count=0,
            revoked_at=dto.revoked_at,
            revoked_reason=dto.revoked_reason,
        )

