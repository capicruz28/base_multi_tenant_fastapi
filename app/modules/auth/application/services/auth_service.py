# app/modules/auth/application/services/auth_service.py
"""
AuthService: Servicio de autenticación.

✅ ARQUITECTURA: Movido desde app/core/auth.py para corregir violación de capas.
La lógica de autenticación pertenece al módulo Auth, no a Core.

Este servicio maneja:
- Autenticación de usuarios (credenciales)
- Autenticación SSO (Azure AD, Google)
- Validación de tokens (access y refresh)
- Gestión de sesiones
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status, Cookie, Request, Body
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.security.password import verify_password
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_auth_query, execute_query, execute_update
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.tables import UsuarioTable
from sqlalchemy import update, func, text
from app.modules.auth.presentation.schemas import TokenPayload
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.superadmin.application.services.audit_service import AuditService
from app.core.tenant.context import get_current_client_id

logger = logging.getLogger(__name__)


# Schema para recibir refresh token en el body (móvil)
class RefreshTokenBody(BaseModel):
    refresh_token: Optional[str] = None


class AuthService:
    """
    Servicio de autenticación y autorización.
    
    ✅ FASE 4A: Documentación mejorada.
    
    Este servicio maneja toda la lógica de autenticación y autorización en un contexto
    multi-tenant, garantizando seguridad y aislamiento entre diferentes clientes.
    
    Características Principales:
    - Autenticación con credenciales (usuario/contraseña)
    - Autenticación SSO (Single Sign-On)
    - Validación de tokens JWT (access y refresh)
    - Gestión de sesiones y refresh tokens
    - Validación de niveles de acceso (RBAC/LBAC)
    - Aislamiento automático por tenant
    
    Operaciones Críticas:
    - Login y logout de usuarios
    - Generación y validación de tokens JWT
    - Refresh de tokens expirados
    - Validación de permisos y niveles de acceso
    - Gestión de sesiones multi-tenant
    
    Seguridad Multi-Tenant:
    - Tokens incluyen información de tenant
    - Validación de que tokens solo funcionen en su tenant
    - Prevención de acceso cross-tenant
    
    Example:
        ```python
        auth_service = AuthService()
        
        # Autenticar usuario
        tokens = await auth_service.login(
            username="usuario",
            password="password",
            cliente_id=current_client_id
        )
        
        # Validar token
        user_info = await auth_service.validate_token(
            token=tokens["access_token"]
        )
        ```
    
    Note:
        - Todos los tokens incluyen información de tenant
        - Los tokens de un tenant no funcionan en otro tenant
        - El servicio valida automáticamente el contexto de tenant
    """
    
    @staticmethod
    def _coerce_uuid(value: Any) -> Optional[UUID]:
        """Normaliza un valor de BD a UUID o None."""
        if value is None:
            return None
        if isinstance(value, UUID):
            null_uuid = UUID("00000000-0000-0000-0000-000000000000")
            return None if value == null_uuid else value
        try:
            parsed = UUID(str(value))
            null_uuid = UUID("00000000-0000-0000-0000-000000000000")
            return None if parsed == null_uuid else parsed
        except (ValueError, AttributeError, TypeError):
            return None

    @staticmethod
    def _empresa_disponible_from_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        eid = AuthService._coerce_uuid(row.get("empresa_id"))
        if not eid:
            return None
        nombre_comercial = row.get("nombre_comercial")
        if nombre_comercial is not None:
            nombre_comercial = str(nombre_comercial).strip() or None
        return {
            "empresa_id": eid,
            "razon_social": str(row.get("razon_social") or "").strip(),
            "nombre_comercial": nombre_comercial,
        }

    @staticmethod
    def _empresa_ids_disponibles(empresas: List[Any]) -> List[UUID]:
        ids: List[UUID] = []
        for item in empresas or []:
            if isinstance(item, dict):
                eid = AuthService._coerce_uuid(item.get("empresa_id"))
            else:
                eid = AuthService._coerce_uuid(item)
            if eid:
                ids.append(eid)
        return ids

    @staticmethod
    async def _listar_empresas_activas_org(cliente_id: UUID) -> List[Dict[str, Any]]:
        """
        Empresas activas del tenant en org_empresa (admin cliente sin usuario_rol por empresa).
        """
        query = text("""
            SELECT empresa_id, razon_social, nombre_comercial
            FROM org_empresa
            WHERE cliente_id = :cliente_id
              AND es_activo = 1
            ORDER BY razon_social
        """).bindparams(cliente_id=cliente_id)
        rows = await execute_query(
            query,
            connection_type=DatabaseConnection.DEFAULT,
            client_id=cliente_id,
        )
        empresas: List[Dict[str, Any]] = []
        seen: set[UUID] = set()
        for row in rows or []:
            item = AuthService._empresa_disponible_from_row(row)
            if item and item["empresa_id"] not in seen:
                seen.add(item["empresa_id"])
                empresas.append(item)
        return empresas

    @staticmethod
    def _platform_superadmin_level_info() -> Dict[str, Any]:
        """Niveles canónicos para superadmin de plataforma (CAXIS / cliente SYSTEM)."""
        return {
            "access_level": 5,
            "is_super_admin": True,
            "user_type": "platform_admin",
        }

    @staticmethod
    def _is_platform_operator_payload(payload: Dict[str, Any]) -> bool:
        """True si el JWT refresh/access indica operador de plataforma."""
        return bool(
            payload.get("is_super_admin")
            or payload.get("es_superadmin")
            or payload.get("user_type") == "platform_admin"
        )

    @staticmethod
    async def resolve_level_info_for_token_refresh(
        *,
        refresh_payload: Dict[str, Any],
        username: str,
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Niveles LBAC al rotar tokens: preservar claims del refresh JWT (login previo).

        Evita recalcular sin username y degradar platform_admin → tenant_admin
        (roles ADMIN nivel 4 en cliente SYSTEM).
        """
        if AuthService._is_platform_operator_payload(refresh_payload):
            return AuthService._platform_superadmin_level_info()

        has_level_claims = (
            refresh_payload.get("user_type") is not None
            and refresh_payload.get("access_level") is not None
        )
        if has_level_claims:
            return {
                "access_level": int(refresh_payload.get("access_level", 1)),
                "is_super_admin": bool(refresh_payload.get("is_super_admin", False)),
                "user_type": str(refresh_payload.get("user_type", "user")),
            }

        info = await AuthService.get_user_access_level_info(
            usuario_id,
            cliente_id,
            empresa_id=empresa_id,
            username=username,
        )
        if refresh_payload.get("es_superadmin") or await AuthService._detect_platform_superadmin(
            usuario_id, username
        ):
            return AuthService._platform_superadmin_level_info()
        return info

    @staticmethod
    def build_token_data_from_level_info(
        *,
        username: str,
        cliente_id: Any,
        level_info: Dict[str, Any],
        refresh_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Arma token_data para create_access_token / create_refresh_token."""
        cid = cliente_id if isinstance(cliente_id, str) else str(cliente_id)
        token_data: Dict[str, Any] = {
            "sub": username,
            "cliente_id": cid,
            "level_info": level_info,
        }
        if level_info.get("is_super_admin") or (
            refresh_payload and refresh_payload.get("es_superadmin")
        ):
            token_data["es_superadmin"] = True
        return token_data

    @staticmethod
    async def _fetch_user_row_for_refresh(
        username: str,
        *,
        payload: Dict[str, Any],
        token_cliente_id: Optional[UUID],
    ) -> Optional[Dict[str, Any]]:
        """
        Carga usuario para refresh. Platform superadmin vive en BD ADMIN (cliente SYSTEM).
        """
        from app.core.tenant.context import try_get_tenant_context

        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        system_cliente_id = AuthService._coerce_uuid(settings.SUPERADMIN_CLIENTE_ID)
        is_platform = AuthService._is_platform_operator_payload(payload)

        if is_platform:
            search_cliente_id = token_cliente_id or system_cliente_id
            if not search_cliente_id:
                return None
            # Misma BD que tenant: usar routing DEFAULT + cliente_id del JWT (SYSTEM).
            # ADMIN solo en login password del username reservado; refresh alinea con persistencia.
            query = text("""
                SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
                FROM usuario
                WHERE cliente_id = :cliente_id
                  AND nombre_usuario = :nombre_usuario
                  AND es_eliminado = 0
            """).bindparams(
                cliente_id=search_cliente_id,
                nombre_usuario=username,
            )
            result = await execute_query(
                query,
                connection_type=DatabaseConnection.DEFAULT,
                client_id=search_cliente_id,
            )
            return result[0] if result else None

        if database_type == "multi":
            query = """
            SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
            FROM usuario
            WHERE nombre_usuario = ? AND es_eliminado = 0
            """
            return await execute_auth_query(query, (username,))

        search_cliente_id = token_cliente_id
        if not search_cliente_id:
            from app.core.tenant.context import try_get_current_client_id

            search_cliente_id = try_get_current_client_id()
        if not search_cliente_id:
            return None

        query = text("""
            SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
            FROM usuario
            WHERE cliente_id = :cliente_id
              AND nombre_usuario = :nombre_usuario
              AND es_eliminado = 0
        """).bindparams(
            cliente_id=search_cliente_id,
            nombre_usuario=username,
        )
        result = await execute_query(
            query,
            connection_type=DatabaseConnection.DEFAULT,
            client_id=search_cliente_id,
        )
        return result[0] if result else None

    @staticmethod
    async def _detect_platform_superadmin(
        usuario_id: UUID,
        username: Optional[str] = None,
    ) -> bool:
        """
        True si es superadmin de plataforma: username reservado o rol SUPER_ADMIN
        nivel 5 en el cliente SYSTEM (BD admin).
        """
        if username and username == settings.SUPERADMIN_USERNAME:
            return True

        system_cliente_id = AuthService._coerce_uuid(settings.SUPERADMIN_CLIENTE_ID)
        if not system_cliente_id:
            return False

        try:
            super_sql = text("""
                SELECT COUNT(*) AS super_admin_count
                FROM usuario_rol ur
                INNER JOIN rol r ON ur.rol_id = r.rol_id
                WHERE ur.usuario_id = :usuario_id
                  AND ur.cliente_id = :cliente_id
                  AND ur.es_activo = 1
                  AND r.es_activo = 1
                  AND r.codigo_rol = 'SUPER_ADMIN'
                  AND r.nivel_acceso = 5
            """).bindparams(usuario_id=usuario_id, cliente_id=system_cliente_id)

            rows = await execute_query(
                super_sql,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None,
            )
            if rows:
                return int(rows[0].get("super_admin_count") or 0) > 0
        except Exception as e:
            logger.warning(
                "[AUTH] No se pudo verificar SUPER_ADMIN en cliente SYSTEM para %s: %s",
                usuario_id,
                e,
            )
        return False

    @staticmethod
    async def get_empresa_activa_para_login(
        usuario_id: UUID,
        cliente_id: UUID,
        *,
        payload: Optional[Dict[str, Any]] = None,
        es_superadmin: Optional[bool] = None,
        user_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resuelve la empresa activa y el estado de selección post-login (solo lectura).

        Returns:
            empresas_disponibles, empresa_activa, es_admin_sin_empresa, requiere_seleccion
        """
        if payload:
            if es_superadmin is None:
                es_superadmin = bool(payload.get("es_superadmin"))
            if user_type is None:
                user_type = payload.get("user_type")

        if es_superadmin or user_type == "platform_admin":
            logger.info(
                "[AUTH] Superadmin plataforma: sin empresa activa ni selección "
                "(usuario=%s, cliente=%s)",
                usuario_id,
                cliente_id,
            )
            return {
                "empresas_disponibles": [],
                "empresa_activa": None,
                "es_admin_sin_empresa": False,
                "requiere_seleccion": False,
            }

        from app.core.tenant.context import try_get_tenant_context

        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"

        empresas_disponibles: List[Dict[str, Any]] = []
        empresa_default_id: Optional[UUID] = None
        es_admin_sin_empresa = False

        try:
            empresas_sql = text("""
                SELECT DISTINCT oe.empresa_id, oe.razon_social, oe.nombre_comercial
                FROM usuario_rol ur
                INNER JOIN org_empresa oe ON oe.empresa_id = ur.empresa_id
                WHERE ur.usuario_id = :usuario_id
                  AND ur.cliente_id = :cliente_id
                  AND ur.es_activo = 1
                  AND ur.empresa_id IS NOT NULL
                  AND oe.es_activo = 1
                ORDER BY oe.razon_social
            """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

            empresas_rows = await execute_query(
                empresas_sql,
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cliente_id,
            )
            seen: set[UUID] = set()
            for row in empresas_rows or []:
                item = AuthService._empresa_disponible_from_row(row)
                if item and item["empresa_id"] not in seen:
                    seen.add(item["empresa_id"])
                    empresas_disponibles.append(item)

            admin_sql = text("""
                SELECT COUNT(*) AS admin_sin_empresa_count
                FROM usuario_rol ur
                WHERE ur.usuario_id = :usuario_id
                  AND ur.cliente_id = :cliente_id
                  AND ur.es_activo = 1
                  AND ur.empresa_id IS NULL
            """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

            admin_rows = await execute_query(
                admin_sql,
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cliente_id,
            )
            if admin_rows:
                es_admin_sin_empresa = int(admin_rows[0].get("admin_sin_empresa_count") or 0) > 0

            if database_type == "multi":
                usuario_sql = text("""
                    SELECT empresa_default_id
                    FROM usuario
                    WHERE usuario_id = :usuario_id
                      AND es_eliminado = 0
                """).bindparams(usuario_id=usuario_id)
            else:
                usuario_sql = text("""
                    SELECT empresa_default_id
                    FROM usuario
                    WHERE usuario_id = :usuario_id
                      AND cliente_id = :cliente_id
                      AND es_eliminado = 0
                """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

            usuario_rows = await execute_query(
                usuario_sql,
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cliente_id,
            )
            if usuario_rows:
                empresa_default_id = AuthService._coerce_uuid(
                    usuario_rows[0].get("empresa_default_id")
                )

        except Exception as e:
            logger.warning(
                "[AUTH] get_empresa_activa_para_login falló para usuario %s: %s",
                usuario_id,
                e,
                exc_info=True,
            )

        # Admin global (usuario_rol.empresa_id NULL): elegibles desde org_empresa (R-LOGIN-06)
        if es_admin_sin_empresa and not empresas_disponibles:
            try:
                empresas_org = await AuthService._listar_empresas_activas_org(cliente_id)
                if empresas_org:
                    empresas_disponibles = empresas_org
                    logger.info(
                        "[AUTH] Admin sin empresa en usuario_rol: %s empresas en org_empresa",
                        len(empresas_org),
                    )
            except Exception as org_err:
                logger.warning(
                    "[AUTH] No se pudo listar org_empresa para cliente %s: %s",
                    cliente_id,
                    org_err,
                )

        ids_disponibles = AuthService._empresa_ids_disponibles(empresas_disponibles)

        # R-DATA-02: preferida inválida → limpiar y tratar como NULL
        if empresa_default_id is not None and ids_disponibles:
            if empresa_default_id not in ids_disponibles:
                try:
                    from app.core.tenant.empresa_preference import (
                        clear_usuario_empresa_default_id,
                    )

                    await clear_usuario_empresa_default_id(usuario_id, cliente_id)
                    logger.info(
                        "[AUTH] empresa_default_id inválida limpiada usuario=%s",
                        usuario_id,
                    )
                except Exception as clear_err:
                    logger.warning(
                        "[AUTH] No se pudo limpiar empresa_default_id inválida: %s",
                        clear_err,
                    )
                empresa_default_id = None

        tiene_default_definida = empresa_default_id is not None
        requiere_seleccion = len(empresas_disponibles) > 1 and not tiene_default_definida

        empresa_activa: Optional[UUID] = None
        if requiere_seleccion:
            empresa_activa = None
        elif empresas_disponibles:
            if empresa_default_id and empresa_default_id in ids_disponibles:
                empresa_activa = empresa_default_id
            else:
                empresa_activa = empresas_disponibles[0]["empresa_id"]

        logger.info(
            "[AUTH] Empresa login usuario=%s cliente=%s disponibles=%s activa=%s "
            "requiere_seleccion=%s admin_sin_empresa=%s",
            usuario_id,
            cliente_id,
            len(empresas_disponibles),
            empresa_activa,
            requiere_seleccion,
            es_admin_sin_empresa,
        )

        return {
            "empresas_disponibles": empresas_disponibles,
            "empresa_activa": empresa_activa,
            "es_admin_sin_empresa": es_admin_sin_empresa,
            "requiere_seleccion": requiere_seleccion,
        }

    @staticmethod
    def assert_operational_login_allowed(
        empresa_ctx: Dict[str, Any],
        *,
        es_superadmin: bool = False,
        user_type: Optional[str] = None,
    ) -> None:
        """
        R-LOGIN-04 / R-LOGIN-05: rechaza login operativo sin empresas elegibles.
        Permite admin onboarding (es_admin_sin_empresa sin org) y platform_admin.
        """
        from app.core.exceptions import AuthorizationError
        from app.core.tenant.empresa_preference import USER_WITHOUT_COMPANY

        if es_superadmin or (user_type or "").lower() == "platform_admin":
            return

        empresas = empresa_ctx.get("empresas_disponibles") or []
        if empresas:
            return

        if empresa_ctx.get("es_admin_sin_empresa"):
            return

        raise AuthorizationError(
            detail=(
                "El usuario no tiene empresas asignadas. "
                "Contacte al administrador del tenant."
            ),
            internal_code=USER_WITHOUT_COMPANY,
        )

    @staticmethod
    async def get_token_expiration_for_cliente(cliente_id: UUID) -> Dict[str, int]:
        """
        Expiración de JWT por tenant desde cliente_auth_config, con fallback a settings.
        """
        from app.modules.auth.application.services.auth_config_service import (
            leer_expiracion_tokens_cliente,
        )

        return await leer_expiracion_tokens_cliente(cliente_id)

    @staticmethod
    async def usuario_tiene_es_admin_cliente(
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: Optional[UUID] = None,
        username: Optional[str] = None,
    ) -> bool:
        """
        True si el usuario tiene al menos un rol activo con rol.es_admin_cliente = 1
        en el cliente (y opcionalmente en la empresa activa o roles globales).
        """
        if await AuthService._detect_platform_superadmin(usuario_id, username):
            return False

        try:
            if empresa_id is not None:
                admin_sql = text("""
                    SELECT COUNT(*) AS admin_cliente_count
                    FROM usuario_rol ur
                    INNER JOIN rol r ON ur.rol_id = r.rol_id
                    WHERE ur.usuario_id = :usuario_id
                      AND ur.cliente_id = :cliente_id
                      AND ur.es_activo = 1
                      AND r.es_activo = 1
                      AND r.es_admin_cliente = 1
                      AND (ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)
                """).bindparams(
                    usuario_id=usuario_id,
                    cliente_id=cliente_id,
                    empresa_id=empresa_id,
                )
            else:
                admin_sql = text("""
                    SELECT COUNT(*) AS admin_cliente_count
                    FROM usuario_rol ur
                    INNER JOIN rol r ON ur.rol_id = r.rol_id
                    WHERE ur.usuario_id = :usuario_id
                      AND ur.cliente_id = :cliente_id
                      AND ur.es_activo = 1
                      AND r.es_activo = 1
                      AND r.es_admin_cliente = 1
                """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

            rows = await execute_query(
                admin_sql,
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cliente_id,
            )
            if rows:
                return int(rows[0].get("admin_cliente_count") or 0) > 0
        except Exception as e:
            logger.warning(
                "[AUTH] usuario_tiene_es_admin_cliente falló para usuario %s: %s",
                usuario_id,
                e,
            )
        return False

    @staticmethod
    async def get_user_access_level_info(
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: Optional[UUID] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene información de niveles de acceso del usuario.
        
        ✅ FASE 2: Refactorizado para usar async.
        ✅ Multi-empresa: filtra por empresa_id del JWT/contexto cuando está definido.
        ✅ Superadmin plataforma: username reservado o SUPER_ADMIN nivel 5 en cliente SYSTEM.
        """
        try:
            if await AuthService._detect_platform_superadmin(usuario_id, username):
                info = AuthService._platform_superadmin_level_info()
                logger.info(
                    "Niveles calculados - Usuario %s: level=%s, super_admin=%s, type=%s "
                    "(platform superadmin)",
                    usuario_id,
                    info["access_level"],
                    info["is_super_admin"],
                    info["user_type"],
                )
                return info

            from app.infrastructure.database.queries_async import execute_query
            from app.infrastructure.database.connection_async import DatabaseConnection
            from sqlalchemy import text
            from app.core.tenant.context import try_get_tenant_context
            from app.core.tenant.empresa_context import resolve_empresa_id, sql_empresa_filter_usuario_rol

            resolved_empresa_id = resolve_empresa_id(empresa_id)
            tenant_context = try_get_tenant_context()
            database_type = tenant_context.database_type if tenant_context else "single"
            empresa_sql = (
                sql_empresa_filter_usuario_rol("ur") if resolved_empresa_id else ""
            )

            if database_type == "multi":
                query = f"""
                SELECT 
                    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
                    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count,
                    COUNT(*) as total_roles
                FROM usuario_rol ur
                INNER JOIN rol r ON ur.rol_id = r.rol_id
                WHERE ur.usuario_id = :usuario_id 
                  AND ur.es_activo = 1
                  AND r.es_activo = 1
                {empresa_sql}
                """
                bind = {"usuario_id": usuario_id}
                if resolved_empresa_id:
                    bind["empresa_id"] = resolved_empresa_id
                result = await execute_query(
                    text(query).bindparams(**bind),
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cliente_id,
                )
            else:
                query = f"""
                SELECT 
                    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
                    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count,
                    COUNT(*) as total_roles
                FROM usuario_rol ur
                INNER JOIN rol r ON ur.rol_id = r.rol_id
                WHERE ur.usuario_id = :usuario_id 
                  AND ur.es_activo = 1
                  AND r.es_activo = 1
                  AND (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
                {empresa_sql}
                """
                bind = {"usuario_id": usuario_id, "cliente_id": cliente_id}
                if resolved_empresa_id:
                    bind["empresa_id"] = resolved_empresa_id
                result = await execute_query(
                    text(query).bindparams(**bind),
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cliente_id,
                )
            
            if result and len(result) > 0:
                level_data = result[0]
                access_level = level_data.get('max_level', 1)
                is_super_admin = level_data.get('super_admin_count', 0) > 0
                
                # Determinar tipo de usuario (tenant-scoped; platform superadmin ya retornó arriba)
                if is_super_admin:
                    user_type = "platform_admin"
                elif access_level >= 4:
                    user_type = "tenant_admin"
                else:
                    user_type = "user"
                    
                logger.info(f"Niveles calculados - Usuario {usuario_id}: level={access_level}, super_admin={is_super_admin}, type={user_type}")
                
                return {
                    'access_level': access_level,
                    'is_super_admin': is_super_admin,
                    'user_type': user_type
                }
            else:
                logger.warning(f"No se pudieron calcular niveles para usuario {usuario_id}, usando valores por defecto")
                return {
                    'access_level': 1,
                    'is_super_admin': False,
                    'user_type': 'user'
                }
                
        except Exception as e:
            logger.error(f"Error al obtener niveles de acceso para usuario {usuario_id}: {e}")
            # Valores por defecto en caso de error
            return {
                'access_level': 1,
                'is_super_admin': False,
                'user_type': 'user'
            }
    
    @staticmethod
    async def authenticate_user(cliente_id: UUID, username: str, password: str) -> Dict:
        """
        Autentica un usuario **dentro de un cliente específico**.
        
        ✅ CORRECCIÓN MULTI-TENANT HÍBRIDO: 
        - Si es el Super Admin: Busca en BD ADMIN (donde está el cliente SYSTEM)
        - Si es un usuario regular: Busca en la BD del cliente (compartida o separada)
        
        AHORA INCLUYE: access_level, is_super_admin, user_type en la respuesta
        """
        
        # ✅ LOGGING CRÍTICO: Verificar qué cliente_id llegó
        logger.info(f"[AUTH] Intento de login: username='{username}', cliente_id_destino={cliente_id}")
        
        # 1. Detectar si es superadmin
        is_superadmin = (username == settings.SUPERADMIN_USERNAME)
        
        # 2. Determinar dónde buscar y en qué BD
        if is_superadmin:
            # SUPERADMIN: Buscar en cliente SYSTEM, usando BD ADMIN
            search_cliente_id = settings.SUPERADMIN_CLIENTE_ID
            target_cliente_id = cliente_id  # Cliente al que quiere acceder
            
            logger.info(
                f"[AUTH] SUPERADMIN detectado. "
                f"Buscando en BD ADMIN (cliente_id={search_cliente_id}), "
                f"accediendo a cliente_id={target_cliente_id}"
            )
        else:
            # USUARIO REGULAR: Buscar en su cliente, usando BD del contexto
            search_cliente_id = cliente_id
            target_cliente_id = cliente_id
            
            logger.info(
                f"[AUTH] Usuario regular. "
                f"Buscando en BD del cliente_id={search_cliente_id}"
            )

        try:
            # ✅ Obtener database_type del contexto para determinar si es BD dedicada
            from app.core.tenant.context import get_tenant_context, try_get_tenant_context
            from sqlalchemy import text
            
            tenant_context = None
            database_type = "single"
            try:
                tenant_context = get_tenant_context()
                database_type = tenant_context.database_type if tenant_context else "single"
            except RuntimeError:
                # Sin contexto, intentar obtener sin lanzar excepción
                tenant_context = try_get_tenant_context()
                database_type = tenant_context.database_type if tenant_context else "single"
            
            # ✅ CORRECCIÓN: Para BD dedicadas (multi), no filtrar por cliente_id
            # porque todos los usuarios en esa BD pertenecen al mismo cliente
            if database_type == "multi":
                query = """
                SELECT usuario_id, cliente_id, nombre_usuario, correo, contrasena,
                       nombre, apellido, es_activo
                FROM usuario
                WHERE nombre_usuario = :nombre_usuario AND es_eliminado = 0
                """
                logger.debug(
                    f"[AUTH] BD dedicada detectada. Buscando usuario sin filtrar por cliente_id: "
                    f"username='{username}'"
                )
            else:
                query = """
                SELECT usuario_id, cliente_id, nombre_usuario, correo, contrasena,
                       nombre, apellido, es_activo
                FROM usuario
                WHERE cliente_id = :cliente_id AND nombre_usuario = :nombre_usuario AND es_eliminado = 0
                """
                logger.debug(
                    f"[AUTH] BD compartida. Buscando usuario con cliente_id: "
                    f"cliente_id={search_cliente_id}, username='{username}'"
                )
            
            # ✅ CORRECCIÓN CRÍTICA: Usar BD apropiada según tipo de usuario
            # ✅ FASE 2: Usar execute_query async con text().bindparams()
            
            if is_superadmin:
                # Superadmin: SIEMPRE usar BD ADMIN
                logger.debug(f"[AUTH] Ejecutando en BD ADMIN: cliente_id={search_cliente_id}, username='{username}'")
                
                result = await execute_query(
                    text(query).bindparams(cliente_id=search_cliente_id, nombre_usuario=username),
                    connection_type=DatabaseConnection.ADMIN,
                    client_id=None
                )
                user = result[0] if result else None
            else:
                # Usuario regular: Usar BD del contexto (tenant-aware)
                logger.debug(f"[AUTH] Ejecutando en BD tenant: cliente_id={search_cliente_id}, username='{username}'")
                
                if database_type == "multi":
                    # BD dedicada: no pasar cliente_id en bindparams
                    result = await execute_query(
                        text(query).bindparams(nombre_usuario=username),
                        connection_type=DatabaseConnection.DEFAULT,
                        client_id=search_cliente_id
                    )
                else:
                    # BD compartida: pasar cliente_id en bindparams
                    result = await execute_query(
                        text(query).bindparams(cliente_id=search_cliente_id, nombre_usuario=username),
                        connection_type=DatabaseConnection.DEFAULT,
                        client_id=search_cliente_id
                    )
                user = result[0] if result else None

            if not user:
                logger.warning(
                    f"[AUTH] Usuario NO ENCONTRADO: "
                    f"username='{username}', "
                    f"cliente_id_buscado={search_cliente_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas"
                )
            
            # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
            # Usar el cliente_id del contexto del tenant en su lugar
            # IMPORTANTE: Hacer esto ANTES del log para que el log muestre el valor correcto
            if database_type == "multi":
                # Convertir cliente_id a UUID si es string para comparar
                user_cliente_id = user.get('cliente_id')
                if user_cliente_id:
                    if isinstance(user_cliente_id, str):
                        try:
                            user_cliente_id = UUID(user_cliente_id)
                        except (ValueError, AttributeError):
                            user_cliente_id = None
                    elif not isinstance(user_cliente_id, UUID):
                        user_cliente_id = None
                
                # Verificar si es None o UUID nulo
                if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                    user['cliente_id'] = search_cliente_id
                    logger.debug(
                        f"[AUTH] BD dedicada: cliente_id del usuario era NULL/nulo, "
                        f"usando cliente_id del contexto: {search_cliente_id}"
                    )
                else:
                    user['cliente_id'] = user_cliente_id
            
            # ✅ LOGGING: Usuario encontrado (después de la corrección)
            logger.debug(f"[AUTH] Usuario encontrado: usuario_id={user['usuario_id']}, cliente_id={user['cliente_id']}")
            
            if not verify_password(password, user['contrasena']):
                logger.warning(
                    f"[AUTH] Contraseña incorrecta para: "
                    f"username='{username}', "
                    f"usuario_id={user['usuario_id']}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas"
                )

            if not user['es_activo']:
                logger.warning(f"[AUTH] Usuario inactivo: usuario_id={user['usuario_id']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario inactivo"
                )

            # Actualizar fecha último acceso
            # ✅ FASE 2: Usar execute_query async para UPDATE
            from app.infrastructure.database.tables import UsuarioTable
            from sqlalchemy import update, func, text
            
            update_query = update(UsuarioTable).where(
                UsuarioTable.c.usuario_id == user['usuario_id']
            ).values(fecha_ultimo_acceso=func.getdate())
            
            await execute_update(update_query)

            # ✅ CALCULAR NIVELES DE ACCESO (NUEVO)
            # ✅ FASE 2: Usar await — incluye detección platform superadmin por username/rol SYSTEM
            level_info = await AuthService.get_user_access_level_info(
                user["usuario_id"],
                user["cliente_id"],
                username=username,
            )
            if is_superadmin or level_info.get("is_super_admin"):
                level_info = AuthService._platform_superadmin_level_info()

            # Agregar niveles al usuario
            user['access_level'] = level_info['access_level']
            user['is_super_admin'] = level_info['is_super_admin']
            user['user_type'] = level_info['user_type']
            
            # Eliminar la contraseña del resultado
            user.pop('contrasena', None)
            
            # ✅ AGREGAR contexto multi-tenant al resultado
            if is_superadmin or level_info.get("is_super_admin"):
                user['target_cliente_id'] = target_cliente_id
                user['es_superadmin'] = True
            else:
                # Para usuarios regulares, asegurar que target_cliente_id sea el cliente_id correcto
                # En BD dedicadas, usar search_cliente_id (del contexto) en lugar del cliente_id del usuario
                if database_type == "multi":
                    user['target_cliente_id'] = search_cliente_id
                else:
                    user['target_cliente_id'] = user['cliente_id']
            
            logger.info(
                f"[AUTH] Login exitoso: "
                f"username='{username}', "
                f"usuario_id={user['usuario_id']}, "
                f"cliente_origen={user['cliente_id']}, "
                f"cliente_destino={target_cliente_id if is_superadmin else 'N/A'}, "
                f"access_level={user['access_level']}, "
                f"user_type={user['user_type']}"
            )
            
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"[AUTH] Error en autenticación: "
                f"username='{username}', "
                f"cliente_id={cliente_id}, "
                f"error={str(e)}", 
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en el proceso de autenticación"
            )
    
    @staticmethod
    async def authenticate_user_sso_azure_ad(cliente_id: UUID, token: str) -> Dict:
        """
        Autentica un usuario utilizando un token de Azure AD.
        """
        # Esta es una implementación placeholder. En la práctica, deberías:
        # 1. Validar el token JWT contra el tenant de Azure del cliente.
        # 2. Extraer el `oid` (Object ID) del usuario.
        # 3. Buscar en la tabla `usuario` con `proveedor_autenticacion = 'azure_ad'` y `referencia_externa_id = <oid>`.
        logger.info(f"Autenticando usuario SSO (Azure AD) para cliente {cliente_id}")
        raise NotImplementedError("Autenticación SSO con Azure AD no implementada.")
    
    @staticmethod
    async def authenticate_user_sso_google(cliente_id: UUID, token: str) -> Dict:
        """
        Autentica un usuario utilizando un token de Google Workspace.
        """
        # Esta es una implementación placeholder. En la práctica, deberías:
        # 1. Validar el token JWT contra Google.
        # 2. Extraer el `sub` (Subject) del usuario.
        # 3. Buscar en la tabla `usuario` con `proveedor_autenticacion = 'google'` y `referencia_externa_id = <sub>`.
        logger.info(f"Autenticando usuario SSO (Google) para cliente {cliente_id}")
        raise NotImplementedError("Autenticación SSO con Google no implementada.")
    
    @staticmethod
    async def get_current_user(token: str) -> Dict:
        """
        Obtiene el usuario actual basado en el access token (Bearer).
        
        ✅ CORRECCIÓN MULTI-TENANT HÍBRIDO:
        - Superadmin: Busca en BD ADMIN
        - Usuario regular: Busca en BD del contexto
        
        AHORA INCLUYE: access_level, is_super_admin, user_type del token
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Usa SECRET_KEY para validar access tokens
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)

            if not token_data.sub or token_data.type != "access":
                raise credentials_exception

            # ✅ REVOCACIÓN: Verificar si el token está en la blacklist
            jti = payload.get("jti")
            if jti:
                try:
                    from app.infrastructure.redis.client import RedisService
                    is_blacklisted = await RedisService.is_token_blacklisted(jti)
                    
                    if is_blacklisted:
                        logger.warning(
                            f"[REVOCACIÓN] Token revocado detectado en AuthService. "
                            f"jti={jti}, usuario={token_data.sub}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token revocado",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                except HTTPException:
                    # Re-lanzar HTTPException (token revocado)
                    raise
                except Exception as redis_error:
                    # Fail-soft: Si Redis falla, loguear pero continuar (no bloquear acceso)
                    logger.error(
                        f"[REVOCACIÓN] Error verificando blacklist en Redis (fail-soft): {redis_error}. "
                        f"Continuando sin verificación de revocación. jti={jti}, usuario={token_data.sub}",
                        exc_info=True
                    )
                    # NO bloquear acceso si Redis falla (fail-soft)
            else:
                logger.warning(
                    f"[REVOCACIÓN] Token sin jti en AuthService. "
                    f"No se puede verificar revocación. usuario={token_data.sub}"
                )

            username = token_data.sub
            es_superadmin = payload.get("es_superadmin", False)
            target_cliente_id = payload.get("cliente_id")  # Cliente al que accede
            token_cliente_id = payload.get("cliente_id")  # Cliente del token
            
            # ✅ EXTRAER CAMPOS DE NIVEL DEL TOKEN
            access_level = payload.get("access_level", 1)
            is_super_admin = payload.get("is_super_admin", False)
            user_type = payload.get("user_type", "user")
            
            # ============================================
            # ✅ FASE 1: VALIDACIÓN DE TENANT EN TOKEN (CON FEATURE FLAG)
            # ============================================
            # IMPORTANTE: Solo se valida si el flag está activo
            # Por defecto está desactivado (comportamiento actual)
            if settings.ENABLE_TENANT_TOKEN_VALIDATION:
                try:
                    current_cliente_id = get_current_client_id()
                    
                    # ✅ Convertir token_cliente_id a UUID si es string
                    token_cliente_id_uuid = None
                    if token_cliente_id is not None:
                        if isinstance(token_cliente_id, str):
                            try:
                                token_cliente_id_uuid = UUID(token_cliente_id)
                            except (ValueError, AttributeError):
                                logger.warning(
                                    f"[SECURITY] token_cliente_id inválido en token: {token_cliente_id}"
                                )
                                token_cliente_id_uuid = None
                        elif isinstance(token_cliente_id, UUID):
                            token_cliente_id_uuid = token_cliente_id
                    
                    # Superadmin puede cambiar de tenant (comportamiento actual)
                    # Solo validamos para usuarios regulares
                    if not es_superadmin and token_cliente_id_uuid is not None:
                        if token_cliente_id_uuid != current_cliente_id:
                            logger.warning(
                                f"[SECURITY] Token de tenant {token_cliente_id_uuid} usado en tenant {current_cliente_id}. "
                                f"Usuario: {username}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Token no válido para este tenant. Por favor, inicie sesión nuevamente."
                            )
                        logger.debug(
                            f"[SECURITY] Validación de tenant exitosa: token_cliente_id={token_cliente_id_uuid}, "
                            f"current_cliente_id={current_cliente_id}"
                        )
                except RuntimeError:
                    # Si no hay contexto (script de fondo, inicialización), permitir
                    # Esto mantiene compatibilidad con código que no tiene contexto
                    logger.debug(
                        "[AUTH] Sin contexto de tenant disponible, validación omitida "
                        "(comportamiento esperado para scripts de fondo)"
                    )
                except HTTPException:
                    # Re-lanzar excepciones HTTP (como la de validación de tenant)
                    raise
                except Exception as e:
                    # Si hay cualquier otro error en la validación, loggear pero NO bloquear
                    # Esto previene que errores en la validación rompan el sistema
                    logger.error(
                        f"[SECURITY] Error en validación de tenant (no bloqueante): {str(e)}",
                        exc_info=True
                    )

        except JWTError as e:
            logger.error(f"Error decodificando token: {str(e)}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"Error procesando payload del token: {str(e)}")
            raise credentials_exception

        # ✅ CORRECCIÓN: Buscar usuario en BD apropiada
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        
        # Query base (sin filtro de cliente_id para BD dedicadas)
        query = """
        SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        
        # ✅ FASE 2: Usar await
        if es_superadmin:
            # Superadmin: Buscar en BD ADMIN
            result = await execute_query(
                text(query.replace("?", ":username")).bindparams(username=username),
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )
            user = result[0] if result else None
            
            # Agregar contexto multi-tenant
            if user:
                user['target_cliente_id'] = target_cliente_id
                user['es_superadmin'] = True
        else:
            # Usuario regular: Buscar en BD del contexto
            # ✅ Para BD dedicadas, execute_auth_query ya busca sin cliente_id
            user = await execute_auth_query(query, (username,))

        if not user:
            raise credentials_exception

        if not user['es_activo']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo"
            )
        
        # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
        # Usar el cliente_id del token o del contexto en su lugar
        if database_type == "multi":
            # Convertir cliente_id del usuario a UUID si es string para comparar
            user_cliente_id = user.get('cliente_id')
            if user_cliente_id:
                if isinstance(user_cliente_id, str):
                    try:
                        user_cliente_id = UUID(user_cliente_id)
                    except (ValueError, AttributeError):
                        user_cliente_id = None
                elif not isinstance(user_cliente_id, UUID):
                    user_cliente_id = None
            
            # Verificar si es None o UUID nulo
            if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                if token_cliente_id:
                    # Convertir token_cliente_id a UUID si es string
                    if isinstance(token_cliente_id, str):
                        try:
                            user['cliente_id'] = UUID(token_cliente_id)
                        except (ValueError, AttributeError):
                            # Si falla, usar el contexto actual
                            from app.core.tenant.context import try_get_current_client_id
                            user['cliente_id'] = try_get_current_client_id()
                    else:
                        user['cliente_id'] = token_cliente_id
                    logger.debug(
                        f"[AUTH] BD dedicada: cliente_id del usuario era NULL/nulo, "
                        f"usando cliente_id del token: {user['cliente_id']}"
                    )
                else:
                    # Si no hay cliente_id en el token, usar el contexto actual
                    from app.core.tenant.context import try_get_current_client_id
                    user['cliente_id'] = try_get_current_client_id()
                    logger.debug(
                        f"[AUTH] BD dedicada: cliente_id del usuario y token eran NULL/nulo, "
                        f"usando cliente_id del contexto: {user['cliente_id']}"
                    )
            else:
                user['cliente_id'] = user_cliente_id
        
        # ✅ AGREGAR CAMPOS DE NIVEL AL USUARIO
        user['access_level'] = access_level
        user['is_super_admin'] = is_super_admin
        user['user_type'] = user_type
        from app.core.tenant.empresa_context import coerce_empresa_id
        user['empresa_id'] = coerce_empresa_id(payload.get('empresa_id'))

        return user
    
    @staticmethod
    async def get_current_user_from_refresh(
        request: Request,
        refresh_token_cookie: Optional[str] = None,
        refresh_token_body: Optional[str] = None
    ) -> Dict:
        """
        Obtiene el usuario actual validando el refresh token.
        
        ✅ CORRECCIÓN: **Verifica el estado de revocación del token en la BD** antes de retornar, previniendo el reuso de tokens cerrados o expirados.
        
        - WEB: Lee desde cookie HttpOnly
        - MÓVIL: Lee desde body JSON (con el header X-Client-Type: mobile)
        - Usa REFRESH_SECRET_KEY para validación JWT
        - AHORA INCLUYE: access_level, is_super_admin, user_type del token
        """
        # Detectar tipo de cliente
        client_type = request.headers.get("X-Client-Type", "web").lower()
        
        # Obtener el refresh token según el tipo de cliente
        refresh_token = None
        if client_type == "web":
            refresh_token = refresh_token_cookie
            logger.debug("[REFRESH] Leyendo token desde cookie (WEB)")
        else:  # mobile
            refresh_token = refresh_token_body
            logger.debug("[REFRESH] Leyendo token desde body (MOBILE)")
        
        if not refresh_token:
            logger.warning(f"[REFRESH] No se proporcionó refresh token. Cliente: {client_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token provided"
            )

        try:
            # 1. Validación JWT (firma y expiración de 7 días)
            payload = decode_refresh_token(refresh_token)
            token_cliente_id = AuthService._coerce_uuid(payload.get("cliente_id"))

            # 2. ✅ CRÍTICO: VALIDACIÓN DE ESTADO EN BASE DE DATOS
            # Fuente de verdad: cliente_id del JWT (no solo Host/Origin del request).
            # En platform, refresh suele ir a backend.* sin subdominio → contexto ACME erróneo.
            db_token_data = await RefreshTokenService.validate_refresh_token(
                refresh_token,
                cliente_id=token_cliente_id,
            )

            if not db_token_data:
                # Si el servicio retorna None, significa que está revocado, expirado, o no existe
                username = payload.get("sub")
                logger.warning(
                    f"[REFRESH] Token JWT válido, pero inactivo/revocado en BD. Usuario: {username}"
                )
                # Registrar evento de token inválido/expirado en auditoría
                try:
                    # ✅ registrar_auth_event ahora maneja la conversión automáticamente
                    await AuditService.registrar_auth_event(
                        cliente_id=payload.get("cliente_id"),
                        usuario_id=None,
                        evento="token_invalid_or_revoked",
                        nombre_usuario_intento=username,
                        descripcion="Refresh token inválido, expirado o revocado en base de datos",
                        exito=False,
                        codigo_error="REFRESH_TOKEN_INVALID_DB",
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        metadata={"client_type": client_type},
                    )
                except Exception:
                    logger.exception(
                        "[AUDIT] Error registrando evento token_invalid_or_revoked (no crítico)"
                    )

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Sesión expirada o cerrada remotamente. Por favor, vuelva a iniciar sesión."
                )
            
            # 3. Obtener datos del usuario (TokenPayload debe aceptar platform_admin)
            try:
                token_data = TokenPayload(**payload)
            except Exception as validation_err:
                logger.error(
                    "[REFRESH] Payload JWT refresh inválido para usuario %s: %s",
                    payload.get("sub"),
                    validation_err,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token payload",
                ) from validation_err

            if not token_data.sub:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token payload"
                )

            username = token_data.sub

            from app.core.tenant.context import try_get_tenant_context

            tenant_context = try_get_tenant_context()
            database_type = tenant_context.database_type if tenant_context else "single"

            user = await AuthService._fetch_user_row_for_refresh(
                username,
                payload=payload,
                token_cliente_id=token_cliente_id,
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado"
                )

            if not user['es_activo']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario inactivo"
                )
            
            # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
            # Usar el cliente_id del token o del contexto en su lugar
            if database_type == "multi":
                # Convertir cliente_id del usuario a UUID si es string para comparar
                user_cliente_id = user.get('cliente_id')
                if user_cliente_id:
                    if isinstance(user_cliente_id, str):
                        try:
                            user_cliente_id = UUID(user_cliente_id)
                        except (ValueError, AttributeError):
                            user_cliente_id = None
                    elif not isinstance(user_cliente_id, UUID):
                        user_cliente_id = None
                
                # Verificar si es None o UUID nulo
                if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                    if token_cliente_id:
                        # Convertir token_cliente_id a UUID si es string
                        if isinstance(token_cliente_id, str):
                            try:
                                user['cliente_id'] = UUID(token_cliente_id)
                            except (ValueError, AttributeError):
                                # Si falla, usar el contexto actual
                                from app.core.tenant.context import try_get_current_client_id
                                user['cliente_id'] = try_get_current_client_id()
                        else:
                            user['cliente_id'] = token_cliente_id
                        logger.debug(
                            f"[REFRESH] BD dedicada: cliente_id del usuario era NULL/nulo, "
                            f"usando cliente_id del token: {user['cliente_id']}"
                        )
                    else:
                        # Si no hay cliente_id en el token, usar el contexto actual
                        from app.core.tenant.context import try_get_current_client_id
                        user['cliente_id'] = try_get_current_client_id()
                        logger.debug(
                            f"[REFRESH] BD dedicada: cliente_id del usuario y token eran NULL/nulo, "
                            f"usando cliente_id del contexto: {user['cliente_id']}"
                        )
                else:
                    user['cliente_id'] = user_cliente_id
            elif token_cliente_id:
                user["cliente_id"] = token_cliente_id

            # ✅ AGREGAR CAMPOS DE NIVEL AL USUARIO DESDE EL TOKEN
            user['access_level'] = payload.get('access_level', 1)
            user['is_super_admin'] = payload.get('is_super_admin', False)
            user['user_type'] = payload.get('user_type', 'user')
            from app.core.tenant.empresa_context import coerce_empresa_id

            # ✅ BLOQUE 5: empresa_id desde refresh_tokens (BD); JWT solo como fallback legacy
            db_empresa_id = coerce_empresa_id(db_token_data.get("empresa_id"))
            jwt_empresa_id = coerce_empresa_id(payload.get("empresa_id"))
            user["empresa_id"] = db_empresa_id if db_empresa_id is not None else jwt_empresa_id

            logger.info(
                f"[REFRESH] Token validado exitosamente (BD OK) para usuario: {username} "
                f"(Cliente: {user['cliente_id']}, Level: {user['access_level']}, "
                f"Type: {user['user_type']}, Empresa: {user['empresa_id']})"
            )
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "[REFRESH] Error validando refresh token: %s",
                e,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    
    @staticmethod
    async def blacklist_access_token_jti(jti: str, exp: Optional[int]) -> None:
        """Invalida un access token por jti (p. ej. selection token tras seleccionar empresa)."""
        if not jti:
            return
        try:
            from app.infrastructure.redis.client import RedisService

            now_ts = int(datetime.utcnow().timestamp())
            ttl = 900
            if exp is not None:
                ttl = max(int(exp) - now_ts, 60)
            await RedisService.set_token_blacklist(jti, ttl)
        except Exception as e:
            logger.warning(
                "[AUTH] No se pudo blacklistear jti %s (fail-soft): %s", jti, e
            )

    @staticmethod
    async def validar_empresa_para_sesion(
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: UUID,
    ) -> None:
        """
        Valida que empresa_id esté asignada al usuario, activa y del mismo tenant.

        Raises:
            HTTPException 400: empresa no asignada al usuario
            HTTPException 403: empresa inactiva o de otro cliente
        """
        from app.infrastructure.database.tables_erp import OrgEmpresaTable
        from sqlalchemy import select, and_

        empresas_ctx = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )
        disponibles = set(
            AuthService._empresa_ids_disponibles(
                empresas_ctx.get("empresas_disponibles") or []
            )
        )
        if empresa_id not in disponibles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa indicada no está asignada a este usuario",
            )

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
    async def construir_user_data_sesion(
        *,
        username: str,
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: Optional[UUID],
        es_superadmin: bool = False,
        user_base_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Arma user_data alineado con login/refresh para Token.user_data."""
        from app.modules.users.application.services.user_service import UsuarioService
        from app.core.auth import get_user_access_level_info

        if es_superadmin:
            user_role_names = ["Super Administrador"]
        else:
            user_role_names = await UsuarioService.get_user_role_names(
                cliente_id, usuario_id, empresa_id=empresa_id
            )

        level_info = await AuthService.get_user_access_level_info(
            usuario_id, cliente_id, empresa_id=empresa_id
        )
        es_admin_cliente = await AuthService.usuario_tiene_es_admin_cliente(
            usuario_id, cliente_id, empresa_id
        )

        from app.modules.auth.presentation.schemas import build_user_data_with_roles_dict

        profile = build_user_data_with_roles_dict(
            usuario_id=usuario_id,
            nombre_usuario=username,
            correo=(user_base_data or {}).get("correo", ""),
            nombre=(user_base_data or {}).get("nombre"),
            apellido=(user_base_data or {}).get("apellido"),
            es_activo=(user_base_data or {}).get("es_activo", True),
            roles=user_role_names,
            access_level=level_info.get("access_level", 1),
            is_super_admin=level_info.get("is_super_admin", False),
            user_type=level_info.get("user_type", "user"),
            cliente_id=cliente_id,
            es_admin_cliente=es_admin_cliente,
            empresa_activa=(
                str(empresa_id) if empresa_id is not None else None
            ),
        )
        profile["level_info"] = level_info
        return profile

    @staticmethod
    async def emitir_sesion_completa_con_empresa(
        *,
        username: str,
        usuario_id: UUID,
        cliente_id: UUID,
        empresa_id: UUID,
        es_superadmin: bool = False,
        user_base_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Genera access + refresh JWT con empresa_id y user_data (sin selection pending).
        """
        user_full_data = await AuthService.construir_user_data_sesion(
            username=username,
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            empresa_id=empresa_id,
            es_superadmin=es_superadmin,
            user_base_data=user_base_data,
        )
        level_info = user_full_data.pop("level_info", None) or await AuthService.get_user_access_level_info(
            usuario_id, cliente_id, empresa_id=empresa_id
        )
        es_admin_cliente = user_full_data.get("es_admin_cliente", False)

        token_data: Dict[str, Any] = {
            "sub": username,
            "cliente_id": str(cliente_id),
            "level_info": level_info,
        }
        if es_superadmin:
            token_data["es_superadmin"] = True

        token_expiration = await AuthService.get_token_expiration_for_cliente(cliente_id)
        access_expire_minutes = token_expiration["access_token_minutes"]
        refresh_expire_days = token_expiration["refresh_token_days"]

        access_token, _access_jti = create_access_token(
            data=token_data,
            empresa_id=empresa_id,
            es_admin_cliente=es_admin_cliente,
            access_token_expire_minutes=access_expire_minutes,
        )
        refresh_token, _refresh_jti = create_refresh_token(
            data=token_data,
            empresa_id=empresa_id,
            es_admin_cliente=es_admin_cliente,
            refresh_token_expire_days=refresh_expire_days,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_data": user_full_data,
            "access_expire_minutes": access_expire_minutes,
            "refresh_expire_days": refresh_expire_days,
        }

    @staticmethod
    async def seleccionar_empresa_post_login(
        *,
        payload: Dict[str, Any],
        empresa_id: UUID,
        client_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> Dict[str, Any]:
        """
        Cierra el flujo de login multi-empresa: valida empresa, emite sesión completa,
        persiste refresh y blacklistea el selection token.

        Impersonación: solo access token (120 min), sin refresh; conserva claims.
        """
        from app.core.auth.impersonation import is_impersonation_payload
        from app.modules.auth.application.services.impersonation_service import (
            ImpersonationService,
        )

        if is_impersonation_payload(payload):
            return await ImpersonationService.seleccionar_empresa_impersonacion(
                payload=payload,
                empresa_id=empresa_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        from app.core.auth.user_context import get_user_auth_context, validate_tenant_access

        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        token_cliente_id = AuthService._coerce_uuid(payload.get("cliente_id"))
        if not token_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sin contexto de tenant",
            )

        try:
            request_cliente_id = get_current_client_id()
        except RuntimeError:
            request_cliente_id = token_cliente_id

        if request_cliente_id != token_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: token no válido para este tenant",
            )

        context = await get_user_auth_context(username, request_cliente_id)
        if not context or not context.es_activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
            )

        if not await validate_tenant_access(context, request_cliente_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: token no válido para este tenant",
            )

        await AuthService.validar_empresa_para_sesion(
            context.usuario_id, request_cliente_id, empresa_id
        )

        from app.core.tenant.empresa_preference import persist_usuario_empresa_default_id

        await persist_usuario_empresa_default_id(
            context.usuario_id, request_cliente_id, empresa_id
        )

        es_superadmin = bool(payload.get("es_superadmin"))
        session = await AuthService.emitir_sesion_completa_con_empresa(
            username=username,
            usuario_id=context.usuario_id,
            cliente_id=request_cliente_id,
            empresa_id=empresa_id,
            es_superadmin=es_superadmin,
        )

        refresh_expire_days = session["refresh_expire_days"]
        stored = await RefreshTokenService.store_refresh_token(
            cliente_id=request_cliente_id,
            usuario_id=context.usuario_id,
            token=session["refresh_token"],
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            is_rotation=False,
            empresa_id=empresa_id,
            refresh_token_expire_days=refresh_expire_days,
        )
        if not stored or not stored.get("token_id"):
            logger.warning(
                "[EMPRESA] Refresh no almacenado tras seleccionar empresa usuario=%s",
                username,
            )

        selection_jti = payload.get("jti")
        await AuthService.blacklist_access_token_jti(
            selection_jti, payload.get("exp")
        )

        try:
            await AuditService.registrar_auth_event(
                cliente_id=request_cliente_id,
                usuario_id=context.usuario_id,
                evento="empresa_seleccionada",
                nombre_usuario_intento=username,
                descripcion="Empresa seleccionada tras login multi-empresa",
                exito=True,
                codigo_error=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "empresa_id_anterior": None,
                    "empresa_id_nueva": str(empresa_id),
                    "client_type": client_type,
                    "selection_jti": selection_jti,
                },
            )
        except Exception:
            logger.exception("[AUDIT] Error registrando empresa_seleccionada")

        return session

    @staticmethod
    async def cambiar_empresa_sesion(
        *,
        payload: Dict[str, Any],
        empresa_id: UUID,
        client_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        old_refresh_token: Optional[str],
    ) -> Dict[str, Any]:
        """
        Cambia empresa activa en sesión existente (rota refresh si se proporciona).
        """
        from app.core.auth.user_context import get_user_auth_context, validate_tenant_access
        from app.core.tenant.empresa_context import coerce_empresa_id

        from app.core.auth.impersonation import is_impersonation_payload

        if is_impersonation_payload(payload):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No se puede cambiar de empresa durante una sesión de "
                    "impersonación de soporte. Finalice la impersonación o seleccione "
                    "la empresa con POST /api/v1/auth/empresa/seleccionar/."
                ),
            )

        if payload.get("empresa_selection_pending"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Debe completar la selección de empresa con "
                    "POST /api/v1/auth/empresa/seleccionar/ antes de cambiar de empresa."
                ),
            )

        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        token_cliente_id = AuthService._coerce_uuid(payload.get("cliente_id"))
        if not token_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sin contexto de tenant",
            )

        try:
            request_cliente_id = get_current_client_id()
        except RuntimeError:
            request_cliente_id = token_cliente_id

        if request_cliente_id != token_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: token no válido para este tenant",
            )

        context = await get_user_auth_context(username, request_cliente_id)
        if not context or not context.es_activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
            )

        if not await validate_tenant_access(context, request_cliente_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: token no válido para este tenant",
            )

        empresa_anterior = coerce_empresa_id(payload.get("empresa_id"))

        await AuthService.validar_empresa_para_sesion(
            context.usuario_id, request_cliente_id, empresa_id
        )

        from app.core.tenant.empresa_preference import persist_usuario_empresa_default_id

        await persist_usuario_empresa_default_id(
            context.usuario_id, request_cliente_id, empresa_id
        )

        if empresa_anterior == empresa_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa indicada ya es la empresa activa de la sesión",
            )

        es_superadmin = bool(payload.get("es_superadmin"))
        session = await AuthService.emitir_sesion_completa_con_empresa(
            username=username,
            usuario_id=context.usuario_id,
            cliente_id=request_cliente_id,
            empresa_id=empresa_id,
            es_superadmin=es_superadmin,
        )

        refresh_expire_days = session["refresh_expire_days"]
        stored = await RefreshTokenService.store_refresh_token(
            cliente_id=request_cliente_id,
            usuario_id=context.usuario_id,
            token=session["refresh_token"],
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            is_rotation=True,
            empresa_id=empresa_id,
            refresh_token_expire_days=refresh_expire_days,
        )

        if old_refresh_token and stored and not stored.get("duplicate_ignored"):
            try:
                await RefreshTokenService.revoke_token(
                    cliente_id=request_cliente_id,
                    usuario_id=context.usuario_id,
                    token=old_refresh_token,
                )
            except Exception as revoke_err:
                logger.warning(
                    "[EMPRESA] Error revocando refresh anterior al cambiar empresa: %s",
                    revoke_err,
                )

        try:
            await AuditService.registrar_auth_event(
                cliente_id=request_cliente_id,
                usuario_id=context.usuario_id,
                evento="empresa_cambiada",
                nombre_usuario_intento=username,
                descripcion="Cambio de empresa activa en sesión",
                exito=True,
                codigo_error=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "empresa_id_anterior": (
                        str(empresa_anterior) if empresa_anterior else None
                    ),
                    "empresa_id_nueva": str(empresa_id),
                    "client_type": client_type,
                },
            )
        except Exception:
            logger.exception("[AUDIT] Error registrando empresa_cambiada")

        return session

    @staticmethod
    async def _extract_refresh_token_for_logout(
        request: Request,
        client_type: str,
    ) -> Optional[str]:
        """Cookie HttpOnly (web) o body JSON refresh_token (mobile)."""
        if client_type == "web":
            return request.cookies.get(settings.REFRESH_COOKIE_NAME)
        try:
            body = await request.json()
            if isinstance(body, dict):
                return body.get("refresh_token")
        except Exception:
            pass
        return None

    @staticmethod
    async def perform_logout(
        *,
        request: Request,
        client_type: str = "web",
    ) -> Dict[str, Any]:
        """
        Cierra sesión: revoca refresh en BD y opcionalmente blacklistea access.

        - cliente_id del JWT refresh (no solo contexto Host), igual que /auth/refresh/.
        - Idempotente: siempre seguro llamar aunque el token ya esté revocado.
        - Fail-soft en JWT inválido: el caller igualmente limpia cookies.
        """
        from app.core.security.jwt import normalize_bearer_jwt_token
        from jose import jwt as jose_jwt

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        refresh_token = await AuthService._extract_refresh_token_for_logout(
            request, client_type
        )

        outcome: Dict[str, Any] = {
            "refresh_revoked": False,
            "access_blacklisted": False,
            "had_refresh_token": bool(refresh_token),
            "client_type": client_type,
        }

        if refresh_token:
            try:
                payload = decode_refresh_token(refresh_token)
                token_cliente_id = AuthService._coerce_uuid(payload.get("cliente_id"))
                username = payload.get("sub")
                usuario_id: Optional[UUID] = None

                if token_cliente_id:
                    db_row = await RefreshTokenService.validate_refresh_token(
                        refresh_token,
                        cliente_id=token_cliente_id,
                    )
                    if db_row:
                        usuario_id = AuthService._coerce_uuid(db_row.get("usuario_id"))

                    if not usuario_id and username:
                        user = await AuthService._fetch_user_row_for_refresh(
                            username,
                            payload=payload,
                            token_cliente_id=token_cliente_id,
                        )
                        if user:
                            usuario_id = AuthService._coerce_uuid(
                                user.get("usuario_id")
                            )

                    if usuario_id:
                        outcome["refresh_revoked"] = (
                            await RefreshTokenService.revoke_token(
                                token_cliente_id,
                                usuario_id,
                                refresh_token,
                            )
                        )
                    else:
                        from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
                            revoke_refresh_token_core,
                        )

                        token_hash = RefreshTokenService.hash_token(refresh_token)
                        rev = await revoke_refresh_token_core(
                            token_hash, token_cliente_id
                        )
                        outcome["refresh_revoked"] = bool(rev)

                    try:
                        await AuditService.registrar_auth_event(
                            cliente_id=token_cliente_id,
                            usuario_id=usuario_id,
                            evento="logout",
                            nombre_usuario_intento=username,
                            descripcion="Logout de sesión (refresh revocado en BD)",
                            exito=True,
                            codigo_error=None,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            metadata={
                                "client_type": client_type,
                                "token_revoked": outcome["refresh_revoked"],
                            },
                        )
                    except Exception:
                        logger.exception(
                            "[AUDIT] Error registrando logout (no crítico)"
                        )

                    logger.info(
                        "[LOGOUT-%s] refresh_revoked=%s user=%s cliente=%s",
                        client_type.upper(),
                        outcome["refresh_revoked"],
                        username,
                        token_cliente_id,
                    )
            except HTTPException:
                logger.info(
                    "[LOGOUT-%s] Refresh JWT inválido; solo limpieza de cookies",
                    client_type.upper(),
                )
            except Exception as e:
                logger.warning(
                    "[LOGOUT-%s] Error revocando refresh (fail-soft): %s",
                    client_type.upper(),
                    e,
                )
        else:
            logger.info(
                "[LOGOUT-%s] Sin refresh token en cookie/body",
                client_type.upper(),
            )

        auth_header = request.headers.get("authorization") or ""
        if auth_header.lower().startswith("bearer "):
            try:
                raw = normalize_bearer_jwt_token(
                    auth_header.split(" ", 1)[1].strip()
                )
                access_payload = jose_jwt.decode(
                    raw,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                jti = access_payload.get("jti")
                if jti:
                    await AuthService.blacklist_access_token_jti(
                        jti, access_payload.get("exp")
                    )
                    outcome["access_blacklisted"] = True
            except Exception as e:
                logger.debug(
                    "[LOGOUT] Access token no blacklisteado (fail-soft): %s", e
                )

        return outcome

    @staticmethod
    async def revoke_session_by_token_id(token_id: str) -> None:
        """
        Revoca un refresh token específico en la base de datos por su ID (jti).
        Esta función es utilizada por los endpoints de cierre de sesión/revocación.
        """
        try:
            await RefreshTokenService.revoke_refresh_token_by_id(token_id)
            logger.info(f"Sesión con ID '{token_id}' revocada exitosamente.")
        except Exception as e:
            logger.error(f"Error al revocar sesión con ID '{token_id}': {str(e)}", exc_info=True)
            # La lógica de la ruta debe manejar el error, aquí solo loggeamos.
            # No levantamos HTTPException aquí.
    
    @staticmethod
    async def get_all_active_sessions(user_id: int) -> list[Dict]:
        """
        Obtiene todas las sesiones (refresh tokens) activas para un usuario.
        Retorna los datos de la BD listos para ser usados en la capa de API.
        """
        try:
            return await RefreshTokenService.get_all_active_sessions(user_id)
        except Exception as e:
            logger.error(f"Error al obtener sesiones activas para usuario {user_id}: {str(e)}", exc_info=True)
            # En caso de error, retornamos lista vacía.
            return []


# ✅ FUNCIONES DE COMPATIBILIDAD: Mantener funciones globales para no romper imports existentes
# Estas funciones son wrappers que llaman a AuthService

async def authenticate_user(cliente_id: int, username: str, password: str) -> Dict:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.authenticate_user(cliente_id, username, password)

async def authenticate_user_sso_azure_ad(cliente_id: int, token: str) -> Dict:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.authenticate_user_sso_azure_ad(cliente_id, token)

async def authenticate_user_sso_google(cliente_id: int, token: str) -> Dict:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.authenticate_user_sso_google(cliente_id, token)

async def get_user_access_level_info(
    usuario_id: int,
    cliente_id: int,
    empresa_id: Optional[UUID] = None,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.get_user_access_level_info(
        usuario_id, cliente_id, empresa_id=empresa_id, username=username
    )


async def get_empresa_activa_para_login(
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    payload: Optional[Dict[str, Any]] = None,
    es_superadmin: Optional[bool] = None,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrapper para resolución de empresa en login."""
    return await AuthService.get_empresa_activa_para_login(
        usuario_id,
        cliente_id,
        payload=payload,
        es_superadmin=es_superadmin,
        user_type=user_type,
    )


async def usuario_tiene_es_admin_cliente(
    usuario_id: UUID,
    cliente_id: UUID,
    empresa_id: Optional[UUID] = None,
    username: Optional[str] = None,
) -> bool:
    """Wrapper para flag es_admin_cliente en login/JWT."""
    return await AuthService.usuario_tiene_es_admin_cliente(
        usuario_id, cliente_id, empresa_id, username=username
    )


async def get_token_expiration_for_cliente(cliente_id: UUID) -> Dict[str, int]:
    """Wrapper para expiración de tokens por tenant."""
    return await AuthService.get_token_expiration_for_cliente(cliente_id)

async def revoke_session_by_token_id(token_id: str) -> None:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.revoke_session_by_token_id(token_id)

async def get_all_active_sessions(user_id: int) -> list[Dict]:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.get_all_active_sessions(user_id)

