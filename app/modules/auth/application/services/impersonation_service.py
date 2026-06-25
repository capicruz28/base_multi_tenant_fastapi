"""
Servicio de impersonación: sesión temporal de soporte de plataforma en un tenant.

Sin refresh token. TTL fijo 120 minutos. Restaura sesión del operador vía Redis.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.core.auth.impersonation import (
    IMPERSONATION_ACCESS_TTL_MINUTES,
    extract_impersonation_claims,
    impersonation_effective_level_info,
    impersonation_ttl_seconds,
    is_impersonation_payload,
    pop_parent_session,
    store_parent_session,
)
from app.core.config import settings
from app.core.security.jwt import create_access_token, decode_refresh_token
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled
from app.modules.auth.presentation.schemas import (
    EmpresaDisponible,
    LoginEmpresaSelectionResponse,
    build_user_data_with_roles_dict,
)
from app.modules.superadmin.application.services.audit_service import AuditService
from app.modules.tenant.application.services.cliente_service import ClienteService

logger = logging.getLogger(__name__)


class ImpersonationService:
    @staticmethod
    def _coerce_uuid(value: Any) -> Optional[UUID]:
        return AuthService._coerce_uuid(value)

    @staticmethod
    async def _assert_parent_refresh_active_v2(
        parent_refresh_token: Optional[str],
        parent_cliente_id: Optional[UUID],
    ) -> None:
        """Valida sesión padre V2 (C08/C10) antes de impersonar o restaurar."""
        if not parent_refresh_token or not parent_cliente_id:
            return
        if not is_session_v2_enabled(parent_cliente_id):
            return

        from app.modules.auth.application.services.session_probe_service import (
            SessionProbeService,
        )

        probe = await SessionProbeService.resolve_context(
            parent_cliente_id,
            refresh_token=parent_refresh_token,
        )
        if not probe.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La sesión del operador no es válida o ha expirado",
            )

    @staticmethod
    async def _assert_parent_refresh_restorable_v2(
        parent_refresh_token: Optional[str],
    ) -> None:
        """Al finalizar impersonación: la sesión padre debe seguir activa (V2)."""
        if not parent_refresh_token:
            return
        try:
            refresh_payload = decode_refresh_token(parent_refresh_token)
        except Exception:
            return

        parent_cliente_id = ImpersonationService._coerce_uuid(
            refresh_payload.get("cliente_id")
        )
        if not parent_cliente_id or not is_session_v2_enabled(parent_cliente_id):
            return

        from app.modules.auth.application.services.session_probe_service import (
            SessionProbeService,
        )

        probe = await SessionProbeService.resolve_context(
            parent_cliente_id,
            refresh_token=parent_refresh_token,
        )
        if not probe.is_active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=(
                    "La sesión original del operador fue cerrada. "
                    "Inicie sesión nuevamente en el panel de plataforma."
                ),
            )

    @staticmethod
    async def validar_empresa_en_tenant(cliente_id: UUID, empresa_id: UUID) -> None:
        """Valida que la empresa exista, esté activa y pertenezca al tenant (soporte impersonación)."""
        from app.infrastructure.database.tables_erp import OrgEmpresaTable
        from sqlalchemy import select, and_
        from app.infrastructure.database.queries_async import execute_query
        from app.infrastructure.database.connection_async import DatabaseConnection

        empresa_query = select(OrgEmpresaTable.c.empresa_id).where(
            and_(
                OrgEmpresaTable.c.cliente_id == cliente_id,
                OrgEmpresaTable.c.empresa_id == empresa_id,
                OrgEmpresaTable.c.es_activo == True,
            )
        )
        empresa_rows = await execute_query(
            empresa_query,
            connection_type=DatabaseConnection.DEFAULT,
            client_id=cliente_id,
        )
        if not empresa_rows:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La empresa no pertenece a este tenant o no está activa",
            )

    @staticmethod
    async def _resolver_operador_superadmin(
        target_cliente_id: UUID,
    ) -> Dict[str, Any]:
        """
        Usuario de plataforma (superadmin) usado como identidad de soporte en el tenant.
        """
        username = settings.SUPERADMIN_USERNAME
        from app.infrastructure.database.connection_async import DatabaseConnection
        from app.infrastructure.database.queries_async import execute_query
        from sqlalchemy import text

        system_cliente_id = AuthService._coerce_uuid(settings.SUPERADMIN_CLIENTE_ID)
        if not system_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPERADMIN_CLIENTE_ID no configurado",
            )

        query = """
        SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
        FROM usuario
        WHERE cliente_id = :cliente_id AND nombre_usuario = :nombre_usuario AND es_eliminado = 0
        """
        result = await execute_query(
            text(query).bindparams(
                cliente_id=system_cliente_id, nombre_usuario=username
            ),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Usuario de plataforma no encontrado en cliente SYSTEM",
            )
        user = dict(result[0])
        user["target_cliente_id"] = target_cliente_id
        return user

    @staticmethod
    def _build_impersonation_claims(
        operator_usuario_id: UUID,
        operator_username: str,
    ) -> Dict[str, Any]:
        return {
            "is_impersonation": True,
            "impersonated_by": str(operator_usuario_id),
            "impersonated_by_username": operator_username,
        }

    @staticmethod
    async def _emitir_access_impersonacion(
        *,
        username: str,
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: Optional[UUID],
        impersonation_claims: Dict[str, Any],
        user_base_data: Optional[Dict[str, Any]] = None,
        empresa_selection_pending: bool = False,
    ) -> Dict[str, Any]:
        """Emite solo access token (120 min) con claims de impersonación; sin refresh."""
        level_info = impersonation_effective_level_info()
        es_admin_cliente = False
        base = user_base_data or {}

        user_profile = build_user_data_with_roles_dict(
            usuario_id=usuario_id,
            nombre_usuario=username,
            correo=str(base.get("correo") or ""),
            nombre=base.get("nombre"),
            apellido=base.get("apellido"),
            es_activo=True,
            roles=["Soporte plataforma"],
            access_level=level_info["access_level"],
            is_super_admin=level_info["is_super_admin"],
            user_type=level_info["user_type"],
            cliente_id=cliente_id,
            es_admin_cliente=es_admin_cliente,
            empresa_activa=(
                str(empresa_id) if empresa_id is not None else None
            ),
        )

        token_data: Dict[str, Any] = {
            "sub": username,
            "cliente_id": str(cliente_id),
            "level_info": level_info,
            "effective_scope": level_info["effective_scope"],
            **impersonation_claims,
        }
        if empresa_selection_pending:
            token_data["empresa_selection_pending"] = True

        access_token, access_jti = create_access_token(
            data=token_data,
            empresa_id=empresa_id,
            es_admin_cliente=es_admin_cliente,
            access_token_expire_minutes=IMPERSONATION_ACCESS_TTL_MINUTES,
        )

        return {
            "access_token": access_token,
            "access_jti": access_jti,
            "user_data": user_profile,
            "token_data": token_data,
        }

    @staticmethod
    async def iniciar_impersonacion(
        *,
        target_cliente_id: UUID,
        operator_usuario_id: UUID,
        operator_username: str,
        parent_access_token: str,
        parent_refresh_token: Optional[str],
        parent_payload: Dict[str, Any],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> Dict[str, Any]:
        """
        Inicia impersonación hacia target_cliente_id.
        Retorna dict con access_token o LoginEmpresaSelectionResponse fields.
        """
        if is_impersonation_payload(parent_payload):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se permite impersonación anidada",
            )

        parent_cliente_id = ImpersonationService._coerce_uuid(
            parent_payload.get("cliente_id")
        )
        await ImpersonationService._assert_parent_refresh_active_v2(
            parent_refresh_token,
            parent_cliente_id,
        )

        cliente = await ClienteService.obtener_cliente_por_id(target_cliente_id)
        if not cliente or not cliente.es_activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente destino no encontrado o inactivo",
            )

        user = await ImpersonationService._resolver_operador_superadmin(
            target_cliente_id
        )
        username = user["nombre_usuario"]
        usuario_id = user["usuario_id"]
        impersonation_claims = ImpersonationService._build_impersonation_claims(
            operator_usuario_id, operator_username
        )

        empresas: List[Dict[str, Any]] = await AuthService._listar_empresas_activas_org(
            target_cliente_id
        )

        if len(empresas) > 1:
            session = await ImpersonationService._emitir_access_impersonacion(
                username=username,
                usuario_id=usuario_id,
                cliente_id=target_cliente_id,
                empresa_id=None,
                impersonation_claims=impersonation_claims,
                user_base_data=user,
                empresa_selection_pending=True,
            )
            stored_parent = await store_parent_session(
                session["access_jti"],
                parent_access_token=parent_access_token,
                parent_refresh_token=parent_refresh_token,
                ttl_seconds=impersonation_ttl_seconds(),
            )
            if not stored_parent:
                await AuthService.blacklist_access_token_jti(
                    session["access_jti"], None
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "No se puede iniciar impersonación: almacenamiento de sesión "
                        "no disponible (Redis requerido)."
                    ),
                )
            try:
                await AuditService.registrar_auth_event(
                    cliente_id=target_cliente_id,
                    usuario_id=operator_usuario_id,
                    evento="impersonation_started",
                    nombre_usuario_intento=operator_username,
                    descripcion="Inicio de sesión de soporte (impersonación) con selección de empresa",
                    exito=True,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "impersonated_by": str(operator_usuario_id),
                        "requiere_seleccion_empresa": True,
                        "empresas_count": len(empresas),
                    },
                )
            except Exception:
                logger.exception("[AUDIT] Error registrando impersonation_started")

            return {
                "kind": "selection",
                "response": LoginEmpresaSelectionResponse(
                    requiere_seleccion_empresa=True,
                    empresas_disponibles=[
                        EmpresaDisponible.model_validate(e) for e in empresas
                    ],
                    selection_token=session["access_token"],
                    token_type="bearer",
                    user_data=session["user_data"],
                ),
            }

        empresa_activa: Optional[UUID] = None
        if len(empresas) == 1:
            empresa_activa = empresas[0]["empresa_id"]

        session = await ImpersonationService._emitir_access_impersonacion(
            username=username,
            usuario_id=usuario_id,
            cliente_id=target_cliente_id,
            empresa_id=empresa_activa,
            impersonation_claims=impersonation_claims,
            user_base_data=user,
            empresa_selection_pending=False,
        )
        stored_parent = await store_parent_session(
            session["access_jti"],
            parent_access_token=parent_access_token,
            parent_refresh_token=parent_refresh_token,
            ttl_seconds=impersonation_ttl_seconds(),
        )
        if not stored_parent:
            await AuthService.blacklist_access_token_jti(session["access_jti"], None)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "No se puede iniciar impersonación: almacenamiento de sesión "
                    "no disponible (Redis requerido)."
                ),
            )

        try:
            await AuditService.registrar_auth_event(
                cliente_id=target_cliente_id,
                usuario_id=operator_usuario_id,
                evento="impersonation_started",
                nombre_usuario_intento=operator_username,
                descripcion="Inicio de sesión de soporte (impersonación)",
                exito=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "impersonated_by": str(operator_usuario_id),
                    "empresa_id": (
                        str(empresa_activa) if empresa_activa else None
                    ),
                },
            )
        except Exception:
            logger.exception("[AUDIT] Error registrando impersonation_started")

        return {
            "kind": "token",
            "access_token": session["access_token"],
            "token_type": "bearer",
            "user_data": session["user_data"],
        }

    @staticmethod
    async def finalizar_impersonacion(
        *,
        payload: Dict[str, Any],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> Dict[str, Any]:
        """Finaliza impersonación y restaura tokens del operador."""
        if not is_impersonation_payload(payload):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La sesión actual no es una impersonación activa",
            )

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de impersonación inválido",
            )

        parent = await pop_parent_session(str(jti))
        if not parent or not parent.get("parent_access_token"):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=(
                    "La sesión de soporte expiró o no se puede restaurar la sesión original. "
                    "Inicie sesión nuevamente en el panel de plataforma."
                ),
            )

        await AuthService.blacklist_access_token_jti(jti, payload.get("exp"))

        parent_refresh = parent.get("parent_refresh_token")
        await ImpersonationService._assert_parent_refresh_restorable_v2(parent_refresh)

        operator_id = ImpersonationService._coerce_uuid(payload.get("impersonated_by"))
        target_cliente = ImpersonationService._coerce_uuid(payload.get("cliente_id"))

        try:
            await AuditService.registrar_auth_event(
                cliente_id=target_cliente,
                usuario_id=operator_id,
                evento="impersonation_ended",
                nombre_usuario_intento=payload.get("impersonated_by_username"),
                descripcion="Fin de sesión de soporte (impersonación)",
                exito=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"impersonation_jti": jti},
            )
        except Exception:
            logger.exception("[AUDIT] Error registrando impersonation_ended")

        result: Dict[str, Any] = {
            "access_token": parent["parent_access_token"],
            "token_type": "bearer",
        }
        refresh = parent.get("parent_refresh_token")
        if refresh:
            result["refresh_token"] = refresh
        return result

    @staticmethod
    async def seleccionar_empresa_impersonacion(
        *,
        payload: Dict[str, Any],
        empresa_id: UUID,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> Dict[str, Any]:
        """
        Cierra selección de empresa durante impersonación: solo access token, sin refresh.
        Propaga claims de impersonación.
        """
        if not is_impersonation_payload(payload):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token sin contexto de impersonación",
            )

        token_cliente_id = AuthService._coerce_uuid(payload.get("cliente_id"))
        if not token_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sin contexto de tenant",
            )

        await ImpersonationService.validar_empresa_en_tenant(
            token_cliente_id, empresa_id
        )

        username = payload.get("sub") or settings.SUPERADMIN_USERNAME
        user = await ImpersonationService._resolver_operador_superadmin(
            token_cliente_id
        )
        impersonation_claims = extract_impersonation_claims(payload)

        session = await ImpersonationService._emitir_access_impersonacion(
            username=username,
            usuario_id=user["usuario_id"],
            cliente_id=token_cliente_id,
            empresa_id=empresa_id,
            impersonation_claims=impersonation_claims,
            user_base_data=user,
            empresa_selection_pending=False,
        )

        # Reasociar sesión padre al nuevo jti (el anterior quedó en selection token)
        old_jti = payload.get("jti")
        if old_jti:
            parent = await pop_parent_session(str(old_jti))
            if parent:
                await store_parent_session(
                    session["access_jti"],
                    parent_access_token=parent.get("parent_access_token", ""),
                    parent_refresh_token=parent.get("parent_refresh_token"),
                    ttl_seconds=impersonation_ttl_seconds(),
                )

        await AuthService.blacklist_access_token_jti(old_jti, payload.get("exp"))

        try:
            await AuditService.registrar_auth_event(
                cliente_id=token_cliente_id,
                usuario_id=ImpersonationService._coerce_uuid(
                    payload.get("impersonated_by")
                ),
                evento="impersonation_empresa_seleccionada",
                nombre_usuario_intento=payload.get("impersonated_by_username"),
                descripcion="Empresa seleccionada en sesión de impersonación",
                exito=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"empresa_id": str(empresa_id)},
            )
        except Exception:
            logger.exception(
                "[AUDIT] Error registrando impersonation_empresa_seleccionada"
            )

        return {
            "access_token": session["access_token"],
            "token_type": "bearer",
            "user_data": session["user_data"],
        }
