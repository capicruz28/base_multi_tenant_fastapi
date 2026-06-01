# E2E Runtime Validation — Bootstrap RBAC (Fase 2)

**Fecha:** 2026-05-21  
**Entorno:** Docker `docker-compose up --build` → `fastapi_backend` + BD `bd_sistema` (host SQL Server vía `host.docker.internal`)  
**Alcance:** Validación funcional **sin cambios de código**. Solo lectura + un tenant de prueba `e2evalid01` creado vía API.

---

## Resumen ejecutivo

| Área | Resultado | Notas |
|------|-----------|-------|
| 1. Startup `permission_sync` | **PASS** | 413 permisos activos; `core.app.acceder` activo; log `Permission synced: core.app.acceder` |
| 2. Onboarding runtime (nuevo tenant) | **PASS (BD)** | `e2evalid01`: ORG+SYS_ADMIN, 44 `rol_permiso`, exclusion `tenant.cliente.crear` |
| 2b. Onboarding tenant `prueba` | **FAIL** | Creado sin bootstrap (0 `cliente_modulo`, 0 `rol_permiso`) |
| 3. Login admin tenant nuevo | **FAIL (500)** | Auth OK internamente; respuesta falla validación Pydantic `apellido` |
| 3. Login admin legacy `acme` | **PASS** | Selection token + refresh; multiempresa OK |
| 4. Menú FE (`GET /auth/menu`) | **PASS (acme)** | Módulos `ORG`, `INV`, `SYS_ADMIN` |
| 5. Permisos API | **PASS (acme)** / **PASS (e2e BD)** | Resolver 79 códigos; grants BD correctos en `e2evalid01` |
| 5b. Denegación `tenant.cliente.crear` | **FAIL (acme legacy)** | Legacy tiene el permiso; **PASS** en `e2evalid01` |
| 6. Primera empresa / cambio empresa | **PARCIAL** | `POST /auth/empresa/cambiar/` OK en acme; crear empresa en `e2evalid01` bloqueado por login 500 |
| 7. Tenants legacy | **GAPS** | 3 tenants sin `rol_permiso`; 1 sin `cliente_modulo`; ver `LEGACY_TENANT_REPAIR_PLAN.md` |

### Confirmación explícita (punto 10)

| Pregunta | Respuesta |
|----------|-----------|
| ¿R010/R020 pueden dejar de ejecutarse en entornos **nuevos**? | **Sí**, siempre que: (1) la app arranque al menos una vez (`permission_sync`), (2) los tenants se creen solo vía `POST /clientes/` con el código desplegado. Evidencia: `e2evalid01` sin R010/R020 → 44 grants + ORG/SYS_ADMIN. |
| ¿Qué pasa con tenants **legacy**? | Siguen operando si ya tenían datos de R010/R020/S040; los incompletos (**prueba**, **techcorp**, **global**) requieren reparación. Los con seeds antiguos (**acme**, **innova**) pueden tener permisos de más (p. ej. `tenant.cliente.crear`). |
| ¿Regresión auth/menu/API? | **Auth:** regresión en login respuesta (`apellido` desde `razon_social` con caracteres no permitidos). **Menú:** OK con `as_tenant_admin`. **API:** rutas ORG usan `/api/v1/org/empresa` (singular, sin trailing slash). |

---

## 1. Startup — `permission_sync` y catálogo `permiso`

### Evidencia logs (`fastapi_backend`, reload ~18:32)

```
[RBAC] Permission synced: core.app.acceder
[RBAC] Permission synced: modulos.menu.leer
[RBAC] Permission synced: org.empresa.crear
...
[RBAC] Permission disabled: admin.platform.access  (obsoletos, no en rutas)
```

### Evidencia SQL

```sql
SELECT COUNT(*) AS total_activos FROM permiso WHERE es_activo = 1;
-- Resultado observado: 413

SELECT codigo, es_activo FROM permiso WHERE codigo = 'core.app.acceder';
-- codigo=core.app.acceder, es_activo=1

SELECT codigo FROM permiso WHERE es_activo = 1
  AND codigo IN (
    'org.empresa.crear','org.empresa.leer','modulos.menu.leer',
    'admin.usuario.leer','tenant.cliente.crear'
  );
-- Los 5 códigos presentes en catálogo
```

### Criterios

| Criterio | Estado |
|----------|--------|
| `RBAC_PERMISSION_SYNC_ENABLED` efectivo | OK (sync en cada startup/reload) |
| `core.app.acceder` en BD y activo | OK |
| Catálogo no vacío antes de onboarding | OK (413 > 0) |
| `core.app.acceder` no desactivado por sync | OK (protección `PROTECTED_PERMISSION_CODIGOS`; tests unitarios PASS) |

---

## 2. Onboarding tenant nuevo (`POST /api/v1/clientes/`)

### Tenant de prueba creado en validación

| Campo | Valor |
|-------|-------|
| `subdominio` | `e2evalid01` |
| `cliente_id` | `db40cccc-c3a1-498b-84a5-b5f97c128d40` |
| Credenciales | `admin` / (generada, no reutilizable aquí) |

### Log onboarding (misma transacción)

```
Onboarding RBAC cliente=DB40CCCC-... modulos=['ORG', 'SYS_ADMIN'] rol_permiso_insertados=44
Onboarding completado para cliente ... (e2evalid01)
```

### Evidencia SQL post-onboarding

```sql
-- Módulos base (reemplazo R020)
SELECT m.codigo
FROM cliente_modulo cm
JOIN modulo m ON m.modulo_id = cm.modulo_id
WHERE cm.cliente_id = 'db40cccc-c3a1-498b-84a5-b5f97c128d40' AND cm.esta_activo = 1;
-- ORG, SYS_ADMIN

-- Grants ADMIN_TENANT (reemplazo R010 + prefijos)
SELECT COUNT(*) FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
WHERE rp.cliente_id = 'db40cccc-c3a1-498b-84a5-b5f97c128d40';
-- 44

SELECT p.codigo FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
JOIN permiso p ON p.permiso_id = rp.permiso_id
WHERE rp.cliente_id = 'db40cccc-c3a1-498b-84a5-b5f97c128d40'
  AND p.codigo IN ('core.app.acceder','org.empresa.crear','org.empresa.leer',
                   'modulos.menu.leer','admin.usuario.leer','tenant.cliente.crear');
-- Presentes: core, org.crear, org.leer, modulos.menu.leer, admin.usuario.leer
-- Ausente: tenant.cliente.crear  ← exclusion runtime OK
```

### Checklist onboarding

| Artefacto | Esperado | `e2evalid01` | `prueba` (CL005) |
|-----------|----------|--------------|------------------|
| `cliente` | 1 fila | OK | OK |
| `rol` ×3 | ADMIN/MANAGER/USER | OK | OK |
| `usuario` admin | 1 | OK | OK |
| `usuario_rol` | 1 | OK | OK |
| `cliente_modulo` ORG+SYS_ADMIN | 2 | OK | **0** |
| `rol_permiso` ADMIN_TENANT | >0 | **44** | **0** |

**Conclusión:** El runtime bootstrap **funciona** en tenants creados con el código actual. El tenant `prueba` es evidencia de creación **previa** al bootstrap o sin despliegue del servicio.

---

## 3. Login admin tenant — JWT, refresh, multiempresa

### `acme` (legacy, seed)

| Paso | Endpoint | Resultado |
|------|----------|-----------|
| Login | `POST /api/v1/auth/login/` + `Origin: http://acme.app.local:5173` | `requiere_seleccion_empresa: true`, `selection_token` JWT con `empresa_selection_pending` |
| Selección | `POST /api/v1/auth/empresa/seleccionar/` | `access_token` con `empresa_id`, `empresa_activa` en `user_data` |
| Refresh | Cookie HttpOnly (web) / almacenado en BD | Log `[STORE-TOKEN]` OK |

Payload observado (selection): `user_type=tenant_admin`, `es_admin_cliente=true`.

### `e2evalid01` (onboarding runtime)

| Paso | Resultado |
|------|-----------|
| Auth interno | Log: `Login exitoso`, `admin_sin_empresa=True`, `disponibles=0` |
| Respuesta HTTP | **500** — `UserDataWithRoles`: `apellido` = `razon_social` truncada (`E2E Validation Tenant S.A.`) no pasa validador (punto `.`) |

**No es fallo de RBAC bootstrap**; es validación de perfil en capa presentación. Bloquea E2E login/menú/API para el tenant nuevo hasta corregir (fuera de alcance de esta validación).

---

## 4. Menú frontend — `GET /api/v1/auth/menu`

**Usuario:** `acme` admin, sesión con `empresa_id`.

| Criterio | Resultado |
|----------|-----------|
| `SYS_ADMIN` visible | OK (módulo en respuesta) |
| `ORG` visible | OK |
| Módulos filtrados por `cliente_modulo` | OK (`ORG`, `INV`, `SYS_ADMIN`; coherente con 3 módulos activos en BD) |
| Elevación admin | `as_tenant_admin=True` en resolver — no depende solo de `rol_menu_permiso` |

Warnings en log: ítems SYS_ADMIN sin permiso RBAC inferido (`admin.platform.*`) — **no bloquean** menú; deuda conocida MenuPermissionResolver.

---

## 5. Permisos API — ADMIN_TENANT

### Resolver — `GET /api/v1/auth/permissions/me` (`acme`, sesión ERP)

| Permiso | En lista (79 códigos) |
|---------|----------------------|
| `org.empresa.crear` | Sí |
| `org.empresa.leer` | Sí |
| `modulos.menu.leer` | Sí |
| `admin.usuario.leer` | Sí |
| `tenant.cliente.crear` | **Sí (legacy)** |

### Rutas HTTP (sesión `acme`)

| Ruta | Permiso requerido | HTTP |
|------|-------------------|------|
| `GET /api/v1/org/empresa` | `org.empresa.leer` | **200** |
| `GET /api/v1/usuarios` | `admin.usuario.leer` | 404 ruta (prefijo correcto: `/api/v1/usuarios` sin slash final en prueba errónea) |

### Denegación `tenant.cliente.crear`

| Tenant | `tenant.cliente.crear` en `rol_permiso` | Esperado onboarding |
|--------|----------------------------------------|---------------------|
| `e2evalid01` | No | OK |
| `acme` | Sí (seed/S040 histórico) | Regresión **legacy**, no runtime nuevo |
| `innova` | Sí (auditoría SQL) | Idem |

`POST /api/v1/clientes/` requiere **superadmin** (`require_super_admin`), no ADMIN_TENANT — la denegación real para tenant admin es vía ausencia del permiso en resolver.

---

## 6. Primera empresa y cambio de empresa activa

| Flujo | Tenant | Estado |
|-------|--------|--------|
| Admin sin empresas (`empresa_id` null, no selection) | `e2evalid01` | OK en auth; login HTTP 500 impide FE |
| Secuencia `org_empresa` en onboarding | `e2evalid01` | OK (`cfg_codigo_secuencia` insertada en onboarding) |
| `POST /api/v1/org/empresa` crear | `e2evalid01` | No probado (sin token válido) |
| `POST /api/v1/auth/empresa/cambiar/` | `acme` | **PASS** — `empresa_activa` actualizada, nuevo `access_token` con `empresa_id` |

---

## 7. Idempotencia (diseño + tests)

| Mecanismo | Validación |
|-----------|------------|
| `cliente_modulo` | `IF NOT EXISTS` + `INSERT` en SQL |
| `rol_permiso` | `NOT EXISTS` en `INSERT ... SELECT` |
| Tests unitarios | `test_onboarding_rbac_bootstrap.py` — 5 tests PASS |
| Re-ejecutar onboarding mismo cliente | No probado en E2E (requeriría segundo POST con mismo subdominio → 409) |

---

## 8. Queries SQL de validación (lista exacta)

Ver sección **Anexo A** al final de este documento (copiable a SSMS).

---

## 9. Riesgos pendientes

1. **Login 500** tenant nuevo si `razon_social` tiene caracteres no alfabéticos en `apellido` derivado.
2. **Tenants legacy incompletos** (`prueba`, `techcorp`, `global`) sin grants/módulos.
3. **Tenants legacy sobre-permisivos** (`acme`, `innova`) con `tenant.cliente.crear`.
4. **`core.app.acceder` ausente** en algunos legacy (query `admin_sin_core` listó `acme` en un momento; puede variar tras R010/sync).
5. **Menú SYS_ADMIN** — warnings permisos plataforma no mapeados en `permiso`.
6. **Mismatch sync** — log `Permission sync summary` no aparece; conviene verificar conteo declarados vs BD en CI.
7. **Metadata tenant nuevo** — warning `[METADATA] No se encontró metadata para cliente` (fallback single-DB).

---

## 10. Checklist go-live

- [ ] App arrancada ≥1 vez en PROD (`permission_sync` pobló `permiso`)
- [ ] `SELECT COUNT(*) FROM permiso WHERE es_activo=1` > 0
- [ ] `core.app.acceder` activo
- [ ] Crear tenant vía API y verificar 2 `cliente_modulo` + N `rol_permiso`
- [ ] Login admin nuevo tenant (corregir validación `apellido` si aplica)
- [ ] `GET /auth/menu` muestra ORG + SYS_ADMIN
- [ ] `GET /auth/permissions/me` incluye `org.empresa.crear`, excluye `tenant.cliente.crear`
- [ ] **No** ejecutar R010/R020 en pipeline de tenant nuevo
- [ ] Plan reparación legacy (`LEGACY_TENANT_REPAIR_PLAN.md`)
- [ ] Smoke `POST /auth/empresa/cambiar/` multiempresa

---

## Anexo A — Queries SQL de validación

```sql
-- A1 Catálogo startup
SELECT COUNT(*) AS permisos_activos FROM permiso WHERE es_activo = 1;
SELECT codigo, es_activo, fecha_actualizacion FROM permiso WHERE codigo = 'core.app.acceder';

-- A2 Onboarding por tenant (reemplazar @cliente_id)
DECLARE @cliente_id UNIQUEIDENTIFIER = 'db40cccc-c3a1-498b-84a5-b5f97c128d40';

SELECT c.subdominio, c.codigo_cliente, c.fecha_creacion
FROM cliente c WHERE c.cliente_id = @cliente_id;

SELECT r.codigo_rol, r.nombre FROM rol r
WHERE r.cliente_id = @cliente_id ORDER BY r.codigo_rol;

SELECT u.nombre_usuario, u.correo, u.empresa_default_id
FROM usuario u WHERE u.cliente_id = @cliente_id;

SELECT ur.rol_id, ur.empresa_id FROM usuario_rol ur
JOIN usuario u ON u.usuario_id = ur.usuario_id
WHERE u.cliente_id = @cliente_id;

SELECT m.codigo, cm.esta_activo, cm.fecha_activacion
FROM cliente_modulo cm
JOIN modulo m ON m.modulo_id = cm.modulo_id
WHERE cm.cliente_id = @cliente_id;

SELECT COUNT(*) AS total_rol_permiso_admin
FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
WHERE rp.cliente_id = @cliente_id;

SELECT p.codigo
FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE rp.cliente_id = @cliente_id
ORDER BY p.codigo;

-- A3 Grants críticos ADMIN_TENANT
SELECT p.codigo,
       CASE WHEN EXISTS (
         SELECT 1 FROM rol_permiso rp
         JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
         WHERE rp.cliente_id = @cliente_id AND rp.permiso_id = p.permiso_id
       ) THEN 1 ELSE 0 END AS asignado
FROM permiso p
WHERE p.codigo IN (
  'core.app.acceder','org.empresa.crear','org.empresa.leer',
  'modulos.menu.leer','admin.usuario.leer','tenant.cliente.crear'
) AND p.es_activo = 1;

-- A4 Legacy: tenants sin cliente_modulo
SELECT c.cliente_id, c.subdominio, c.codigo_cliente
FROM cliente c
WHERE c.es_activo = 1
  AND NOT EXISTS (
    SELECT 1 FROM cliente_modulo cm
    WHERE cm.cliente_id = c.cliente_id AND cm.esta_activo = 1
  );

-- A5 Legacy: tenants sin rol_permiso
SELECT c.cliente_id, c.subdominio
FROM cliente c
WHERE c.es_activo = 1
  AND NOT EXISTS (SELECT 1 FROM rol_permiso rp WHERE rp.cliente_id = c.cliente_id);

-- A6 Legacy: ADMIN sin core.app.acceder
SELECT c.subdominio, r.rol_id
FROM cliente c
JOIN rol r ON r.cliente_id = c.cliente_id AND r.codigo_rol = 'ADMIN_TENANT'
WHERE c.es_activo = 1
  AND NOT EXISTS (
    SELECT 1 FROM rol_permiso rp
    JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.codigo = 'core.app.acceder'
    WHERE rp.cliente_id = c.cliente_id AND rp.rol_id = r.rol_id
  );

-- A7 Legacy: ADMIN con tenant.cliente.crear (no deseado post-onboarding)
SELECT c.subdominio
FROM cliente c
JOIN rol r ON r.cliente_id = c.cliente_id AND r.codigo_rol = 'ADMIN_TENANT'
JOIN rol_permiso rp ON rp.cliente_id = c.cliente_id AND rp.rol_id = r.rol_id
JOIN permiso p ON p.permiso_id = rp.permiso_id
WHERE p.codigo = 'tenant.cliente.crear' AND c.es_activo = 1;

-- A8 Secuencias onboarding
SELECT codigo_secuencia, prefijo, ultimo_numero
FROM cfg_codigo_secuencia
WHERE cliente_id = @cliente_id AND codigo_secuencia = 'org_empresa';

-- A9 Refresh tokens post-login
SELECT TOP 5 token_id, usuario_id, fecha_creacion, es_revocado
FROM refresh_token
WHERE cliente_id = @cliente_id
ORDER BY fecha_creacion DESC;
```

---

## Anexo B — Comandos API (desarrollo)

```http
# Login tenant (Origin obligatorio en dev)
POST http://localhost:8000/api/v1/auth/login/
Origin: http://acme.app.local:5173
Content-Type: application/x-www-form-urlencoded
username=admin&password=admin123

POST http://localhost:8000/api/v1/auth/empresa/seleccionar/
Authorization: Bearer <selection_token>
{"empresa_id":"<uuid>"}

GET http://localhost:8000/api/v1/auth/permissions/me
GET http://localhost:8000/api/v1/auth/menu
GET http://localhost:8000/api/v1/org/empresa

# Crear tenant (superadmin)
POST http://localhost:8000/api/v1/clientes/
Origin: http://platform.app.local:5173
Authorization: Bearer <superadmin_token>
```

---

## Referencias

- `RUNTIME_BOOTSTRAP_FLOW.md`
- `RUNTIME_DEPENDENCY_MATRIX.md`
- Tests: `tests/unit/test_core_permission_sync.py`, `tests/unit/test_onboarding_rbac_bootstrap.py`
