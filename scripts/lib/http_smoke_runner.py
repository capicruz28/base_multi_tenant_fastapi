"""
Suite smoke HTTP reutilizable — tenant ERP post-onboarding / post-repair.

No modifica RBAC; solo valida contrato HTTP esperado.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from scripts.lib.http_smoke_client import HttpSmokeClient


def tenant_origin(subdominio: str, fe_port: str = "5173") -> str:
    return f"http://{subdominio}.app.local:{fe_port}"


def platform_origin(fe_port: str = "5173") -> str:
    return f"http://platform.app.local:{fe_port}"


def run_platform_smoke(
    *,
    base_url: str,
    username: str = "superadmin",
    password: str = "admin123",
    fe_port: str = "5173",
) -> SmokeReport:
    """Smoke operador plataforma (Origin platform, sin skip por falta de empresa)."""
    origin = platform_origin(fe_port)
    client = HttpSmokeClient(base_url=base_url)
    report = SmokeReport(subdominio="platform", base_url=base_url)

    login_resp = _login(client, username=username, password=password, origin=origin)
    if login_resp.status != 200 or not isinstance(login_resp.body, dict):
        _step(report, "login", False, login_resp.status, _body_detail(login_resp.body))
        report.finished_at = time.time()
        return report

    token_data = login_resp.body
    access = token_data.get("access_token")
    refresh = token_data.get("refresh_token")
    _step(report, "login", True, login_resp.status, {"has_access": bool(access)})
    if not access:
        report.finished_at = time.time()
        return report

    bearer = access
    hdrs = {"Origin": origin, "X-Client-Type": "mobile"}

    me_resp = client.request("GET", "/api/v1/auth/me/", headers=hdrs, bearer=bearer)
    me_ok = me_resp.status == 200
    user_type = None
    if me_ok and isinstance(me_resp.body, dict):
        ud = me_resp.body.get("user_data") or me_resp.body
        user_type = ud.get("user_type") if isinstance(ud, dict) else None
    _step(
        report,
        "auth_me",
        me_ok,
        me_resp.status,
        {"user_type": user_type} if me_ok else _body_detail(me_resp.body),
    )

    menu_resp = client.request("GET", "/api/v1/auth/menu", headers=hdrs, bearer=bearer)
    menu_ok = menu_resp.status == 200
    mod_count = None
    if menu_ok and isinstance(menu_resp.body, dict):
        mod_count = len(menu_resp.body.get("modulos") or [])
    _step(
        report,
        "auth_menu",
        menu_ok and (mod_count is None or mod_count > 0),
        menu_resp.status,
        {"modulos_count": mod_count} if menu_ok else _body_detail(menu_resp.body),
    )

    perm_resp = client.request(
        "GET", "/api/v1/auth/permissions/me", headers=hdrs, bearer=bearer
    )
    perm_ok = perm_resp.status == 200 and isinstance(perm_resp.body, dict)
    codes: List[str] = []
    if perm_ok:
        raw = perm_resp.body.get("permissions") or perm_resp.body.get("permisos") or []
        codes = [p if isinstance(p, str) else str(p.get("codigo", "")) for p in raw]
        codes = [c for c in codes if c]
    checks = {
        "admin.platform.access": "admin.platform.access" in codes,
        "core.app.acceder": "core.app.acceder" in codes,
        "tenant.cliente.crear": "tenant.cliente.crear" in codes,
        "admin.usuario.leer": "admin.usuario.leer" in codes,
        "sample_count": len(codes),
    }
    perm_step = (
        perm_ok
        and checks["sample_count"] > 5
        and (
            checks["admin.platform.access"]
            or checks["admin.usuario.leer"]
            or checks["tenant.cliente.crear"]
        )
    )
    _step(report, "permissions_me_platform", perm_step, perm_resp.status, checks)

    if refresh:
        ref = client.request(
            "POST",
            "/api/v1/auth/refresh/",
            headers=hdrs,
            json_body={"refresh_token": refresh},
            bearer=bearer,
        )
        _step(
            report,
            "refresh",
            ref.status == 200,
            ref.status,
            None if ref.status == 200 else _body_detail(ref.body),
        )

    report.finished_at = time.time()
    return report


@dataclass
class SmokeStepResult:
    name: str
    ok: bool
    status: Optional[int] = None
    detail: Any = None


@dataclass
class SmokeReport:
    subdominio: str
    base_url: str
    steps: List[SmokeStepResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    @property
    def passed(self) -> bool:
        return all(s.ok for s in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subdominio": self.subdominio,
            "base_url": self.base_url,
            "passed": self.passed,
            "duration_sec": round((self.finished_at or time.time()) - self.started_at, 3),
            "steps": [
                {
                    "name": s.name,
                    "ok": s.ok,
                    "status": s.status,
                    "detail": s.detail,
                }
                for s in self.steps
            ],
        }


def _step(
    report: SmokeReport,
    name: str,
    ok: bool,
    status: Optional[int] = None,
    detail: Any = None,
) -> None:
    report.steps.append(SmokeStepResult(name=name, ok=ok, status=status, detail=detail))


def _body_detail(body: Any, max_len: int = 200) -> Any:
    if isinstance(body, dict):
        return body.get("detail") or body
    text = str(body)
    return text[:max_len] if len(text) > max_len else text


def _login(
    client: HttpSmokeClient,
    *,
    username: str,
    password: str,
    origin: str,
) -> Dict[str, Any]:
    return client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        form_body={"username": username, "password": password},
    )


def run_tenant_smoke(
    *,
    base_url: str,
    subdominio: str,
    username: str,
    password: str,
    fe_port: str = "5173",
    require_org_empresa_leer: bool = True,
    require_core_app_acceder: bool = True,
    forbid_tenant_cliente_crear: bool = True,
) -> SmokeReport:
    origin = tenant_origin(subdominio, fe_port)
    client = HttpSmokeClient(base_url=base_url)
    report = SmokeReport(subdominio=subdominio, base_url=base_url)

    # --- login ---
    login_resp = _login(client, username=username, password=password, origin=origin)
    if login_resp.status != 200 or not isinstance(login_resp.body, dict):
        _step(report, "login", False, login_resp.status, _body_detail(login_resp.body))
        report.finished_at = time.time()
        return report

    token_data = login_resp.body
    access = token_data.get("access_token")
    refresh = token_data.get("refresh_token")
    selection_token = token_data.get("selection_token")
    _step(report, "login", True, login_resp.status, {"has_access": bool(access)})

    if not access and selection_token:
        _step(
            report,
            "login_has_access_or_selection",
            True,
            login_resp.status,
            "selection_token (multi-empresa)",
        )
        bearer = selection_token
    elif access:
        bearer = access
    else:
        _step(report, "login_has_access_or_selection", False, login_resp.status, token_data)
        report.finished_at = time.time()
        return report

    mobile_hdrs = {"Origin": origin, "X-Client-Type": "mobile"}

    # --- org.empresa listar (antes de menu/permissions: requiere empresa en sesión ERP) ---
    org_resp = client.request(
        "GET",
        "/api/v1/org/empresa",
        headers=mobile_hdrs,
        bearer=bearer,
    )
    org_ok = org_resp.status == 200 and isinstance(org_resp.body, list)
    _step(
        report,
        "org_empresa_listar",
        org_ok,
        org_resp.status,
        {"count": len(org_resp.body)} if org_ok else _body_detail(org_resp.body),
    )

    empresas = org_resp.body if org_ok else []
    session_has_empresa = bool(token_data.get("user_data", {}).get("empresa_activa"))

    # --- selección / cambio empresa ---
    if empresas and access and not selection_token:
        emp_id = empresas[0].get("empresa_id") or empresas[0].get("id")
        if emp_id:
            cambiar = client.request(
                "POST",
                "/api/v1/auth/empresa/cambiar/",
                headers=mobile_hdrs,
                bearer=bearer,
                json_body={"empresa_id": str(emp_id), "refresh_token": refresh},
            )
            ok_cambio = cambiar.status == 200
            already_active = cambiar.status == 400 and isinstance(cambiar.body, dict) and (
                "ya es la empresa activa" in str(cambiar.body.get("detail", "")).lower()
            )
            if ok_cambio and isinstance(cambiar.body, dict) and cambiar.body.get("access_token"):
                bearer = cambiar.body["access_token"]
                session_has_empresa = True
            elif already_active:
                ok_cambio = True
                session_has_empresa = True
            _step(
                report,
                "empresa_cambiar",
                ok_cambio,
                cambiar.status,
                "already_active_session"
                if already_active
                else (None if ok_cambio else _body_detail(cambiar.body)),
            )
        else:
            _step(report, "empresa_cambiar", True, None, "skipped (sin empresa_id en item)")
    elif selection_token and empresas:
        emp_id = empresas[0].get("empresa_id") or empresas[0].get("id")
        sel = client.request(
            "POST",
            "/api/v1/auth/empresa/seleccionar/",
            headers=mobile_hdrs,
            bearer=bearer,
            json_body={"empresa_id": str(emp_id)} if emp_id else {},
        )
        ok_sel = sel.status == 200
        if ok_sel and isinstance(sel.body, dict) and sel.body.get("access_token"):
            bearer = sel.body["access_token"]
            session_has_empresa = True
        _step(
            report,
            "empresa_seleccionar",
            ok_sel,
            sel.status,
            None if ok_sel else _body_detail(sel.body),
        )
    else:
        _step(
            report,
            "empresa_cambiar_o_seleccionar",
            True,
            None,
            "skipped (sin empresas; admin onboarding sin empresa)",
        )

    admin_sin_empresa = not session_has_empresa and not empresas

    # --- /auth/me ---
    me_resp = client.request(
        "GET",
        "/api/v1/auth/me/",
        headers=mobile_hdrs,
        bearer=bearer,
    )
    me_ok = me_resp.status == 200
    if admin_sin_empresa and me_resp.status in (403, 409):
        me_ok = True
    _step(
        report,
        "auth_me",
        me_ok,
        me_resp.status,
        "skipped_admin_sin_empresa"
        if admin_sin_empresa and me_resp.status in (403, 409)
        else (None if me_ok else _body_detail(me_resp.body)),
    )

    # --- /auth/menu (403 esperado si admin sin empresa en sesión) ---
    menu_resp = client.request(
        "GET",
        "/api/v1/auth/menu",
        headers=mobile_hdrs,
        bearer=bearer,
    )
    menu_ok = menu_resp.status == 200
    menu_detail: Any = None
    if menu_ok and isinstance(menu_resp.body, dict):
        modulo_codigos = [
            str(m.get("codigo", "")).upper()
            for m in (menu_resp.body.get("modulos") or [])
            if isinstance(m, dict) and m.get("codigo")
        ]
        forbidden_menu_codigos: List[str] = []
        org_rutas_sample: List[str] = []
        for mod in menu_resp.body.get("modulos") or []:
            if not isinstance(mod, dict):
                continue
            mod_code = str(mod.get("codigo", "")).upper()
            for sec in mod.get("secciones") or []:
                if not isinstance(sec, dict):
                    continue
                for item in sec.get("menus") or []:
                    if not isinstance(item, dict):
                        continue
                    cod = str(item.get("codigo") or "")
                    if "SYS_ADMIN.CATALOGOS" in cod or "SYS_ADMIN.PLATFORM" in cod:
                        forbidden_menu_codigos.append(cod)
                    if mod_code == "ORG":
                        ruta = str(item.get("ruta") or "")
                        if ruta:
                            org_rutas_sample.append(ruta)
        org_rutas_app_prefix = (
            all(r.startswith("/app/") for r in org_rutas_sample)
            if org_rutas_sample
            else True
        )
        menu_checks = {
            "ORG": "ORG" in modulo_codigos,
            "SYS_ADMIN": "SYS_ADMIN" in modulo_codigos,
            "no_platform_or_catalogos_menus": len(forbidden_menu_codigos) == 0,
            "org_rutas_app_prefix": org_rutas_app_prefix,
        }
        menu_detail = {
            "modulos_count": len(modulo_codigos),
            "modulo_codigos": modulo_codigos,
            "checks": menu_checks,
            "forbidden_menu_codigos": forbidden_menu_codigos,
            "org_rutas_sample": org_rutas_sample[:6],
        }
        menu_ok = menu_ok and all(menu_checks.values())
    if admin_sin_empresa and menu_resp.status in (403, 409):
        menu_ok = True
        menu_detail = "skipped_admin_sin_empresa"
    _step(
        report,
        "auth_menu",
        menu_ok,
        menu_resp.status,
        menu_detail
        if menu_detail is not None
        else (None if menu_ok else _body_detail(menu_resp.body)),
    )

    # --- refresh (después de posible selección de empresa) ---
    if refresh and access:
        ref_resp = client.request(
            "POST",
            "/api/v1/auth/refresh/",
            headers=mobile_hdrs,
            json_body={"refresh_token": refresh},
            bearer=bearer,
        )
        ok_ref = ref_resp.status == 200 and isinstance(ref_resp.body, dict)
        if ok_ref and ref_resp.body.get("access_token"):
            bearer = ref_resp.body["access_token"]
            refresh = ref_resp.body.get("refresh_token") or refresh
        _step(
            report,
            "refresh",
            ok_ref,
            ref_resp.status,
            None if ok_ref else _body_detail(ref_resp.body),
        )
    else:
        _step(report, "refresh", True, None, "skipped (no refresh_token en login)")

    # --- permissions/me (ADMIN_TENANT efectivos) ---
    perm_resp = client.request(
        "GET",
        "/api/v1/auth/permissions/me",
        headers=mobile_hdrs,
        bearer=bearer,
    )
    perm_ok = perm_resp.status == 200 and isinstance(perm_resp.body, dict)
    if admin_sin_empresa and perm_resp.status in (403, 409):
        perm_ok = True
    codigos: List[str] = []
    if perm_resp.status == 200 and isinstance(perm_resp.body, dict):
        raw_perms = perm_resp.body.get("permissions") or perm_resp.body.get("permisos") or []
        if isinstance(raw_perms, list):
            for p in raw_perms:
                if isinstance(p, str):
                    codigos.append(p)
                elif isinstance(p, dict) and p.get("codigo"):
                    codigos.append(str(p["codigo"]))

    checks: Dict[str, bool] = {}
    if require_org_empresa_leer:
        checks["org.empresa.leer"] = "org.empresa.leer" in codigos
    if require_core_app_acceder:
        checks["core.app.acceder"] = "core.app.acceder" in codigos
    if forbid_tenant_cliente_crear:
        checks["tenant.cliente.crear_absent"] = "tenant.cliente.crear" not in codigos

    perm_step_ok = perm_ok
    if perm_resp.status == 200 and checks:
        perm_step_ok = all(checks.values())
    _step(
        report,
        "permissions_me_admin_tenant",
        perm_step_ok,
        perm_resp.status,
        {"checks": checks, "sample_count": len(codigos), "skipped_admin_sin_empresa": admin_sin_empresa}
        if perm_resp.status in (403, 409) and admin_sin_empresa
        else ({"checks": checks, "sample_count": len(codigos)} if perm_resp.status == 200 else _body_detail(perm_resp.body)),
    )

    report.finished_at = time.time()
    return report
