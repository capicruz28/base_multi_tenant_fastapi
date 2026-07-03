# F12-E2B3I — Runtime Logging Final Cleanup Audit

**Fecha:** 2026-06-28  
**Modo:** Solo auditoría — sin cambios de código  
**Referencias:** F12-E2B3B/C/D/E (baseline), F12-E2B3F (impersonation trace), F12-E2B3G (ORG scope), F12-E2B3H (QUERY DEPRECATED)

---

## 1. Conclusión ejecutiva

Tras F12-E2B3F/G/H, el runtime en `LOG_LEVEL=INFO` con **todas las flags diagnósticas OFF** alcanza el objetivo de las fases de limpieza previas:

| Familia eliminada / gateada | F12-E2B3E | F12-E2B3I (captura actual) |
|-----------------------------|----------:|---------------------------:|
| `[QUERY_AUDITOR]` WARNING | 0 | **0** |
| `authorization.rbac` INFO runtime | 0 | **0** |
| `[MENU_USUARIO]` por ítem | 0 | **0** |
| `[IMPERSONATION-TRACE]` | ~6/ciclo | **0** |
| `[ORG-*]` session scope | ~5/org/empresa | **0** |
| `[QUERY] DEPRECATED` | ~1/menu | **0** |

**Volumen actual (smoke completo Platform + Shared, ~4 s):** **78 líneas** logger aplicación (excl. `permission_startup`, access log uvicorn salvo health).  
**F12-E2B3E comparable (2 planos, ciclo menor):** ~56 líneas → incremento explicado por flujos adicionales en este smoke (branding, usuarios, roles, sesiones admin, logout explícito).

**Ruido residual dominante (backlog producción):**

1. **AUTH narrativo** — múltiples INFO por login/refresh (~12–14 Platform, ~22–26 Shared).
2. **Auditoría + Redis blacklist** — ~11 + ~8 INFO/ciclo completo Shared (operacional útil, volumen alto).
3. **Pipeline admin** — `[ROLES-PAGINADOS]` ×4 + presentation/service duplicado por listado.
4. **`Niveles calculados`** — duplicado `auth_service` + `identity_gateway` (~2/login tenant).
5. **Presentation layer** — `Solicitud GET …` en endpoints admin/branding/sessions.

**Dedicated:** login parcial (`acce`/`admin123` → 401). Emisores observados: `AsyncEngine` lazy + `[AUTH] Contraseña incorrecta` WARNING + `[AUDIT] login_failed`. Paridad de código con Shared para el resto.

**Sin regresiones HTTP** en Platform y Shared. Este documento es el **backlog definitivo** para runtime listo producción; no incluye propuestas de implementación.

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

### 2.2 Smoke ejecutado

| Plano | Tenant | Credencial | Resultado |
|-------|--------|------------|-----------|
| **Platform** | `platform` | `superadmin` / `admin123` | ✅ Ciclo completo |
| **Shared** | `acme` | `admin` / `admin123` | ✅ Ciclo completo |
| **Dedicated** | `acce` | `admin` / `admin123` | ❌ 401 login |

**Flujos por plano:**

| Flujo | Platform | Shared |
|-------|:--------:|:------:|
| login | ✅ | ✅ |
| auth/me | ✅ | ✅ |
| permissions/me | ✅ | ✅ |
| menu | ✅ | ✅ |
| org/empresa | — | ✅ |
| empresa/cambiar | — | ✅ (400 already_active) |
| tenant/branding | — | ✅ |
| usuarios (paginado) | — | ✅ |
| roles (paginado) | — | ✅ |
| auth/sessions | — | ✅ |
| auth/sessions/admin | — | ✅ |
| refresh | ✅ | ✅ |
| logout | ✅ | ✅ |

Dedicated: solo `login` (401) + side-effect `AsyncEngine` tenant.

### 2.3 Leyenda de clasificación

| Clase | Significado | Propuesta de destino |
|-------|-------------|----------------------|
| **A** | Operacional obligatorio | Mantener nivel actual (ERROR/WARNING/INFO startup) |
| **B** | Operacional útil | Mantener **INFO** en producción |
| **C** | Diagnóstico | Emitir solo con **`ENABLE_AUTH_VERBOSE=true`** (u otra flag ya definida F12-E2B1) |
| **D** | Ruido | Migrar a **DEBUG** o consolidar emisores |
| **E** | Deuda técnica | Corregir causa raíz (no silenciar) |

---

## 3. Comparativa volumétrica

| Métrica | F12-E2B3A | F12-E2B3E | F12-E2B3I |
|---------|----------:|----------:|----------:|
| Líneas app / smoke (2 planos) | ~240 | ~56 | **~72** (mismos 2 planos, +logout) |
| Líneas app / smoke extendido | — | ~56 | **78** (incl. branding, users, roles, sessions) |
| Familias P1 cerradas (F/G/H) | activas | parcial | **0 ocurrencias** |

---

## 4. Inventario completo — runtime request-path

Freq. aproximada: **P** = por ciclo Platform, **S** = incremental Shared (tenant admin), **D** = Dedicated login fallido observado.

### 4.1 Autenticación — login / me

| ID | Archivo | Logger | Nivel | Freq | Mensaje (patrón) | Clase | Destino |
|----|---------|--------|-------|-----:|------------------|-------|---------|
| I-01 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 1×/login P+S | `Cliente {id} resuelto y validado para login` | **D** | DEBUG |
| I-02 | `auth/application/services/auth_service.py` | `…auth_service` | INFO | 1×/login | `[AUTH] Intento de login: username=…` | **D** | DEBUG |
| I-03 | `auth_service.py` | `…auth_service` | INFO | 1×/login | `[AUTH] SUPERADMIN detectado…` / `Usuario regular…` | **D** | DEBUG |
| I-04 | `auth_service.py` | `…auth_service` | INFO | 1×/login OK | `[AUTH] Login exitoso: username=…` | **B** | INFO |
| I-05 | `auth_service.py` | `…auth_service` | INFO | 0–1×/login | `[AUTH] Superadmin plataforma: sin empresa…` | **C** | AUTH_VERBOSE |
| I-06 | `auth_service.py` | `…auth_service` | INFO | 1–3×/login+me S | `[AUTH] Admin sin empresa…` / `[AUTH] Empresa login usuario=…` | **C** | AUTH_VERBOSE |
| I-07 | `auth_service.py` | `…auth_service` | INFO | 2×/login P | `Niveles calculados - Usuario … (platform superadmin)` | **D** | DEBUG; emisor único gateway |
| I-08 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 1×/login | `[LOGIN] Superadmin accediendo…` | **D** | DEBUG (dup I-04) |
| I-09 | `auth_service.py` | `…auth_service` | INFO | 1×/login OK | `[LOGIN-V2] Sesión persistida usuario=…` | **B** | INFO |
| I-10 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 1×/login | `Usuario … autenticado exitosamente (MOBILE)` | **B** | INFO (consolidar con I-04) |
| I-11 | `auth_service.py` | `…auth_service` | WARNING | 1×/login D | `[AUTH] Contraseña incorrecta…` | **A** | WARNING |

### 4.2 IdentityGateway

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-20 | `core/identity/identity_gateway.py` | `…identity_gateway` | INFO | 2×/login S | `Niveles calculados - Usuario … type=tenant_admin` | **D** | DEBUG; suprimir dup auth_service |

### 4.3 Refresh / logout

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-30 | `auth_service.py` | `…auth_service` | INFO | 1×/refresh P+S | `[REFRESH-V2] Identidad refresh resuelta…` | **C** | AUTH_VERBOSE |
| I-31 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 2×/refresh | `[REFRESH-MOBILE] Token rotado…` + `…refrescado exitosamente` | **D** | DEBUG o 1× INFO resumen |
| I-32 | `auth_service.py` | `…auth_service` | INFO | 1×/logout | `[LOGOUT-V2-MOBILE] refresh_revoked=…` | **B** | INFO |

### 4.4 Auditoría seguridad + Redis

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-40 | `superadmin/…/audit_service.py` | `…audit_service` | INFO | ~5×/login P | `[AUDIT] auth_audit_log … login_success, session_limit_evicted` | **B** | INFO |
| I-41 | `audit_service.py` | `…audit_service` | INFO | ~2×/refresh | `…refresh_success`, `token_refresh` | **B** | INFO (evaluar dup I-40) |
| I-42 | `audit_service.py` | `…audit_service` | INFO | 1×/logout | `…evento=logout` | **B** | INFO |
| I-43 | `audit_service.py` | `…audit_service` | INFO | 1×/login D | `…login_failed` | **B** | INFO |
| I-44 | `infrastructure/redis/client.py` | `…client` | INFO | ~2×/refresh+logout | `[REDIS_BLACKLIST] Token revocado: jti=… TTL=…` | **B** | INFO prod; DEBUG opcional post-estabilización |

### 4.5 Menú usuario

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-50 | `modulos/…/modulo_menu_service.py` | `…modulo_menu_service` | INFO | 2×/menu | `[MENU_USUARIO] Inicio` + `Fin modulos=…` | **B** | INFO (acordado E2B3C) |
| I-51 | `modulo_menu_service.py` | `…modulo_menu_service` | INFO | 0 | `[MENU_USUARIO] INCLUIDO` / item-level | — | **Cerrado** E2B3C |

### 4.6 Empresa / branding

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-60 | `core/tenant/empresa_preference.py` | `…empresa_preference` | INFO | 1×/cambiar S | `[EMPRESA_PREF] empresa_default_id=…` | **C** | AUTH_VERBOSE |
| I-61 | `tenant/presentation/endpoints_clientes.py` | `…endpoints_clientes` | INFO | 1×/branding S | `Solicitud GET /tenant/branding recibida…` | **D** | DEBUG |
| I-62 | `tenant/…/cliente_service.py` | `…cliente_service` | INFO | 2×/branding S | `Solicitando branding…` / `Branding obtenido exitosamente…` | **D** | DEBUG |

### 4.7 Admin — usuarios / roles

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-70 | `users/presentation/endpoints.py` | `…endpoints` | INFO | 1×/usuarios S | `Solicitud GET /usuarios/ recibida…` | **D** | DEBUG |
| I-71 | `users/…/user_service.py` | `…user_service` | INFO | 1×/usuarios S | `Obteniendo usuarios paginados…` | **D** | DEBUG |
| I-72 | `user_service.py` | `…user_service` | INFO | 2×/usuarios S | `[USUARIOS-PAGINADOS] Procesados…` + `Obtención paginada…completada` | **D** | DEBUG |
| I-73 | `users/presentation/endpoints.py` | `…endpoints` | INFO | 1×/usuarios S | `Lista paginada de usuarios recuperada…` | **D** | DEBUG |
| I-74 | `rbac/presentation/endpoints.py` | `…endpoints` | INFO | 2×/roles S | `Solicitud GET /roles/…` + `Respuesta exitosa…` | **D** | DEBUG |
| I-75 | `rbac/…/rol_service.py` | `…rol_service` | INFO | 5×/roles S | `Obteniendo roles paginados…` + `[ROLES-PAGINADOS]` ×4 | **D** | DEBUG pipeline; 0–1 INFO resumen |

### 4.8 Sesiones IAM

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-80 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 1×/sessions S | `Solicitud /sessions/ recibida para usuario: …` | **D** | DEBUG |
| I-81 | `auth/presentation/endpoints.py` | `…endpoints` | INFO | 2×/sessions/admin S | `[ADMIN] Solicitud /sessions/admin/…` + `Recuperadas N sesiones…` | **D** | DEBUG |

### 4.9 Infraestructura conexión

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-90 | `infrastructure/database/connection_async.py` | `…connection_async` | INFO | 0–1×/tenant D | `[ASYNC_CONNECTION] AsyncEngine creado para tenant_{id}` | **B** | INFO (lazy dedicated/shared cold start) |

### 4.10 Familias cerradas en F12-E2B3F/G/H (verificación 0 en captura)

| ID | Familia | Fase cierre | Freq actual | Clase histórica | Destino aplicado |
|----|---------|-------------|------------:|-------------------|------------------|
| I-X1 | `[QUERY_AUDITOR]` | E2B3B | **0** | E | Gate `ENABLE_QUERY_AUDITOR_VERBOSE` |
| I-X2 | `rbac` INFO `Validando permiso` | E2B3D | **0** | D | DEBUG / AUTH_VERBOSE |
| I-X3 | `[IMPERSONATION-TRACE]` | E2B3F | **0** | C | `ENABLE_IMPERSONATE_DIAG` |
| I-X4 | `[ORG-*]` session scope | E2B3G | **0** | C | `ENABLE_AUTH_VERBOSE` |
| I-X5 | `[QUERY] DEPRECATED` | E2B3H | **0** | E | Migración `text()` consumidores smoke |

### 4.11 Startup (fuera ventana smoke; referencia)

| ID | Archivo | Logger | Nivel | Freq | Mensaje | Clase | Destino |
|----|---------|--------|-------|-----:|---------|-------|---------|
| I-S1 | `core/authorization/permission_startup.py` | `…permission_startup` | WARNING | N×/arranque | `[RBAC] Endpoint sin @RequirePermission…` | **A** | WARNING startup (no request-path) |
| I-S2 | `core/authorization/rbac.py` | `…rbac` | INFO | 1×/arranque | `Sistema de autorización inicializado…` | **A** | INFO startup |

---

## 5. Matriz resumen por clase (backlog producción)

| Clase | ~Líneas / smoke extendido | % aprox. | Acción backlog |
|-------|--------------------------:|---------:|----------------|
| **A** | 1 (Dedicated WARNING) | 1% | Mantener |
| **B** | ~28 | 36% | Mantener INFO; evaluar consolidación audit/redis |
| **C** | ~8–10 (si me re-ejecuta empresa) | 10% | Gate AUTH_VERBOSE |
| **D** | ~38–40 | 51% | DEBUG / consolidar |
| **E** | 0 runtime | 0% | SQL legacy residual fuera smoke (ver E2B3H §8) |

---

## 6. Estimación por endpoint (Shared tenant, post F/G/H)

| Endpoint | ~INFO+WARN app | Principales emisores |
|----------|---------------:|----------------------|
| `POST /auth/login` | 10–14 | auth_service, identity_gateway, audit, endpoints, redis |
| `GET /auth/me` | 0–2 | AUTH empresa (si deps reconstruyen) |
| `GET /auth/menu` | **2** | MENU_USUARIO Inicio+Fin |
| `GET /auth/permissions/me` | 0 | silencioso |
| `GET /org/empresa` | 0 | ORG gateado |
| `POST /auth/empresa/cambiar` | 0–1 | EMPRESA_PREF (si aplica) |
| `GET /clientes/tenant/branding` | 3 | endpoints_clientes, cliente_service |
| `GET /usuarios/` | 4 | endpoints + user_service pipeline |
| `GET /roles/` | 7 | endpoints + rol_service `[ROLES-PAGINADOS]` |
| `GET /auth/sessions/` | 1 | endpoints |
| `GET /auth/sessions/admin/` | 2 | endpoints |
| `POST /auth/refresh` | 6–8 | refresh V2/mobile, redis, audit |
| `POST /auth/logout` | 3–4 | logout V2, redis, audit |
| **Ciclo Shared completo** | **~46–50** | vs ~35–45 estimado E2B3E |

Platform (superadmin, sin tenant admin): **~26 líneas** por ciclo login→menu→refresh→logout.

---

## 7. Dedicated — observaciones

| Aspecto | Resultado |
|---------|-----------|
| Smoke credencial | `acce` + `admin123` → **401** |
| Logs observados | I-01/I-02/I-03 parcial, I-90 AsyncEngine, I-11 WARNING, I-43 audit failed |
| Paridad código | Mismos servicios que Shared; familias F/G/H gateadas igual |
| Gap | Repetir smoke con credencial onboarding real para validar volumen tenant dedicated |

---

## 8. Backlog priorizado (solo clasificación — sin implementación)

| Prioridad | IDs | Clase | Tema |
|-----------|-----|-------|------|
| **P0** | I-40–I-44, I-11, I-S1 | A/B | Auditoría, login fallido, startup RBAC — no reducir |
| **P1** | I-31, I-07/I-20, I-75 | D | Consolidar refresh + niveles + roles pipeline |
| **P2** | I-01–I-03, I-08, I-70–I-74, I-80–I-81 | D | Presentation + AUTH narrativo → DEBUG |
| **P2** | I-05, I-06, I-30, I-60 | C | Gate AUTH_VERBOSE |
| **P3** | I-44 redis TTL detalle | B→DEBUG | Opcional post hardening IAM |
| **Cerrado** | I-X1–I-X5 | — | Verificado 0 ocurrencias |

---

## 9. SQL legacy residual (clase E — fuera del smoke, referencia E2B3H)

Consumidores `execute_query(str)` no ejecutados en este smoke permanecen en codebase (`user_service`, `area_service`, `permiso_service`, etc.). El warning `[QUERY] DEPRECATED` en `queries_async.py` **permanece como guardia**. No emitido en flujos normales validados.

---

## 10. Criterio “runtime listo producción”

| Criterio | Estado F12-E2B3I |
|----------|------------------|
| Flags diagnósticas OFF → sin telemetría opt-in | ✅ |
| Sin QUERY_AUDITOR / rbac INFO / MENU item / IMPERSONATION / ORG / DEPRECATED en smoke | ✅ |
| Eventos seguridad (audit, login failed, blacklist) visibles | ✅ |
| Volumen INFO request-path ≤ umbral operativo | ⚠️ Backlog **D** ~51% líneas — reducible sin perder **B** |
| Dedicated validado E2E | ⚠️ Pendiente credencial |

---

## 11. Conclusión

F12-E2B3F/G/H cerraron las deudas **P1** identificadas en E2B3E. El runtime ya no emite las familias de ruido arquitectónico corregidas. El residual es **previsible y clasificado**: narrativa AUTH, duplicación presentation/service en listados admin, y diagnósticos empresa/refresh candidatos a **AUTH_VERBOSE** o **DEBUG**.

Este informe cierra la serie de auditorías E2B3 y define el backlog para producción **sin continuar a implementación automática**.
