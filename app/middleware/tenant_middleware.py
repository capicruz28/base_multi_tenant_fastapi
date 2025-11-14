# app/middleware/tenant_middleware.py
"""
Middleware para la identificación y contextualización del cliente (tenant)
basado en el subdominio de la solicitud (Host header).
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from typing import Dict, Any, Optional

from app.core.tenant_context import current_client_id, current_tenant_context, TenantContext
from app.core.config import settings
from app.db.connection import get_db_connection
from app.core.exceptions import ClientNotFoundException

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que resuelve el ID del cliente (tenant) a partir del subdominio.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.default_client_id = settings.SUPERADMIN_CLIENTE_ID
        self.base_domain = settings.BASE_DOMAIN

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        
        # 1. Inicialización segura de variables
        host = request.headers.get("Host", "")
        subdomain = self._extract_subdomain(host)
        
        client_id: Optional[int] = self.default_client_id
        client_data: Dict[str, Any] = {
            "cliente_id": settings.SUPERADMIN_CLIENTE_ID,
            "codigo_cliente": settings.SUPERADMIN_CLIENTE_CODIGO
        }
        
        # ✅ CORRECCIÓN CRÍTICA: Logging para debugging
        logger.debug(f"[TENANT] Host recibido: {host}")
        logger.debug(f"[TENANT] Subdominio extraído: {subdomain}")
        
        if subdomain:
            if subdomain.lower() == settings.SUPERADMIN_SUBDOMINIO.lower():
                # Caso 1: Acceso al subdominio del super admin (Ej: platform.localhost)
                client_id = settings.SUPERADMIN_CLIENTE_ID
                logger.info(f"[TENANT] Subdominio SUPERADMIN detectado: {subdomain} → Cliente ID: {client_id}")
            else:
                # Caso 2: Buscar cliente por subdominio en la DB
                try:
                    # ✅ CORRECCIÓN: Añadir logging antes de la búsqueda
                    logger.debug(f"[TENANT] Buscando cliente con subdominio: '{subdomain}'")
                    
                    client_data_db = self._get_client_data_by_subdomain(subdomain)
                    
                    if client_data_db:
                        client_data = client_data_db
                        client_id = client_data["cliente_id"]
                        # ✅ CORRECCIÓN: Logging más detallado
                        logger.info(
                            f"[TENANT] Cliente resuelto exitosamente: "
                            f"Subdominio='{subdomain}', "
                            f"Código='{client_data['codigo_cliente']}', "
                            f"ID={client_id}"
                        )
                    else:
                        # ✅ CORRECCIÓN: Logging antes de lanzar excepción
                        logger.error(f"[TENANT] Subdominio '{subdomain}' no encontrado en BD")
                        raise ClientNotFoundException(
                            f"Subdominio '{subdomain}' no está asociado a ningún cliente activo."
                        )
                        
                except ClientNotFoundException as e:
                    logger.warning(f"[TENANT] Error de Tenant: {e}")
                    return JSONResponse(
                        status_code=404,
                        content={"detail": str(e)}
                    )
                except Exception as e:
                    logger.error(f"[TENANT] Error al resolver el tenant: {e}", exc_info=True)
                    return JSONResponse(
                        status_code=500,
                        content={"detail": "Error interno al resolver el contexto de la organización."}
                    )
        else:
            # Caso 3: Sin subdominio (Ej: localhost:8000)
            logger.warning(
                f"[TENANT] Sin subdominio detectado en Host: {host}. "
                f"Usando Cliente ID por defecto: {client_id} (SYSTEM)"
            )

        # 2. ✅ CORRECCIÓN CRÍTICA: Establecer el Contexto ANTES de logging
        token = current_client_id.set(client_id)
        
        tenant_ctx = TenantContext(
            client_id=client_id, 
            subdominio=subdomain, 
            codigo_cliente=client_data.get('codigo_cliente')
        )
        ctx_token = current_tenant_context.set(tenant_ctx)
        
        # ✅ VERIFICACIÓN INMEDIATA (para debugging)
        verificacion = current_client_id.get()
        logger.info(
            f"[TENANT] CONTEXTO ESTABLECIDO: "
            f"cliente_id={client_id}, "
            f"verificación_contexto={verificacion}, "
            f"path={request.url.path}"
        )

        try:
            # 3. Llamar al siguiente middleware/endpoint
            response = await call_next(request)
        finally:
            # 4. Limpiar el contexto
            current_client_id.reset(token)
            current_tenant_context.reset(ctx_token)
            logger.debug(f"[TENANT] Contexto limpiado para cliente_id={client_id}")
        
        return response

    def _extract_subdomain(self, host: str) -> Optional[str]:
        """
        Extrae el subdominio del header Host.
        
        ✅ MEJORADO: Manejo más robusto de dominios personalizados
        """
        # Limpieza de puerto
        if ":" in host:
            host = host.split(":")[0]
        
        # ✅ LOGGING CRÍTICO (INFO level para que siempre se vea)
        logger.info(f"[SUBDOMAIN] Procesando host limpio: '{host}'")
        logger.info(f"[SUBDOMAIN] BASE_DOMAIN configurado: '{self.base_domain}'")
        
        # Caso especial: localhost con subdominio (cliente1.localhost)
        if host.endswith('.localhost'):
            parts = host.split('.')
            if len(parts) >= 2:
                subdomain = parts[0]
                logger.info(f"[SUBDOMAIN] Detectado en localhost: '{subdomain}'")
                return subdomain
        
        # Caso: dominios personalizados (cliente1.midominio.com)
        # ✅ CORRECCIÓN CRÍTICA: Verificar con endswith para asegurar match exacto
        if host.endswith(f".{self.base_domain}") or host == self.base_domain:
            # Si es exactamente el base_domain (sin subdominio)
            if host == self.base_domain:
                logger.info(f"[SUBDOMAIN] Host es el dominio base sin subdominio")
                return None
            
            # Extraer el subdominio (todo lo que está antes del .base_domain)
            subdomain = host.replace(f".{self.base_domain}", "")
            
            if subdomain:
                logger.info(f"[SUBDOMAIN] Detectado en dominio personalizado: '{subdomain}'")
                return subdomain
        
        logger.warning(f"[SUBDOMAIN] No se detectó subdominio válido en: '{host}'")
        logger.warning(f"[SUBDOMAIN] Verifica que BASE_DOMAIN='{self.base_domain}' sea correcto")
        return None

    def _get_client_data_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """
        Consulta la BD para obtener el cliente_id y código basado en el subdominio.
        
        ✅ MEJORADO: Logging detallado para debugging
        """
        query = """
            SELECT cliente_id, codigo_cliente 
            FROM cliente 
            WHERE subdominio = ? AND es_activo = 1
        """
        try:
            logger.debug(f"[DB] Ejecutando query para subdominio: '{subdomain}'")
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (subdomain,))
                row = cursor.fetchone()
                
                if row:
                    result = {"cliente_id": row[0], "codigo_cliente": row[1]}
                    logger.debug(f"[DB] Cliente encontrado: {result}")
                    return result
                else:
                    logger.debug(f"[DB] No se encontró cliente para subdominio: '{subdomain}'")
                    return None
                    
        except Exception as e:
            logger.error(
                f"[DB] Error al buscar cliente por subdominio '{subdomain}': {e}", 
                exc_info=True
            )
            raise