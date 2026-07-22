# Comparación de patrones · Dictamen CFG · Matriz · Faltantes

---

## §3. Diferencias ORG · INV · IAM

| Dimensión | ORG | INV | IAM (Tenant Admin) |
|-----------|-----|-----|---------------------|
| ¿Módulo propio en `modulo`? | **Sí** (`ORG`) | **Sí** (`INV`) | **No** (usa `SYS_ADMIN`) |
| Seed catálogo | `S010` | `S010` | `S020` |
| UUID fijos de menú | Sí (`E301…`) | Sí (`E302…`) | No (`NEWID()`) |
| Sección | `PRINCIPAL` | `PRINCIPAL` | `TENANT_ADMIN` |
| Prefijo código menú | `ORG_*` | `INV_*` | `SYS_ADMIN.TENANT.*` |
| Rutas | `/org` → `/app/org` | `/inv` → `/app/inv` | `/admin/*` (sin rewrite S021) |
| Plano FE | `/app` | `/app` | `/admin` |
| `cliente_modulo` | Código `ORG` | Código `INV` | Código `SYS_ADMIN` |
| Activación contrato | Onboarding trial / comercial | Igual | `R020` + trial |
| Owner RMP | Todos los menús del módulo | Todos los menús del módulo | Solo `SYS_ADMIN.TENANT.%` |
| `es_core` / licencia | core=1, licencia=0 | core=0, licencia=1 | core=1, licencia=0 |
| API HTTP de dominio | `/api/v1/org` | `/api/v1/inv` | users/rbac (no `/iam`) |

**Síntesis:** ORG e INV son **módulos ERP de catálogo**. IAM es **capacidad UI** dentro del módulo de sistema `SYS_ADMIN`.

---

## §4. Patrón real de IAM

| Pregunta | Dictamen |
|----------|----------|
| ¿Es un módulo propio? | **No** |
| ¿Qué es? | **Solamente menús** (`modulo_menu`) bajo `modulo=SYS_ADMIN` / `seccion=TENANT_ADMIN` |
| ¿Contrato comercial? | Suscripción a **`SYS_ADMIN`**, no a “IAM” |
| ¿Filtro owner? | Prefijo de código de menú `SYS_ADMIN.TENANT.%` |

---

## §5. Patrón arquitectónico correcto para CFG

### 5.1 Dictamen

**CFG debe seguir el patrón de registro de módulo propio (ORG/INV), con `modulo.codigo = CFG`.**  
**No** el patrón IAM (menú embebido solo en `SYS_ADMIN`).

Esto es determinación de consistencia; **no** es un plan de implementación.

### 5.2 Evidencia (arquitectura aprobada + docs + FE + Backend)

| Fuente | Qué impone |
|--------|------------|
| `cfg-platform-architecture/00` | Código de módulo **`cfg`**; módulo ERP transversal; **no** Platform Administration; **no** extensión ORG/INV |
| `cfg-platform-architecture/04` | Estructura de módulo ERP alineada a ORG/INV; montaje `/cfg`; menú sugerido en **tenant shell ERP**, no SuperAdmin |
| `codigo-generation-admin/00` | Nuevo módulo ERP código **`cfg`** |
| Backend AS-IS | Paquete `app/modules/cfg/` + router `prefix="/cfg"` en `api.py` |
| FE certificado | Contrato “módulo CFG”; base `/api/v1/cfg`; permiso de entrada `cfg.secuencias.consultar` |
| Modelo menú SaaS | Un módulo ERP con API propia se registra en catálogo como fila `modulo` + menús propios (precedente ORG/INV) |

### 5.3 Por qué no el patrón IAM

| Criterio | IAM | CFG |
|----------|-----|-----|
| ¿Existe código de módulo de dominio? | No (`IAM` inexistente) | **Sí** (`cfg` normativo y en código) |
| ¿API bajo prefijo de dominio? | No `/iam` | **Sí** `/cfg` |
| ¿Decisión “módulo ERP”? | No — admin de sistema | **Sí** — explícita |
| ¿Embebido en SYS_ADMIN? | Sí (único contenedor) | Contradiría “código de módulo = cfg” como fila de catálogo |

> Separar ejes: **persona** (ADMIN_TENANT, como IAM) ≠ **registro de catálogo** (módulo propio, como ORG/INV).

### 5.4 Implicación para el plano de ruta FE

La documentación normativa sitúa el menú en el **shell ERP del tenant** (no SuperAdmin).  
El patrón de módulo propio implica, en el modelo actual de rutas:

- Catálogo con rutas tipo `/cfg/...` alineables a `/app/cfg/...` (mismo mecanismo S021/normalizer que ORG/INV), **o** ruta absoluta ya bajo `/app/cfg/...`.

Colocar el ítem solo como `SYS_ADMIN.TENANT.*` bajo `/admin` sería patrón IAM y **no** el patrón de registro coherente con la decisión de módulo `cfg`.

*(La etiqueta UX “Configuración → Secuencias” es agrupación FE; no cambia que el contenedor de catálogo deba ser el módulo `CFG`.)*

---

## §6. Matriz comparativa

Leyenda columna **CFG debería**: estado de registro **coherente con el patrón dictaminado** (§5), no un backlog de implementación.

| Tabla / aspecto | ORG | INV | IAM | CFG debería |
|-----------------|-----|-----|-----|-------------|
| `modulo` | Fila `ORG` | Fila `INV` | Fila `SYS_ADMIN` | Fila **`CFG`** |
| `modulo_seccion` | `PRINCIPAL` | `PRINCIPAL` | `TENANT_ADMIN` (+ otras SYS_ADMIN) | Sección propia del módulo CFG (p.ej. `PRINCIPAL` u equivalente de agrupación) |
| `modulo_menu` | 6 × `ORG_*` | 9 × `INV_*` | 3 × `SYS_ADMIN.TENANT.*` | ≥1 pantalla dominio CFG (p.ej. secuencias), código bajo namespace CFG, **no** `SYS_ADMIN.TENANT.*` |
| Rutas menú | `/app/org/...` | `/app/inv/...` | `/admin/...` | Shell ERP tenant (alineado a `/app/cfg/...` en el modelo SaaS actual) |
| `cliente_modulo` | Por `ORG` | Por `INV` | Por `SYS_ADMIN` | Por **`CFG`** (contrato del módulo) |
| `rol_menu_permiso` | Menús ORG | Menús INV | Solo TENANT.* de SYS_ADMIN | Menús del módulo **CFG** (roles con grant, tipicamente ADMIN_TENANT) |
| Seed catálogo | `S010` | `S010` | `S020` | *(inexistente hoy)* |
| Owner sync código | `ORG` | `INV` | `SYS_ADMIN` + filtro TENANT | Sync por código **`CFG`** (cuando exista catálogo + contrato) |
| Permisos API | `org.*` + `modulo_id` ORG | `inv.*` | `admin.tenant.access` + IAM | `cfg.secuencias.*` (**ya existen**, `modulo_id` NULL) |
| Presente en `/auth/menu` hoy | Sí (si RMP) | Sí (si RMP) | Sí (si RMP) | **No** |

---

## §7. Registros que faltan para que `GET /auth/menu` devuelva CFG

> **Solo inventario.** No crearlos. No SQL. No seeds.

Asumiendo el patrón dictaminado (§5: módulo propio `CFG`):

### 7.1 Catálogo (global)

| ID | Registro faltante | Tabla | Notas |
|----|-------------------|-------|-------|
| F1 | Fila módulo `codigo='CFG'` | `modulo` | Contenedor comercial/UI; hoy **ausente** |
| F2 | Sección(es) del módulo CFG | `modulo_seccion` | Hoy **ausente** |
| F3 | Ítem(s) de pantalla (p.ej. Secuencias de código) | `modulo_menu` | Hoy **ausente**; requiere `ruta`, `codigo`, `es_activo`, `es_visible` |

### 7.2 Contrato por tenant

| ID | Registro faltante | Tabla | Notas |
|----|-------------------|-------|-------|
| F4 | Activación `CFG` por tenant | `cliente_modulo` | Q1 exige módulo contratado; hoy **ausente** (trial actual = ORG, SYS_ADMIN, INV) |

### 7.3 Visibilidad UI

| ID | Registro faltante | Tabla | Notas |
|----|-------------------|-------|-------|
| F5 | Grants `puede_ver` (y flags UI) sobre menús F3 | `rol_menu_permiso` | Por rol (p.ej. ADMIN_TENANT); hoy **ausente** |
| F6 | `usuario_rol` vigente | `usuario_rol` | Debe enlazar usuario → rol con F5 (suele existir para admin; no es gap CFG específico) |

### 7.4 Ya presente (no es gap de menú, pero necesario para navegar FE)

| ID | Registro | Tabla | Estado |
|----|----------|-------|--------|
| P1 | `cfg.secuencias.consultar` | `permiso` | Presente (`S068`) |
| P2 | `cfg.secuencias.actualizar` | `permiso` | Presente (`S068`) |
| P3 | Grants API a ADMIN_TENANT | `rol_permiso` | Presente (`S068` / onboarding `cfg.%`) |

P1–P3 habilitan `/auth/permissions/me` y la API; **no** hacen aparecer CFG en `/auth/menu`.

### 7.5 Checklist mínimo de aparición

```text
F1 ∧ F2 ∧ F3 ∧ F4 ∧ F5  →  CFG puede salir en GET /auth/menu
P1                       →  FE PermissionGuard puede dejar pasar la ruta
```

### 7.6 Qué no falta para el dictamen de patrón

- No hace falta inventar `cfg.ver` (inexistente y no normativo).
- No hace falta fila `modulo.codigo='IAM'`.
- Embebido solo en `SYS_ADMIN` **no** cierra el gap de forma coherente con §5 (sería otro patrón).

---

## Apéndice — Fuentes leídas

- `S010__seed_modulo_menu_completo.sql`
- `S020__seed_admin_menu.sql`
- `S021__menu_routes_saas_alignment.sql`
- `R020__relacion_sys_admin_cliente_modulo.sql`
- `owner_sync_service.py` / `owner_sync_constants.py`
- `onboarding_rbac_service.py` (`TRIAL_MODULES`)
- `cfg-platform-architecture/00`, `04`
- `frontend-contracts/cfg/*`
- `app/modules/cfg/`, `app/api/v1/api.py` (mount `/cfg`)
