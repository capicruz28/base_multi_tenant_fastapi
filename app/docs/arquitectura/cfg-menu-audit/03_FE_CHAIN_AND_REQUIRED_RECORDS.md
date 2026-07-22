# §6–§7 — Cadena Frontend ↔ Backend y registros necesarios para CFG

---

## §6. Relación ERP_MODULES → Menu → PermissionGuard → usePermission → auth/menu

### 6.1 Hallazgo previo

La constante **`ERP_MODULES` no existe en el Backend**. Es un artefacto de Frontend (mapa de módulos/rutas). El Backend no la lee ni la valida.

### 6.2 Cadena real (dos canales independientes)

```text
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                         │
│  ERP_MODULES / rutas hardcodeadas  →  shell + router             │
│       │                                                          │
│       ├─► GET /api/v1/auth/menu                                  │
│       │      → arma sidebar dinámico (si hay nodos)              │
│       │                                                          │
│       └─► GET /api/v1/auth/permissions/me                        │
│              → PermissionGuard / usePermission()                 │
│              → permite/niega navegación y acciones               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND                                                          │
│  Menú:     cliente_modulo ∩ rol_menu_permiso                     │
│  Permisos: PermissionResolver ← rol_permiso (+ elevaciones)      │
│                                                                  │
│  required_permission en nodos de menú = metadato opcional;       │
│  no es el gate canónico del árbol.                               │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Responsabilidades

| Pieza | Responsabilidad | Fuente de verdad |
|-------|-----------------|------------------|
| `ERP_MODULES` (FE) | Catálogo local de módulos/rutas UI | FE only |
| `GET /auth/menu` | Qué aparece en sidebar | `modulo*` + `cliente_modulo` + `rol_menu_permiso` |
| `GET /auth/permissions/me` | Códigos para `PermissionGuard` / `usePermission` | `rol_permiso` vía Permission Resolver |
| `PermissionGuard` | Bloquear ruta/componente sin permiso API | Lista de `permissions/me` |
| `require_permission` (BE) | 403 en API | Mismo catálogo `permiso` |

### 6.4 Desacoplamiento crítico (CFG hoy)

Un usuario puede:

- Tener `cfg.secuencias.consultar` en `/permissions/me` → FE puede dejar pasar `PermissionGuard`
- Y **no** ver CFG en `/auth/menu` → porque no hay fila en `modulo_menu` / RMP

O al revés (si se sembrara menú sin RP): ver ítem en menú pero fallar al llamar API (403).

**Contrato FE CFG** (`frontend-contracts/cfg/04_RBAC.md`): la entrada de menú “Secuencias de código” debe exigir `cfg.secuencias.consultar`. Eso es regla **FE + RP**, independiente del árbol Backend hasta que el menú dinámico exista.

### 6.5 `required_permission` en el árbol

`menu_permission_resolver` anota permisos `*.leer` por `modulo_id` + recurso inferido del código de menú.  
Para CFG transversal (`permiso.modulo_id IS NULL`, acciones `consultar`/`actualizar`), ese enriquecedor **no** es el mecanismo adecuado para `cfg.secuencias.*` tal como está implementado hoy.

---

## §7. Registros que deberían existir para que aparezca un módulo administrativo CFG

> **Solo inventario.** No implementar. No crear seeds ni migraciones en esta auditoría.

Para que `GET /auth/menu` entregue un nodo CFG (siguiendo el patrón AS-IS de ORG/INV o el de `SYS_ADMIN.TENANT`), el sistema necesitaría **como mínimo**:

### 7.1 Catálogo (global / bootstrap)

| # | Registro | Tabla | Propósito |
|---|----------|-------|-----------|
| R1 | Módulo `CFG` (o decisión de colgar bajo `SYS_ADMIN`) | `modulo` | Contenedor comercial / UI |
| R2 | Sección(es) del módulo (si aplica) | `modulo_seccion` | Agrupación sidebar |
| R3 | Ítem(s) `modulo_menu` (pantalla) | `modulo_menu` | `codigo`, `nombre`, `ruta`, `es_activo`, `es_visible`, `tipo_menu` |
| R4 | Ruta FE coherente | `modulo_menu.ruta` | p.ej. bajo `/admin/...` o `/app/cfg/...` (según decisión de producto alineada a arquitectura; ver §10) |

### 7.2 Contrato comercial

| # | Registro | Tabla | Propósito |
|---|----------|-------|-----------|
| R5 | Activación por tenant | `cliente_modulo` | Q1 exige módulo contratado y activo |

Si CFG se modela como capacidad **dentro de `SYS_ADMIN`** (como IAM), R1/R5 pueden reutilizar el módulo ya activado por `R020` — pero seguirían haciendo falta R3 (y RMP).

### 7.3 Visibilidad UI

| # | Registro | Tabla | Propósito |
|---|----------|-------|-----------|
| R6 | Grants `puede_ver=1` (y flags UI) | `rol_menu_permiso` | Q2 — sin esto el ítem no sale |
| R7 | Asignación usuario↔rol | `usuario_rol` | Une usuario a roles con R6 |

Owner sync / onboarding deberían incluir CFG en el alcance de sync de menú **si** se crea como módulo comercial; hoy `OwnerSync` solo conoce códigos de módulo contratados (ORG, INV, SYS_ADMIN, …).

### 7.4 RBAC API (ya parcialmente presente)

| # | Registro | Tabla | Estado actual |
|---|----------|-------|---------------|
| R8 | `cfg.secuencias.consultar` | `permiso` | **Existe** (`S068`) |
| R9 | `cfg.secuencias.actualizar` | `permiso` | **Existe** (`S068`) |
| R10 | Grant a roles | `rol_permiso` | **Existe** para `ADMIN_TENANT` (`S068` + onboarding `cfg.%`) |
| R11 | `cfg.ver` | `permiso` | **No existe** — no inventariar como requisito Backend |

### 7.5 Matriz “qué falta” vs “qué ya hay”

| Registro | ¿Presente? |
|----------|------------|
| API `/cfg/*` | Sí |
| R8–R10 permisos API | Sí (`ADMIN_TENANT`) |
| R1 módulo CFG en catálogo | **No** |
| R2–R3 menú | **No** |
| R5 `cliente_modulo` CFG | **No** (salvo reutilizar SYS_ADMIN) |
| R6–R7 RMP | **No** |

### 7.6 Criterio de aparición en menú (checklist factual)

Un nodo CFG aparece en `/auth/menu` **solo si**:

1. Existe en catálogo (`modulo_menu` activo/visible + módulo activo)
2. El tenant lo tiene contratado (`cliente_modulo`)
3. El rol del usuario tiene `rol_menu_permiso.puede_ver`
4. No se depende de `cfg.ver` (inexistente)

La navegación útil además requiere R8 en `/permissions/me` para que el FE no bloquee la ruta.
