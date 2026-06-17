# Matriz de impacto — FORCE PASSWORD CHANGE

**Tipo:** Auditoría de impacto pre-implementación (sin código)  
**Fecha:** 2026-06-08  
**Relacionado:** [`FORCE_PASSWORD_CHANGE_AUDIT.md`](FORCE_PASSWORD_CHANGE_AUDIT.md)

**Método:** barrido estático del repo `app/` (Python `re` sobre `*.py`). Conteos reproducibles.

---

## 0. Resumen ejecutivo

| Métrica | Valor |
|---------|-------|
| Emisores `create_access_token` | **5 archivos**, **11 llamadas** |
| Emisores `create_refresh_token` | **4 archivos**, **8 llamadas** |
| Consumidores JWT (access) | **~12 archivos** (cadena `oauth2_scheme` → `get_current_user_data`) |
| Consumidores JWT (refresh) | **4 archivos** |
| `Depends(get_current_active_user)` | **128 archivos**, **733 ocurrencias** |
| `require_erp_session` | **4 archivos**, **10 ocurrencias** |
| `require_full_session_payload` | **3 archivos**, **10 ocurrencias** |
| `validate_erp_operational_session` | **3 archivos**, **6 ocurrencias** |
| Router con `require_erp_session` a nivel módulo | **Solo INV** |
| Router ORG con deps de sesión | **6 sub-routers** (`require_org_*`) |

**Conclusión de cobertura:** Si el enforcement se implementa **solo** en `require_erp_session`, se bloquea **menos del 5 %** de las rutas ERP. La mayoría del ERP usa `get_current_active_user` + `require_permission` sin `require_erp_session`. El punto de inyección del enforcement define el alcance real.

---

## 1. Emisores de JWT (todos)

### 1.1 `create_access_token`

| # | Archivo | Contexto / flujo | ¿Debe incluir `requires_password_change`? |
|---|---------|------------------|---------------------------------------------|
| 1 | `app/core/security/jwt.py:112` | Definición + ejemplo SSO en docstring (`:274`) | N/A (factory) |
| 2 | `app/modules/auth/presentation/endpoints.py` | `POST /login/` selection token (`:354`) | ✅ Sí (si aplica al usuario) |
| 3 | `app/modules/auth/presentation/endpoints.py` | `POST /login/` sesión completa (`:395`) | ✅ Sí |
| 4 | `app/modules/auth/presentation/endpoints.py` | `POST /refresh/` (`:1252`) | ✅ Sí (re-leer BD) |
| 5 | `app/modules/auth/presentation/endpoints.py` | `POST /sso/azure/` (`:1816`) | ⚠️ Solo si SSO user tiene flag |
| 6 | `app/modules/auth/presentation/endpoints.py` | `POST /sso/google/` (`:1957`) | ⚠️ Idem |
| 7 | `app/modules/auth/application/services/auth_service.py` | `emitir_sesion_completa_con_empresa()` (`:1616`) | ✅ Sí — usado por seleccionar/cambiar empresa |
| 8 | `app/modules/auth/application/services/impersonation_service.py` | `_emitir_access_impersonacion()` (`:163`) | ❌ No — excluir impersonación |
| 9 | `app/modules/auth/application/use_cases/refresh_token_use_case.py` | Use case (`:111`) | ⚠️ **No cableado** a endpoints actuales; mantener alineado si se usa en futuro |
| 10 | `tests/unit/test_empresa_sesion_auth.py` | Tests | Actualizar fixtures |

### 1.2 `create_refresh_token`

| # | Archivo | Contexto | Notas |
|---|---------|----------|-------|
| 1 | `app/core/security/jwt.py:178` | Factory | Paridad de claims con access |
| 2 | `endpoints.py` | Login (`:401`), refresh (`:1258`), SSO Azure/Google | Misma regla que access |
| 3 | `auth_service.py` | `emitir_sesion_completa_con_empresa()` (`:1622`) | Post selección/cambio empresa |
| 4 | `refresh_token_use_case.py` | Use case | No usado en runtime actual |

### 1.3 Emisión indirecta (helpers)

| Helper | Archivo | Usado por |
|--------|---------|-----------|
| `build_token_data_from_level_info()` | `auth_service.py:228` | Refresh |
| `build_token_payload_for_sso()` | `jwt.py:244` | SSO Azure/Google |
| `emitir_sesion_completa_con_empresa()` | `auth_service.py:1579` | `seleccionar_empresa_post_login`, `cambiar_empresa_sesion` |
| `_emitir_access_impersonacion()` | `impersonation_service.py:120` | Impersonación (sin refresh) |

### 1.4 Emisores que NO aplican al onboarding tenant admin

| Flujo | Motivo |
|-------|--------|
| `POST /api/v1/clientes/` (onboarding) | No emite JWT; solo credenciales en JSON |
| `scripts/bootstrap_platform.py` | CLI; no JWT |
| Impersonación | Token de operador plataforma, sin flag tenant admin |

---

## 2. Consumidores de JWT

### 2.1 Access token

| Capa | Archivo | Función | Rol |
|------|---------|---------|-----|
| Entrada HTTP | `app/core/security/jwt.py` | `oauth2_scheme` | Extrae Bearer |
| Normalización | `app/core/security/jwt.py` | `normalize_bearer_jwt_token()` | Valida forma JWT |
| Decodificación | `app/api/deps.py` | `get_current_user_data()` | `jwt.decode` + blacklist Redis |
| Usuario activo | `app/api/deps.py` | `get_current_active_user()` | BD + tenant + roles |
| Sesión ERP | `app/api/deps_auth.py` | `require_full_session_payload()` | Rechaza selection token |
| Sesión ERP | `app/api/deps_auth.py` | `require_erp_session()` | + `validate_erp_operational_session` |
| ORG | `app/modules/org/presentation/org_deps.py` | `require_org_*_erp_session()` | Sesión + scope ORG |
| RBAC | `app/core/authorization/rbac.py` | `require_permission()` | Usa `get_current_active_user` |
| LBAC | `app/core/authorization/lbac.py` | `require_super_admin()`, `require_admin()` | Usa `get_current_active_user` |
| Impersonación | `app/core/auth/impersonation.py` | `is_impersonation_payload()`, `suppress_platform_privileges()` | Lee claims |
| Empresa | `app/core/tenant/company_scope.py` | `validate_erp_operational_session()`, `resolve_empresa_id_for_rbac()` | Lee `empresa_id` del payload |
| Menú/permisos | `endpoints.py` | `/permissions/me`, `/menu` | Payload + resolver |
| Parámetros ORG | `endpoints_parametros.py` | `get_current_user_data` directo | Lectura payload |

### 2.2 Refresh token

| Archivo | Función | Rol |
|---------|---------|-----|
| `app/core/security/jwt.py` | `decode_refresh_token()` | Valida firma + `type=refresh` |
| `app/core/auth/__init__.py` | `get_current_user_from_refresh()` | Wrapper FastAPI |
| `app/modules/auth/application/services/auth_service.py` | `get_current_user_from_refresh()` | Valida BD + carga usuario |
| `app/modules/auth/presentation/endpoints.py` | `POST /refresh/` | Rota tokens |
| `app/modules/auth/application/services/auth_service.py` | `perform_logout()` | Revoca refresh |

### 2.3 Middleware (no consume JWT directamente)

| Middleware | Archivo | Impacto FORCE PASSWORD |
|------------|---------|------------------------|
| `TenantMiddleware` | `app/core/tenant/middleware.py` | Resuelve `cliente_id` por Host; **sin cambio** |
| `ImpersonateAuthDiagMiddleware` | `app/core/auth/impersonate_auth_diag.py` | Solo logs |
| `CORSMiddleware` | `app/main.py` | Sin cambio |
| Rate limiting | `app/core/security/rate_limiting.py` | Sin cambio |

---

## 3. Endpoints y dependencias — matriz por capa

### 3.1 Capa A — `require_erp_session` (bloqueo ERP “oficial” I1)

**Definición:** `app/api/deps_auth.py:75` → `require_full_session_payload` + `get_current_active_user` + `validate_erp_operational_session`.

| Ubicación | Endpoints afectados |
|-----------|---------------------|
| `app/modules/inv/presentation/endpoints.py` | **Todo el módulo INV** (router `dependencies=[Depends(require_erp_session)]`) — categorías, productos, almacenes, stock, movimientos, kardex, inventario físico, etc. |
| `app/modules/auth/presentation/endpoints.py` | `GET /auth/permissions/me` |
| `app/modules/auth/presentation/endpoints.py` | `GET /auth/menu` |
| `app/api/deps_auth.py` | Definición + `get_current_active_user_full_session` |
| `app/core/tenant/company_scope.py` | Implementación `validate_erp_operational_session` |
| `tests/integration/test_erp_session_contract.py` | Contrato I1 |

**Conteo:** 4 archivos de producción, ~10 referencias + **todos los hijos del router INV**.

---

### 3.2 Capa B — `require_full_session_payload` (sin `validate_erp_operational_session`)

| Ubicación | Uso |
|-----------|-----|
| `app/api/deps_auth.py` | Definición; rechaza `empresa_selection_pending` (salvo impersonación) |
| `app/modules/org/presentation/org_deps.py` | `require_org_tenant_erp_session`, `require_org_company_erp_session` |
| `app/modules/auth/presentation/endpoints.py` | `/permissions/me`, `/menu` (combinado con Capa A) |

**Sub-routers ORG afectados si se añade check aquí:**

| Prefijo | Dep ORG |
|---------|---------|
| `/org/empresa` | `require_org_tenant_erp_session` |
| `/org/sucursales` | `require_org_company_erp_session` |
| `/org/centros-costo` | `require_org_company_erp_session` |
| `/org/departamentos` | `require_org_company_erp_session` |
| `/org/cargos` | `require_org_company_erp_session` |
| `/org/parametros` | `require_org_company_erp_session` |

**Nota:** ORG **no** llama `validate_erp_operational_session` directamente; usa `require_company_scope_if_needed` (`session_scope.py`).

---

### 3.3 Capa C — `get_current_active_user` (mayoría del backend)

**Conteo:** **128 archivos**, **733** `Depends(get_current_active_user)`.

**Módulos representativos (cada uno con múltiples endpoints):**

| Dominio | Archivos endpoint (muestra) | Protección actual |
|---------|----------------------------|-------------------|
| Platform / tenant admin | `endpoints_clientes.py`, `endpoints_conexiones.py`, `superadmin/*` | `get_current_active_user` + `require_super_admin` / `require_permission` |
| Users / RBAC | `users/endpoints.py`, `rbac/endpoints*.py` | Idem |
| ERP operativo | `fin/*`, `pur/*`, `sls/*`, `crm/*`, `hcm/*`, `mfg/*`, `mrp/*`, `wms/*`, `log/*`, `pos/*`, `qms/*`, `tax/*`, `bdg/*`, `bi/*`, `dms/*`, `wfl/*`, `tkt/*`, `mnt/*`, `cst/*`, `pm/*`, `svc/*`, `aud/*`, `invbill/*`, `prc/*`, `mps/*`, `modulos/*`, `menus/*`, `catalogos/*` | `get_current_active_user` + `require_permission` / `RequirePermission` |
| Auth perfil | `GET /auth/me/` | `get_current_active_user` — **debe permanecer accesible** |
| Auth config | `endpoints_auth_config.py` | `get_current_active_user` |

**Brecha crítica:** Si el enforcement vive solo en Capa A, un admin con `requires_password_change=true` **sigue pudiendo** llamar la gran mayoría de APIs ERP (Capa C).

---

### 3.4 Capa D — Sin JWT / sin `get_current_active_user`

| Endpoint | Auth | Impacto |
|----------|------|---------|
| `POST /auth/login/` | Público (tenant por middleware) | Emitir flag en respuesta; no bloquear |
| `POST /auth/refresh/` | Refresh cookie/body | Re-leer flag; rotar claims |
| `POST /auth/logout/` | Opcional Bearer | Sin bloqueo |
| `POST /auth/empresa/seleccionar/` | Selection token | Decidir si permite cambio password antes/después |
| `GET /health`, `/debug-*` | Público | Sin impacto |

---

## 4. Flujos críticos — matriz de impacto

| Flujo | Archivos clave | Emite JWT | Lee flag hoy | Impacto implementación |
|-------|----------------|-----------|--------------|------------------------|
| **Login web** | `endpoints.py:login`, `get_client_type=web` | ✅ access + cookie refresh | ❌ | Añadir claim + `user_data`; cookie refresh sin cambio estructural |
| **Login mobile** | `endpoints.py:login`, `X-Client-Type: mobile` | ✅ access + refresh JSON | ❌ | Mismo; mobile depende de `user_data` o `/me` |
| **Refresh** | `endpoints.py:refresh`, `auth_service.get_current_user_from_refresh` | ✅ rota ambos | ❌ | **Re-leer BD** obligatorio; hoy `user_data=null` en respuesta |
| **Logout** | `auth_service.perform_logout` | ❌ | ❌ | Sin bloqueo; whitelist |
| **Selección empresa** | `seleccionar_empresa_post_login` → `emitir_sesion_completa_con_empresa` | ✅ | ❌ | Propagar flag; admin onboarding puede no tener empresa aún |
| **Cambio empresa** | `cambiar_empresa_sesion` | ✅ rota | ❌ | Propagar flag actualizado |
| **Onboarding tenant** | `cliente_onboarding_service` → `POST /clientes/` | ❌ | N/A (solo `credenciales_iniciales`) | Sin cambio JWT; primer login es el trigger |
| **Onboarding plataforma** | `platform_identity_bootstrap_service`, `bootstrap_platform.py` | ❌ | `requiere_cambio` no seteado en INSERT | **Excluir** del enforcement |
| **Impersonación** | `impersonation_service`, `POST /impersonate/{id}/` | ✅ access only 120min | ❌ | **Excluir** `is_impersonation`; no refresh |
| **Impersonación end** | `POST /impersonate/end/` | Restaura tokens padre | — | Sin impacto en flag tenant |
| **SSO Azure/Google** | `endpoints.py` SSO, `build_token_payload_for_sso` | ✅ | ❌ | Usuarios SSO normalmente sin flag; excluir `proveedor != local` |
| **GET /me** | `endpoints.py:get_me` | ❌ | ❌ | Exponer flag; **no bloquear** |
| **GET /permissions/me** | `require_erp_session` | ❌ | — | Bloqueado si enforcement en Capa A |
| **GET /menu** | `require_erp_session` | ❌ | — | Idem |

---

## 5. Punto de inyección del enforcement — opciones y alcance

| Opción | Archivo | Endpoints bloqueados | Riesgo |
|--------|---------|---------------------|--------|
| **O1** Solo `require_erp_session` | `deps_auth.py:75` | INV + permissions/me + menu | **Cobertura insuficiente** (~95 % ERP sigue abierto) |
| **O2** `require_full_session_payload` | `deps_auth.py:53` | O1 + todo ORG | Sigue insuficiente para FIN/PUR/SLS/… |
| **O3** `get_current_active_user` + whitelist rutas | `deps.py:141` | **Todos** los 733 depends salvo whitelist | Máxima cobertura; requiere lista blanca cuidadosa |
| **O4** Nueva dep `require_password_change_cleared` compuesta | Nuevo + routers | Depende de adopción manual | Migración larga (128 archivos) |
| **O5** Híbrido **O3 + whitelist** (recomendado en auditoría previa) | `deps.py` + `deps_auth.py` | ERP completo + auth parcial | Balance cobertura/riesgo |

### Whitelist mínima (si O3/O5)

| Ruta | Motivo |
|------|--------|
| `POST /api/v1/auth/password/change/` | Nuevo — ejecuta el cambio |
| `GET /api/v1/auth/me/` | Frontend lee estado |
| `POST /api/v1/auth/logout/` | Cerrar sesión |
| `POST /api/v1/auth/refresh/` | Mantener sesión durante pantalla de cambio |
| `POST /api/v1/auth/empresa/seleccionar/` | Completar multi-empresa |
| `POST /api/v1/auth/impersonate/*` | Operador plataforma |
| `POST /api/v1/auth/impersonate/end/` | Restaurar sesión |

---

## 6. Riesgos de regresión

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| R1 | Admin tenant bloqueado en **toda** la API incluido `/me` | Alta | Whitelist explícita |
| R2 | Impersonación soporte bloqueada en tenant con admin pendiente | Alta | Excluir `is_impersonation` |
| R3 | Superadmin plataforma con flag accidental en BD | Media | Excluir `platform_admin` / `es_superadmin` |
| R4 | Claim JWT obsoleto tras cambio password hasta refresh | Media | Re-leer BD en refresh + emitir tokens en change endpoint |
| R5 | Frontend recibe 403 masivo en ERP sin manejar `PASSWORD_CHANGE_REQUIRED` | Alta | Contrato `internal_code` + coordinación FE |
| R6 | Selection token + cambio password: orden incorrecto | Media | Permitir change con selection token o documentar orden |
| R7 | SSO usuarios afectados por error | Baja | Excluir `proveedor_autenticacion != local` |
| R8 | Tests de sesión empresa (`test_empresa_sesion_auth`) rotos | Media | Actualizar fixtures JWT |
| R9 | Cobertura parcial (solo Capa A): falsa sensación de seguridad | **Crítica** | No usar solo `require_erp_session` |
| R10 | `RefreshTokenUseCase` divergente del endpoint refresh | Baja | Alinear o deprecar use case |
| R11 | Mobile: refresh sin `user_data` — FE no detecta flag post-refresh | Media | Incluir flag en refresh o forzar `/me` |
| R12 | Integraciones/scripts que usan token admin temporal post-onboarding | Media | Documentar flujo change password en scripts QA |

---

## 7. Lista exacta de archivos a modificar

### 7.1 P0 — Obligatorios

| Archivo | Cambio |
|---------|--------|
| `app/modules/auth/application/services/auth_service.py` | SELECT `requiere_cambio_contrasena` en `authenticate_user`, `_fetch_user_row_for_refresh`; helper flag; integración change password |
| `app/core/security/jwt.py` | Serializar `requires_password_change` en `create_access_token` / `create_refresh_token` |
| `app/modules/auth/presentation/schemas.py` | `UserDataWithRoles`, `MeResponse`, `build_user_data_with_roles_dict`; schema request/response change password |
| `app/modules/auth/presentation/endpoints.py` | Login, refresh, `/me`, nuevo `POST /password/change/` |
| `app/api/deps.py` o `app/api/deps_auth.py` | Enforcement + whitelist (según opción O3/O5) |
| `app/core/tenant/company_scope.py` | Opcional: error tipado `PASSWORD_CHANGE_REQUIRED` |

### 7.2 P1 — Emisión de tokens en flujos secundarios

| Archivo | Cambio |
|---------|--------|
| `app/modules/auth/application/services/auth_service.py` | `emitir_sesion_completa_con_empresa`, `construir_user_data_sesion`, `seleccionar_empresa_post_login`, `cambiar_empresa_sesion` |
| `app/core/security/jwt.py` | `build_token_payload_for_sso` (si aplica) |
| `app/modules/auth/application/services/impersonation_service.py` | Confirmar exclusión explícita (sin flag o forzar `false`) |

### 7.3 P1 — Nuevo servicio

| Archivo | Cambio |
|---------|--------|
| `app/modules/auth/application/services/password_change_service.py` *(nuevo)* | Orquestar verify/hash/update/revoke tokens |

### 7.4 P2 — Tests

| Archivo | Cambio |
|---------|--------|
| `tests/unit/test_force_password_change.py` *(nuevo)* | Login flag, enforcement, change, impersonación excluida |
| `tests/unit/test_empresa_sesion_auth.py` | Claims actualizados |
| `tests/unit/test_impersonation_auth.py` | Sin regresión impersonación |
| `tests/integration/test_erp_session_contract.py` | 403 PASSWORD_CHANGE_REQUIRED |

### 7.5 P2 — Documentación / contrato

| Archivo | Cambio |
|---------|--------|
| `app/docs/auditoria/FORCE_PASSWORD_CHANGE_AUDIT.md` | Enlace a esta matriz |
| Contrato frontend *(externo)* | `requires_password_change`, código error 403 |

### 7.6 No modificar (verificado)

| Archivo | Motivo |
|---------|--------|
| `app/core/tenant/middleware.py` | No participa en JWT |
| `app/modules/tenant/application/services/cliente_onboarding_service.py` | Ya setea flag; sin JWT |
| `app/modules/tenant/application/services/platform_identity_bootstrap_service.py` | Fuera de alcance tenant admin |
| `app/modules/auth/application/use_cases/refresh_token_use_case.py` | No referenciado por endpoints runtime |

### 7.7 Archivos NO requeridos masivamente (si se usa O3)

Los **128 archivos** con `get_current_active_user` **no necesitan edición individual** si el enforcement se centraliza en `deps.py` con whitelist.

---

## 8. Compatibilidad OpenAPI / contratos existentes

### 8.1 ¿Se puede implementar sin romper OpenAPI?

**Sí — con matices.** Análisis por schema:

| Schema / contrato | Cambio propuesto | Compatibilidad OpenAPI |
|-------------------|------------------|------------------------|
| `Token` | `user_data.requires_password_change: bool = false` | ✅ **Aditivo** — campo opcional con default |
| `UserDataWithRoles` | Campo nuevo opcional | ✅ Aditivo |
| `MeResponse` | Campo nuevo opcional | ✅ Aditivo |
| `LoginEmpresaSelectionResponse` | Opcional en `user_data` | ✅ Aditivo |
| JWT (string opaque) | Claim interno no modelado en OpenAPI | ✅ Sin cambio de schema publicado |
| `POST /clientes/` `ClienteCreateResponse` | Ya tiene `credenciales_iniciales.requiere_cambio` | ✅ Sin cambio |
| Nuevo `POST /auth/password/change/` | Endpoint nuevo | ✅ Aditivo |
| Respuestas 403 existentes | Nuevo `detail` / `internal_code` | ⚠️ **Comportamiento** cambia, no estructura — clientes deben manejar nuevo caso |
| `UsuarioUpdate` / `UsuarioRead` | Sin cambio obligatorio | ✅ |

### 8.2 Reglas OpenAPI / JSON Schema

- Campos **nuevos opcionales con default** en response → clientes antiguos ignoran el campo (forward-compatible).
- Campos **nuevos en request** solo en endpoint nuevo → sin impacto.
- **No** renombrar ni eliminar campos existentes.
- **No** cambiar `response_model` de login (`Union[Token, LoginEmpresaSelectionResponse]` se mantiene).

### 8.3 Incompatibilidades de comportamiento (no de schema)

| Cambio | Tipo | Cliente afectado |
|--------|------|------------------|
| ERP APIs devuelven 403 si flag activo | Comportamiento | Frontend debe redirigir a pantalla cambio password |
| Refresh devuelve JWT sin flag tras cambio en BD | Comportamiento | Positivo; mobile debe refrescar o llamar `/me` |

### 8.4 Veredicto

| Pregunta | Respuesta |
|----------|-----------|
| ¿Rompe contratos OpenAPI publicados? | **No** (cambios aditivos en schemas) |
| ¿Requiere coordinación frontend? | **Sí** (nuevo campo + manejo 403 + pantalla cambio) |
| ¿Requiere versión API nueva? | **No** estrictamente; basta v1 con extensión aditiva |

---

## 9. Diagrama de alcance del enforcement

```
                    ┌─────────────────────────────────────┐
                    │   POST /auth/login/ (éxito)        │
                    │   JWT.requires_password_change     │
                    └──────────────┬──────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
   WHITELIST (OK)           ENFORCEMENT              EXCLUIDOS
   • /auth/me               get_current_active_user   • is_impersonation
   • /auth/refresh          (733 endpoints)           • platform_admin
   • /auth/password/change  OR require_erp_session    • SSO external
   • /auth/logout           → 403 PASSWORD_CHANGE     • superadmin
   • /empresa/seleccionar
          │
          ▼
   POST /auth/password/change/
   → requiere_cambio_contrasena = 0
   → nuevos JWT (flag false)
          │
          ▼
   ERP APIs (Capa A+B+C) → acceso normal
```

---

## 10. Checklist pre-implementación

- [ ] Elegir punto de inyección: **O3/O5 recomendado** (no solo Capa A)
- [ ] Definir whitelist de rutas auth
- [ ] Confirmar exclusión impersonación y platform_admin
- [ ] Definir `internal_code` estándar: `PASSWORD_CHANGE_REQUIRED`
- [ ] Acordar con frontend: login → change screen → ERP (orden vs empresa selection)
- [ ] Plan de tests: onboarding E2E admin `admin` + password temporal
- [ ] Verificar scripts QA (`run_t1_base_operative_integration.py`, etc.) que consumen `credenciales_iniciales`

---

## 11. Referencia rápida — conteos verificados

```
create_access_token     →  5 files,  11 occ
create_refresh_token    →  4 files,   8 occ
get_current_active_user → 128 files, 733 occ
require_erp_session     →  4 files,  10 occ
require_full_session    →  3 files,  10 occ
validate_erp_operational → 3 files,   6 occ
require_org_company     →  3 files,   8 occ
require_org_tenant      →  3 files,   4 occ
```

Comando de reproducción (desde raíz del repo):

```powershell
.\venv\Scripts\python.exe -c "
import re; from pathlib import Path
root = Path('app')
for name, pat in [
  ('get_current_active_user', r'Depends\(get_current_active_user\)'),
  ('require_erp_session', r'require_erp_session'),
]:
  c = sum(len(re.findall(pat, p.read_text(errors='ignore'))) for p in root.rglob('*.py'))
  print(name, c)
"
```
