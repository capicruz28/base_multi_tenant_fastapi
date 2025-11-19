# app/middleware/tenant_middleware.py
"""
Middleware para identificación y contextualización del cliente (tenant)
con soporte para arquitectura HÍBRIDA (Single-DB + Multi-DB).

MEJORAS EN ESTA VERSIÓN:
- Carga metadata de conexión desde cliente_modulo_conexion
- Determina database_type (single/multi) automáticamente
- Establece contexto enriquecido con información de BD
- Mantiene compatibilidad con código existente
- 🔧 FIX: Soporte para proxies de desarrollo (extrae host de origin/referer)

FLUJO:
1. Extraer host real (con fallback a origin/referer para proxies)
2. Extraer subdominio del Host header
3. Resolver cliente_id desde BD (bd_sistema)
4. Cargar metadata de conexión para el cliente
5. Determinar database_type (single/multi)
6. Establecer TenantContext enriquecido
7. Procesar request
8. Limpiar contexto
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from app.core.tenant_context import TenantContext, set_tenant_context, reset_tenant_context
from app.core.config import settings
from app.db.connection import get_db_connection, DatabaseConnection
from app.core.exceptions import ClientNotFoundException

# NUEVO: Importar función para obtener metadata
from app.core.multi_db import get_connection_metadata

logger = logging.getLogger(__name__)


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
        logger.info(
            f"[TENANT_MW] Inicializado - "
            f"BASE_DOMAIN={self.base_domain}, "
            f"SYSTEM_ID={self.default_client_id}, "
            f"EXCLUDED_SUBDOMAINS={self.EXCLUDED_SUBDOMAINS}"
        )

    def _get_host_from_request(self, request: Request) -> str:
        """
        Extrae el host de la petición con fallback a origin/referer.
        Esto es necesario para proxies de desarrollo (Vite, etc.) que 
        reescriben el header Host pero preservan origin/referer.
        
        ✅ CORRECCIÓN: También detecta subdominios de infraestructura (backend, api)
        y usa origin/referer para obtener el tenant real.
        
        Returns:
            str: Host completo (puede incluir puerto)
        """
        host = request.headers.get("host", "")
        
        # 🔍 DEBUG: Mostrar headers relevantes
        logger.debug(f"[HOST_DETECTION] Headers recibidos:")
        logger.debug(f"  - host: {host}")
        logger.debug(f"  - origin: {request.headers.get('origin', 'N/A')}")
        logger.debug(f"  - referer: {request.headers.get('referer', 'N/A')}")
        
        # ✅ CORRECCIÓN: Extraer subdominio del host para verificar si es excluido
        host_without_port = host.split(':')[0] if ':' in host else host
        host_subdomain = host_without_port.split('.')[0]
        
        # Si el host es localhost, 127.0.0.1, o un subdominio excluido, 
        # intentar extraer del origin o referer
        should_extract_from_origin = (
            host.startswith(("localhost", "127.0.0.1")) or
            host_subdomain in self.EXCLUDED_SUBDOMAINS
        )
        
        if should_extract_from_origin:
            logger.info(
                f"[HOST_DETECTION] Host '{host}' es localhost/infraestructura, "
                f"buscando tenant real en origin/referer"
            )
            
            # Intentar primero con origin
            origin = request.headers.get("origin", "")
            if origin:
                parsed = urlparse(origin)
                if parsed.netloc and not parsed.netloc.startswith(("localhost", "127.0.0.1")):
                    # Verificar que el origin no sea también un subdominio excluido
                    origin_subdomain = parsed.netloc.split(':')[0].split('.')[0]
                    if origin_subdomain not in self.EXCLUDED_SUBDOMAINS:
                        host = parsed.netloc
                        logger.info(f"[HOST_DETECTION] Tenant extraído de 'origin': {host}")
                        return host
            
            # Si no, intentar con referer
            referer = request.headers.get("referer", "")
            if referer:
                parsed = urlparse(referer)
                if parsed.netloc and not parsed.netloc.startswith(("localhost", "127.0.0.1")):
                    # Verificar que el referer no sea también un subdominio excluido
                    referer_subdomain = parsed.netloc.split(':')[0].split('.')[0]
                    if referer_subdomain not in self.EXCLUDED_SUBDOMAINS:
                        host = parsed.netloc
                        logger.info(f"[HOST_DETECTION] Tenant extraído de 'referer': {host}")
                        return host
            
            logger.warning(
                f"[HOST_DETECTION] No se pudo extraer tenant real de origin/referer, "
                f"usando cliente por defecto (SYSTEM)"
            )
        
        logger.debug(f"[HOST_DETECTION] Host final: {host}")
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
        host = self._get_host_from_request(request)
        subdomain = self._extract_subdomain(host)
        
        client_id: Optional[int] = self.default_client_id
        client_data: Dict[str, Any] = {
            "cliente_id": settings.SUPERADMIN_CLIENTE_ID,
            "codigo_cliente": settings.SUPERADMIN_CLIENTE_CODIGO
        }
        
        logger.debug(f"[TENANT] Host: {host}, Subdominio: {subdomain}")
        
        # Resolver cliente por subdominio
        if subdomain:
            if subdomain.lower() == settings.SUPERADMIN_SUBDOMINIO.lower():
                # Caso 1: Subdominio SUPERADMIN
                client_id = settings.SUPERADMIN_CLIENTE_ID
                logger.info(
                    f"[TENANT] Subdominio SUPERADMIN: {subdomain} → "
                    f"Cliente ID: {client_id}"
                )
            else:
                # Caso 2: Buscar cliente en BD
                try:
                    logger.debug(f"[TENANT] Buscando cliente: '{subdomain}'")
                    
                    client_data_db = self._get_client_data_by_subdomain(subdomain)
                    
                    if client_data_db:
                        client_data = client_data_db
                        client_id = client_data["cliente_id"]
                        logger.info(
                            f"[TENANT] Cliente resuelto: "
                            f"Subdominio='{subdomain}', "
                            f"Código='{client_data['codigo_cliente']}', "
                            f"ID={client_id}"
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
            # Caso 3: Sin subdominio
            logger.warning(
                f"[TENANT] Sin subdominio en Host: {host}. "
                f"Usando Cliente ID por defecto: {client_id} (SYSTEM)"
            )
        
        # ============================================
        # FASE 2: CARGA DE METADATA DE CONEXIÓN (NUEVO)
        # ============================================
        
        connection_metadata: Dict[str, Any] = {}
        database_type: str = "single"
        nombre_bd: Optional[str] = settings.DB_DATABASE
        servidor: Optional[str] = None
        puerto: Optional[int] = None
        tipo_instalacion: str = "cloud"
        
        try:
            # CRÍTICO: Cargar metadata de conexión
            logger.debug(f"[TENANT] Cargando metadata de conexión para cliente {client_id}")
            
            conn_metadata = get_connection_metadata(client_id)
            
            if conn_metadata:
                connection_metadata = conn_metadata
                database_type = conn_metadata.get("database_type", "single")
                nombre_bd = conn_metadata.get("nombre_bd", settings.DB_DATABASE)
                servidor = conn_metadata.get("servidor")
                puerto = conn_metadata.get("puerto")
                tipo_instalacion = conn_metadata.get("tipo_instalacion", "cloud")
                
                logger.info(
                    f"[TENANT] Metadata cargada: "
                    f"db_type={database_type}, "
                    f"bd={nombre_bd}, "
                    f"servidor={servidor or 'N/A'}"
                )
            else:
                logger.warning(
                    f"[TENANT] No se pudo cargar metadata para cliente {client_id}. "
                    f"Usando Single-DB por defecto."
                )
                
        except Exception as metadata_err:
            logger.error(
                f"[TENANT] Error al cargar metadata para cliente {client_id}: {metadata_err}. "
                f"Usando Single-DB como fallback.",
                exc_info=True
            )
            # Valores por defecto ya están establecidos arriba
        
        # ============================================
        # FASE 3: ESTABLECER CONTEXTO ENRIQUECIDO
        # ============================================
        
        tenant_ctx = TenantContext(
            client_id=client_id,
            subdominio=subdomain,
            codigo_cliente=client_data.get('codigo_cliente'),
            # NUEVOS CAMPOS HÍBRIDOS:
            database_type=database_type,
            nombre_bd=nombre_bd,
            connection_metadata=connection_metadata,
            servidor=servidor,
            puerto=puerto,
            tipo_instalacion=tipo_instalacion
        )
        
        # Establecer contexto
        tokens = set_tenant_context(tenant_ctx)
        
        # Logging de verificación
        logger.info(
            f"[TENANT] CONTEXTO ESTABLECIDO: "
            f"cliente_id={client_id}, "
            f"db_type={database_type}, "
            f"bd={nombre_bd}, "
            f"path={request.url.path}"
        )
        
        # ============================================
        # FASE 4: PROCESAR REQUEST
        # ============================================
        
        try:
            response = await call_next(request)
        finally:
            # FASE 5: LIMPIAR CONTEXTO
            reset_tenant_context(tokens)
            logger.debug(f"[TENANT] Contexto limpiado para cliente_id={client_id}")
        
        return response

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
        
        logger.info(f"[SUBDOMAIN] Procesando host: '{host}'")
        logger.info(f"[SUBDOMAIN] BASE_DOMAIN: '{self.base_domain}'")
        
        # Caso especial: localhost con subdominio
        if host.endswith('.localhost'):
            parts = host.split('.')
            if len(parts) >= 2:
                subdomain = parts[0]
                
                # ✅ NUEVO: Verificar si es subdominio excluido
                if subdomain in self.EXCLUDED_SUBDOMAINS:
                    logger.info(
                        f"[SUBDOMAIN] '{subdomain}' es infraestructura, ignorando (usando SYSTEM)"
                    )
                    return None  # Retornar None para usar cliente por defecto
                
                logger.info(f"[SUBDOMAIN] Detectado en localhost: '{subdomain}'")
                return subdomain
        
        # Caso: dominios personalizados
        if host.endswith(f".{self.base_domain}") or host == self.base_domain:
            # Si es exactamente el base_domain (sin subdominio)
            if host == self.base_domain:
                logger.info("[SUBDOMAIN] Host es el dominio base (sin subdominio)")
                return None
            
            # Extraer subdominio
            subdomain = host.replace(f".{self.base_domain}", "")
            
            if subdomain:
                # ✅ NUEVO: Verificar si es subdominio excluido
                if subdomain in self.EXCLUDED_SUBDOMAINS:
                    logger.info(
                        f"[SUBDOMAIN] '{subdomain}' es infraestructura, ignorando (usando SYSTEM)"
                    )
                    return None  # Retornar None para usar cliente por defecto
                
                logger.info(f"[SUBDOMAIN] Detectado: '{subdomain}'")
                return subdomain
        
        logger.warning(
            f"[SUBDOMAIN] No se detectó subdominio válido en: '{host}'. "
            f"Verifica BASE_DOMAIN='{self.base_domain}'"
        )
        return None

    def _get_client_data_by_subdomain(
        self, 
        subdomain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta la BD para obtener cliente_id y código por subdominio.
        
        IMPORTANTE: Usa conexión ADMIN porque aún no tenemos contexto establecido.
        """
        query = """
            SELECT cliente_id, codigo_cliente 
            FROM cliente 
            WHERE subdominio = ? AND es_activo = 1
        """
        
        try:
            logger.debug(f"[DB] Consultando subdominio: '{subdomain}'")
            
            # CRÍTICO: Usar conexión ADMIN para evitar recursión
            with get_db_connection(DatabaseConnection.ADMIN) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (subdomain,))
                row = cursor.fetchone()
                
                if row:
                    result = {
                        "cliente_id": row[0], 
                        "codigo_cliente": row[1]
                    }
                    logger.debug(f"[DB] Cliente encontrado: {result}")
                    return result
                else:
                    logger.debug(
                        f"[DB] No se encontró cliente para subdominio: '{subdomain}'"
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

logger.info("Módulo tenant_middleware cargado (versión híbrida con soporte para proxies)")