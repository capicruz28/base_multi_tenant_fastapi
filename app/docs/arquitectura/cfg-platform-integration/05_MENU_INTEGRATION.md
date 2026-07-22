# Menú dinámico — integración CFG

---

## 1. Pipeline (sin cambio de código de menú)

`GET /api/v1/auth/menu` → `MenuResolverService` → `ModuloMenuService.obtener_menu_usuario`:

| Query | Condición para ver CFG |
|-------|-------------------------|
| Q1 | `cliente_modulo(CFG)` activo + menús CFG activos/visibles |
| Q2 | `rol_menu_permiso.puede_ver` para rol del usuario |
| Post | `normalize_menu_ruta_for_fe` → garantiza `/app/cfg/secuencias` |

No hay filtro hard-coded que excluya `CFG`. El gap es **datos**, no lógica.

---

## 2. Registros mínimos para aparición automática

| # | Tabla | Registro |
|---|-------|----------|
| 1 | `modulo` | `codigo='CFG'`, `es_activo=1` |
| 2 | `modulo_seccion` | Sección del módulo CFG activa |
| 3 | `modulo_menu` | Pantalla con ruta final `/app/cfg/secuencias`, `es_activo=1`, `es_visible=1` |
| 4 | `cliente_modulo` | Tenant + módulo CFG, `esta_activo=1` |
| 5 | `rol_menu_permiso` | `ADMIN_TENANT` + `menu_id` CFG + `puede_ver=1` |
| 6 | `usuario_rol` | Usuario admin ↔ `ADMIN_TENANT` (ya en onboarding) |

Paralelo (navegación FE / API, no ocultan menú por sí solos):

| # | Tabla | Registro | Estado |
|---|-------|----------|--------|
| 7 | `permiso` | `cfg.secuencias.consultar` (+ actualizar) | **Ya** (S068) |
| 8 | `rol_permiso` | ADMIN_TENANT ↔ esos permisos | **Ya** (S068 + global grants) |

---

## 3. `rol_menu_permiso` — qué hacer para CFG

| Origen | Comportamiento |
|--------|----------------|
| **OwnerSync** al incluir `CFG` en sync trial | Inserta RMP owner sobre menús del módulo (flags ver/crear/editar/… como ORG/INV) |
| Manager Standard | **No** añadir |
| User Standard | **No** añadir |

Resultado seed inicial: **solo ADMIN_TENANT** ve CFG en sidebar.

---

## 4. `rol_permiso` — confirmación

| Permiso | ¿Suficiente? | Integración |
|---------|--------------|-------------|
| `cfg.secuencias.consultar` | Sí | Entrada FE + GET/preview |
| `cfg.secuencias.actualizar` | Sí | PATCH / soft / reactivar |
| `cfg.ver` | No existe | **No crear** |

No modificar S068 ni inventar permisos. Solo asegurar que Dedicated también tenga las filas `permiso` (ver `06`).

---

## 5. Ruta FE aprobada

| Capa | Valor |
|------|--------|
| Decisión producto | `/app/cfg/secuencias` |
| Seed menú | `/cfg/secuencias` o `/app/cfg/secuencias` |
| S021 | Debe cubrir `/cfg/%` si se usa forma corta |
| Normalizer runtime | Antepone `/app` si falta |

---

## 6. Impersonación

`obtener_menu_impersonacion_tenant` usa RMP de `ADMIN_TENANT` del tenant.  
Tras OwnerSync CFG, el operador impersonado verá CFG igual que el admin tenant (mismo pipeline ORG/INV).
