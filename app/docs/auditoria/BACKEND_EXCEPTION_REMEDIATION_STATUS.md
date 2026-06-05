# Estado de remediación — manejo de excepciones en Presentation

**Fecha:** 2026-06-02  
**Modo:** solo lectura — sin cambios de código, sin repair, sin commit  
**Referencias:**

| Documento | Rol |
|-----------|-----|
| `BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md` | Auditoría sistémica y estándar normativo |
| `CLIENTES_EXCEPTION_MAPPING_AUDIT.md` | Caso origen (`POST /clientes/` → 500) |
| `TENANT_EXCEPTION_HANDLING_REMEDIATION.md` | Evidencia de cierre P0 |
| Commit `444ade4` | Implementación P0 Tenant |

---

## 1. Resumen ejecutivo

| Estado | Alcance |
|--------|---------|
| **P0 Tenant** | **Cerrado** — `endpoints_clientes.py`, `endpoints_conexiones.py` sin anti-patrón A en handlers de ruta |
| **P1 / P2 / P3** | **No iniciados** — decisión explícita: no implementar más cambios de excepciones hasta nueva autorización |
| **Infraestructura global** | **Correcta** — `CustomException` + `configure_exception_handlers` en `app/main.py` |

Tras P0, el inventario de Presentation queda así:

| Métrica | Antes (auditoría 2026-06-02) | Ahora |
|---------|------------------------------|-------|
| Archivos `presentation` con `except Exception` en rutas | 16 | **14** |
| Bloques `except Exception` (aprox.) | 108 | **~92** |
| Módulos con anti-patrón **crítico** (sin `CustomException` previo) | `tenant` + `auth` (subconjunto) | Solo **`auth`** (config + SSO + handlers sesión) |
| Módulos ERP sin anti-patrón en Presentation | 28 | **28** (sin cambio) |

---

## 2. P0 Tenant — Cerrado

### 2.1 Alcance completado

| Archivo | Handlers remediados | Patrón final |
|---------|---------------------|--------------|
| `tenant/presentation/endpoints_clientes.py` | 10 | Delegación al servicio; propagación de `CustomException` al handler global |
| `tenant/presentation/endpoints_conexiones.py` | 6 | Idem |

### 2.2 Verificación (código actual)

- **Cero** coincidencias de `except Exception` en `app/modules/tenant/presentation/`.
- Excepciones locales permitidas y documentadas:
  - `obtener_cliente`: `HTTPException(404)` si el servicio devuelve `None`.
  - `obtener_branding_tenant`: `RuntimeError` → `HTTPException(400)` (contexto de tenant).

### 2.3 QA registrado

Tests: `tests/unit/test_tenant_exception_propagation.py` (6 passed).  
Detalle en `TENANT_EXCEPTION_HANDLING_REMEDIATION.md`.

**Criterio de aceptación P0:** `ConflictError` en `POST /clientes/` y rutas hermanas dejan de degradarse a HTTP 500.

---

## 3. Módulos que continúan con el anti-patrón

### 3.1 Definición operativa

**Anti-patrón A (crítico):** en un handler de ruta, `except Exception` → `HTTPException(500)` **sin** bloque previo que propague o mapee `CustomException`.

**Anti-patrón B (medio):** mismo `except Exception` → 500, pero **después** de `except CustomException` → `HTTPException(status_code, detail)`. Hoy las reglas de negocio suelen responder bien; el riesgo es deuda técnica y regresión.

**Fail-soft (bajo):** `except Exception` en bloques internos (auditoría, cleanup) que no alteran el status HTTP del endpoint.

### 3.2 Crítico — Patrón A (pendiente P1)

| Módulo | Archivo | Bloques `except Exception` | Captura `CustomException` |
|--------|---------|---------------------------|---------------------------|
| **auth** | `presentation/endpoints_auth_config.py` | 3 | **No** |
| **auth** | `presentation/endpoints_sso.py` | 4 | **No** |

**Rutas afectadas (resumen):**

- Configuración de autenticación por cliente y global (`GET/PUT` auth-config).
- Flujos SSO (inicio, callback, metadatos, errores de proveedor).

**Impacto:** cualquier `ValidationError`, `NotFoundError`, `ConflictError` o `AuthorizationError` lanzada por servicios en estos flujos puede responder **500** en lugar del HTTP de negocio correcto.

### 3.3 Medio-alto — `auth/endpoints.py` (pendiente P2)

| Métrica | Valor |
|---------|-------|
| Bloques `except Exception` | ~26 (incluye anidados / fail-soft) |
| Handlers con `except CustomException: raise` | **1** (`login` — corregido en iteraciones previas) |
| Handlers de ruta con Patrón A estimados | ~10+ |

**Handlers de ruta con riesgo Patrón A (sin re-raise / mapeo previo):**

| Handler | Riesgo típico |
|---------|----------------|
| `seleccionar_empresa_post_login` | `CustomException` de empresa/contexto → 500 |
| `cambiar_empresa_sesion` | Idem |
| `iniciar_impersonacion` / `finalizar_impersonacion` | Idem |
| `get_me` / `read_users_me` | Idem |
| `get_permissions_me` / `get_menu_me` | Idem |
| `refresh_token` (cuerpo principal) | Parcial: algunos tipos mapeados; resto → 500 |
| `get_sessions` / `logout_all_sessions` / `get_all_sessions_admin` | Idem |

**Fail-soft documentado (bajo — no bloquea remediación de negocio):**

- Auditoría interna (`login_failed`, `login_success`, `token_refresh`, `logout_forced`).
- `revoke_err` en refresh.
- Bloques `lookup_db` / contexto en `/me`.

### 3.4 Medio — Patrón B (pendiente P3)

Capturan `CustomException` antes del `except Exception`; **funcionan hoy** para subclases de dominio.

| Módulo | Archivo(s) | Bloques `except Exception` | Bloques `CustomException` (aprox.) |
|--------|------------|---------------------------|-----------------------------------|
| **users** | `presentation/endpoints.py` | 8 | 8 |
| **rbac** | `endpoints.py` | 11 | 11 |
| **rbac** | `endpoints_permisos.py` | 4 | 4 |
| **rbac** | `endpoints_permisos_catalogo.py` | 1 | 1 |
| **menus** | `endpoints.py` | 8 | 8 |
| **menus** | `endpoints_areas.py` | 7 | 7 |
| **modulos** | `endpoints_modulos.py` | 6 | 6+ |
| **modulos** | `endpoints_cliente_modulo.py` | 2 | 8+ |
| **modulos** | `endpoints_menus.py` | 3 | 11+ (1 interno fail-soft) |
| **superadmin** | `endpoints_usuarios.py` | 5 | 5 |
| **superadmin** | `endpoints_auditoria.py` | 4 | 4 |

**Total Patrón B:** ~56 bloques `except Exception` redundantes en **11 archivos** / **6 módulos funcionales**.

### 3.5 Inventario consolidado de archivos con `except Exception` en Presentation

```
app/modules/auth/presentation/endpoints.py              (~26)
app/modules/auth/presentation/endpoints_auth_config.py (3)
app/modules/auth/presentation/endpoints_sso.py         (4)
app/modules/users/presentation/endpoints.py              (8)
app/modules/rbac/presentation/endpoints.py               (11)
app/modules/rbac/presentation/endpoints_permisos.py      (4)
app/modules/rbac/presentation/endpoints_permisos_catalogo.py (1)
app/modules/menus/presentation/endpoints.py              (8)
app/modules/menus/presentation/endpoints_areas.py      (7)
app/modules/modulos/presentation/endpoints_modulos.py  (6)
app/modules/modulos/presentation/endpoints_cliente_modulo.py (2)
app/modules/modulos/presentation/endpoints_menus.py    (3)
app/modules/superadmin/presentation/endpoints_usuarios.py (5)
app/modules/superadmin/presentation/endpoints_auditoria.py (4)
```

**Ya no aparecen en esta lista:**

```
app/modules/tenant/presentation/endpoints_clientes.py    — P0 cerrado
app/modules/tenant/presentation/endpoints_conexiones.py — P0 cerrado
```

---

## 4. Módulos que ya cumplen el estándar

### 4.1 Criterio de cumplimiento

Un módulo se considera **alineado** cuando sus handlers de ruta en `presentation/endpoints*.py`:

- No usan Patrón A (`except Exception` → 500 envolviendo llamadas a servicios con `CustomException`), **o**
- Usan Patrón B/C/D/E documentado en `BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md` de forma que `CustomException` llega al cliente con el HTTP correcto.

### 4.2 Cumplimiento pleno (Patrón D/E — referencia sana)

**Módulos ERP y transaccionales** sin `except Exception` en archivos `presentation/endpoints*.py` analizados:

`aud`, `bdg`, `bi`, `catalogos`, `crm`, `cst`, `dms`, `fin`, `hcm`, `inv`, `invbill`, `log`, `mfg`, `mnt`, `mps`, `mrp`, `org`, `pm`, `pos`, `prc`, `pur`, `qms`, `sls`, `svc`, `tax`, `tkt`, `wfl`, `wms`

**Subconjuntos destacados dentro de módulos mixtos:**

| Módulo | Archivos alineados (sin `except Exception`) |
|--------|---------------------------------------------|
| **tenant** | `endpoints_clientes.py`, `endpoints_conexiones.py` (**P0**) |
| **modulos** | `endpoints_plantillas.py`, `endpoints_secciones.py` |
| **superadmin** | `endpoints_catalogos_globales.py` |
| **org** | Todos los `endpoints_*.py` de presentation (mapeo explícito o propagación) |

### 4.3 Cumplimiento operativo con deuda (Patrón B)

Los módulos **users**, **rbac**, **menus**, **modulos** (parcial), **superadmin** (usuarios, auditoría) **cumplen el contrato HTTP de negocio hoy**, pero mantienen bloques `except Exception` redundantes que no deberían existir en endpoints nuevos según el estándar objetivo (delegación al handler global).

### 4.4 Infraestructura compartida (siempre vigente)

| Componente | Estado |
|------------|--------|
| `app/core/exceptions.py` — jerarquía + handler global | OK |
| `BaseService.handle_service_errors` | OK — re-lanza `CustomException` |
| Respuesta JSON estándar | `{"detail", "error_code"}` |

---

## 5. Prioridad real de remediación futura

> **Nota:** P1/P2/P3 quedan **congelados** hasta nueva decisión de producto/arquitectura. Esta sección describe prioridad **si** se retoma el programa.

| Prioridad | Estado | Alcance | Esfuerzo relativo | Valor |
|-----------|--------|---------|-------------------|-------|
| **P0** | **Cerrado** | `tenant/presentation/*` | — | Bug QA resuelto; administración de clientes estable |
| **P1** | Pendiente | `auth/endpoints_auth_config.py`, `auth/endpoints_sso.py` (7 bloques) | Bajo | Misma superficie “plataforma admin” que tenant; sin Patrón B previo |
| **P2** | Pendiente | `auth/endpoints.py` — handlers de sesión/RBAC/impersonación (~10 rutas) | Medio | Alto tráfico; impacto UX en login post-empresa, `/me`, refresh |
| **P3** | Pendiente | users, rbac, menus, modulos, superadmin (11 archivos, ~56 bloques) | Medio-alto (mecánico) | Simplificación; `error_code` homogéneo; menor riesgo funcional **hoy** |

**Orden recomendado si se reanuda:** P1 → P2 → P3 (no invertir: P3 es deuda, P1 es defecto activo potencial).

**Estrategia técnica acordada (sin cambiar):** eliminar `try/except Exception` en rutas de negocio y delegar `CustomException` al handler global — mismo criterio aplicado en P0 Tenant.

---

## 6. Riesgo de no ejecutar P1/P2 inmediatamente

### 6.1 Matriz de riesgo

| Área | Sin P1 | Sin P2 | Sin P3 |
|------|--------|--------|--------|
| **Administración de clientes (tenant)** | — | — | — |
| **Config auth / SSO (plataforma)** | **Alto** — errores de negocio posibles como 500 | — | — |
| **Login / sesión / empresa activa / impersonación** | — | **Medio-alto** — flujos frecuentes; UX y soporte confundidos | — |
| **Users / RBAC / menús / módulos / superadmin usuarios** | — | — | **Bajo operativo** / **medio mantenimiento** |
| **Módulos ERP (ORG, INV, SLS, …)** | — | — | — |

### 6.2 Riesgos concretos

1. **P1 no ejecutado**
   - Operadores de plataforma que configuren auth por cliente o usen SSO pueden recibir **500** ante conflictos, validaciones o recursos inexistentes, con logs correctos pero respuesta incorrecta (mismo síntoma que `POST /clientes/` antes de P0).
   - Soporte y frontend interpretan fallo de servidor, no regla de negocio.
   - No hay mitigación por Patrón B en esos archivos.

2. **P2 no ejecutado**
   - Tras login exitoso, selección de empresa, cambio de contexto, impersonación y `/me` pueden enmascarar `AuthorizationError` / `ValidationError` / `NotFoundError` como **500**.
   - Impacto en **todos los tenants** y usuarios autenticados, no solo superadmin.
   - El endpoint `login` ya propaga `CustomException`; el resto del módulo auth queda **inconsistente** con P0 y con login.

3. **P3 no ejecutado**
   - **Riesgo funcional bajo a corto plazo:** Patrón B protege respuestas HTTP de negocio.
   - **Riesgo de mantenimiento medio:** nuevos endpoints pueden copiar solo `except Exception` y romper el mapeo; duplicación de ~56 bloques dificulta revisión y CI.
   - Respuestas vía `HTTPException` desde Patrón B pueden **omitir** `error_code` en JSON frente al handler global.

4. **Riesgo sistémico transversal (con P0 cerrado)**
   - La causa raíz **no está eliminada en el repo**, solo **acotada** al dominio tenant en Presentation.
   - Sin gobernanza CI (grep / checklist del estándar), es probable que nuevos endpoints en `auth` o admin reintroduzcan Patrón A.

### 6.3 ¿Es aceptable posponer P1/P2?

| Escenario | Evaluación |
|-----------|------------|
| Solo operación ERP por tenant (sin tocar auth-config/SSO ni flujos post-login problemáticos) | Posponer P1/P2 puede ser **aceptable temporalmente** con monitoreo de 500 en esas rutas |
| Onboarding de clientes, conexiones, branding (tenant API) | **Riesgo mitigado** — P0 cerrado |
| Despliegue activo de SSO o cambios auth-config | **No recomendable** posponer P1 |
| Impersonación, multiempresa post-login, refresh masivo | **No recomendable** posponer P2 |

---

## 7. Estándar vigente (recordatorio)

Norma acordada y aplicada en P0:

1. **Prohibido** en handlers de ruta que llaman servicios con `CustomException`:
   ```python
   except Exception:
       raise HTTPException(status_code=500, ...)
   ```
2. **Permitido:** sin `try/except` en la ruta, o solo `except HTTPException: raise` cuando el handler lanza 404/403 localmente.
3. **Servicios:** siguen lanzando `ValidationError`, `ConflictError`, `NotFoundError`, etc.
4. **Handler global** produce `detail` + `error_code`.

Mapeo HTTP de referencia (sin cambio):

| Excepción | HTTP |
|-----------|------|
| `ConflictError` | 409 |
| `ValidationError` | 400 |
| `NotFoundError` | 404 |
| `AuthorizationError` | 403 |
| `AuthenticationError` | 401 |

---

## 8. Gobernanza sugerida (sin implementar)

Para evitar regresiones mientras P1/P2/P3 están congelados:

| Mecanismo | Objetivo |
|-----------|----------|
| Regla en `.cursorrules` | “Presentation no convierte `CustomException` en 500” |
| Checklist de PR | Confirmar propagación en endpoints nuevos de `auth` y admin |
| Script CI (concepto en auditoría sistémica) | Fallar si `except Exception` + `HTTP_500` en handler sin `CustomException` previo |

---

## 9. Conclusión

1. **P0 Tenant = Cerrado.** Los 16 handlers de clientes y conexiones delegan excepciones de negocio al handler global; el caso `ConflictError` → 500 queda resuelto en ese dominio.

2. **Persisten 14 archivos** de Presentation con `except Exception` (~92 bloques), concentrados en **auth** (crítico/medio-alto) y **administración de identidad/menús** (medio, Patrón B).

3. **~28 módulos ERP** y **tenant post-P0** constituyen la referencia de cumplimiento; no requieren acción inmediata.

4. **Posponer P1/P2** deja riesgo **real y activo** en plataforma auth/SSO y flujos de sesión; **posponer P3** es principalmente riesgo de deuda y regresión en desarrollo futuro, no de producción inmediata en la mayoría de rutas RBAC/users.

5. **No se implementarán más cambios** de manejo de excepciones hasta nueva autorización; este documento fija la línea base para retomar P1/P2/P3 con datos actualizados.

---

## 10. Historial de documentos

| Fase | Documento |
|------|-----------|
| Auditoría sistémica | `BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md` |
| Caso puntual clientes | `CLIENTES_EXCEPTION_MAPPING_AUDIT.md` |
| Implementación P0 | `TENANT_EXCEPTION_HANDLING_REMEDIATION.md` + commit `444ade4` |
| **Estado actual (este documento)** | `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` |
