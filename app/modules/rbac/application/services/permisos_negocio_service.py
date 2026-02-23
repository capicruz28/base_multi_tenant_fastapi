# app/modules/rbac/application/services/permisos_negocio_service.py
"""
Servicio para catálogo de permisos de negocio (permiso) y asignación rol → permiso (rol_permiso).
Usado por los endpoints GET /permisos-catalogo/ y GET/PUT /roles/{rol_id}/permisos-negocio/.

Filtro por módulos del tenant: si se pasa cliente_id, solo se devuelven permisos de
módulos habilitados en cliente_modulo para ese cliente, más siempre admin.* y modulos.*.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from sqlalchemy import text

from app.infrastructure.database.queries_async import (
    execute_query,
    execute_update,
    execute_insert,
)
from app.infrastructure.database.connection_async import DatabaseConnection
from app.core.exceptions import NotFoundError, ValidationError
from app.core.tenant.context import try_get_tenant_context

logger = logging.getLogger(__name__)

# Prefijos de permisos que siempre se muestran (no dependen de módulo contratado)
PREFIJOS_GLOBALES = {"admin", "modulos"}


async def _obtener_codigos_modulos_habilitados(cliente_id: UUID) -> List[str]:
    """
    Devuelve los códigos de módulos (ej. ORG, LOG) habilitados para el cliente
    según cliente_modulo + modulo en BD central.
    """
    sql = text("""
        SELECT m.codigo
        FROM cliente_modulo cm
        INNER JOIN modulo m ON m.modulo_id = cm.modulo_id AND m.es_activo = 1
        WHERE cm.cliente_id = :cliente_id
          AND cm.esta_activo = 1
          AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
    """).bindparams(cliente_id=cliente_id)
    rows = await execute_query(sql, connection_type=DatabaseConnection.ADMIN)
    if not rows:
        return []
    return [str(r.get("codigo", "")).strip() for r in rows if r.get("codigo")]


def _prefijo_permiso(codigo: str) -> str:
    """Extrae el prefijo del permiso (ej. 'org' de 'org.area.leer')."""
    if not codigo or "." not in codigo:
        return ""
    return codigo.split(".", 1)[0].strip().lower()


async def listar_catalogo_permisos(cliente_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
    """
    Lista permisos activos del catálogo (tabla permiso en BD central).

    Si se pasa cliente_id, filtra por módulos habilitados del tenant (cliente_modulo):
    - Siempre incluye permisos con prefijo 'admin' y 'modulos'.
    - Incluye permisos cuyo prefijo coincida (sin importar mayúsculas) con el código
      de un módulo habilitado para ese cliente (ej. org, log, mfg).
    Si permiso.modulo_id está poblado en el futuro, se puede filtrar también por él.
    """
    sql = text("""
        SELECT permiso_id, codigo, nombre, descripcion, recurso, accion, modulo_id, es_activo
        FROM permiso
        WHERE es_activo = 1
        ORDER BY codigo
    """)
    rows = await execute_query(sql, connection_type=DatabaseConnection.ADMIN)
    items = [dict(r) for r in rows] if rows else []

    if not cliente_id:
        return items

    codigos_habilitados = await _obtener_codigos_modulos_habilitados(cliente_id)
    codigos_lower = {c.strip().lower() for c in codigos_habilitados if c}

    def incluir(p: Dict[str, Any]) -> bool:
        codigo = (p.get("codigo") or "").strip()
        prefijo = _prefijo_permiso(codigo)
        if not prefijo:
            return True
        if prefijo in PREFIJOS_GLOBALES:
            return True
        return prefijo in codigos_lower

    filtrados = [p for p in items if incluir(p)]
    logger.debug(
        f"Catálogo filtrado por tenant {cliente_id}: "
        f"{len(filtrados)} de {len(items)} permisos (módulos habilitados: {list(codigos_lower)})"
    )
    return filtrados


async def get_permisos_negocio_by_rol(rol_id: UUID, cliente_id: UUID) -> List[Dict[str, Any]]:
    """
    Obtiene los permisos de negocio asignados a un rol (rol_permiso + permiso).
    Valida que el rol pertenezca al tenant (cliente_id) o sea rol del sistema.
    """
    tenant_ctx = try_get_tenant_context()
    database_type = tenant_ctx.database_type if tenant_ctx else "single"

    # 1) Validar que el rol existe y pertenece al tenant o es sistema (cliente_id NULL). str() evita 403 por UUID vs string.
    from app.modules.rbac.application.services.rol_service import RolService
    rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
    if not rol:
        raise NotFoundError(detail=f"Rol con ID {rol_id} no encontrado.", internal_code="ROLE_NOT_FOUND")
    rol_cliente_id = rol.get("cliente_id")
    mismo_tenant = rol_cliente_id is not None and str(rol_cliente_id) == str(cliente_id)
    rol_sistema = rol_cliente_id is None
    if not (mismo_tenant or rol_sistema):
        raise ValidationError(
            detail="El rol no pertenece a su cliente.",
            internal_code="ROLE_OTHER_TENANT",
        )

    if database_type == "multi":
        return await _permisos_negocio_rol_dedicated(rol_id, cliente_id)
    return await _permisos_negocio_rol_single(rol_id, cliente_id)


async def _permisos_negocio_rol_single(rol_id: UUID, cliente_id: UUID) -> List[Dict[str, Any]]:
    """BD central: rol_permiso y permiso en la misma BD."""
    sql = text("""
        SELECT p.permiso_id, p.codigo, p.nombre, p.descripcion, p.recurso, p.accion
        FROM rol_permiso rp
        INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
        WHERE rp.rol_id = :rol_id AND rp.cliente_id = :cliente_id
        ORDER BY p.codigo
    """).bindparams(rol_id=rol_id, cliente_id=cliente_id)
    rows = await execute_query(sql, client_id=cliente_id, connection_type=DatabaseConnection.DEFAULT)
    return [dict(r) for r in rows] if rows else []


async def _permisos_negocio_rol_dedicated(rol_id: UUID, cliente_id: UUID) -> List[Dict[str, Any]]:
    """BD dedicada: rol_permiso en tenant; permiso en central."""
    sql_ids = text("""
        SELECT rp.permiso_id
        FROM rol_permiso rp
        WHERE rp.rol_id = :rol_id AND rp.cliente_id = :cliente_id
    """).bindparams(rol_id=rol_id, cliente_id=cliente_id)
    rows = await execute_query(sql_ids, client_id=cliente_id, connection_type=DatabaseConnection.DEFAULT)
    if not rows:
        return []
    permiso_ids = [r["permiso_id"] for r in rows if r.get("permiso_id")]
    if not permiso_ids:
        return []
    placeholders = ", ".join(f":p{i}" for i in range(len(permiso_ids)))
    sql_perm = text(
        f"SELECT permiso_id, codigo, nombre, descripcion, recurso, accion FROM permiso "
        f"WHERE es_activo = 1 AND permiso_id IN ({placeholders}) ORDER BY codigo"
    )
    params = {f"p{i}": pid for i, pid in enumerate(permiso_ids)}
    sql_perm = sql_perm.bindparams(**params)
    # permiso es tabla global; no requiere skip_tenant_validation
    rows_perm = await execute_query(
        sql_perm,
        connection_type=DatabaseConnection.ADMIN,
    )
    return [dict(r) for r in rows_perm] if rows_perm else []


async def set_permisos_negocio_rol(rol_id: UUID, cliente_id: UUID, permiso_ids: List[UUID]) -> None:
    """
    Reemplaza los permisos de negocio asignados a un rol.
    Elimina todas las asignaciones actuales (rol_permiso) para ese rol en el tenant e inserta las nuevas.
    """
    if not isinstance(permiso_ids, list):
        raise ValidationError(
            detail="permiso_ids debe ser una lista.",
            internal_code="INVALID_PAYLOAD",
        )

    # Validar que el rol existe y pertenece al tenant o es sistema (cliente_id NULL). str() evita 403 por UUID vs string.
    from app.modules.rbac.application.services.rol_service import RolService
    rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
    if not rol:
        raise NotFoundError(detail=f"Rol con ID {rol_id} no encontrado.", internal_code="ROLE_NOT_FOUND")
    rol_cliente_id = rol.get("cliente_id")
    mismo_tenant = rol_cliente_id is not None and str(rol_cliente_id) == str(cliente_id)
    rol_sistema = rol_cliente_id is None
    if not (mismo_tenant or rol_sistema):
        raise ValidationError(
            detail="El rol no pertenece a su cliente.",
            internal_code="ROLE_OTHER_TENANT",
        )

    # Eliminar asignaciones actuales
    delete_sql = text("""
        DELETE FROM rol_permiso
        WHERE rol_id = :rol_id AND cliente_id = :cliente_id
    """).bindparams(rol_id=rol_id, cliente_id=cliente_id)
    await execute_update(delete_sql, client_id=cliente_id, connection_type=DatabaseConnection.DEFAULT)

    # Insertar nuevas (una fila por permiso_id)
    for permiso_id in permiso_ids:
        insert_sql = text("""
            INSERT INTO rol_permiso (cliente_id, rol_id, permiso_id)
            VALUES (:cliente_id, :rol_id, :permiso_id)
        """).bindparams(cliente_id=cliente_id, rol_id=rol_id, permiso_id=permiso_id)
        await execute_insert(insert_sql, client_id=cliente_id, connection_type=DatabaseConnection.DEFAULT)

    logger.info(f"Permisos de negocio actualizados para rol {rol_id}: {len(permiso_ids)} asignados.")
