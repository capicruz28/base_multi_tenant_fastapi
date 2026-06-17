# Arranque mínimo — Cliente plataforma (primer despliegue)

> **Obsoleto (2026-06):** usar `scripts/bootstrap_platform.py --apply` en lugar de SQL manual D010 A–E + `repair_platform_rbac.py`. Ver [`DEPLOYMENT_FIRST_INSTALL_GUIDE.md`](DEPLOYMENT_FIRST_INSTALL_GUIDE.md) Fase 4.

Pasos ejecutables **después** de bootstrap SQL (`V010→V030`, `S010→S020`) y **primer arranque** del backend (`permission_sync` OK).

---

## Respuestas directas

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | ¿Comando oficial automático? | **SÍ:** `bootstrap_platform.py --apply` (Docker: `docker exec …`). |
| 2 | ¿Qué ejecutar? | `bootstrap_platform.py --apply` (reemplaza D010 A–E + repair) |
| 3 | ¿Repair obligatorio? | **No** si se usa `--apply` (incluye RBAC). Legacy: `repair_platform_rbac.py` deprecado. |
| 4 | ¿Validación SQL? | Ver §4 al final. |

---

## Prerrequisitos (.env)

Deben coincidir con el seed D010:

```env
SUPERADMIN_CLIENTE_ID=00000000-0000-0000-0000-000000000001
SUPERADMIN_CLIENTE_CODIGO=SUPERADMIN
SUPERADMIN_SUBDOMINIO=platform
SUPERADMIN_USERNAME=superadmin
```

---

## Paso 1 — Seed SQL plataforma (mínimo producción)

**Archivo fuente:** `app/bootstrap_v2/04_qa/D010__seed_bd_central.sql`

**NO ejecutar D010 completo en producción** (crea 5 clientes demo).

### Bloques a ejecutar (en orden)

| Bloque | Líneas D010 | Contenido |
|--------|-------------|-----------|
| A | 13–14 | `USE <tu_bd>;` — **sustituir** `bd_hybrid_sistema_central` por `DB_DATABASE` |
| B | 20–59 | `INSERT cliente` SUPERADMIN (único cliente) |
| C | 986–1005 | `INSERT rol` `ADMIN_PLATFORM` |
| D | 1049–1071 | `INSERT usuario` `superadmin` |
| E | 1129–1135 | Primer `INSERT usuario_rol` (superadmin → ADMIN_PLATFORM) |

### Omitir explícitamente

- Líneas 61–224: clientes demo (ACME, INNOVA, …)
- Secciones 2–5 (módulos/menús — ya vienen de `S010`/`S020`)
- Líneas 1007–1149 restantes: roles/usuarios SUPPORT/USER plataforma (opcionales)
- Línea 1151 en adelante: tenants demo
- Sección 7: permisos — los aplica `repair_platform_rbac.py`

### Comando (ejemplo)

```powershell
# 1. Crear archivo temporal con solo los bloques A–E (USE corregido)
# 2. Ejecutar:
sqlcmd -S <HOST> -d <BD> -U <USER> -P '<PWD>' -C -I -i D010_platform_min.sql -b
```

---

## Paso 2 — UUID y credenciales

| Campo | Valor fijo |
|-------|------------|
| `cliente_id` | `00000000-0000-0000-0000-000000000001` |
| `codigo_cliente` | `SUPERADMIN` |
| `subdominio` | `platform` |
| `rol_id` ADMIN_PLATFORM | `00000000-0000-0000-0000-000000000010` |
| `usuario_id` superadmin | `00000000-0000-0000-0000-000000000100` |
| **Usuario** | `superadmin` |
| **Contraseña** | `admin123` |

> Cambiar contraseña inmediatamente tras el primer login en producción.

---

## Paso 3 — Repair RBAC plataforma (obligatorio)

```bash
python scripts/repair_platform_rbac.py --audit-only
python scripts/repair_platform_rbac.py --apply
```

Docker:

```bash
docker exec -w /app -e PYTHONPATH=/app fastapi_backend python scripts/repair_platform_rbac.py --apply
```

**Qué hace:** activa `cliente_modulo` (SYS_ADMIN) + `rol_permiso` para ADMIN_PLATFORM (incluye `tenant.cliente.crear`).

---

## Paso 4 — Validación SQL (plataforma lista)

Ejecutar en la BD central. Reemplazar el UUID si usó otro (convención: el de arriba).

```sql
DECLARE @cid UNIQUEIDENTIFIER = '00000000-0000-0000-0000-000000000001';

-- 1. Cliente plataforma existe
SELECT codigo_cliente, subdominio, es_activo
FROM cliente WHERE cliente_id = @cid;
-- Esperado: SUPERADMIN, platform, es_activo=1

-- 2. Usuario superadmin + rol
SELECT u.nombre_usuario, r.codigo_rol
FROM usuario u
JOIN usuario_rol ur ON ur.usuario_id = u.usuario_id AND ur.es_activo = 1
JOIN rol r ON r.rol_id = ur.rol_id
WHERE u.cliente_id = @cid AND u.nombre_usuario = 'superadmin';
-- Esperado: ADMIN_PLATFORM

-- 3. Módulo SYS_ADMIN activo (post-repair)
SELECT COUNT(*) AS cm_sysadmin
FROM cliente_modulo cm
JOIN modulo m ON m.modulo_id = cm.modulo_id
WHERE cm.cliente_id = @cid AND cm.esta_activo = 1 AND m.codigo = 'SYS_ADMIN';
-- Esperado: >= 1

-- 4. Grants ADMIN_PLATFORM (post-repair)
SELECT COUNT(*) AS rp_count
FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id
WHERE rp.cliente_id = @cid AND r.codigo_rol = 'ADMIN_PLATFORM';
-- Esperado: >= 5 (típico ~20+)

-- 5. Permiso crítico para crear tenants
SELECT 1 AS ok
FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id
JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE rp.cliente_id = @cid
  AND r.codigo_rol = 'ADMIN_PLATFORM'
  AND p.codigo = 'tenant.cliente.crear';
-- Esperado: 1 fila

-- 6. Catálogo permisos global (startup previo)
SELECT COUNT(*) AS permisos_activos FROM permiso WHERE es_activo = 1;
-- Esperado: > 0
```

**PASS:** los 6 checks OK → puede ejecutar `POST /api/v1/clientes/`.

---

## Paso 5 — Smoke rápido (opcional)

```bash
python scripts/http_smoke_platform_rbac.py --base-url http://localhost:8000
```

Credenciales por defecto del smoke: `superadmin` / `admin123`.

---

## Secuencia completa (checklist)

```
[ ] Bootstrap SQL (V010→V030, S010→S020)
[ ] .env con SUPERADMIN_* alineado al UUID D010
[ ] docker compose up -d  (o uvicorn)
[ ] Log: [RBAC] Permission sync — permiso > 0
[ ] sqlcmd D010_platform_min.sql (bloques A–E)
[ ] python scripts/repair_platform_rbac.py --apply
[ ] Validación SQL §4 — PASS
[ ] POST /api/v1/clientes/  → primer tenant
```

---

## Alternativa QA (no producción)

Ejecutar **D010 completo** con `USE` corregido + repair. Añade 4 tenants demo y usuarios extra. Ver `STAGING_VALIDATION_PIPELINE.md`.
