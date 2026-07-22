# Integración de catálogo — `modulo` / `modulo_seccion` / `modulo_menu`

---

## 1. Dónde registrar CFG

**Archivo canónico:**  
`app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql`

Mismo patrón que ORG/INV (no `S020`).

---

## 2. Registros a crear (especificación de implementación futura)

### 2.1 `modulo`

| Campo | Valor propuesto (implementación) |
|-------|----------------------------------|
| `codigo` | `CFG` |
| `nombre` | p.ej. Configuración de códigos / Motor de códigos |
| `categoria` | coherente con catálogo (p.ej. `configuracion` o `operaciones`) |
| `es_core` / `requiere_licencia` / `orden` / `es_activo` | Definir al implementar; `es_activo=1` obligatorio |
| `modulo_id` | UUID fijo nuevo (siguiente slot tras `E100001B` / convención del seed) |

Actualizar comentarios/conteos del script que digan “27 módulos” → **28**.

### 2.2 `modulo_seccion`

| Campo | Valor |
|-------|--------|
| `modulo_id` | FK al módulo CFG |
| `codigo` | `PRINCIPAL` (patrón ORG/INV) |
| `es_activo` | `1` |

### 2.3 `modulo_menu` (mínimo MVP)

| Campo | Valor aprobado |
|-------|----------------|
| `codigo` | Namespace CFG (p.ej. `CFG_SECUENCIAS`) |
| `nombre` | Secuencias de código (o equivalente FE) |
| `ruta` seed | `/cfg/secuencias` **o** ya `/app/cfg/secuencias` |
| `ruta` FE final | **`/app/cfg/secuencias`** (decisión aprobada) |
| `tipo_menu` | `pantalla` |
| `cliente_id` | `NULL` |
| `es_visible` / `es_activo` | `1` |
| `seccion_id` | sección CFG |

Si se siembra `/cfg/secuencias`, `S021` + normalizer producen `/app/cfg/secuencias`.  
Si se siembra ya `/app/cfg/secuencias`, normalizer/S021 no la alteran.

---

## 3. Qué no tocar en catálogo menú

| Archivo | Acción |
|---------|--------|
| `S020__seed_admin_menu.sql` | **No** registrar CFG aquí |
| Tablas legacy `menu` / `area_menu` | **No** |

---

## 4. Permisos de catálogo (confirmación)

| Archivo | Estado |
|---------|--------|
| `permisos_rbac/S068__permisos_rbac_cfg.sql` | **Ya OK** — `cfg.secuencias.consultar` / `actualizar` |
| Nuevos permisos | **Prohibido** en este plan |

Mantener `modulo_id IS NULL` en S068 (AS-IS). OwnerSync de RP por módulo **no** debe ser el vehículo de estos permisos; ya lo son S068 + `bootstrap_global_grants_admin_tenant`.

---

## 5. Dependencias

| Dependencia | Detalle |
|-------------|---------|
| Downstream | Sin fila `modulo` CFG, onboarding falla al activar `CFG` en trial (`ONBOARDING_MODULOS_BASE_NOT_FOUND`) |
| Downstream | Sin `modulo_menu`, OwnerSync inserta 0 RMP para CFG |
| Upstream | Ninguno nuevo (API ya existe) |
