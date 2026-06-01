# Diseño funcional — Bundle `MANAGER_STANDARD` (T2)

## Contexto confirmado (runtime)

- `MANAGER_TENANT` **ya tiene** `rol_permiso` mínimo (`BASE_OPERATIVE`).
- `MANAGER_TENANT` **tiene 0 filas** en `rol_menu_permiso`.
- `GET /auth/menu` **depende** de `rol_menu_permiso` con `puede_ver=1` para incluir menús; si no hay filas ⇒ `modulos=[]`.

**Objetivo T2:** definir un bundle completo **`MANAGER_STANDARD`** que incluya:

- **`rol_permiso`** (permisos API / RBAC) para operación estándar en `ORG` + `INV`.
- **`rol_menu_permiso`** (visibilidad UI / acciones UI por `menu_id`) para que `/auth/menu` muestre módulos y menús.

Sin implementación, sin repair, sin frontend, sin commit.

---

## 1) Catálogo real (BD central) — Menús visibles `ORG` y `INV`

Consulta usada para inventario del catálogo (BD central):

```sql
SELECT
  m.codigo AS modulo_codigo,
  mm.menu_id,
  mm.codigo AS menu_codigo,
  mm.nombre AS menu_nombre,
  mm.ruta AS menu_ruta,
  mm.menu_padre_id,
  mm.nivel,
  mm.tipo_menu,
  mm.orden
FROM modulo_menu mm
INNER JOIN modulo m ON m.modulo_id = mm.modulo_id AND m.es_activo = 1
WHERE mm.es_activo = 1
  AND mm.es_visible = 1
  AND m.codigo IN ('ORG','INV')
ORDER BY m.codigo, mm.nivel, mm.orden;
```

Resultado actual: **15 menús** (todos `tipo_menu='pantalla'`, todos raíz `menu_padre_id IS NULL`).

### 1.1 ORG (6 menús)

- `ORG_MI_EMPRESA` → `menu_id` `E3010001-0000-4000-8000-000000000001` → `/app/org/empresa`
- `ORG_SUCURSALES` → `menu_id` `E3010002-0000-4000-8000-000000000002` → `/app/org/sucursales`
- `ORG_DEPARTAMENTOS` → `menu_id` `E3010003-0000-4000-8000-000000000003` → `/app/org/departamentos`
- `ORG_CARGOS` → `menu_id` `E3010004-0000-4000-8000-000000000004` → `/app/org/cargos`
- `ORG_CENTROS_COSTO` → `menu_id` `E3010005-0000-4000-8000-000000000005` → `/app/org/centros-costo`
- `ORG_PARAMETROS` → `menu_id` `E3010006-0000-4000-8000-000000000006` → `/app/org/parametros`

### 1.2 INV (9 menús)

- `INV_CATEGORIAS` → `menu_id` `E3020002-0000-4000-8000-000000000001` → `/app/inv/categorias`
- `INV_PRODUCTOS` → `menu_id` `E3020001-0000-4000-8000-000000000002` → `/app/inv/productos`
- `INV_UNIDADES` → `menu_id` `E3020003-0000-4000-8000-000000000003` → `/app/inv/unidades-medida`
- `INV_ALMACENES` → `menu_id` `E3020004-0000-4000-8000-000000000004` → `/app/inv/almacenes`
- `INV_STOCK` → `menu_id` `E3020005-0000-4000-8000-000000000005` → `/app/inv/stock`
- `INV_TIPOS_MOV` → `menu_id` `E3020006-0000-4000-8000-000000000006` → `/app/inv/tipos-movimiento`
- `INV_MOVIMIENTOS` → `menu_id` `E3020007-0000-4000-8000-000000000007` → `/app/inv/movimientos`
- `INV_INV_FISICO` → `menu_id` `E3020008-0000-4000-8000-000000000008` → `/app/inv/inventario-fisico`
- `INV_INV_KARDEX` → `menu_id` `E3020009-0000-4000-8000-000000000009` → `/app/inv/kardex`

---

## 2) Reglas de exclusión (explícitas)

`MANAGER_STANDARD` **DEBE EXCLUIR**:

- `SYS_ADMIN` en cualquiera de sus variantes (incluye administración de tenant).
- `PLATFORM.*`
- `CATALOGOS.*`
- configuración global / administración de tenant (cualquier menú no-operativo).

En esta versión del diseño, esto se cumple “por construcción” al limitar el bundle a módulos **`ORG`** e **`INV`** y sus `menu_id` visibles.

---

## 3) Permisos requeridos por menú (cómo se infieren)

### 3.1 Fuente de verdad en backend

El backend enriquece el árbol de menú con un `required_permission` por menú (metadata), con el resolver:

- `app/core/authorization/menu_permission_resolver.py`

Algoritmo (resumen):

- infiere `recurso` desde `menu_codigo`: toma el último segmento al dividir por `_` (ej. `ORG_SUCURSALES` → `sucursales` → normaliza singular).
- busca en catálogo `permiso` el código con:
  - `accion='leer'`
  - `modulo_id` del módulo del menú
  - `recurso` compatible
- asigna `required_permission = <permiso.codigo>`

### 3.2 Catálogo real de permisos `.leer` para ORG/INV

Consulta (BD central):

```sql
SELECT p.codigo, p.modulo_id, p.recurso, p.accion, m.codigo AS modulo_codigo
FROM permiso p
INNER JOIN modulo m ON m.modulo_id = p.modulo_id AND m.es_activo = 1
WHERE p.es_activo = 1
  AND p.accion = 'leer'
  AND m.codigo IN ('ORG','INV')
ORDER BY m.codigo, p.recurso;
```

Permisos de lectura existentes (14):

- ORG:
  - `org.empresa.leer`
  - `org.sucursal.leer`
  - `org.departamento.leer`
  - `org.cargo.leer`
  - `org.centro_costo.leer`
  - `org.parametro.leer`
- INV:
  - `inv.categoria.leer`
  - `inv.producto.leer`
  - `inv.unidad_medida.leer`
  - `inv.almacen.leer`
  - `inv.stock.leer`
  - `inv.tipo_movimiento.leer`
  - `inv.movimiento.leer`
  - `inv.inventario_fisico.leer`

### 3.3 Gap detectado: `KARDEX`

El menú `INV_INV_KARDEX` infiere `recurso='kardex'`, pero el catálogo de permisos no contiene ningún:

- `permiso.recurso='kardex'` para INV, ni
- `codigo LIKE 'inv.%kardex%'`

Por lo tanto, el resolver no puede asignar `required_permission` para ese menú (hoy quedaría `None` / warning).

**Decisión de diseño para T2 (propuesta):**

- **Opción A (recomendada para RC):** excluir `INV_INV_KARDEX` del bundle hasta que exista `inv.kardex.leer` en catálogo.
- **Opción B:** incluirlo con `rol_menu_permiso.puede_ver=1` pero documentar que carece de `required_permission` (y requiere fix previo de catálogo).

Este documento define el bundle “cerrado” con **Opción A** (excluye Kardex).

---

## 4) Definición del bundle `MANAGER_STANDARD`

### 4.1 Menús visibles (rol_menu_permiso) — incluidos

**Incluidos (14)**:

ORG (6):
- `E3010001-0000-4000-8000-000000000001` (`ORG_MI_EMPRESA`)
- `E3010002-0000-4000-8000-000000000002` (`ORG_SUCURSALES`)
- `E3010003-0000-4000-8000-000000000003` (`ORG_DEPARTAMENTOS`)
- `E3010004-0000-4000-8000-000000000004` (`ORG_CARGOS`)
- `E3010005-0000-4000-8000-000000000005` (`ORG_CENTROS_COSTO`)
- `E3010006-0000-4000-8000-000000000006` (`ORG_PARAMETROS`)

INV (8):
- `E3020002-0000-4000-8000-000000000001` (`INV_CATEGORIAS`)
- `E3020001-0000-4000-8000-000000000002` (`INV_PRODUCTOS`)
- `E3020003-0000-4000-8000-000000000003` (`INV_UNIDADES`)
- `E3020004-0000-4000-8000-000000000004` (`INV_ALMACENES`)
- `E3020005-0000-4000-8000-000000000005` (`INV_STOCK`)
- `E3020006-0000-4000-8000-000000000006` (`INV_TIPOS_MOV`)
- `E3020007-0000-4000-8000-000000000007` (`INV_MOVIMIENTOS`)
- `E3020008-0000-4000-8000-000000000008` (`INV_INV_FISICO`)

**Excluido (1)**:
- `E3020009-0000-4000-8000-000000000009` (`INV_INV_KARDEX`) — por gap de catálogo de permisos.

### 4.2 Política de acciones UI (rol_menu_permiso)

Propuesta de política (alineada a “manager estándar”):

- **Restricción aprobada (no eliminar para MANAGER_STANDARD)**:
  - Mantener `leer`, `crear`, `actualizar` (UI: `ver`, `crear`, `editar`)
  - Excluir `eliminar` (UI: `eliminar=0`) para **todos** los recursos ORG e INV

- catálogos ORG/INV: `ver=1`, `crear=1`, `editar=1`, `eliminar=0`, `exportar=1`, `imprimir=0`, `aprobar=0`
- operaciones INV (movimientos / inventario físico): `ver=1`, `crear=1`, `editar=1`, `eliminar=0`, `exportar=1`, `imprimir=1`, `aprobar=1`
- stock: `ver=1`, `crear=0`, `editar=1`, `eliminar=0`, `exportar=1`, `imprimir=0`, `aprobar=0`

Nota: `rol_menu_permiso` es UI; la seguridad real es `rol_permiso`. En implementación T2, idealmente se mantiene coherencia entre ambos.

### 4.3 Permisos API (rol_permiso) — incluidos

Consulta usada para inventario de permisos por recurso/acción (BD central):

```sql
SELECT m.codigo AS modulo_codigo, p.recurso, p.accion, p.codigo
FROM permiso p
INNER JOIN modulo m ON m.modulo_id = p.modulo_id AND m.es_activo = 1
WHERE p.es_activo = 1
  AND m.codigo IN ('ORG','INV')
  AND p.recurso IN (
    'empresa','sucursal','departamento','cargo','centro_costo','parametro',
    'categoria','producto','unidad_medida','almacen','stock','tipo_movimiento',
    'movimiento','inventario_fisico'
  )
ORDER BY m.codigo, p.recurso, p.accion;
```

Permisos disponibles (catálogo) para estos recursos:

- ORG (6 recursos, 4 acciones cada uno): `leer`, `crear`, `actualizar`, `eliminar`
- INV:
  - catálogos (`categoria`, `producto`, `unidad_medida`, `almacen`, `tipo_movimiento`): `leer`, `crear`, `actualizar`, `eliminar`
  - `stock`: `leer`, `crear`, `actualizar` (no hay `eliminar` en catálogo actual)
  - `movimiento`: `leer`, `crear`, `actualizar`, `anular`, `autorizar`, `procesar`
  - `inventario_fisico`: `leer`, `crear`, `actualizar`, `anular`, `aprobar`, `finalizar`

#### 4.3.1 `rol_permiso` — baseline mínimo (T2)

Para que `MANAGER_STANDARD` sea consistente con los menús incluidos y las acciones UI propuestas, este diseño define:

- **Siempre incluir** (T1 / BASE_OPERATIVE):
  - `core.app.acceder`
  - `tenant.branding.leer`
  - `org.empresa.leer`

- **ORG (6 pantallas / gestión estándar)**:
  - **Restricción aprobada (no administración de empresas)**:
    - Mantener `org.empresa.leer` (ya está en T1 / BASE_OPERATIVE)
    - Excluir `org.empresa.crear`, `org.empresa.actualizar`, `org.empresa.eliminar` (exclusivo de `ADMIN_TENANT`)
  - **Restricción aprobada (no eliminar para MANAGER_STANDARD)**:
    - Excluir `*.eliminar` en todos los recursos ORG/INV (exclusivo de `ADMIN_TENANT`)
  - `org.sucursal.*`: `leer`, `crear`, `actualizar`
  - `org.departamento.*`: `leer`, `crear`, `actualizar`
  - `org.cargo.*`: `leer`, `crear`, `actualizar`
  - `org.centro_costo.*`: `leer`, `crear`, `actualizar`
  - `org.parametro.*`: `leer`, `crear`, `actualizar`

- **INV (8 pantallas incluidas)**:
  - catálogos:
    - `inv.categoria.*`: `leer`, `crear`, `actualizar`
    - `inv.producto.*`: `leer`, `crear`, `actualizar`
    - `inv.unidad_medida.*`: `leer`, `crear`, `actualizar`
    - `inv.almacen.*`: `leer`, `crear`, `actualizar`
    - `inv.tipo_movimiento.*`: `leer`, `crear`, `actualizar`
  - stock (operación estándar):
    - `inv.stock.leer`
    - `inv.stock.actualizar`
    - (excluido por diseño) `inv.stock.crear` — opcional, solo si existe caso de uso explícito
  - movimientos (operativo):
    - `inv.movimiento.leer`
    - `inv.movimiento.crear`
    - `inv.movimiento.actualizar`
    - `inv.movimiento.procesar`
    - `inv.movimiento.autorizar`
    - `inv.movimiento.anular`
  - inventario físico (operativo):
    - `inv.inventario_fisico.leer`
    - `inv.inventario_fisico.crear`
    - `inv.inventario_fisico.actualizar`
    - `inv.inventario_fisico.finalizar`
    - `inv.inventario_fisico.aprobar`
    - `inv.inventario_fisico.anular`

> Nota: este bundle evita cualquier `SYS_ADMIN.*`, `PLATFORM.*`, `CATALOGOS.*`, `tenant.*` administrativo y permisos no-operativos.

---

## 5) Registros esperados a generar

### 5.1 `rol_menu_permiso` esperado (MANAGER_STANDARD)

**Cantidad esperada:** **14 filas** (1 por `menu_id` incluido), con:

- `cliente_id = <tenant.cliente_id>`
- `rol_id = <rol_id de MANAGER_TENANT>`
- `empresa_id = NULL` (tenant-wide)
- flags según política (4.2)

#### SQL esperado (plantilla)

```sql
-- Insert idempotente: 14 menu_ids (ORG/INV sin Kardex)
INSERT INTO rol_menu_permiso (
  rol_menu_permiso_id, cliente_id, rol_id, menu_id, empresa_id,
  puede_ver, puede_crear, puede_editar, puede_eliminar,
  puede_exportar, puede_imprimir, puede_aprobar,
  fecha_creacion
)
SELECT
  NEWID(), :cliente_id, :manager_rol_id, x.menu_id, NULL,
  x.puede_ver, x.puede_crear, x.puede_editar, x.puede_eliminar,
  x.puede_exportar, x.puede_imprimir, x.puede_aprobar,
  GETDATE()
FROM (
  -- ORG (catálogos)
  SELECT CAST('E3010001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER) AS menu_id, 1 AS puede_ver, 1 AS puede_crear, 1 AS puede_editar, 0 AS puede_eliminar, 1 AS puede_exportar, 0 AS puede_imprimir, 0 AS puede_aprobar
  UNION ALL SELECT CAST('E3010002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3010003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3010004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3010005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3010006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0

  -- INV (catálogos)
  UNION ALL SELECT CAST('E3020002-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3020001-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3020003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3020004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0
  UNION ALL SELECT CAST('E3020006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 1,1,1,0,1,0,0

  -- INV (operativo)
  UNION ALL SELECT CAST('E3020005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER), 1,0,1,0,1,0,0  -- stock
  UNION ALL SELECT CAST('E3020007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER), 1,1,1,0,1,1,1  -- movimientos
  UNION ALL SELECT CAST('E3020008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER), 1,1,1,0,1,1,1  -- inventario físico
) AS x
WHERE NOT EXISTS (
  SELECT 1 FROM rol_menu_permiso rmp
  WHERE rmp.cliente_id = :cliente_id
    AND rmp.rol_id = :manager_rol_id
    AND rmp.menu_id = x.menu_id
    AND rmp.empresa_id IS NULL
);
```

### 5.2 `rol_permiso` esperado (MANAGER_STANDARD)

**Conteo esperado (si se aplica exactamente este diseño):**

- base (T1): \(3\) = `core.app.acceder`, `tenant.branding.leer`, `org.empresa.leer`
- ORG (sin administrar empresa + sin eliminar): \(5 recursos × 3 acciones = 15\)
- INV:
  - catálogos: \(5 recursos × 3 acciones = 15\)
  - stock: \(2 acciones = 2\)
  - movimiento: \(6 acciones = 6\)
  - inventario_fisico: \(6 acciones = 6\)
  - total INV = \(15 + 2 + 6 + 6 = 29\)

**Total** \(3 + 15 + 29 = 47\) códigos de permiso.

#### SQL esperado (plantilla, idempotente)

```sql
-- Inserta en rol_permiso todos los permiso_id cuyo codigo esté en el bundle
INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)
SELECT NEWID(), :cliente_id, :manager_rol_id, p.permiso_id, GETDATE()
FROM permiso p
WHERE p.es_activo = 1
  AND p.codigo IN (
    -- T1
    'core.app.acceder','tenant.branding.leer','org.empresa.leer',

    -- ORG
    'org.sucursal.leer','org.sucursal.crear','org.sucursal.actualizar',
    'org.departamento.leer','org.departamento.crear','org.departamento.actualizar',
    'org.cargo.leer','org.cargo.crear','org.cargo.actualizar',
    'org.centro_costo.leer','org.centro_costo.crear','org.centro_costo.actualizar',
    'org.parametro.leer','org.parametro.crear','org.parametro.actualizar',

    -- INV catálogos
    'inv.categoria.leer','inv.categoria.crear','inv.categoria.actualizar',
    'inv.producto.leer','inv.producto.crear','inv.producto.actualizar',
    'inv.unidad_medida.leer','inv.unidad_medida.crear','inv.unidad_medida.actualizar',
    'inv.almacen.leer','inv.almacen.crear','inv.almacen.actualizar',
    'inv.tipo_movimiento.leer','inv.tipo_movimiento.crear','inv.tipo_movimiento.actualizar',

    -- INV stock
    'inv.stock.leer','inv.stock.actualizar',

    -- INV movimientos
    'inv.movimiento.leer','inv.movimiento.crear','inv.movimiento.actualizar',
    'inv.movimiento.procesar','inv.movimiento.autorizar','inv.movimiento.anular',

    -- INV inventario físico
    'inv.inventario_fisico.leer','inv.inventario_fisico.crear','inv.inventario_fisico.actualizar',
    'inv.inventario_fisico.finalizar','inv.inventario_fisico.aprobar','inv.inventario_fisico.anular'
  )
  AND NOT EXISTS (
    SELECT 1 FROM rol_permiso rp
    WHERE rp.cliente_id = :cliente_id
      AND rp.rol_id = :manager_rol_id
      AND rp.permiso_id = p.permiso_id
  );
```

---

## 6) Validaciones esperadas (SQL + /auth/menu)

### 6.1 Validación SQL — rol_menu_permiso

```sql
SELECT COUNT(*) AS total
FROM rol_menu_permiso
WHERE cliente_id = :cliente_id
  AND rol_id = :manager_rol_id
  AND empresa_id IS NULL
  AND puede_ver = 1;
-- esperado: 14
```

### 6.2 Validación SQL — rol_permiso (conteo bundle)

```sql
SELECT COUNT(DISTINCT p.codigo) AS c
FROM rol_permiso rp
INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE rp.cliente_id = :cliente_id
  AND rp.rol_id = :manager_rol_id
  AND p.codigo IN (/* lista bundle */);
-- esperado: 47 (si el bundle se aplica completo)
```

### 6.3 Validación funcional — `/auth/menu`

Con `rol_menu_permiso` poblado, `/auth/menu` debe retornar:

- `modulos` contiene `ORG` y `INV`
- `ORG.secciones[0].menus` contiene los 6 `ORG_*`
- `INV.secciones[0].menus` contiene los 8 `INV_*` (sin Kardex)

