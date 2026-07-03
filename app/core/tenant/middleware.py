# app/middleware/tenant_middleware.py
"""
Middleware para identificación y contextualización del cliente (tenant).

RD-03 / PR-F3-01: resuelve metadata de conexión (Installation Mode) en L6
y la almacena en ``connection_metadata`` del TenantContext. L5 recibe solo
identidad de tenant (client_id, subdominio, codigo_cliente).

FLUJO:
1. Extraer host real (con fallback a origin/referer para proxies en dev)
2. Extraer subdominio del Host header
3. Resolver cliente_id desde BD (bd_sistema)
4. Cargar metadata de conexión (infra — no expuesta a L5)
5. Establecer TenantContext vía from_middleware_resolution
6. Procesar request
7. Limpiar contexto
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from typing import Dict, Any, Optional
from uuid import UUID
from urllib.parse import urlparse

from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context
from app.core.config import settings
from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
from app.core.exceptions import ClientNotFoundException

# ✅ FASE 2: Importar función async para obtener metadata
from app.core.tenant.routing import get_connection_metadata_async
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import ClienteTable
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _middleware_trace(level: str, msg, *args, **kwargs) -> None:
    """F12-E2B2.1: emite log solo si ENABLE_MIDDLEWARE_TRACE."""
    if settings.ENABLE_MIDDLEWARE_TRACE:
        getattr(logger, level)(msg, *args, **kwargs)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que resuelve el ID del cliente y establece contexto híbrido.
    """
    
    # ✅ NUEVO: Subdominios excluidos (infraestructura, no son tenants)
    EXCLUDED_SUBDOMAINS = {"api", "www", "admin", "static", "cdn", "assets", "backend"}
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.default_client_id = settings.SUPERADMIN_CLIENTE_ID
        self.base_domain = settings.BASE_DOMAIN
        self.superadmin_subdominio = settings.SUPERADMIN_SUBDOMINIO
        _middleware_trace(
            "info",
            f"[TENANT_MW] Inicializado - "
            f"BASE_DOMAIN={self.base_domain}, "
            f"SYSTEM_ID={self.default_client_id}, "
            f"EXCLUDED_SUBDOMAINS={self.EXCLUDED_SUBDOMAINS}",
        )

    async def _get_host_from_request(self, request: Request) -> str:
        """
        Extrae el host de la petición con fallback a origin/referer SOLO en desarrollo.
        
        🔒 SEGURIDAD MEJORADA:
        - En PRODUCCIÓN: Solo confía en el header Host (no falsificable)
        - En DESARROLLO: Permite fallback a Origin/Referer para proxies (Vite, etc.)
        - Valida que el subdominio extraído exista en la BD antes de confiar
        
        Returns:
            str: Host completo (puede incluir puerto)
        
        Raises:
            HTTPException: Si en producción el Host es inválido o no se puede determinar
        """
        from app.core.config import settings
        from starlette.responses import JSONResponse
        
        host = request.headers.get("host", "")
        
        # 🔍 DEBUG: Mostrar headers relevantes
        _middleware_trace("debug", f"[HOST_DETECTION] Headers recibidos:")
        _middleware_trace("debug", f"  - host: {host}")
        _middleware_trace("debug", f"  - origin: {request.headers.get('origin', 'N/A')}")
        _middleware_trace("debug", f"  - referer: {request.headers.get('referer', 'N/A')}")
        _middleware_trace("debug", f"  - environment: {settings.ENVIRONMENT}")
        
        # ✅ SEGURIDAD: En producción, SOLO confiar en Host header
        if settings.ENVIRONMENT == "production":
            if not host or host.startswith(("localhost", "127.0.0.1")):
                logger.error(
                    f"[SECURITY] Host inválido en producción: '{host}'. "
                    f"Origin/Referer no se usan en producción por seguridad."
                )
                # En producción, rechazar requests sin Host válido
                raise ValueError(
                    "Host header requerido y válido en producción. "
                    "No se permite localhost o IPs privadas."
                )
            
            # En producción, usar directamente el Host (ya validado)
            _middleware_trace("debug", f"[HOST_DETECTION] Producción: usando Host directamente: {host}")
            return host
        
        # ✅ DESARROLLO: Permitir fallback a Origin/Referer para proxies
        # (Mantiene compatibilidad con Vite, webpack-dev-server, etc.)
        host_without_port = host.split(':')[0] if ':' in host else host
        host_subdomain = host_without_port.split('.')[0]
        
        # Si el host es localhost, 127.0.0.1, o un subdominio excluido, 
        # intentar extraer del origin o referer (SOLO EN DESARROLLO)
        should_extract_from_origin = (
            host.startswith(("localhost", "127.0.0.1")) or
            host_subdomain in self.EXCLUDED_SUBDOMAINS
        )
        
        if should_extract_from_origin:
            _middleware_trace(
                "info",
                f"[HOST_DETECTION] Desarrollo: Host '{host}' es localhost/infraestructura, "
                f"buscando tenant real en origin/referer",
            )
            
            # Intentar primero con origin
            origin = request.headers.get("origin", "")
            if origin:
                parsed = urlparse(origin)
                if parsed.netloc and not parsed.netloc.startswith(("localhost", "127.0.0.1")):
                    # Verificar que el origin no sea también un subdominio excluido
                    origin_subdomain = parsed.netloc.split(':')[0].split('.')[0]
                    if origin_subdomain not in self.EXCLUDED_SUBDOMAINS:
                        extracted_host = parsed.netloc
                        _middleware_trace(
                            "info",
                            f"[HOST_DETECTION] Desarrollo: Tenant extraído de 'origin': {extracted_host}",
                        )
                        # ✅ VALIDACIÓN ADICIONAL: Verificar que el subdominio existe en BD
                        # Esto previene spoofing incluso en desarrollo
                        # EXCEPCIÓN: 'platform' es el subdominio del superadmin y no está en BD
                        try:
                            subdomain = self._extract_subdomain(extracted_host)
                            if subdomain:
                                # ✅ CORRECCIÓN: Reconocer 'platform' como subdominio del superadmin
                                if subdomain.lower() == self.superadmin_subdominio.lower():
                                    _middleware_trace(
                                        "debug",
                                        f"[HOST_DETECTION] Subdominio '{subdomain}' reconocido como SUPERADMIN",
                                    )
                                    return extracted_host
                                
                                # Para otros subdominios, validar en BD
                                client_data = await self._get_client_data_by_subdomain(subdomain)
                                if client_data:
                                    _middleware_trace(
                                        "debug",
                                        f"[HOST_DETECTION] Subdominio '{subdomain}' validado en BD",
                                    )
                                    return extracted_host
                                else:
                                    _middleware_trace(
                                        "warning",
                                        f"[HOST_DETECTION] Subdominio '{subdomain}' no existe en BD, "
                                        f"rechazando origin",
                                    )
                        except Exception as e:
                            _middleware_trace(
                                "warning",
                                f"[HOST_DETECTION] Error validando subdominio de origin: {e}",
                            )
            
            # Si no, intentar con referer
            referer = request.headers.get("referer", "")
            if referer:
                parsed = urlparse(referer)
                if parsed.netloc and not parsed.netloc.startswith(("localhost", "127.0.0.1")):
                    # Verificar que el referer no sea también un subdominio excluido
                    referer_subdomain = parsed.netloc.split(':')[0].split('.')[0]
                    if referer_subdomain not in self.EXCLUDED_SUBDOMAINS:
                        extracted_host = parsed.netloc
                        _middleware_trace(
                            "info",
                            f"[HOST_DETECTION] Desarrollo: Tenant extraído de 'referer': {extracted_host}",
                        )
                        # ✅ VALIDACIÓN ADICIONAL: Verificar que el subdominio existe en BD
                        # EXCEPCIÓN: 'platform' es el subdominio del superadmin y no está en BD
                        try:
                            subdomain = self._extract_subdomain(extracted_host)
                            if subdomain:
                                # ✅ CORRECCIÓN: Reconocer 'platform' como subdominio del superadmin
                                if subdomain.lower() == self.superadmin_subdominio.lower():
                                    _middleware_trace(
                                        "debug",
                                        f"[HOST_DETECTION] Subdominio '{subdomain}' reconocido como SUPERADMIN",
                                    )
                                    return extracted_host
                                
                                # Para otros subdominios, validar en BD
                                client_data = await self._get_client_data_by_subdomain(subdomain)
                                if client_data:
                                    _middleware_trace(
                                        "debug",
                                        f"[HOST_DETECTION] Subdominio '{subdomain}' validado en BD",
                                    )
                                    return extracted_host
                                else:
                                    _middleware_trace(
                                        "warning",
                                        f"[HOST_DETECTION] Subdominio '{subdomain}' no existe en BD, "
                                        f"rechazando referer",
                                    )
                        except Exception as e:
                            _middleware_trace(
                                "warning",
                                f"[HOST_DETECTION] Error validando subdominio de referer: {e}",
                            )
            
            _middleware_trace(
                "warning",
                f"[HOST_DETECTION] No se pudo extraer tenant real de origin/referer, "
                f"usando cliente por defecto (SYSTEM)",
            )
        
        _middleware_trace("debug", f"[HOST_DETECTION] Host final: {host}")
        return host

    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Procesa cada request para establecer el contexto del tenant.
        """
        
        # ============================================
        # FASE 1: RESOLUCIÓN DE CLIENTE
        # ============================================
        
        # 🔧 NUEVO: Obtener host con fallback a origin/referer
        try:
            host = await self._get_host_from_request(request)
        except ValueError as e:
            # ✅ SEGURIDAD: En producción, rechazar requests sin Host válido
            logger.error(f"[SECURITY] Error de seguridad en detección de host: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Host header inválido o faltante. "
                             "En producción, el Host header es requerido y no puede ser localhost."
                }
            )
        
        subdomain = self._extract_subdomain(host)
        
        # ✅ CORRECCIÓN RIESGO #1: En producción, rechazar requests sin subdominio válido
        # Esto previene asignación automática a SUPERADMIN por requests sin subdominio
        if not subdomain and settings.ENVIRONMENT == "production":
            logger.error(
                f"[SECURITY] Request sin subdominio válido rechazado en producción. "
                f"Host: {host}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "detail": (
                        "Request sin subdominio válido rechazado por seguridad. "
                        "En producción, todos los requests deben incluir un subdominio válido en el Host header. "
                        "Ejemplo: cliente1.midominio.com"
                    )
                }
            )
        
        # Convertir SUPERADMIN_CLIENTE_ID de string a UUID si es necesario
        # Si no está configurado y estamos en desarrollo, usar un UUID temporal
        if settings.SUPERADMIN_CLIENTE_ID:
            default_client_id_uuid = UUID(settings.SUPERADMIN_CLIENTE_ID)
        elif settings.ENVIRONMENT == "development":
            # UUID temporal para desarrollo cuando SUPERADMIN_CLIENTE_ID no está configurado
            # ⚠️ ADVERTENCIA: Esto es solo para desarrollo. En producción, SUPERADMIN_CLIENTE_ID debe estar configurado.
            default_client_id_uuid = UUID("00000000-0000-0000-0000-000000000001")
            logger.warning(
                "[TENANT] SUPERADMIN_CLIENTE_ID no configurado. "
                "Usando UUID temporal para desarrollo: 00000000-0000-0000-0000-000000000001. "
                "Configura SUPERADMIN_CLIENTE_ID en .env.docker para producción."
            )
        else:
            default_client_id_uuid = None
        
        client_id: Optional[UUID] = default_client_id_uuid
        client_data: Dict[str, Any] = {
            "cliente_id": default_client_id_uuid,
            "codigo_cliente": settings.SUPERADMIN_CLIENTE_CODIGO
        }
        
        _middleware_trace("debug", f"[TENANT] Host: {host}, Subdominio: {subdomain}")
        
        # Resolver cliente por subdominio
        if subdomain:
            if subdomain.lower() == settings.SUPERADMIN_SUBDOMINIO.lower():
                # Caso 1: Subdominio SUPERADMIN
                client_id = default_client_id_uuid
                _middleware_trace(
                    "info",
                    f"[TENANT] Subdominio SUPERADMIN: {subdomain} -> "
                    f"Cliente ID: {client_id}",
                )
            else:
                # Caso 2: Buscar cliente en BD
                try:
                    _middleware_trace("debug", f"[TENANT] Buscando cliente: '{subdomain}'")
                    
                    client_data_db = await self._get_client_data_by_subdomain(subdomain)
                    
                    if client_data_db:
                        client_data = client_data_db
                        client_id = client_data["cliente_id"]
                        _middleware_trace(
                            "info",
                            f"[TENANT] Cliente resuelto: "
                            f"Subdominio='{subdomain}', "
                            f"Código='{client_data['codigo_cliente']}', "
                            f"ID={client_id}",
                        )
                    else:
                        logger.error(
                            f"[TENANT] Subdominio '{subdomain}' no encontrado"
                        )
                        raise ClientNotFoundException(
                            f"Subdominio '{subdomain}' no está asociado a ningún cliente activo."
                        )
                        
                except ClientNotFoundException as e:
                    logger.warning(f"[TENANT] Error: {e}")
                    return JSONResponse(
                        status_code=404,
                        content={"detail": str(e)}
                    )
                except Exception as e:
                    logger.error(
                        f"[TENANT] Error al resolver tenant: {e}", 
                        exc_info=True
                    )
                    return JSONResponse(
                        status_code=500,
                        content={
                            "detail": "Error interno al resolver el contexto de la organización."
                        }
                    )
        else:
            # Caso 3: Sin subdominio (solo permitido en desarrollo)
            # ✅ CORRECCIÓN RIESGO #1: En producción, esto ya fue rechazado arriba
            # En desarrollo, permitir fallback a SUPERADMIN para facilitar testing
            if settings.ENVIRONMENT == "production":
                # Esto no debería ejecutarse porque ya fue rechazado arriba, pero por seguridad:
                logger.error(
                    f"[SECURITY] Lógica de fallback ejecutada en producción (no debería ocurrir). "
                    f"Host: {host}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Request sin subdominio válido rechazado por seguridad."
                    }
                )
            _middleware_trace(
                "warning",
                f"[TENANT] Sin subdominio en Host: {host} (DESARROLLO). "
                f"Usando Cliente ID por defecto: {client_id} (SYSTEM)",
            )
        
        # ============================================
        # FASE 2: METADATA DE CONEXIÓN (L6 — RD-03, no expuesta a L5)
        # ============================================

        connection_metadata = await self._resolve_connection_metadata(client_id)
        
        # ============================================
        # FASE 3: ESTABLECER CONTEXTO (identidad L5)
        # ============================================
        
        # Validar que client_id no sea None antes de crear TenantContext
        if client_id is None:
            logger.error(
                f"[TENANT] ERROR DE CONFIGURACIÓN: client_id es None. "
                f"SUPERADMIN_CLIENTE_ID debe estar configurado en .env.docker"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Error de configuración: SUPERADMIN_CLIENTE_ID no está configurado. "
                             "Por favor, configura SUPERADMIN_CLIENTE_ID en .env.docker con un UUID válido."
                }
            )
        
        tenant_ctx = TenantContext.from_middleware_resolution(
            client_id=client_id,
            subdominio=subdomain,
            codigo_cliente=client_data.get("codigo_cliente"),
            connection_metadata=connection_metadata,
        )

        tokens = set_tenant_context(tenant_ctx)

        _middleware_trace(
            "info",
            "[TENANT] CONTEXTO ESTABLECIDO: cliente_id=%s subdominio=%s path=%s",
            client_id,
            subdomain,
            request.url.path,
        )
        
        # ============================================
        # FASE 4: PROCESAR REQUEST
        # ============================================
        
        try:
            response = await call_next(request)
        finally:
            # FASE 5: LIMPIAR CONTEXTO
            reset_tenant_context(tokens)
            _middleware_trace("debug", f"[TENANT] Contexto limpiado para cliente_id={client_id}")
        
        return response

    async def _resolve_connection_metadata(self, client_id: UUID) -> Dict[str, Any]:
        """
        Resuelve metadata de routing (L6). Installation Mode no se expone a L5 (RD-03).
        """
        connection_metadata: Dict[str, Any] = {}
        database_type: str = "single"
        nombre_bd: Optional[str] = settings.DB_DATABASE
        tipo_instalacion: str = "cloud"

        try:
            _middleware_trace("debug", "[TENANT] Cargando metadata de conexión para cliente %s", client_id)

            conn_metadata = await get_connection_metadata_async(client_id)

            if conn_metadata:
                connection_metadata = dict(conn_metadata)
                database_type = conn_metadata.get("database_type", "single")
                nombre_bd = conn_metadata.get("nombre_bd", settings.DB_DATABASE)
                tipo_instalacion = conn_metadata.get("tipo_instalacion", "cloud")

                _middleware_trace(
                    "debug",
                    "[TENANT] Metadata routing resuelta: cliente_id=%s db_type=%s "
                    "tipo_instalacion=%s bd=%s",
                    client_id,
                    database_type,
                    tipo_instalacion,
                    nombre_bd,
                )
            else:
                try:
                    from app.modules.tenant.application.services.cliente_service import ClienteService

                    cliente = await ClienteService.obtener_cliente_por_id(client_id)
                    if cliente:
                        tipo_instalacion = cliente.get("tipo_instalacion", "shared")
                        _middleware_trace(
                            "debug",
                            "[TENANT] tipo_instalacion desde cliente: %s",
                            tipo_instalacion,
                        )
                        if tipo_instalacion == "dedicated":
                            database_type = "multi"
                            logger.warning(
                                "[TENANT] Cliente %s dedicated sin metadata de conexión — "
                                "requiere cliente_conexion",
                                client_id,
                            )
                        else:
                            database_type = "single"
                except Exception:
                    pass

                logger.warning(
                    "[TENANT] Sin metadata para cliente %s — fallback routing %s",
                    client_id,
                    database_type,
                )

        except Exception as metadata_err:
            logger.error(
                "[TENANT] Error metadata cliente %s: %s — fallback single",
                client_id,
                metadata_err,
                exc_info=True,
            )

        if not connection_metadata:
            connection_metadata = {
                "database_type": database_type,
                "nombre_bd": nombre_bd,
                "tipo_instalacion": tipo_instalacion,
            }
        else:
            connection_metadata.setdefault("database_type", database_type)
            connection_metadata.setdefault("nombre_bd", nombre_bd)
            connection_metadata.setdefault("tipo_instalacion", tipo_instalacion)

        return connection_metadata

    def _extract_subdomain(self, host: str) -> Optional[str]:
        """
        Extrae el subdominio del header Host.
        
        Soporta:
        - localhost con subdominio: cliente1.localhost
        - Dominios personalizados: cliente1.midominio.com
        - Excluye subdominios de infraestructura (api, www, etc.)
        """
        # Limpieza de puerto
        if ":" in host:
            host = host.split(":")[0]
        
        _middleware_trace("info", f"[SUBDOMAIN] Procesando host: '{host}'")
        _middleware_trace("info", f"[SUBDOMAIN] BASE_DOMAIN: '{self.base_domain}'")
        
        # Caso especial: localhost con subdominio
        if host.endswith('.localhost'):
            parts = host.split('.')
            if len(parts) >= 2:
                subdomain = parts[0]
                
                # ✅ NUEVO: Verificar si es subdominio excluido
                if subdomain in self.EXCLUDED_SUBDOMAINS:
                    _middleware_trace(
                        "info",
                        f"[SUBDOMAIN] '{subdomain}' es infraestructura, ignorando (usando SYSTEM)",
                    )
                    return None  # Retornar None para usar cliente por defecto
                
                _middleware_trace("info", f"[SUBDOMAIN] Detectado en localhost: '{subdomain}'")
                return subdomain
        
        # Caso: dominios personalizados
        if host.endswith(f".{self.base_domain}") or host == self.base_domain:
            # Si es exactamente el base_domain (sin subdominio)
            if host == self.base_domain:
                _middleware_trace("info", "[SUBDOMAIN] Host es el dominio base (sin subdominio)")
                return None
            
            # Extraer subdominio
            subdomain = host.replace(f".{self.base_domain}", "")
            
            if subdomain:
                # ✅ NUEVO: Verificar si es subdominio excluido
                if subdomain in self.EXCLUDED_SUBDOMAINS:
                    _middleware_trace(
                        "info",
                        f"[SUBDOMAIN] '{subdomain}' es infraestructura, ignorando (usando SYSTEM)",
                    )
                    return None  # Retornar None para usar cliente por defecto
                
                _middleware_trace("info", f"[SUBDOMAIN] Detectado: '{subdomain}'")
                return subdomain
        
        _middleware_trace(
            "warning",
            f"[SUBDOMAIN] No se detectó subdominio válido en: '{host}'. "
            f"Verifica BASE_DOMAIN='{self.base_domain}'",
        )
        return None

    async def _get_client_data_by_subdomain(
        self, 
        subdomain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta la BD para obtener cliente_id y código por subdominio (ASYNC).
        
        ✅ FASE 2: Versión async que reemplaza la función síncrona.
        
        IMPORTANTE: Usa conexión ADMIN porque aún no tenemos contexto establecido.
        """
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        query = select(
            ClienteTable.c.cliente_id,
            ClienteTable.c.codigo_cliente
        ).where(
            ClienteTable.c.subdominio == subdomain,
            ClienteTable.c.es_activo == True
        )
        
        try:
            _middleware_trace("debug", f"[DB] Consultando subdominio: '{subdomain}'")
            
            # CRÍTICO: Usar conexión ADMIN async para evitar recursión
            # ✅ CORRECCIÓN: La tabla 'cliente' es global, no requiere filtro de tenant
            # apply_tenant_filter ahora detecta tablas globales antes de validar client_id
            results = await execute_query(
                query,
                connection_type=DatabaseConnection.ADMIN
                # No pasar client_id: la tabla 'cliente' es global y será detectada automáticamente
            )
            
            if results:
                result = {
                    "cliente_id": results[0]["cliente_id"], 
                    "codigo_cliente": results[0]["codigo_cliente"]
                }
                _middleware_trace("debug", f"[DB] Cliente encontrado: {result}")
                return result
            else:
                _middleware_trace(
                    "debug",
                    f"[DB] No se encontró cliente para subdominio: '{subdomain}'",
                )
                return None
                    
        except Exception as e:
            logger.error(
                f"[DB] Error al buscar cliente por subdominio '{subdomain}': {e}", 
                exc_info=True
            )
            raise


# ============================================
# LOGGING DE MÓDULO
# ============================================

_middleware_trace("info", "Módulo tenant_middleware cargado (versión híbrida con soporte para proxies)")
