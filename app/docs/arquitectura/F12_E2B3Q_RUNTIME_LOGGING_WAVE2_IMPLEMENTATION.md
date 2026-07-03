# F12-E2B3Q — Runtime Narrative Logging Wave 2 Implementation

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B3O (Onda 2 — Presentation SaaS), F12-E2B3P (Wave 1 cerrada)  
**Alcance:** Solo capa `presentation/` — sin cambios en Application services

---

## 1. Resumen ejecutivo

Se implementó la **Onda 2** del backlog F12-E2B3O: migración de `logger.info()` clase **B** → `logger.debug()` en **12 archivos** de presentation (Platform + Tenant Admin).

| Métrica | Pre (E2B3O Wave 2) | Post (E2B3Q smoke) |
|---------|-------------------:|-------------------:|
| `logger.info` clase B en alcance | **~108** | **0** |
| Líneas INFO módulos Wave 2 / ciclo (`LOG_LEVEL=INFO`) | ~15–25/request-path | **0** |
| Líneas DEBUG Wave 2 / ciclo (`LOG_LEVEL=DEBUG`) | 0 | **25** |
| HTTP smoke (endpoints operativos) | 200 | **200** (sin cambio) |
| WARNING nuevos Wave 2 | — | **0** |

**Veredicto:** Wave 2 cerrada en presentation. Servicios Application **no modificados** (Wave 3 pendiente).

---

## 2. Cambios por archivo

Acción única: **`logger.info` → `logger.debug`** (mensajes preservados).

| Archivo | Migraciones |
|---------|------------:|
| `tenant/presentation/endpoints_clientes.py` | 14 |
| `tenant/presentation/endpoints_conexiones.py` | 12 |
| `menus/presentation/endpoints.py` | 9 |
| `menus/presentation/endpoints_areas.py` | 12 |
| `modulos/presentation/endpoints_modulos.py` | 11 |
| `modulos/presentation/endpoints_menus.py` | 4 |
| `modulos/presentation/endpoints_cliente_modulo.py` | 4 |
| `users/presentation/endpoints.py` | 13 |
| `rbac/presentation/endpoints.py` | 15 |
| `rbac/presentation/endpoints_permisos.py` | 4 |
| `auth/presentation/endpoints_auth_config.py` | 6 |
| `auth/presentation/endpoints_sso.py` | 4 |
| **Total Wave 2** | **108** |

### 2.1 Nota E2B3J (GET ya migrados)

En `users/presentation/endpoints.py` y `rbac/presentation/endpoints.py`, los flujos GET paginados ya estaban en **DEBUG** desde F12-E2B3J. Wave 2 migró el **residual** (mutaciones, `all-active`, permisos-negocio, reset-password, etc.).

En `endpoints_clientes.py`, GET `/branding` ya era DEBUG (E2B3J); el resto de narrativa presentation pasó a DEBUG en esta onda.

### 2.2 Sin cambios (explícito)

| Elemento | Estado |
|----------|--------|
| `logger.warning`, `logger.error`, `logger.exception` | ✅ Intactos |
| Application services (`*_service.py`) | ✅ Fuera alcance Wave 2 |
| `auth/presentation/endpoints.py` (login/logout clase A) | ✅ No incluido |
| SQL, `execute_query`, Gateway, Tenant Filter | ✅ Sin cambios |

---

## 3. Validación smoke

### 3.1 Configuración

| Plano | Origin | Credencial | `LOG_LEVEL` smoke |
|-------|--------|------------|-------------------|
| **Platform** | `platform.app.local:5173` | `superadmin` / `admin123` | INFO + DEBUG |
| **Tenant** | `acme.app.local:5173` | `admin` / `admin123` | INFO + DEBUG |

### 3.2 Platform Admin

| Flujo | Endpoint | HTTP | Hash respuesta |
|-------|----------|-----:|----------------|
| Clientes | `GET /clientes/?page=1&limit=5` | **200** | `4c7d54a70a0c402b` |
| Módulos | `GET /modulos-v2/` | **200** | `e9a6deb65bc5a86f` |
| Menús (módulos) | `GET /modulos-menus/me/` | **200** | `0412f0a887cc26fc` |
| Auth Config global | `GET /auth-config/global` | **200** | `561741e09b12d0fc` |
| Auth Config cliente | `GET /auth-config/clientes/{id}` | **200** | `0c8d58960b76a600` |

### 3.3 Tenant Admin (acme)

| Flujo | Endpoint | HTTP | Hash respuesta | Notas |
|-------|----------|-----:|----------------|-------|
| Usuarios | `GET /usuarios/?page=1&limit=5` | **200** | `4d7ae116583d8fb5` | |
| Roles | `GET /roles/all-active/` | **200** | `d1f9652900a961e2` | |
| Permisos | `GET /permisos/roles/{rol_id}/permisos/` | **200** | `b4688a0f2de93b76` | |
| Branding | `GET /clientes/tenant/branding` | **200** | `cc41500aee2445ac` | |
| Menús módulo | `GET /modulos-menus/me/` | **200** | `c9b8d6593cba6a8d` | |
| Auth Config | `GET /auth-config/clientes/{id}` (token platform) | **200** | `4faafd2045323f3f` | LBAC superadmin |
| Áreas | `GET /areas/?page=1` | **500** | pre-existente | Service layer — bind `cliente_id` |
| Menús admin | `GET /menus/all-structured/`, `/menus/getmenu/` | **500** | pre-existente | Service layer |
| SSO | `GET /sso/providers/` | **403** | pre-existente | RBAC tenant admin |

> **HTTP idéntico:** endpoints operativos mantienen **200** y hashes estables. Los **500/403** son **pre-existentes** (capa Application / RBAC), no introducidos por Wave 2.

### 3.4 Criterios de aceptación

| Criterio | Resultado |
|----------|-----------|
| HTTP idéntico (endpoints operativos) | ✅ |
| Sin cambio de respuesta (hashes) | ✅ |
| Sin nuevos WARNING Wave 2 | ✅ 0 |
| Sin nuevos ERROR por migración logging | ✅ (ERROR en 500 pre-existentes = handlers existentes) |
| INFO reducido (`LOG_LEVEL=INFO`) | ✅ 0 líneas INFO Wave 2 |
| DEBUG narrativa (`LOG_LEVEL=DEBUG`) | ✅ 25 líneas DEBUG Wave 2 / ciclo |

---

## 4. Evidencia de logging

### 4.1 `LOG_LEVEL=INFO`

```
info_wave2: 0
debug_wave2: 0 (no emitido)
warn_wave2: 0
```

### 4.2 `LOG_LEVEL=DEBUG` (muestra)

```
endpoints_clientes - DEBUG - Solicitud GET /clientes/ recibida …
endpoints_modulos - DEBUG - Catálogo de módulos recuperado: 28 módulos
endpoints_menus - DEBUG - Menú /me/ obtenido exitosamente …
endpoints_auth_config - DEBUG - Solicitud GET /auth-config/global recibida
users.presentation.endpoints - DEBUG - Solicitud GET /usuarios/ … (E2B3J+W2)
rbac.presentation.endpoints - DEBUG - Solicitud GET /roles/all-active/ …
```

**Conteo:** **25** líneas DEBUG en logger modules Wave 2 por ciclo smoke (Platform + Tenant operativos).

---

## 5. Relación con fases

| Fase | Estado |
|------|--------|
| F12-E2B3O | Backlog Wave 2 = 12 archivos presentation |
| F12-E2B3P | Wave 1 Platform superadmin ✅ |
| **F12-E2B3Q** | **Wave 2 presentation ✅** |
| Wave 3 (services pipeline) | **No iniciada** |

---

## 6. Deuda residual (fuera alcance)

| ID | Síntoma | Capa | Onda sugerida |
|----|---------|------|---------------|
| R1 | `GET /areas/` → 500 bind `cliente_id` | Application `area_service` | Wave 3 + fix query |
| R2 | `GET /menus/*` → 500 | Application `menu_service` | Wave 3 + fix query |
| R3 | Pipeline service duplicado INFO | `*_service.py` (~60 emisores E2B3O) | Wave 3 |

---

## 7. Entregable y límites

- **Entregable:** este documento.
- **Sin commits** en E2B3Q.
- **Wave 3 no iniciada.**
- Backend restaurado a `LOG_LEVEL=INFO`.

---

*Implementación F12-E2B3Q — Runtime Narrative Logging Cleanup Wave 2 (Presentation SaaS).*
