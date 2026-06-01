# app/core/authorization/permission_startup.py
"""
Rutinas de startup para RBAC code-first:
- Rellena PermissionRegistry desde dependencias require_permission(perm) que no usan RequirePermission(metadata).
- Ejecuta PermissionSyncService.sync().
- Advierte por endpoints sin permiso declarado.
"""
from __future__ import annotations

import logging
from typing import Any, Generator

from app.core.authorization.permission_registry import (
    register as register_permission,
    get_all as get_all_permissions,
)
from app.core.authorization.permission_sync_service import sync as sync_permissions
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.connection_async import DatabaseConnection
from sqlalchemy import text
from fastapi import Depends
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from starlette.routing import Mount, Router
from app.core.authorization.rbac import require_permission

logger = logging.getLogger(__name__)

RBAC_LOG_PREFIX = "[RBAC]"

# Rutas que no requieren declarar permiso (públicas o sistema)
SKIP_PATHS = frozenset({
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/test",
    "/drivers",
    "/debug-env",
    "/debug-headers",
    "/debug-detailed",
})
SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/api/v1/auth")


def _iter_routes(app: Any) -> Generator[tuple[str, set, Any], None, None]:
    """
    Recorre recursivamente todas las rutas (incluyendo Mount y routers anidados)
    y devuelve (path, methods, dependant) para cada APIRoute.
    """

    def walk(routes):
        for route in routes:
            if isinstance(route, APIRoute):
                path = route.path or "/"
                methods = route.methods or set()
                dependant = getattr(route, "dependant", None)
                try:
                    print("[RBAC DEBUG] APIRoute detected:", path)
                except Exception:
                    pass
                yield path, methods, dependant
            elif isinstance(route, Mount) and hasattr(route, "routes"):
                yield from walk(route.routes)
            elif isinstance(route, Router):
                yield from walk(route.routes)

    yield from walk(getattr(app, "routes", []))


def _iter_api_routes(app: Any, prefix: str = "") -> Generator[tuple[APIRoute, str, set], None, None]:
    """Recorre todas las APIRoute (incluyendo las montadas) y devuelve (route, path, methods)."""
    for route in getattr(app, "routes", []):
        if hasattr(route, "app"):  # Mount
            path = prefix + (route.path.rstrip("/") or "")
            yield from _iter_api_routes(route.app, path + "/")
        elif isinstance(route, APIRoute):
            path = prefix.rstrip("/") + (route.path if route.path != "/" else "")
            path = path or "/"
            methods = route.methods or set()
            yield route, path, methods


def _get_dependency_callables(dependant: Any) -> list:
    """Obtiene todos los callables de dependencias (dependant.dependencies y route.dependencies)."""
    out = []
    if not dependant:
        return out
    for dep in getattr(dependant, "dependencies", []) or []:
        call = getattr(dep, "call", None)
        if call is not None:
            out.append(call)
    return out


def _has_permission_dependency(dependant: Any) -> bool:
    """True si alguna dependencia del route tiene __permission_codigo__ o __permission_metadata__."""
    for call in _get_dependency_callables(dependant):
        if getattr(call, "__permission_codigo__", None) is not None:
            return True
        if getattr(call, "__permission_metadata__", None) is not None:
            return True
    return False


def _register_from_route_dependencies(dependant: Any) -> None:
    """Registra en el registry permisos que solo tienen __permission_codigo__ (sin metadata)."""
    for call in _get_dependency_callables(dependant):
        codigo = getattr(call, "__permission_codigo__", None)
        if codigo and getattr(call, "__permission_metadata__", None) is None:
            recurso = ""
            accion = ""
            modulo_codigo = None
            parts = codigo.split(".") if isinstance(codigo, str) else []
            if len(parts) >= 3:
                modulo_codigo = parts[0]
                recurso = parts[1]
                accion = parts[2]
            elif len(parts) == 2:
                modulo_codigo = parts[0]
                recurso = parts[1]
            if not recurso or not accion:
                logger.warning(
                    "%s Permission metadata incompleta para codigo=%s (recurso=%s, accion=%s) registrada via require_permission().",
                    RBAC_LOG_PREFIX,
                    codigo,
                    recurso,
                    accion,
                )
            meta: dict[str, Any] = {
                "codigo": codigo,
                "nombre": codigo,
                "recurso": recurso,
                "accion": accion,
            }
            if modulo_codigo:
                meta["modulo_codigo"] = modulo_codigo
            register_permission(meta)


def _infer_module_and_resource(path: str) -> tuple[str | None, str | None]:
    """
    Inferir modulo_codigo (ORG/LOG/ADMIN) y recurso desde la ruta.

    Regla:
      - paths que empiezan con /org -> ORG
      - paths que empiezan con /log -> LOG
      - paths que empiezan con /admin -> ADMIN
      - recurso = último segmento no param, singularizado (rutas -> ruta)
    """
    if not path:
        return None, None

    norm = path.split("?", 1)[0]
    if norm.startswith("/api/v1"):
        norm = norm[len("/api/v1") :] or "/"

    parts = [p for p in norm.split("/") if p]
    if not parts:
        return None, None

    first = parts[0].lower()
    modulo_codigo: str | None
    if first == "org":
        modulo_codigo = "ORG"
    elif first == "log":
        modulo_codigo = "LOG"
    elif first == "admin":
        modulo_codigo = "ADMIN"
    else:
        modulo_codigo = None

    recurso_segment = None
    for segment in reversed(parts):
        if segment.startswith("{") and segment.endswith("}"):
            continue
        recurso_segment = segment
        break

    if not recurso_segment:
        return modulo_codigo, None

    recurso = recurso_segment.lower()
    if recurso.endswith("s"):
        recurso = recurso[:-1]

    return modulo_codigo, recurso


def _infer_action(methods: set[str] | None) -> str | None:
    """Inferir accion a partir de métodos HTTP del endpoint."""
    if not methods:
        return None
    upper = {m.upper() for m in methods}
    if "GET" in upper:
        return "leer"
    if "POST" in upper:
        return "crear"
    if "PUT" in upper or "PATCH" in upper:
        return "actualizar"
    if "DELETE" in upper:
        return "eliminar"
    return None


def ensure_registry_from_routes(app: Any) -> None:
    """Recorre todas las rutas y registra permisos; loguea endpoint y permiso detectado."""
    seen_codigos: set[str] = set()

    # 1) Rutas que ya declaran permisos (require_permission / RequirePermission)
    for path, methods, dependant in _iter_routes(app):
        # DEBUG: loggear cada ruta detectada para validar timing del startup
        try:
            for m in sorted(methods or []):
                print(f"[RBAC DEBUG] route found: {m} {path}")
        except Exception:
            pass
        for call in _get_dependency_callables(dependant):
            codigo = getattr(call, "__permission_codigo__", None)
            meta = getattr(call, "__permission_metadata__", None)
            if codigo is not None:
                logger.info(
                    "%s Scanning endpoint: %s %s",
                    RBAC_LOG_PREFIX,
                    ",".join(sorted(methods)) if methods else "?",
                    path,
                )
                logger.info("%s Permission detected: %s", RBAC_LOG_PREFIX, codigo)
                if meta is None:
                    recurso = ""
                    accion = ""
                    modulo_codigo = None
                    parts = codigo.split(".") if isinstance(codigo, str) else []
                    if len(parts) >= 3:
                        modulo_codigo = parts[0]
                        recurso = parts[1]
                        accion = parts[2]
                    elif len(parts) == 2:
                        modulo_codigo = parts[0]
                        recurso = parts[1]
                    if not recurso or not accion:
                        logger.warning(
                            "%s Permission metadata incompleta para %s %s: codigo=%s recurso=%s accion=%s",
                            RBAC_LOG_PREFIX,
                            ",".join(sorted(methods)) if methods else "?",
                            path,
                            codigo,
                            recurso,
                            accion,
                        )
                    meta_dict: dict[str, Any] = {
                        "codigo": codigo,
                        "nombre": codigo,
                        "recurso": recurso,
                        "accion": accion,
                    }
                    if modulo_codigo:
                        meta_dict["modulo_codigo"] = modulo_codigo
                    if codigo not in seen_codigos:
                        register_permission(meta_dict)
                        seen_codigos.add(codigo)
                else:
                    cod_meta = meta.get("codigo")
                    if isinstance(cod_meta, str) and cod_meta not in seen_codigos:
                        register_permission(meta)  # type: ignore[arg-type]
                        seen_codigos.add(cod_meta)
            elif meta is not None:
                logger.info(
                    "%s Scanning endpoint: %s %s",
                    RBAC_LOG_PREFIX,
                    ",".join(sorted(methods)) if methods else "?",
                    path,
                )
                logger.info("%s Permission detected: %s", RBAC_LOG_PREFIX, meta.get("codigo"))
                cod_meta = meta.get("codigo")
                if isinstance(cod_meta, str) and cod_meta not in seen_codigos:
                    register_permission(meta)  # type: ignore[arg-type]
                    seen_codigos.add(cod_meta)

    # 2) Rutas sin permisos declarados: inferir metadata según path/method
    for path, methods, dependant in _iter_routes(app):
        if path in SKIP_PATHS:
            continue
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            continue
        if _has_permission_dependency(dependant):
            continue

        accion = _infer_action(methods)
        modulo_codigo, recurso = _infer_module_and_resource(path)
        if not accion or not modulo_codigo or not recurso:
            continue

        codigo = f"{modulo_codigo.lower()}.{recurso}.{accion}"
        if codigo in seen_codigos:
            continue

        meta_auto: dict[str, Any] = {
            "codigo": codigo,
            "nombre": codigo,
            "recurso": recurso,
            "accion": accion,
            "modulo_codigo": modulo_codigo,
        }
        logger.info(
            "%s Inferred permission for %s %s -> %s",
            RBAC_LOG_PREFIX,
            ",".join(sorted(methods)) if methods else "?",
            path,
            codigo,
        )
        register_permission(meta_auto)
        seen_codigos.add(codigo)

    # 3) Asegurar también registro para dependencias con __permission_codigo__ sin metadata
    for _path, _methods, dependant in _iter_routes(app):
        _register_from_route_dependencies(dependant)


def warn_routes_without_permission(app: Any) -> None:
    """Log warning por cada ruta que no declara permiso (excluye públicas)."""
    for path, methods, dependant in _iter_routes(app):
        if path in SKIP_PATHS:
            continue
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            continue
        if not methods or "GET" in methods and path in ("/docs", "/redoc", "/openapi.json"):
            continue
        if _has_permission_dependency(dependant):
            continue
        logger.warning(
            "%s Endpoint sin @RequirePermission ni require_permission: %s %s",
            RBAC_LOG_PREFIX,
            ",".join(sorted(methods)) if methods else "?",
            path,
        )


def audit_routes_permissions(app: Any) -> None:
    """
    Auditoría de endpoints protegidos vs no protegidos.

    Imprime:
      [RBAC] Total routes discovered: X
      [RBAC] Routes with permission metadata: Y
      [RBAC] Routes missing permission metadata: Z
    y lista las rutas que faltan (respetando SKIP_PATHS / SKIP_PREFIXES).
    """
    total = 0
    with_perm = 0
    without_perm = 0
    missing: list[tuple[str, str]] = []

    for path, methods, dependant in _iter_routes(app):
        if path in SKIP_PATHS:
            continue
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            continue
        if not methods or ("GET" in methods and path in ("/docs", "/redoc", "/openapi.json")):
            continue

        total += 1
        if _has_permission_dependency(dependant):
            with_perm += 1
        else:
            without_perm += 1
            missing.append((",".join(sorted(methods)) if methods else "?", path))

    logger.info("%s Total routes discovered: %s", RBAC_LOG_PREFIX, total)
    logger.info("%s Routes with permission metadata: %s", RBAC_LOG_PREFIX, with_perm)
    logger.info("%s Routes missing permission metadata: %s", RBAC_LOG_PREFIX, without_perm)

    for methods, path in missing:
        logger.warning("%s Route missing permission metadata: %s %s", RBAC_LOG_PREFIX, methods, path)


def apply_rbac_enforcement(app: Any) -> None:
    """
    Inyecta dinámicamente require_permission(codigo) en rutas que no declaran permisos,
    usando la misma lógica de inferencia de ensure_registry_from_routes.
    """
    for route, path, methods in _iter_api_routes(app):
        # Excluir rutas públicas
        if path in SKIP_PATHS:
            continue
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            continue
        dependant = getattr(route, "dependant", None)
        if _has_permission_dependency(dependant):
            continue

        accion = _infer_action(methods)
        modulo_codigo, recurso = _infer_module_and_resource(path)
        if not accion or not modulo_codigo or not recurso:
            continue

        codigo = f"{modulo_codigo.lower()}.{recurso}.{accion}"

        # Añadir dependencia de autorización a nivel de ruta
        dependency_callable = require_permission(codigo)
        # Para FastAPI internals (Dependant)
        sub_dep = get_parameterless_sub_dependant(
            dependency=dependency_callable,
            path=path,
        )
        if dependant is not None:
            dependant.dependencies.append(sub_dep)
        # Para introspección en route.dependencies
        route.dependencies.append(Depends(dependency_callable))

        logger.info(
            "%s Enforcement applied: %s %s -> %s",
            RBAC_LOG_PREFIX,
            ",".join(sorted(methods)) if methods else "?",
            path,
            codigo,
        )


async def run_rbac_startup(app: Any) -> None:
    """
    Ejecutar al startup: rellena registry desde rutas, sync con BD y advierte rutas sin permiso.
    Orden: ensure_registry -> enforcement -> sync -> warn.
    """
    try:
        # DEBUG: verificar cantidad de rutas registradas al momento del startup RBAC
        try:
            print("[RBAC DEBUG] total routes:", len(getattr(app, "routes", [])))
        except Exception:
            pass

        from app.core.authorization.core_permissions import register_core_permissions

        register_core_permissions()
        ensure_registry_from_routes(app)
        apply_rbac_enforcement(app)
        await sync_permissions()

        # Auditoría de rutas declaradas con permiso vs sin permiso
        audit_routes_permissions(app)

        # Verificación de conteo en tabla permiso vs permisos declarados
        try:
            declared = get_all_permissions()
            declared_count = len(declared)
            sql_count = text("SELECT COUNT(*) AS total FROM permiso WHERE es_activo = 1")
            rows = await execute_query(
                sql_count,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None,
            )
            db_total = 0
            if rows:
                row0 = rows[0]
                db_total = row0.get("total") or row0.get("TOTAL") or 0
            logger.info(
                "%s Permission sync summary: declared=%s, db_total_activos=%s",
                RBAC_LOG_PREFIX,
                declared_count,
                db_total,
            )
            if db_total != declared_count:
                logger.warning(
                    "%s Mismatch entre permisos declarados en endpoints (%s) y permisos activos en tabla permiso (%s).",
                    RBAC_LOG_PREFIX,
                    declared_count,
                    db_total,
                )
        except Exception as count_err:
            logger.warning("%s No se pudo verificar conteo de tabla permiso: %s", RBAC_LOG_PREFIX, count_err)

        warn_routes_without_permission(app)
    except Exception as e:
        logger.warning("%s Error en startup RBAC (no bloqueante): %s", RBAC_LOG_PREFIX, e)
