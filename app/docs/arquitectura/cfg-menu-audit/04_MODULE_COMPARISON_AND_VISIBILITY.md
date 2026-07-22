# §8–§10 — Comparación ORG / IAM / INV vs CFG · Permisos · Visibilidad

---

## §8. ¿ORG / IAM / INV usan el mismo mecanismo? Comparación con CFG

### 8.1 Mecanismo común

**Sí:** todos los ítems del sidebar ERP moderno pasan por el mismo pipeline:

`GET /auth/menu` → `MenuResolver` → `ModuloMenuService` → Q1 (`cliente_modulo`) ∩ Q2 (`rol_menu_permiso`).

No hay un resolver distinto por dominio ORG vs INV vs admin.

### 8.2 Matriz de comparación

| Dimensión | ORG | INV | IAM (usuarios/roles/sesiones) | CFG |
|-----------|-----|-----|-------------------------------|-----|
| Código módulo catálogo | `ORG` (`S010`) | `INV` (`S010`) | **No** hay módulo `IAM` | **Ausente** |
| Dónde vive en menú | Módulo operativo | Módulo operativo | `SYS_ADMIN` / `SYS_ADMIN.TENANT.*` | **Sin fila** |
| Rutas sembradas | `/org/...` → `/app/org/...` | `/inv/...` → `/app/inv/...` | `/admin/usuarios`, `/admin/roles`, `/admin/sesiones` | — |
| Plano FE | `/app` | `/app` | `/admin` | Por definir en catálogo |
| `cliente_modulo` | Sí (trial/onboarding) | Sí (trial) | `SYS_ADMIN` vía `R020` | — |
| Owner RMP sync | Sí (menús ORG) | Sí (menús INV) | Solo `SYS_ADMIN.TENANT.%` | — |
| Permisos API | `org.*.leer/crear/...` con `modulo_id` ORG | `inv.*.…` | `admin.tenant.access` + permisos IAM específicos | `cfg.secuencias.*` (`modulo_id IS NULL`) |
| API de negocio | `/api/v1/org/...` | `/api/v1/inv/...` | Admin/users/rbac | `/api/v1/cfg/...` **certificada** |
| En menú dinámico hoy | Sí (si RMP) | Sí (si RMP) | Sí (si RMP) | **No** |

### 8.3 Lectura arquitectónica

| Dominio | Patrón de menú |
|---------|----------------|
| **ORG / INV** | Módulo ERP comercial propio + rutas `/app/{cod}/...` |
| **IAM** | Capacidad de **administración de tenant** embebida en `SYS_ADMIN` + `/admin/*` |
| **CFG** | Decisión de dominio: **módulo ERP transversal `cfg`** (no Platform, no extensión ORG/INV) — ver `cfg-platform-architecture/00_EXECUTIVE_SUMMARY.md`. **Menú aún no cableado.** |

CFG se parece a ORG/INV en **tipo de módulo API** (ERP + `require_erp_session`), y se parece a IAM en **persona** (ADMIN_TENANT / parametrización). El cableado de menú aún no elige explícitamente entre “módulo `CFG` en `/app/cfg`” vs “ítem bajo `SYS_ADMIN.TENANT` en `/admin`”.

---

## §9. Permisos que debe devolver el Backend para navegar (FE)

### 9.1 Verificación de códigos solicitados

| Código | ¿Existe en Backend/seed? | ¿Otorgado por defecto? | Uso FE (contrato CFG) |
|--------|---------------------------|-------------------------|------------------------|
| `cfg.secuencias.consultar` | **Sí** (`S068`) | **Sí** → `ADMIN_TENANT` | Entrada menú, listado, detalle, preview |
| `cfg.secuencias.actualizar` | **Sí** (`S068`) | **Sí** → `ADMIN_TENANT` | PATCH, desactivar, reactivar |
| `cfg.ver` | **No** | — | **No usar.** No hay equivalente en catálogo Backend |

### 9.2 Canal de entrega al FE

| Necesidad FE | Endpoint | Condición |
|--------------|----------|-----------|
| `usePermission('cfg.secuencias.consultar')` | `GET /auth/permissions/me` | `rol_permiso` (o elevación) |
| Ítem en sidebar dinámico | `GET /auth/menu` | Catálogo + RMP (**hoy ausente para CFG**) |
| Defensa API | `require_permission` en routers CFG | Mismos códigos |

### 9.3 Matriz mínima para “navegar y operar MVP”

| Acción FE | Permiso necesario en `permissions/me` |
|-----------|----------------------------------------|
| Ver módulo / abrir listado | `cfg.secuencias.consultar` |
| Solo lectura (detalle + preview) | `cfg.secuencias.consultar` |
| Editar / soft-delete / reactivar | `cfg.secuencias.consultar` **y** `cfg.secuencias.actualizar` |

Sin `consultar`: el contrato FE manda **ocultar** el módulo completo.

### 9.4 Nota sobre `admin.tenant.access`

Si la UI CFG se monta bajo shell `/admin/*`, el FE puede además exigir `admin.tenant.access` (patrón de plano admin). Eso es **ortogonal** a `cfg.secuencias.*` y ya existe en `S020` para `ADMIN_TENANT`. No sustituye los permisos de negocio CFG.

---

## §10. ¿CFG visible solo para Tenant Admin u otros roles administrativos?

### 10.1 Respuesta según arquitectura existente (no opinión)

**Usuario primario y grant por defecto: Tenant Admin (`ADMIN_TENANT`).**  
**No es exclusivo de Tenant Admin por diseño documental; tampoco es para roles operativos diarios ni para Platform.**

### 10.2 Evidencia normativa / de código

| Fuente | Qué establece |
|--------|----------------|
| `cfg-platform-architecture/00` | Usuario primario: **ADMIN_TENANT** / roles de parametrización del tenant. **No** Platform Administration. |
| `S068` | Grants API solo a `ADMIN_TENANT` en seed |
| `codigo-generation-admin/06_SECURITY_RBAC_AND_FRONTEND.md` | `consultar` tipificado también para **MANAGER_TENANT** / consultor; `actualizar` para ADMIN_TENANT / responsable parametrización |
| `frontend-contracts/cfg/04_RBAC.md` | Visibilidad UI por `cfg.secuencias.consultar` / `actualizar` — **sin** amarrar a un único `codigo_rol` |
| Modelo Owner (menú) | Visibilidad = **RMP del rol** que tenga el usuario; no hay flag “solo tenant admin” en `/auth/menu` |
| `OwnerSync` / trial | Bundles de menú owner apuntan a **ADMIN_TENANT**; Manager/User Standard tienen bundles **distintos** (ORG/INV operativos, no admin motor) |

### 10.3 Lectura arquitectónica consolidada

1. **Plano Platform (`/super-admin`):** CFG **no** pertenece ahí (dato en DEFAULT/tenant; STANDARDS ADMIN vs ERP).
2. **Plano Tenant Admin:** CFG es capacidad de **parametrización del tenant** — audiencia alineada con ADMIN_TENANT (como IAM en espíritu, aunque el dominio sea módulo ERP `cfg`).
3. **Otros roles administrativos / implantación:** la arquitectura RBAC **permite** otorgar `cfg.secuencias.consultar` (y eventualmente `actualizar`) a roles distintos de `ADMIN_TENANT` mediante `rol_permiso` (+ RMP si hay menú). El seed actual **no** lo hace.
4. **Roles operativos (USER / operador INV):** fuera del alcance primario; no hay grant seed ni bundle estándar que les dé CFG.
5. **Visibilidad en menú dinámico:** quien tenga RMP del ítem CFG lo verá; quien no, no — independientemente del nombre del rol. Hoy nadie lo ve porque el ítem no existe.

### 10.4 Conclusión §10 (auditoría)

| Pregunta | Dictamen factual |
|----------|------------------|
| ¿Solo Tenant Admin? | **Por defecto sí** (seed + persona primaria). |
| ¿Pueden otros roles admin/parametrización? | **Sí, arquitectónicamente**, vía grants explícitos RP (+ RMP); ya anticipado en docs de seguridad admin. |
| ¿Debe ser visible a Platform Super Admin como módulo platform? | **No** según decisión de dominio CFG. |
| ¿Debe ser visible a cualquier usuario con sesión ERP? | **No** — Modelo Owner exige permiso API y, para sidebar, RMP. |

---

## Apéndice — Referencias cruzadas

- Menú resolver: `app/docs/MENU_RESOLVER_FLUJO.md`, auditorías RBAC V1
- Seeds: `S010`, `S020`, `S021`, `S068`, `R020`
- Contrato FE CFG: `app/docs/frontend-contracts/cfg/`
- Decisión ERP vs Platform: `app/docs/arquitectura/code-generation/cfg-platform-architecture/`
