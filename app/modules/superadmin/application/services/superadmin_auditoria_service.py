# app/services/superadmin_auditoria_service.py
"""
Servicio exclusivo para Superadmin - Auditoría.

Este servicio proporciona operaciones de Superadmin sobre auditoría,
incluyendo logs de autenticación y sincronización con filtrado opcional por cliente.

Características principales:
- NO modifica servicios existentes
- Filtrado opcional por cliente_id
- Incluye información de usuario y cliente en respuestas
"""

from datetime import datetime
import math
import json
from typing import Dict, List, Optional, Any
import logging

# Importaciones de base de datos
from app.infrastructure.database.queries import execute_query

# Schemas
from app.modules.superadmin.presentation.schemas import (
    AuthAuditLogRead,
    PaginatedAuthAuditLogResponse,
    LogSincronizacionRead,
    PaginatedLogSincronizacionResponse,
    AuditoriaEstadisticasResponse,
    PeriodoInfo,
    AutenticacionStats,
    SincronizacionStats,
    IPStats,
    UsuarioStats,
    ClienteInfo,
    UsuarioInfo
)

# Servicios existentes (reutilizar)
from app.modules.tenant.application.services.cliente_service import ClienteService

# Excepciones
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    ServiceError,
    DatabaseError,
)

# Base Service
from app.infrastructure.database.repositories.base_repository import BaseService

logger = logging.getLogger(__name__)


class SuperadminAuditoriaService(BaseService):
    """
    Servicio para operaciones Superadmin sobre auditoría.
    Permite ver logs de todos los clientes con filtrado opcional.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def get_logs_autenticacion(
        cliente_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        evento: Optional[str] = None,
        exito: Optional[bool] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        ordenar_por: str = "fecha_evento",
        orden: str = "desc"
    ) -> Dict:
        """
        Obtiene logs de autenticación con filtros avanzados.
        """
        logger.info(f"Obteniendo logs de autenticación - cliente_id: {cliente_id}, page: {page}")

        # Validar parámetros
        if page < 1:
            raise ValidationError(
                detail="El número de página debe ser mayor o igual a 1.",
                internal_code="INVALID_PAGE_NUMBER"
            )
        if limit < 1 or limit > 200:
            raise ValidationError(
                detail="El límite por página debe estar entre 1 y 200.",
                internal_code="INVALID_LIMIT"
            )
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError(
                detail="fecha_desde debe ser anterior a fecha_hasta.",
                internal_code="INVALID_DATE_RANGE"
            )

        # Validar cliente_id si se proporciona y obtener información del cliente
        cliente_info_cache: Optional[ClienteInfo] = None
        if cliente_id:
            cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
            if not cliente:
                raise NotFoundError(
                    detail=f"Cliente con ID {cliente_id} no encontrado.",
                    internal_code="CLIENT_NOT_FOUND"
                )
            # Cachear información del cliente
            cliente_info_cache = ClienteInfo(
                cliente_id=cliente.cliente_id,
                razon_social=cliente.razon_social,
                subdominio=cliente.subdominio,
                codigo_cliente=cliente.codigo_cliente,
                nombre_comercial=cliente.nombre_comercial,
                tipo_instalacion=getattr(cliente, 'tipo_instalacion', 'cloud'),
                estado_suscripcion=getattr(cliente, 'estado_suscripcion', 'activo')
            )

        offset = (page - 1) * limit

        # Construir condiciones WHERE
        where_conditions = []
        params = []

        if cliente_id:
            where_conditions.append("a.cliente_id = ?")
            params.append(cliente_id)

        if usuario_id:
            where_conditions.append("a.usuario_id = ?")
            params.append(usuario_id)

        if evento:
            where_conditions.append("a.evento = ?")
            params.append(evento)

        if exito is not None:
            where_conditions.append("a.exito = ?")
            params.append(1 if exito else 0)

        if fecha_desde:
            where_conditions.append("a.fecha_evento >= ?")
            params.append(fecha_desde)

        if fecha_hasta:
            where_conditions.append("a.fecha_evento <= ?")
            params.append(fecha_hasta)

        if ip_address:
            where_conditions.append("a.ip_address = ?")
            params.append(ip_address)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Validar ordenar_por
        valid_order_fields = {
            "fecha_evento": "a.fecha_evento",
            "evento": "a.evento",
            "usuario_id": "a.usuario_id"
        }
        order_field = valid_order_fields.get(ordenar_por, "a.fecha_evento")
        order_dir = "DESC" if orden.lower() == "desc" else "ASC"

        # Query para contar total
        count_query = f"""
        SELECT COUNT(*) as total
        FROM dbo.auth_audit_log a
        WHERE {where_clause}
        """
        # Si se filtra por cliente_id, usar la conexión de ese cliente
        count_result = execute_query(count_query, tuple(params), client_id=cliente_id)
        total_logs = count_result[0]['total'] if count_result else 0

        # Query para obtener datos (SIN JOIN con cliente, ya que cliente está en BD centralizada)
        data_query = f"""
        SELECT 
            a.log_id,
            a.cliente_id,
            a.usuario_id,
            a.evento,
            a.nombre_usuario_intento,
            a.descripcion,
            a.exito,
            a.codigo_error,
            a.ip_address,
            a.user_agent,
            a.device_info,
            a.geolocation,
            a.metadata_json,
            a.fecha_evento,
            u.nombre_usuario,
            u.correo
        FROM dbo.auth_audit_log a
        LEFT JOIN dbo.usuario u ON a.usuario_id = u.usuario_id
        WHERE {where_clause}
        ORDER BY {order_field} {order_dir}
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, limit])
        # Si se filtra por cliente_id, usar la conexión de ese cliente
        logs_raw = execute_query(data_query, tuple(params), client_id=cliente_id)

        # Procesar logs
        logs = []
        for log_row in logs_raw:
            # Información del cliente (usar cache si está disponible, sino obtener desde ADMIN)
            cliente_info = None
            if log_row.get('cliente_id'):
                if cliente_info_cache and cliente_info_cache.cliente_id == log_row['cliente_id']:
                    cliente_info = cliente_info_cache
                else:
                    # Obtener desde BD centralizada (ADMIN)
                    from app.infrastructure.database.connection import DatabaseConnection
                    query_cliente = """
                    SELECT cliente_id, razon_social, subdominio, codigo_cliente, 
                           nombre_comercial, tipo_instalacion, estado_suscripcion
                    FROM dbo.cliente
                    WHERE cliente_id = ?
                    """
                    cliente_raw = execute_query(query_cliente, (log_row['cliente_id'],), connection_type=DatabaseConnection.ADMIN)
                    if cliente_raw:
                        cliente_row = cliente_raw[0]
                        cliente_info = ClienteInfo(
                            cliente_id=cliente_row['cliente_id'],
                            razon_social=cliente_row['razon_social'],
                            subdominio=cliente_row['subdominio'],
                            codigo_cliente=cliente_row.get('codigo_cliente'),
                            nombre_comercial=cliente_row.get('nombre_comercial'),
                            tipo_instalacion=cliente_row.get('tipo_instalacion', 'cloud'),
                            estado_suscripcion=cliente_row.get('estado_suscripcion', 'activo')
                        )

            # Información del usuario
            usuario_info = None
            if log_row.get('usuario_id'):
                usuario_info = UsuarioInfo(
                    usuario_id=log_row['usuario_id'],
                    nombre_usuario=log_row.get('nombre_usuario', ''),
                    correo=log_row.get('correo')
                )

            # Parsear metadata_json
            metadata = None
            if log_row.get('metadata_json'):
                try:
                    metadata = json.loads(log_row['metadata_json'])
                except:
                    pass

            log = AuthAuditLogRead(
                log_id=log_row['log_id'],
                cliente_id=log_row['cliente_id'],
                cliente=cliente_info,
                usuario_id=log_row.get('usuario_id'),
                usuario=usuario_info,
                evento=log_row['evento'],
                nombre_usuario_intento=log_row.get('nombre_usuario_intento'),
                descripcion=log_row.get('descripcion'),
                exito=bool(log_row['exito']),
                codigo_error=log_row.get('codigo_error'),
                ip_address=log_row.get('ip_address'),
                user_agent=log_row.get('user_agent'),
                device_info=log_row.get('device_info'),
                geolocation=log_row.get('geolocation'),
                metadata_json=metadata,
                fecha_evento=log_row['fecha_evento']
            )
            logs.append(log)

        total_paginas = math.ceil(total_logs / limit) if limit > 0 else 0

        return {
            "logs": [l.model_dump() for l in logs],
            "total_logs": total_logs,
            "pagina_actual": page,
            "total_paginas": total_paginas
        }

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_log_autenticacion(log_id: int) -> Optional[Dict]:
        """
        Obtiene detalle completo de un log de autenticación.
        """
        logger.info(f"Obteniendo log de autenticación ID {log_id}")

        query = """
        SELECT 
            a.*,
            c.razon_social as cliente_razon_social,
            c.subdominio as cliente_subdominio,
            c.codigo_cliente,
            c.nombre_comercial,
            c.tipo_instalacion,
            c.estado_suscripcion,
            u.nombre_usuario,
            u.correo
        FROM dbo.auth_audit_log a
        LEFT JOIN dbo.cliente c ON a.cliente_id = c.cliente_id
        LEFT JOIN dbo.usuario u ON a.usuario_id = u.usuario_id
        WHERE a.log_id = ?
        """
        # Primero obtener el cliente_id del log desde la BD centralizada (ADMIN)
        from app.infrastructure.database.connection import DatabaseConnection
        query_cliente = """
        SELECT cliente_id
        FROM dbo.auth_audit_log
        WHERE log_id = ?
        """
        cliente_info_raw = execute_query(query_cliente, (log_id,), connection_type=DatabaseConnection.ADMIN)
        
        if not cliente_info_raw:
            raise NotFoundError(
                detail=f"Log de autenticación con ID {log_id} no encontrado.",
                internal_code="LOG_NOT_FOUND"
            )
        
        log_cliente_id = cliente_info_raw[0]['cliente_id']
        
        # Obtener el log usando la conexión del cliente
        log_raw = execute_query(query, (log_id,), client_id=log_cliente_id)

        if not log_raw:
            return None

        log_row = log_raw[0]

        # Información del cliente
        cliente_info = None
        if log_row.get('cliente_id'):
            cliente_info = ClienteInfo(
                cliente_id=log_row['cliente_id'],
                razon_social=log_row.get('cliente_razon_social', ''),
                subdominio=log_row.get('cliente_subdominio', ''),
                codigo_cliente=log_row.get('codigo_cliente'),
                nombre_comercial=log_row.get('nombre_comercial'),
                tipo_instalacion=log_row.get('tipo_instalacion', 'cloud'),
                estado_suscripcion=log_row.get('estado_suscripcion', 'activo')
            )

        # Información del usuario
        usuario_info = None
        if log_row.get('usuario_id'):
            usuario_info = UsuarioInfo(
                usuario_id=log_row['usuario_id'],
                nombre_usuario=log_row.get('nombre_usuario', ''),
                correo=log_row.get('correo')
            )

        # Parsear metadata_json
        metadata = None
        if log_row.get('metadata_json'):
            try:
                metadata = json.loads(log_row['metadata_json'])
            except:
                pass

        log = AuthAuditLogRead(
            log_id=log_row['log_id'],
            cliente_id=log_row['cliente_id'],
            cliente=cliente_info,
            usuario_id=log_row.get('usuario_id'),
            usuario=usuario_info,
            evento=log_row['evento'],
            nombre_usuario_intento=log_row.get('nombre_usuario_intento'),
            descripcion=log_row.get('descripcion'),
            exito=bool(log_row['exito']),
            codigo_error=log_row.get('codigo_error'),
            ip_address=log_row.get('ip_address'),
            user_agent=log_row.get('user_agent'),
            device_info=log_row.get('device_info'),
            geolocation=log_row.get('geolocation'),
            metadata_json=metadata,
            fecha_evento=log_row['fecha_evento']
        )

        return log.model_dump()

    @staticmethod
    @BaseService.handle_service_errors
    async def get_logs_sincronizacion(
        cliente_origen_id: Optional[int] = None,
        cliente_destino_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        tipo_sincronizacion: Optional[str] = None,
        direccion: Optional[str] = None,
        operacion: Optional[str] = None,
        estado: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
        ordenar_por: str = "fecha_sincronizacion",
        orden: str = "desc"
    ) -> Dict:
        """
        Obtiene logs de sincronización con filtros avanzados.
        """
        logger.info(f"Obteniendo logs de sincronización - page: {page}")

        # Validar parámetros
        if page < 1:
            raise ValidationError(
                detail="El número de página debe ser mayor o igual a 1.",
                internal_code="INVALID_PAGE_NUMBER"
            )
        if limit < 1 or limit > 200:
            raise ValidationError(
                detail="El límite por página debe estar entre 1 y 200.",
                internal_code="INVALID_LIMIT"
            )
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError(
                detail="fecha_desde debe ser anterior a fecha_hasta.",
                internal_code="INVALID_DATE_RANGE"
            )

        # Validar clientes si se proporcionan
        if cliente_origen_id:
            cliente = await ClienteService.obtener_cliente_por_id(cliente_origen_id)
            if not cliente:
                raise NotFoundError(
                    detail=f"Cliente origen con ID {cliente_origen_id} no encontrado.",
                    internal_code="CLIENT_ORIGIN_NOT_FOUND"
                )

        if cliente_destino_id:
            cliente = await ClienteService.obtener_cliente_por_id(cliente_destino_id)
            if not cliente:
                raise NotFoundError(
                    detail=f"Cliente destino con ID {cliente_destino_id} no encontrado.",
                    internal_code="CLIENT_DEST_NOT_FOUND"
                )

        offset = (page - 1) * limit

        # Construir condiciones WHERE
        where_conditions = []
        params = []

        if cliente_origen_id:
            where_conditions.append("l.cliente_origen_id = ?")
            params.append(cliente_origen_id)

        if cliente_destino_id:
            where_conditions.append("l.cliente_destino_id = ?")
            params.append(cliente_destino_id)

        if usuario_id:
            where_conditions.append("l.usuario_id = ?")
            params.append(usuario_id)

        if tipo_sincronizacion:
            where_conditions.append("l.tipo_sincronizacion = ?")
            params.append(tipo_sincronizacion)

        if direccion:
            where_conditions.append("l.direccion = ?")
            params.append(direccion)

        if operacion:
            where_conditions.append("l.operacion = ?")
            params.append(operacion)

        if estado:
            where_conditions.append("l.estado = ?")
            params.append(estado)

        if fecha_desde:
            where_conditions.append("l.fecha_sincronizacion >= ?")
            params.append(fecha_desde)

        if fecha_hasta:
            where_conditions.append("l.fecha_sincronizacion <= ?")
            params.append(fecha_hasta)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Validar ordenar_por
        valid_order_fields = {
            "fecha_sincronizacion": "l.fecha_sincronizacion",
            "estado": "l.estado",
            "usuario_id": "l.usuario_id"
        }
        order_field = valid_order_fields.get(ordenar_por, "l.fecha_sincronizacion")
        order_dir = "DESC" if orden.lower() == "desc" else "ASC"

        # Query para contar total
        count_query = f"""
        SELECT COUNT(*) as total
        FROM dbo.log_sincronizacion_usuario l
        WHERE {where_clause}
        """
        # Determinar qué cliente usar para la conexión (priorizar origen, luego destino)
        target_client_id = cliente_origen_id or cliente_destino_id
        # Si se filtra por cliente, usar la conexión de ese cliente
        count_result = execute_query(count_query, tuple(params), client_id=target_client_id)
        total_logs = count_result[0]['total'] if count_result else 0

        # Query para obtener datos (SIN JOIN con cliente, ya que cliente está en BD centralizada)
        data_query = f"""
        SELECT 
            l.*,
            u.nombre_usuario,
            u.correo,
            ue.nombre_usuario as ejecutor_nombre_usuario,
            ue.correo as ejecutor_correo
        FROM dbo.log_sincronizacion_usuario l
        LEFT JOIN dbo.usuario u ON l.usuario_id = u.usuario_id
        LEFT JOIN dbo.usuario ue ON l.usuario_ejecutor_id = ue.usuario_id
        WHERE {where_clause}
        ORDER BY {order_field} {order_dir}
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, limit])
        # Determinar qué cliente usar para la conexión (priorizar origen, luego destino)
        target_client_id = cliente_origen_id or cliente_destino_id
        # Si se filtra por cliente, usar la conexión de ese cliente
        logs_raw = execute_query(data_query, tuple(params), client_id=target_client_id)
        
        # Obtener información de clientes desde BD centralizada (ADMIN) si es necesario
        clientes_cache = {}
        from app.infrastructure.database.connection import DatabaseConnection
        for log_row in logs_raw:
            if log_row.get('cliente_origen_id') and log_row['cliente_origen_id'] not in clientes_cache:
                query_cliente = """
                SELECT cliente_id, razon_social, subdominio, codigo_cliente, 
                       nombre_comercial, tipo_instalacion, estado_suscripcion
                FROM dbo.cliente
                WHERE cliente_id = ?
                """
                cliente_raw = execute_query(query_cliente, (log_row['cliente_origen_id'],), connection_type=DatabaseConnection.ADMIN)
                if cliente_raw:
                    cliente_row = cliente_raw[0]
                    clientes_cache[log_row['cliente_origen_id']] = ClienteInfo(
                        cliente_id=cliente_row['cliente_id'],
                        razon_social=cliente_row['razon_social'],
                        subdominio=cliente_row['subdominio'],
                        codigo_cliente=cliente_row.get('codigo_cliente'),
                        nombre_comercial=cliente_row.get('nombre_comercial'),
                        tipo_instalacion=cliente_row.get('tipo_instalacion', 'cloud'),
                        estado_suscripcion=cliente_row.get('estado_suscripcion', 'activo')
                    )
            if log_row.get('cliente_destino_id') and log_row['cliente_destino_id'] not in clientes_cache:
                query_cliente = """
                SELECT cliente_id, razon_social, subdominio, codigo_cliente, 
                       nombre_comercial, tipo_instalacion, estado_suscripcion
                FROM dbo.cliente
                WHERE cliente_id = ?
                """
                cliente_raw = execute_query(query_cliente, (log_row['cliente_destino_id'],), connection_type=DatabaseConnection.ADMIN)
                if cliente_raw:
                    cliente_row = cliente_raw[0]
                    clientes_cache[log_row['cliente_destino_id']] = ClienteInfo(
                        cliente_id=cliente_row['cliente_id'],
                        razon_social=cliente_row['razon_social'],
                        subdominio=cliente_row['subdominio'],
                        codigo_cliente=cliente_row.get('codigo_cliente'),
                        nombre_comercial=cliente_row.get('nombre_comercial'),
                        tipo_instalacion=cliente_row.get('tipo_instalacion', 'cloud'),
                        estado_suscripcion=cliente_row.get('estado_suscripcion', 'activo')
                    )

        # Procesar logs
        logs = []
        for log_row in logs_raw:
            # Cliente origen (usar cache)
            cliente_origen = clientes_cache.get(log_row.get('cliente_origen_id')) if log_row.get('cliente_origen_id') else None

            # Cliente destino (usar cache)
            cliente_destino = clientes_cache.get(log_row.get('cliente_destino_id')) if log_row.get('cliente_destino_id') else None

            # Usuario sincronizado
            usuario = None
            if log_row.get('usuario_id'):
                usuario = UsuarioInfo(
                    usuario_id=log_row['usuario_id'],
                    nombre_usuario=log_row.get('nombre_usuario', ''),
                    correo=log_row.get('correo')
                )

            # Usuario ejecutor
            usuario_ejecutor = None
            if log_row.get('usuario_ejecutor_id'):
                usuario_ejecutor = UsuarioInfo(
                    usuario_id=log_row['usuario_ejecutor_id'],
                    nombre_usuario=log_row.get('ejecutor_nombre_usuario', ''),
                    correo=log_row.get('ejecutor_correo')
                )

            # Parsear JSON fields
            campos_sincronizados = None
            if log_row.get('campos_sincronizados'):
                try:
                    campos_sincronizados = json.loads(log_row['campos_sincronizados'])
                except:
                    pass

            cambios_detectados = None
            if log_row.get('cambios_detectados'):
                try:
                    cambios_detectados = json.loads(log_row['cambios_detectados'])
                except:
                    pass

            log = LogSincronizacionRead(
                log_id=log_row['log_id'],
                cliente_origen_id=log_row.get('cliente_origen_id'),
                cliente_origen=cliente_origen,
                cliente_destino_id=log_row.get('cliente_destino_id'),
                cliente_destino=cliente_destino,
                usuario_id=log_row['usuario_id'],
                usuario=usuario,
                tipo_sincronizacion=log_row['tipo_sincronizacion'],
                direccion=log_row['direccion'],
                operacion=log_row['operacion'],
                estado=log_row['estado'],
                mensaje_error=log_row.get('mensaje_error'),
                campos_sincronizados=campos_sincronizados,
                cambios_detectados=cambios_detectados,
                hash_antes=log_row.get('hash_antes'),
                hash_despues=log_row.get('hash_despues'),
                fecha_sincronizacion=log_row['fecha_sincronizacion'],
                usuario_ejecutor_id=log_row.get('usuario_ejecutor_id'),
                usuario_ejecutor=usuario_ejecutor,
                duracion_ms=log_row.get('duracion_ms')
            )
            logs.append(log)

        total_paginas = math.ceil(total_logs / limit) if limit > 0 else 0

        return {
            "logs": [l.model_dump() for l in logs],
            "total_logs": total_logs,
            "pagina_actual": page,
            "total_paginas": total_paginas
        }

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_estadisticas(
        cliente_id: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict:
        """
        Obtiene estadísticas agregadas de auditoría.
        """
        logger.info(f"Obteniendo estadísticas de auditoría - cliente_id: {cliente_id}")

        # Validar fechas
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError(
                detail="fecha_desde debe ser anterior a fecha_hasta.",
                internal_code="INVALID_DATE_RANGE"
            )

        # Validar cliente_id si se proporciona
        if cliente_id:
            cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
            if not cliente:
                raise NotFoundError(
                    detail=f"Cliente con ID {cliente_id} no encontrado.",
                    internal_code="CLIENT_NOT_FOUND"
                )

        # Construir condiciones WHERE para autenticación
        where_auth = []
        params_auth = []
        if cliente_id:
            where_auth.append("a.cliente_id = ?")
            params_auth.append(cliente_id)
        if fecha_desde:
            where_auth.append("a.fecha_evento >= ?")
            params_auth.append(fecha_desde)
        if fecha_hasta:
            where_auth.append("a.fecha_evento <= ?")
            params_auth.append(fecha_hasta)
        where_auth_clause = " AND ".join(where_auth) if where_auth else "1=1"

        # Estadísticas de autenticación
        auth_stats_query = f"""
        SELECT 
            COUNT(*) as total_eventos,
            SUM(CASE WHEN evento IN ('login_success', 'sso_login_success') AND exito = 1 THEN 1 ELSE 0 END) as login_exitosos,
            SUM(CASE WHEN evento IN ('login_failed', 'sso_login_failed') AND exito = 0 THEN 1 ELSE 0 END) as login_fallidos,
            evento,
            COUNT(*) as eventos_por_tipo
        FROM dbo.auth_audit_log a
        WHERE {where_auth_clause}
        GROUP BY evento
        """
        # Si se filtra por cliente_id, usar la conexión de ese cliente
        auth_stats_raw = execute_query(auth_stats_query, tuple(params_auth), client_id=cliente_id)

        # Procesar estadísticas de autenticación
        total_eventos = 0
        login_exitosos = 0
        login_fallidos = 0
        eventos_por_tipo = {}
        
        if auth_stats_raw:
            for row in auth_stats_raw:
                total_eventos += row.get('total_eventos', 0)
                login_exitosos += row.get('login_exitosos', 0)
                login_fallidos += row.get('login_fallidos', 0)
                if row.get('evento'):
                    eventos_por_tipo[row['evento']] = row.get('eventos_por_tipo', 0)

        # Construir condiciones WHERE para sincronización
        where_sync = []
        params_sync = []
        if cliente_id:
            where_sync.append("(l.cliente_origen_id = ? OR l.cliente_destino_id = ?)")
            params_sync.extend([cliente_id, cliente_id])
        if fecha_desde:
            where_sync.append("l.fecha_sincronizacion >= ?")
            params_sync.append(fecha_desde)
        if fecha_hasta:
            where_sync.append("l.fecha_sincronizacion <= ?")
            params_sync.append(fecha_hasta)
        where_sync_clause = " AND ".join(where_sync) if where_sync else "1=1"

        # Estadísticas de sincronización
        sync_stats_query = f"""
        SELECT 
            COUNT(*) as total_sincronizaciones,
            SUM(CASE WHEN estado = 'exitoso' THEN 1 ELSE 0 END) as exitosas,
            SUM(CASE WHEN estado = 'fallido' THEN 1 ELSE 0 END) as fallidas,
            tipo_sincronizacion,
            COUNT(*) as por_tipo
        FROM dbo.log_sincronizacion_usuario l
        WHERE {where_sync_clause}
        GROUP BY tipo_sincronizacion
        """
        # Si se filtra por cliente_id, usar la conexión de ese cliente
        sync_stats_raw = execute_query(sync_stats_query, tuple(params_sync), client_id=cliente_id)

        # Procesar estadísticas de sincronización
        total_sincronizaciones = 0
        exitosas = 0
        fallidas = 0
        por_tipo = {}
        
        if sync_stats_raw:
            for row in sync_stats_raw:
                total_sincronizaciones += row.get('total_sincronizaciones', 0)
                exitosas += row.get('exitosas', 0)
                fallidas += row.get('fallidas', 0)
                if row.get('tipo_sincronizacion'):
                    por_tipo[row['tipo_sincronizacion']] = row.get('por_tipo', 0)

        # Top IPs
        top_ips_query = f"""
        SELECT TOP 10
            ip_address,
            COUNT(*) as total_eventos,
            SUM(CASE WHEN exito = 0 THEN 1 ELSE 0 END) as eventos_fallidos
        FROM dbo.auth_audit_log a
        WHERE {where_auth_clause} AND ip_address IS NOT NULL
        GROUP BY ip_address
        ORDER BY total_eventos DESC
        """
        # Si se filtra por cliente_id, usar la conexión de ese cliente
        top_ips_raw = execute_query(top_ips_query, tuple(params_auth), client_id=cliente_id)
        top_ips = [
            IPStats(
                ip_address=row['ip_address'],
                total_eventos=row['total_eventos'],
                eventos_fallidos=row['eventos_fallidos']
            ) for row in top_ips_raw
        ] if top_ips_raw else []

        # Top usuarios
        top_usuarios_query = f"""
        SELECT TOP 10
            u.usuario_id,
            u.nombre_usuario,
            COUNT(*) as total_eventos
        FROM dbo.auth_audit_log a
        INNER JOIN dbo.usuario u ON a.usuario_id = u.usuario_id
        WHERE {where_auth_clause} AND a.usuario_id IS NOT NULL
        GROUP BY u.usuario_id, u.nombre_usuario
        ORDER BY total_eventos DESC
        """
        # Si se filtra por cliente_id, usar la conexión de ese cliente
        top_usuarios_raw = execute_query(top_usuarios_query, tuple(params_auth), client_id=cliente_id)
        top_usuarios = [
            UsuarioStats(
                usuario_id=row['usuario_id'],
                nombre_usuario=row['nombre_usuario'],
                total_eventos=row['total_eventos']
            ) for row in top_usuarios_raw
        ] if top_usuarios_raw else []

        # Construir respuesta
        periodo = PeriodoInfo(
            fecha_desde=fecha_desde or datetime.min,
            fecha_hasta=fecha_hasta or datetime.now()
        )

        autenticacion = AutenticacionStats(
            total_eventos=total_eventos,
            login_exitosos=login_exitosos,
            login_fallidos=login_fallidos,
            eventos_por_tipo=eventos_por_tipo
        )

        sincronizacion = SincronizacionStats(
            total_sincronizaciones=total_sincronizaciones,
            exitosas=exitosas,
            fallidas=fallidas,
            por_tipo=por_tipo
        )

        estadisticas = AuditoriaEstadisticasResponse(
            periodo=periodo,
            autenticacion=autenticacion,
            sincronizacion=sincronizacion,
            top_ips=top_ips if top_ips else None,
            top_usuarios=top_usuarios if top_usuarios else None
        )

        return estadisticas.model_dump()

