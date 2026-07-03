# F12-E2B3E — Runtime Residual Logging Final Audit

**Fecha:** 2026-06-28  
**Modo:** Solo auditoría — sin cambios de código  
**Referencias:** F12-E2B3A (baseline residual), F12-E2B3B (QueryAuditor), F12-E2B3C (Menu), F12-E2B3D (RBAC), F12-G3 (Dedicated alineado)

---

## 1. Conclusión ejecutiva

Tras F12-E2B3B/C/D, el runtime en `LOG_LEVEL=INFO` con flags diagnósticas **OFF** dejó de emitir los tres focos de ruido dominantes de E2B3A:

| Familia | F12-E2B3A (ventana smoke) | Estado actual |
|---------|---------------------------:|---------------|
| `[QUERY_AUDITOR]` WARNING | ~52 | **0** |
| `rbac` INFO por `require_permission` | ~24 | **0** |
| `[MENU_USUARIO]` INFO por ítem | ~18×/menu | **2** (Inicio + Fin) |

**Ruido residual actual** se concentra en:

1. **AUTH** — narrativa duplicada login/me/refresh/logout (~15–20 INFO/ciclo tenant).
2. **`[IMPERSONATION-TRACE]`** — INFO sin flag en refresh y `empresa/cambiar` (~4–6/ciclo).
3. **`[ORG-*]` session scope** — INFO solo `ENVIRONMENT=development` (~4–5 por `GET /org/empresa`).
4. **`[QUERY] DEPRECATED`** — WARNING legacy string SQL (~1× por `GET /auth/menu` tenant).
5. **Listados admin** — `[ROLES-PAGINADOS]` INFO pipeline + presentation layer duplicada.
6. **`Niveles calculados`** — duplicado `auth_service` + `identity_gateway` (~2–4/login tenant).

No se detectaron errores funcionales. El sistema responde HTTP 200 en Platform y Shared durante la captura.

**Limitación de captura Dedicated:** tenants `access`, `acmec`, `acces`, `acce` rechazaron `admin`/`admin123` (401). El plano Dedicated se analiza por **paridad de código** (mismos servicios, `database_type=multi`) más login parcial (`AsyncEngine` tenant + audit `login_failed`). Se recomienda repetir smoke Dedicated con credencial de onboarding real en F12-E2B3F.

---

## 2. Condiciones de auditoría

### 2.1 Configuración efectiva (`fastapi_backend`)

| Variable | Valor |
|----------|-------|
| `LOG_LEVEL` | `INFO` |
| `ENVIRONMENT` | `development` |
| `ENABLE_REDIS_TRACE` | `False` |
| `ENABLE_RBAC_TRACE` | `False` |
| `ENABLE_HTTP_TRACE` | `False` |
| `ENABLE_MIDDLEWARE_TRACE` | `False` |
| `ENABLE_IMPERSONATE_DIAG` | `False` |
| `ENABLE_AUTH_VERBOSE` | `False` |
| `ENABLE_QUERY_AUDITOR_VERBOSE` | `False` |

### 2.2 Pruebas HTTP ejecutadas

| Plano | Tenant | Credencial | Resultado |
|-------|--------|------------|-----------|
| **Platform** | `platform` | `superadmin` / `admin123` | ✅ Smoke completo |
| **Shared** | `acme` | `admin` / `admin123` | ✅ Smoke completo |
| **Dedicated** | `access`, `acmec`, … | `admin` / `admin123` | ❌ 401 (password distinta al seed smoke) |

**Endpoints recorridos (Platform + Shared):**  
`POST /auth/login` → `GET /org/empresa` → `POST /auth/empresa/cambiar` → `GET /auth/me` → `GET /auth/menu` → `GET /auth/permissions/me` → `POST /auth/refresh` → (`GET /users/`, `/roles/`, `/tenant/branding` en corridas extendidas) → logout implícito vía refresh blacklist.

**Captura limpia (1 ciclo Platform + Shared, sin ruido startup):** **56 líneas** logger aplicación en ventana ~15 s (`docker logs --since 15s`, excl. `permission_startup`).

---

## 3. Comparativa volumétrica vs F12-E2B3A

| Métrica | F12-E2B3A | F12-E2B3E (actual) | Δ |
|---------|----------:|-------------------:|---|
| Líneas app / smoke 3 planos (~4 s) | ~240 | ~56 (2 planos, ventana comparable) | **−77%** |
| `[QUERY_AUDITOR]` WARNING | ~52 | **0** | Eliminado |
| `rbac` INFO runtime | ~24 | **0** | Eliminado |
| `[MENU_USUARIO]` INFO / menu | ~35–45 | **2** | −95% |
| `[IMPERSONATION-TRACE]` INFO | ~4 | ~6 (refresh×2 planos + empresa/cambiar) | Similar |
| `[ORG-*]` INFO | ~16 | ~5 (solo Shared org/empresa) | Similar proporción |
| `[QUERY] DEPRECATED` | ~6 | **1** (Shared menu) | Reducido |

---

## 4. Inventario completo residual (runtime request-path)

Cada fila: **archivo**, **logger**, **nivel**, **freq** (por ciclo completo tenant salvo nota), **clasificación**, **justificación**.

### 4.1 Autenticación — `endpoints.py` + `auth_service.py`

| ID | Archivo | Logger | Nivel | Freq | Mensaje (patrón) | Clase |
|----|---------|--------|-------|-----:|------------------|-------|
| L-01 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 1×/login | `Cliente {id} resuelto y validado para login` | **A** |
| L-02 | `auth/application/services/auth_service.py` | `…auth_service` | INFO | 1×/login | `[AUTH] Intento de login: username=…` | **A** |
| L-03 | `auth_service.py` | `…auth_service` | INFO | 1×/login | `[AUTH] SUPERADMIN detectado…` / `Usuario regular…` | **A** |
| L-04 | `auth_service.py` | `…auth_service` | INFO | 1×/login OK | `[AUTH] Login exitoso: username=…` | **A** |
| L-05 | `auth_service.py` | `…auth_service` | INFO | 1×/login | `[AUTH] Superadmin plataforma: sin empresa…` / `Admin sin empresa…` | **C** |
| L-06 | `auth_service.py` | `…auth_service` | INFO | 1–2×/login | `[AUTH] Empresa login usuario=… disponibles=…` | **C** |
| L-07 | `auth_service.py` | `…auth_service` | INFO | 2×/login platform | `Niveles calculados - Usuario … (platform superadmin)` | **D** (dup L-20) |
| L-08 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 1×/login | `[LOGIN] Superadmin accediendo…` / `Usuario … autenticado (MOBILE)` | **A** |
| L-09 | `auth_service.py` | `…auth_service` | INFO | 1×/login OK | `[LOGIN-V2] Sesión persistida usuario=…` | **B** |
| L-10 | `auth_service.py` | `…auth_service` | INFO | 1×/refresh | `[REFRESH-V2] Identidad refresh resuelta…` | **C** |
| L-11 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 2×/refresh | `[REFRESH-MOBILE] Token rotado…` + `…refrescado exitosamente` | **C** |
| L-12 | `auth_service.py` | `…auth_service` | INFO | 1×/logout V2 | `[LOGOUT-V2-MOBILE] refresh_revoked…` | **B** |
| L-13 | `auth_service.py` | `…auth_service` | WARNING | 0–1× | `[AUTH] Contraseña incorrecta…` | **B** (solo fallos) |

**AUTH operacional mínimo recomendado:** L-02, L-04, L-08 (1 línea éxito), L-09.  
**Candidatos a DEBUG/opt-in:** L-05, L-06, L-07, L-10, L-11.

---

### 4.2 IdentityGateway — niveles de acceso

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-20 | `core/identity/identity_gateway.py` | `…identity_gateway` | INFO | 2×/login tenant | `Niveles calculados - Usuario … level=… type=tenant_admin` | **C** |
| L-21 | `auth_service.py` | `…auth_service` | INFO | 2×/login | Idem patrón (re-log en auth) | **D** (duplicado L-20) |

**Justificación:** Cálculo correcto y útil en diagnóstico; en INFO duplica emisión con auth_service.  
**Riesgo eliminar:** Bajo si se conserva una sola fuente (gateway **o** auth).

---

### 4.3 Auditoría seguridad — `audit_service.py`

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-30 | `superadmin/…/audit_service.py` | `…audit_service` | INFO | 1×/evento | `[AUDIT] auth_audit_log registrado: evento=…` | **B** |

Eventos observados: `login_success`, `login_failed`, `session_limit_evicted`, `refresh_success`, `token_refresh`, logout.

**Riesgo eliminar:** **Alto** — trazabilidad seguridad/compliance.

---

### 4.4 Redis blacklist — `redis/client.py`

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-31 | `infrastructure/redis/client.py` | `…redis.client` | INFO | 1–2×/refresh+logout | `[REDIS_BLACKLIST] Token revocado: jti=…` | **B** |

Distinto de `[REDIS-TRACE-01]` (flag-gated, ausente).  
**Riesgo eliminar:** Medio-alto en operaciones IAM.

---

### 4.5 Menú — post F12-E2B3C

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-40 | `modulos/…/modulo_menu_service.py` | `…modulo_menu_service` | INFO | 1×/menu | `[MENU_USUARIO] Inicio usuario=…` | **A** (contrato E2B3C) |
| L-41 | `modulo_menu_service.py` | `…modulo_menu_service` | INFO | 1×/menu | `[MENU_USUARIO] Fin modulos=N duracion_ms=…` | **A** |
| L-42 | `core/authorization/menu_permission_resolver.py` | `…menu_permission_resolver` | WARNING | 0–N×/menu | `MenuPermissionResolver: no se encontró permiso leer para menú …` | **E** / **C** |
| L-43 | `menu_permission_resolver.py` | `…menu_permission_resolver` | DEBUG | — | `error resolviendo menú` | **C** (OK en DEBUG) |

**L-42:** En captura Platform/Shared reciente → **0**. En E2B3A Dedicated `acce` → ~3× (menús SYS_ADMIN sin permiso `leer` mapeado). **Comportamiento esperado** del resolver; no indica fallo HTTP.

---

### 4.6 RBAC runtime — post F12-E2B3D

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-50 | `core/authorization/rbac.py` | `…rbac` | DEBUG | 0 en INFO | Checks permiso / tipo usuario | **C** |
| L-51 | `core/authorization/rbac.py` | `…rbac` | WARNING | 0–N | Acceso denegado / `Intento sin permiso` | **B** |
| L-52 | `core/authorization/rbac.py` | `…rbac` | INFO | **solo startup** | `Inicializando sistema de autorización…` | **A** |

**Veredicto F12-E2B3D:** ✅ Confirmado — **0 INFO rbac** en request-path con flags OFF.

---

### 4.7 QueryAuditor — post F12-E2B3B

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-60 | `core/security/query_auditor.py` | `…query_auditor` | WARNING/ERROR | **0** en smoke | `[QUERY_AUDITOR]…` | — |
| L-61 | `core/security/query_auditor.py` | `…query_auditor` | DEBUG | 0 (flag OFF) | ENGINE_SCOPED esperado | **C** |

**Veredicto F12-E2B3B:** ✅ Confirmado — silencio en runtime normal.

---

### 4.8 ORG session scope — `session_scope.py`

Solo emite si `settings.ENVIRONMENT == "development"`.

| ID | Marcador | Nivel | Freq / `GET /org/empresa` | Clase |
|----|----------|-------|--------------------------:|-------|
| L-70 | `[ORG-SESSION-SCOPE]` | INFO | 2× (dup mismo endpoint) | **C** |
| L-71 | `[ORG-SCOPE-POLICY]` | INFO | 1× | **C** |
| L-72 | `[ORG-ERP-SESSION]` | INFO | 1× | **C** |
| L-73 | `[ORG-TENANT-SCOPE]` | INFO | 1× | **C** |

**Producción (`ENVIRONMENT=production`):** **0 emisiones** — diseño condicional correcto.  
**Riesgo eliminar en dev:** Bajo (diagnóstico scope ERP); **riesgo en prod:** N/A (ya silenciado).

---

### 4.9 Impersonation trace — `impersonation_trace_diag.py`

| ID | Archivo | Logger | Nivel | Freq | Trigger | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-80 | `core/auth/impersonation_trace_diag.py` | `…impersonation_trace_diag` | INFO | 2×/refresh | REQUEST + RESPONSE `/auth/refresh/` | **C** |
| L-81 | Idem | INFO | 2×/empresa/cambiar | REQUEST + RESPONSE (400 esperado) | **C** |

**No depende** de `ENABLE_IMPERSONATE_DIAG` (módulo distinto de `impersonate_auth_diag.py`).  
**Riesgo eliminar:** Bajo en prod si se gatea; medio en RC impersonation debugging.

---

### 4.10 SQL legacy — `queries_async.py` ⚠️ Foco especial §5.1

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-90 | `infrastructure/database/queries_async.py` L382–385 | `…queries_async` | WARNING | **~1×/menu tenant** | `[QUERY] DEPRECATED: execute_query() recibió string SQL` | **D** |

**Origen código:** `modulo_menu_service.py` — ramas `query_raw` / f-string permisos (~L1178, L1223) pasan `str` a `execute_query`.

**Necesario en runtime:** No — es **deuda técnica** de migración a SQLAlchemy Core/TextClause.  
**Riesgo eliminar warning sin migrar:** Medio (oculta deuda); **riesgo migrar SQL:** Medio (requiere tests menu).

---

### 4.11 Infraestructura conexión / routing

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-100 | `connection_async.py` | `…connection_async` | INFO | 1×/tenant lazy | `[ASYNC_CONNECTION] AsyncEngine creado para tenant_…` | **A** (lifecycle) |
| L-101 | `core/tenant/routing.py` | `…routing` | WARNING | 0–1× | `[METADATA] No se encontró metadata… fallback` | **E** |
| L-102 | `core/tenant/empresa_preference.py` | `…empresa_preference` | INFO | 1×/empresa/cambiar | `[EMPRESA_PREF] empresa_default_id=…` | **C** |

---

### 4.12 Listados admin — usuarios / roles

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-110 | `users/presentation/endpoints.py` | `…endpoints` | INFO | 1×/list | `Solicitud GET /usuarios/ recibida…` | **D** |
| L-111 | `users/…/user_service.py` | `…user_service` | INFO | 1×/list | `[USUARIOS-PAGINADOS] Procesados N usuarios…` | **C** |
| L-112 | `users/…/user_service.py` | `…user_service` | DEBUG | 4×/list | Pipeline count/query (mayoría ya DEBUG) | **C** |
| L-113 | `rbac/presentation/endpoints.py` | `…endpoints` | INFO | 1×/list | `Solicitud GET /roles/…` | **D** |
| L-114 | `rbac/…/rol_service.py` | `…rol_service` | INFO | 3–4×/list | `[ROLES-PAGINADOS] Iniciando…` / `Total…` / `Procesados…` | **D** |

---

### 4.13 Branding — tenant

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase |
|----|---------|--------|-------|-----:|---------|-------|
| L-120 | `tenant/…/cliente_service.py` | `…cliente_service` | INFO | 1×/branding | `Solicitando branding para cliente_id=…` | **C** |

---

### 4.14 Rate limiting / infra

| ID | Logger | Nivel | Freq | Clase |
|----|--------|-------|-----:|-------|
| L-130 | `slowapi` | WARNING | 2+ tras ráfagas login | **A** (protección) |

---

### 4.15 Familias silenciadas correctamente (flags OFF — no residual)

Ausentes en captura: `[REDIS-TRACE-01]`, `[RBAC_DEBUG]`, `[TENANT] Host`, `[HTTP] Request/Response` duplicado, `[ME]` verbose, `[IMPERSONATE-AUTH]` middleware diag, `[MENU_USUARIO] INCLUIDO` por ítem.

---

## 5. Análisis focal (sin modificar)

### 5.1 `queries_async` — `[QUERY] DEPRECATED`

| Pregunta | Respuesta |
|----------|-----------|
| ¿Cuántas veces? | **~1 WARNING** por `GET /auth/menu` en tenant Shared; **~1 por menu** en Dedicated (mismo código path) |
| ¿Qué métodos? | `ModuloMenuService.obtener_menu_usuario` → `execute_query(query_raw, params=…)` con SQL string (permisos rol / impersonación) |
| ¿Necesario? | **No** — aviso de migración pendiente |
| ¿Deuda técnica? | **Sí** — único emisor relevante en smoke actual |

**Prioridad F12-E2B3F:** **P1** — migrar queries menu a `text().bindparams()` / Core.

---

### 5.2 `MenuPermissionResolver` — WARNING permiso leer

| Pregunta | Respuesta |
|----------|-----------|
| ¿Anómalo? | **No** en general — menú pantalla sin permiso `*.leer` mapeado en catálogo |
| ¿Esperado? | **Sí** para entradas SYS_ADMIN / rutas sin recurso inferible |
| ¿Impacto HTTP? | Ninguno — menú sigue 200; `required_permission` queda unset |
| Captura actual | **0** Platform/Shared; histórico **~3** Dedicated outlier |

**Clasificación:** **E** (falso positivo operativo) o **C** si se quiere silenciar menús conocidos.

**Prioridad F12-E2B3F:** **P2** — bajar a DEBUG o allowlist códigos menú admin.

---

### 5.3 ORG session scope (`ORG-SESSION-SCOPE`, `ORG-SCOPE-POLICY`, `ORG-ERP-SESSION`, `ORG-TENANT-SCOPE`)

| Pregunta | Respuesta |
|----------|-----------|
| ¿Diagnóstico? | **Sí** — helpers `_log_org_*` en `session_scope.py` |
| ¿Siempre? | **Solo development** — guard `ENVIRONMENT != "development"` → return |
| ¿Logging temporal? | **Sí** — introducido para depuración session scope ORG/INV |
| ¿Prod? | **Ausente** |

**Prioridad F12-E2B3F:** **P2** — flag `ENABLE_ORG_SCOPE_TRACE` o DEBUG-only.

---

### 5.4 IdentityGateway — «Niveles calculados»

- **Emisor canónico:** `identity_gateway.py` L211 (INFO).
- **Duplicado:** `auth_service.py` re-emite en flujo login (~L579 platform, post-lookup tenant).
- **Clase:** **C** (diagnóstico) + **D** (duplicación).
- **Riesgo unificar:** Bajo — mantener solo gateway.

**Prioridad F12-E2B3F:** **P2**.

---

### 5.5 AUTH — qué debe permanecer INFO operacional

| Mantener INFO | Mover a DEBUG / verbose |
|---------------|-------------------------|
| Login fallido (WARNING) | `[AUTH] Empresa login…` detalle numérico |
| `[AUTH] Login exitoso` (1 línea) | `Niveles calculados` duplicado en auth_service |
| `[LOGIN-V2] Sesión persistida` | `[REFRESH-V2] Identidad refresh…` |
| `[AUDIT] auth_audit_log…` | `[REFRESH-MOBILE]` doble línea rotación + éxito |
| `[REDIS_BLACKLIST] Token revocado` | `[AUTH] Superadmin plataforma: sin empresa…` |
| Cliente resuelto login (opcional 1 línea) | Rama SUPERADMIN vs regular (DEBUG) |

---

## 6. Estimación por endpoint (Shared tenant, post-cleanup)

| Endpoint | ~Líneas INFO+WARN app | Principales emisores |
|----------|----------------------:|----------------------|
| `POST /auth/login` | 8–12 | auth_service, identity_gateway, audit, endpoints |
| `GET /org/empresa` | 4–5 | ORG-* (dev only) |
| `POST /auth/empresa/cambiar` | 4–6 | impersonation_trace, auth_service, empresa_pref |
| `GET /auth/me` | 1–2 | auth_service empresa (si deps reconstruyen) |
| `GET /auth/menu` | **3–4** | MENU_USUARIO×2, QUERY DEPRECATED×1, menu_perm WARN 0–N |
| `GET /auth/permissions/me` | 0–1 | (silencioso) |
| `POST /auth/refresh` | 8–10 | impersonation_trace×2, redis×1, audit×2, endpoints×2 |
| `GET /users/` | 2–3 | endpoints + USUARIOS-PAGINADOS INFO |
| `GET /roles/` | 4–5 | endpoints + ROLES-PAGINADOS INFO×3 |
| `GET /tenant/branding` | 1 | cliente_service |
| **Ciclo completo** | **~35–45** | vs ~240 E2B3A |

Platform (superadmin): **~25–30** (menú 2 líneas, sin ORG scope tenant).

---

## 7. Matriz clasificación A / B / C / D / E

| Clase | Significado | Familias actuales |
|-------|-------------|-------------------|
| **A** | Operacional obligatorio | Login exitoso mínimo, audit security, redis blacklist, MENU inicio/fin, slowapi, AsyncEngine lazy |
| **B** | Seguridad | audit_service, login_failed WARNING, rbac denied WARNING |
| **C** | Diagnóstico | ORG-* (dev), impersonation_trace, AUTH empresa/niveles, branding, USUARIOS/ROLES pipeline |
| **D** | Ruido / duplicación | QUERY DEPRECATED, presentation GET logs, ROLES-PAGINADOS INFO×3, Niveles dup |
| **E** | Falso positivo | MenuPermissionResolver WARN en menús admin sin permiso leer; metadata fallback routing |

---

## 8. Riesgo de eliminación / reducción

| ID | Reducir a DEBUG / gate | Riesgo |
|----|------------------------|--------|
| L-30 AUDIT | No | **Alto** — compliance |
| L-31 REDIS_BLACKLIST | No | **Alto** — IAM revoke |
| L-51 rbac WARNING denied | No | **Alto** — intrusion detection |
| L-40–41 MENU inicio/fin | No | **Medio** — observabilidad acordada E2B3C |
| L-80 IMPERSONATION-TRACE | Gate flag | **Medio** — RC impersonation |
| L-70–73 ORG-* | Dev-only OK | **Bajo** en prod (ya off) |
| L-90 QUERY DEPRECATED | Tras migrar SQL | **Medio** — ocultar deuda |
| L-114 ROLES-PAGINADOS | DEBUG | **Bajo** |
| L-07/20 Niveles | Unificar 1 emisor | **Bajo** |

---

## 9. Priorización P0 / P1 / P2 (para F12-E2B3F)

| Prioridad | Item | Acción sugerida (solo diseño) |
|-----------|------|------------------------------|
| **P0** | — | Ninguno — no hay ruido que oculte fallos de seguridad |
| **P1** | L-90 QUERY DEPRECATED | Migrar `modulo_menu_service` raw SQL → Core/TextClause |
| **P1** | L-80 IMPERSONATION-TRACE sin flag | Cablear `ENABLE_IMPERSONATE_DIAG` o flag dedicado RC |
| **P2** | L-70–73 ORG-* dev | Flag `ENABLE_ORG_SCOPE_TRACE` o downgrade DEBUG |
| **P2** | L-07/20 Niveles dup | Eliminar re-log auth_service; conservar IdentityGateway |
| **P2** | L-114 ROLES-PAGINADOS | Alinear con USUARIOS (DEBUG pipeline + 1 INFO resumen) |
| **P2** | L-42 MenuPermissionResolver WARN | DEBUG o suppress list SYS_ADMIN.* |
| **P2** | L-110/113 presentation GET | Eliminar logs espejo en endpoints admin |
| **P3** | L-10/11 REFRESH narrativa | Consolidar 2→1 línea INFO |

---

## 10. Recomendación F12-E2B3F (siguiente fase)

**Nombre sugerido:** F12-E2B3F — Residual Trace Gating & SQL Legacy Cleanup

**Alcance propuesto (implementación futura):**

1. **Gate impersonation trace** — alinear `impersonation_trace_diag.py` con política F12-E2B1.
2. **ORG scope trace** — flag opt-in o DEBUG-only; documentar en `.env.example`.
3. **Migración SQL menu** — eliminar WARNING DEPRECATED (P1).
4. **Dedupe AUTH/Identity** — single source «Niveles calculados».
5. **Admin listados** — misma política que E2B3C: 1 INFO inicio/fin por listado.
6. **Validación Dedicated** — smoke con credencial onboarding real + confirmar paridad volumen.

**Fuera de alcance E2B3F:** RBAC checks, QueryAuditor, MENU_USUARIO (ya cerrados), onboarding, Dedicated DDL.

---

## 11. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿F12-E2B3B/C/D cumplieron objetivo? | **Sí** — eliminaron >75% ruido request-path |
| ¿Queda ruido residual material? | **Sí** — AUTH narrativo, impersonation trace, ORG dev, SQL deprecated, roles paginados |
| ¿Hay regresión funcional? | **No** |
| ¿Dedicated auditado en runtime? | **Parcial** — password smoke; paridad código confirma mismos emisores + DEPRECATED en menu |
| ¿Listo para prod INFO? | **Sí**, con conciencia de ORG-* solo dev y WARNING menu resolver esporádico |

**Estado:** Auditoría F12-E2B3E **cerrada** — entregable documental únicamente; **cero cambios de código**.
