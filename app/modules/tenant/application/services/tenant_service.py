# app/services/tenant_service.py
"""
Servicio para operaciones específicas del tenant actual.
Este servicio permite acceder a la configuración, módulos activos y políticas
del cliente (tenant) asociado al contexto de la solicitud actual.

Este servicio asume que el cliente_id ya fue resuelto y está disponible
a través de un mecanismo de contexto (middleware de tenant), que se implementará
en fases posteriores.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_query
from app.core.exceptions import (
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.tenant.presentation.schemas import ClienteWithConfig
from app.modules.auth.presentation.schemas import AuthConfigRead, FederacionRead

logger = logging.getLogger(__name__)


class TenantService(BaseService):
    """
    Servicio para acceder a la configuración y estado del tenant actual.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_configuracion_tenant(cliente_id: UUID) -> ClienteWithConfig:
        """
        Obtiene la configuración completa del tenant, incluyendo políticas de autenticación
        y proveedores de identidad configurados.
        """
        # 1. Obtener datos del cliente
        cliente_query = """
        SELECT 
            cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
            tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
            favicon_url, color_primario, color_secundario, tema_personalizado,
            plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
            fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
            es_activo, es_demo, fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
        FROM cliente
        WHERE cliente_id = ? AND es_activo = 1
        """
        # ✅ FASE 2: Usar await
        cliente_result = await execute_query(cliente_query, (cliente_id,))
        if not cliente_result:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado o inactivo.",
                internal_code="TENANT_NOT_FOUND"
            )
        cliente_data = cliente_result[0]

        # 2. Obtener configuración de autenticación
        auth_config = None
        auth_query = "SELECT * FROM cliente_auth_config WHERE cliente_id = ?"
        auth_result = await execute_query(auth_query, (cliente_id,))
        if auth_result:
            auth_config = AuthConfigRead(**auth_result[0])

        # 3. Obtener proveedores SSO
        sso_providers: List[FederacionRead] = []
        sso_query = "SELECT * FROM federacion_identidad WHERE cliente_id = ? AND es_activo = 1"
        sso_results = await execute_query(sso_query, (cliente_id,))
        for row in sso_results:
            sso_providers.append(FederacionRead(**row))

        return ClienteWithConfig(
            **cliente_data,
            auth_config=auth_config,
            sso_providers=sso_providers
        )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos_activos(cliente_id: UUID) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de módulos activos para el cliente.
        """
        query = """
        SELECT 
            cma.cliente_modulo_activo_id,
            cm.modulo_id,
            cm.codigo_modulo,
            cm.nombre,
            cm.descripcion,
            cma.esta_activo,
            cma.fecha_activacion,
            cma.fecha_vencimiento,
            cma.configuracion_json,
            cma.limite_usuarios,
            cma.limite_registros
        FROM cliente_modulo_activo cma
        INNER JOIN cliente_modulo cm ON cma.modulo_id = cm.modulo_id
        WHERE cma.cliente_id = ? AND cma.esta_activo = 1
        """
        # ✅ FASE 2: Usar await
        resultados = await execute_query(query, (cliente_id,))
        return resultados