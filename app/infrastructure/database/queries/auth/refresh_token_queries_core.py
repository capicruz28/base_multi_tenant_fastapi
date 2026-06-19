"""
Queries SQLAlchemy Core para Refresh Tokens (Migración desde TextClause).

✅ FASE 1 SEGURIDAD: Queries críticas migradas a SQLAlchemy Core para máxima seguridad.
- Filtro automático de tenant garantizado
- Type safety mejorado
- Mejor mantenibilidad

QUERIES INCLUIDAS:
- get_refresh_token_by_hash_core()
- insert_refresh_token_core()
- revoke_refresh_token_core()

USO:
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        get_refresh_token_by_hash_core
    )
    
    token_data = await get_refresh_token_by_hash_core(token_hash, cliente_id)
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, func, and_, or_

from app.infrastructure.database.tables import RefreshTokensTable
# Importaciones tardías para evitar circular imports
import logging

logger = logging.getLogger(__name__)


async def record_refresh_token_activity_core(
    token_id: UUID,
    cliente_id: UUID,
) -> bool:
    """
    Actualiza last_used_at y uso_count tras validación exitosa del refresh token.

    Returns:
        True si se actualizó al menos una fila.
    """
    from app.infrastructure.database.queries_async import execute_update

    query = (
        update(RefreshTokensTable)
        .where(
            and_(
                RefreshTokensTable.c.token_id == token_id,
                RefreshTokensTable.c.cliente_id == cliente_id,
                RefreshTokensTable.c.is_revoked == False,  # noqa: E712
            )
        )
        .values(
            last_used_at=func.getdate(),
            uso_count=func.coalesce(RefreshTokensTable.c.uso_count, 0) + 1,
        )
    )

    result = await execute_update(query, client_id=cliente_id)
    return result.get("rows_affected", 0) > 0


async def is_refresh_token_session_idle_expired_core(
    token_id: UUID,
    cliente_id: UUID,
    idle_timeout_minutes: int,
) -> bool:
    """
    Evalúa idle timeout usando únicamente GETDATE() de SQL Server y los timestamps
    persistidos en la fila (last_used_at o created_at).

    Evita comparar datetime Python (UTC) contra timestamps SQL (local GETDATE).
    """
    if not idle_timeout_minutes or idle_timeout_minutes <= 0:
        return False

    from app.infrastructure.database.queries_async import execute_query
    from sqlalchemy import text

    query = text("""
        SELECT CASE
            WHEN COALESCE(last_used_at, created_at) IS NULL THEN 0
            WHEN DATEDIFF(
                minute,
                COALESCE(last_used_at, created_at),
                GETDATE()
            ) > :idle_timeout_minutes THEN 1
            ELSE 0
        END AS idle_expired
        FROM refresh_tokens
        WHERE token_id = :token_id
          AND cliente_id = :cliente_id
    """).bindparams(
        token_id=token_id,
        cliente_id=cliente_id,
        idle_timeout_minutes=idle_timeout_minutes,
    )

    results = await execute_query(query, client_id=cliente_id)
    if not results:
        return False
    return bool(results[0].get("idle_expired", 0))


async def get_refresh_token_by_hash_any_state_core(
    token_hash: str,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un refresh token por hash sin filtrar revocado/expirado.

    Usado para detectar reutilización de tokens previamente revocados.
    """
    from app.infrastructure.database.queries_async import execute_query

    query = select(
        RefreshTokensTable.c.token_id,
        RefreshTokensTable.c.usuario_id,
        RefreshTokensTable.c.token_hash,
        RefreshTokensTable.c.expires_at,
        RefreshTokensTable.c.is_revoked,
        RefreshTokensTable.c.cliente_id,
        RefreshTokensTable.c.revoked_reason,
    ).where(
        and_(
            RefreshTokensTable.c.token_hash == token_hash,
            RefreshTokensTable.c.cliente_id == cliente_id,
        )
    )

    results = await execute_query(query, client_id=cliente_id)
    if results:
        return results[0]
    return None


async def get_refresh_token_by_hash_core(
    token_hash: str,
    cliente_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un refresh token por su hash usando SQLAlchemy Core.
    
    ✅ FASE 1 SEGURIDAD: Migrado a SQLAlchemy Core para filtro automático garantizado.
    
    Args:
        token_hash: Hash del token a buscar
        cliente_id: ID del cliente (tenant)
    
    Returns:
        Diccionario con datos del token o None si no existe/está revocado/expirado
    
    Example:
        ```python
        token_data = await get_refresh_token_by_hash_core(token_hash, cliente_id)
        if token_data:
            print(f"Token válido para usuario {token_data['usuario_id']}")
        ```
    """
    # Importación tardía para evitar circular imports
    from app.infrastructure.database.queries_async import execute_query
    
    query = select(
        RefreshTokensTable.c.token_id,
        RefreshTokensTable.c.usuario_id,
        RefreshTokensTable.c.token_hash,
        RefreshTokensTable.c.expires_at,
        RefreshTokensTable.c.is_revoked,
        RefreshTokensTable.c.created_at,
        RefreshTokensTable.c.last_used_at,
        RefreshTokensTable.c.client_type,
        RefreshTokensTable.c.cliente_id,
        RefreshTokensTable.c.empresa_id,
    ).where(
        and_(
            RefreshTokensTable.c.token_hash == token_hash,
            RefreshTokensTable.c.cliente_id == cliente_id,  # ✅ Filtro explícito + automático
            RefreshTokensTable.c.is_revoked == False,
            RefreshTokensTable.c.expires_at > func.getdate()
        )
    )
    
    results = await execute_query(query, client_id=cliente_id)
    
    if results and len(results) > 0:
        return results[0]
    return None


async def insert_refresh_token_core(
    usuario_id: UUID,
    token_hash: str,
    expires_at: datetime,
    cliente_id: UUID,
    client_type: str = "web",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_name: Optional[str] = None,
    device_id: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Inserta un nuevo refresh token usando SQLAlchemy Core.
    
    ✅ FASE 1 SEGURIDAD: Migrado a SQLAlchemy Core para filtro automático garantizado.
    
    Args:
        usuario_id: ID del usuario
        token_hash: Hash del token
        expires_at: Fecha de expiración
        cliente_id: ID del cliente (tenant)
        client_type: Tipo de cliente (web, mobile, etc.)
        ip_address: IP del cliente (opcional)
        user_agent: User agent del cliente (opcional)
        device_name: Nombre del dispositivo (opcional)
        device_id: ID del dispositivo (opcional)
        empresa_id: Empresa activa de la sesión (opcional)
    
    Returns:
        Diccionario con datos del token insertado (incluye token_id)
    
    Note:
        SQL Server OUTPUT clause se maneja mediante execute_insert que retorna los datos insertados.
    
    Example:
        ```python
        result = await insert_refresh_token_core(
            usuario_id=usuario_id,
            token_hash=token_hash,
            expires_at=expires_at,
            cliente_id=cliente_id,
            client_type="web"
        )
        token_id = result['token_id']
        ```
    """
    # Importación tardía para evitar circular imports
    from app.infrastructure.database.queries_async import execute_insert
    from sqlalchemy import text
    
    # SQLAlchemy Core no soporta OUTPUT directamente en Insert
    # Usamos text() para OUTPUT pero con validación de tenant garantizada
    # Query con OUTPUT usando text() pero con parámetros seguros
    # El filtro automático se aplicará aunque sea TextClause
    query = text("""
        INSERT INTO refresh_tokens (
            usuario_id, token_hash, expires_at, client_type,
            ip_address, user_agent, cliente_id, empresa_id, device_name, device_id
        )
        OUTPUT INSERTED.token_id, INSERTED.usuario_id, INSERTED.cliente_id,
               INSERTED.empresa_id, INSERTED.expires_at, INSERTED.created_at
        VALUES (:usuario_id, :token_hash, :expires_at, :client_type,
                :ip_address, :user_agent, :cliente_id, :empresa_id, :device_name, :device_id)
    """).bindparams(
        usuario_id=usuario_id,
        token_hash=token_hash,
        expires_at=expires_at,
        client_type=client_type,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        cliente_id=cliente_id,  # ✅ Filtro explícito
        empresa_id=empresa_id,
        device_name=device_name,
        device_id=device_id
    )
    
    result = await execute_insert(query, client_id=cliente_id)
    return result


async def revoke_refresh_token_core(
    token_hash: str,
    cliente_id: UUID,
    revoked_reason: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Revoca un refresh token por su hash usando SQLAlchemy Core.
    
    ✅ FASE 1 SEGURIDAD: Migrado a SQLAlchemy Core para filtro automático garantizado.
    
    Args:
        token_hash: Hash del token a revocar
        cliente_id: ID del cliente (tenant)
    
    Returns:
        Diccionario con datos del token revocado o None si no existe
    
    Example:
        ```python
        result = await revoke_refresh_token_core(token_hash, cliente_id)
        if result:
            print(f"Token {result['token_id']} revocado")
        ```
    """
    # Importación tardía para evitar circular imports
    from app.infrastructure.database.queries_async import execute_update
    from sqlalchemy import text
    
    # SQLAlchemy Core no soporta OUTPUT directamente en Update
    # Usamos text() para OUTPUT pero con validación de tenant garantizada
    query = text("""
        UPDATE refresh_tokens
        SET is_revoked = 1, revoked_at = GETDATE(), revoked_reason = :revoked_reason
        OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
        WHERE token_hash = :token_hash
          AND cliente_id = :cliente_id
    """).bindparams(
        token_hash=token_hash,
        cliente_id=cliente_id,
        revoked_reason=revoked_reason,
    )
    
    result = await execute_update(query, client_id=cliente_id)
    
    # execute_update con OUTPUT retorna los datos del OUTPUT cuando result.returns_rows es True
    # Si hay OUTPUT, los datos están en el dict result directamente
    if result.get("rows_affected", 0) > 0:
        # Si hay datos del OUTPUT, retornarlos directamente
        if "token_id" in result:
            return {
                "token_id": result.get("token_id"),
                "is_revoked": result.get("is_revoked", True),
                "cliente_id": result.get("cliente_id", cliente_id)
            }
        else:
            # Si no hay OUTPUT pero rows_affected > 0, el token fue revocado
            return {
                "token_id": None,
                "is_revoked": True,
                "cliente_id": cliente_id
            }
    
    return None


async def revoke_all_user_tokens_core(
    usuario_id: UUID,
    cliente_id: UUID,
    revoked_reason: Optional[str] = None,
) -> int:
    """
    Revoca todos los tokens activos de un usuario usando SQLAlchemy Core.
    
    ✅ FASE 1 SEGURIDAD: Migrado a SQLAlchemy Core para filtro automático garantizado.
    
    Args:
        usuario_id: ID del usuario
        cliente_id: ID del cliente (tenant)
    
    Returns:
        Número de tokens revocados
    
    Example:
        ```python
        count = await revoke_all_user_tokens_core(usuario_id, cliente_id)
        print(f"{count} tokens revocados")
        ```
    """
    # Importación tardía para evitar circular imports
    from app.infrastructure.database.queries_async import execute_update
    
    query = update(RefreshTokensTable).where(
        and_(
            RefreshTokensTable.c.usuario_id == usuario_id,
            RefreshTokensTable.c.cliente_id == cliente_id,  # ✅ Filtro explícito + automático
            RefreshTokensTable.c.is_revoked == False
        )
    ).values(
        is_revoked=True,
        revoked_at=func.getdate(),
        revoked_reason=revoked_reason,
    )
    
    result = await execute_update(query, client_id=cliente_id)
    return result.get("rows_affected", 0)


async def get_active_sessions_by_user_core(
    usuario_id: UUID,
    cliente_id: UUID
) -> List[Dict[str, Any]]:
    """
    Obtiene todas las sesiones activas de un usuario usando SQLAlchemy Core.
    
    ✅ FASE 1 SEGURIDAD: Migrado a SQLAlchemy Core para filtro automático garantizado.
    
    Args:
        usuario_id: ID del usuario
        cliente_id: ID del cliente (tenant)
    
    Returns:
        Lista de diccionarios con datos de sesiones activas
    
    Example:
        ```python
        sessions = await get_active_sessions_by_user_core(usuario_id, cliente_id)
        for session in sessions:
            print(f"Sesión: {session['device_name']} desde {session['ip_address']}")
        ```
    """
    # Importación tardía para evitar circular imports
    from app.infrastructure.database.queries_async import execute_query
    
    query = select(
        RefreshTokensTable.c.token_id,
        RefreshTokensTable.c.usuario_id,
        RefreshTokensTable.c.cliente_id,
        RefreshTokensTable.c.created_at,
        RefreshTokensTable.c.last_used_at,
        RefreshTokensTable.c.uso_count,
        RefreshTokensTable.c.device_name,
        RefreshTokensTable.c.device_id,
        RefreshTokensTable.c.ip_address,
        RefreshTokensTable.c.client_type
    ).where(
        and_(
            RefreshTokensTable.c.usuario_id == usuario_id,
            RefreshTokensTable.c.cliente_id == cliente_id,  # ✅ Filtro explícito + automático
            RefreshTokensTable.c.is_revoked == False,
            RefreshTokensTable.c.expires_at > func.getdate()
        )
    ).order_by(
        RefreshTokensTable.c.last_used_at.desc()
    )
    
    results = await execute_query(query, client_id=cliente_id)
    return results


async def get_active_sessions_by_user_oldest_first_core(
    usuario_id: UUID,
    cliente_id: UUID,
) -> List[Dict[str, Any]]:
    """Sesiones activas del usuario ordenadas por created_at ASC (más antigua primero)."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(
        RefreshTokensTable.c.token_id,
        RefreshTokensTable.c.usuario_id,
        RefreshTokensTable.c.cliente_id,
        RefreshTokensTable.c.created_at,
        RefreshTokensTable.c.device_name,
        RefreshTokensTable.c.client_type,
    ).where(
        and_(
            RefreshTokensTable.c.usuario_id == usuario_id,
            RefreshTokensTable.c.cliente_id == cliente_id,
            RefreshTokensTable.c.is_revoked == False,  # noqa: E712
            RefreshTokensTable.c.expires_at > func.getdate(),
        )
    ).order_by(
        RefreshTokensTable.c.created_at.asc(),
        RefreshTokensTable.c.token_id.asc(),
    )

    return await execute_query(query, client_id=cliente_id)


async def delete_expired_tokens_core(
    cliente_id: UUID
) -> int:
    """
    Elimina tokens expirados y revocados usando SQLAlchemy Core.
    
    ✅ FASE 1 SEGURIDAD: Migrado a SQLAlchemy Core para filtro automático garantizado.
    
    Args:
        cliente_id: ID del cliente (tenant)
    
    Returns:
        Número de tokens eliminados
    
    Example:
        ```python
        deleted = await delete_expired_tokens_core(cliente_id)
        print(f"{deleted} tokens expirados eliminados")
        ```
    """
    # Importación tardía para evitar circular imports
    from app.infrastructure.database.queries_async import execute_query
    from sqlalchemy import delete
    
    query = delete(RefreshTokensTable).where(
        and_(
            RefreshTokensTable.c.expires_at < func.getdate(),
            RefreshTokensTable.c.is_revoked == True,
            RefreshTokensTable.c.cliente_id == cliente_id  # ✅ Filtro explícito + automático
        )
    )
    
    result = await execute_query(query, client_id=cliente_id)
    # execute_query para DELETE retorna [{"rows_affected": N}]
    if result and len(result) > 0:
        return result[0].get("rows_affected", 0)
    return 0


async def revoke_refresh_token_by_id_core(
    token_id: UUID,
    cliente_id: UUID,
    revoked_reason: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Revoca un refresh token por token_id (admin revoke).

    Returns:
        Dict con token_id revocado o None si no existe / ya revocado.
    """
    from app.infrastructure.database.queries_async import execute_update
    from sqlalchemy import text

    query = text("""
        UPDATE refresh_tokens
        SET is_revoked = 1, revoked_at = GETDATE(), revoked_reason = :revoked_reason
        OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.usuario_id, INSERTED.cliente_id
        WHERE token_id = :token_id
          AND cliente_id = :cliente_id
          AND is_revoked = 0
    """).bindparams(
        token_id=token_id,
        cliente_id=cliente_id,
        revoked_reason=revoked_reason,
    )

    result = await execute_update(query, client_id=cliente_id)
    if result and result.get("token_id"):
        return {
            "token_id": result.get("token_id"),
            "is_revoked": result.get("is_revoked", True),
            "usuario_id": result.get("usuario_id"),
            "cliente_id": result.get("cliente_id", cliente_id),
        }
    return None


__all__ = [
    "record_refresh_token_activity_core",
    "is_refresh_token_session_idle_expired_core",
    "get_refresh_token_by_hash_any_state_core",
    "get_refresh_token_by_hash_core",
    "insert_refresh_token_core",
    "revoke_refresh_token_core",
    "revoke_all_user_tokens_core",
    "get_active_sessions_by_user_core",
    "get_active_sessions_by_user_oldest_first_core",
    "delete_expired_tokens_core",
    "revoke_refresh_token_by_id_core",
]
