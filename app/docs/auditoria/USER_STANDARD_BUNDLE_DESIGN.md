# Diseño funcional — Bundle `USER_STANDARD` (T3)

## Objetivo

Definir el bundle **`USER_STANDARD`** para `USER_TENANT`, siguiendo el modelo RBAC aprobado:

- **Hereda `BASE_OPERATIVE`** (T1).
- Es **predominantemente lectura**.
- Debe habilitar `/auth/menu` (depende de `rol_menu_permiso`).

Sin implementación, sin repair, sin commit.

---

## Lineamientos (restricciones)

`USER_STANDARD` debe excluir:

- `SYS_ADMIN.*`
- `PLATFORM.*`
- `CATALOGOS.*`
- administración de tenant (`tenant.*` administrativo, `admin.*`, `modulos.*`)
- administración de empresas (crear/actualizar/eliminar empresa)
- **eliminación de registros** (no incluir `*.eliminar`; UI `puede_eliminar=0`)

---

## Catálogo real (BD central) — Menús ORG/INV disponibles

Este diseño reutiliza los **IDs reales** del catálogo central `modulo_menu` (mismos que T2):

### ORG (6 menús)

- `ORG_MI_EMPRESA` → `menu_id` `E3010001-0000-4000-8000-000000000001` → `/app/org/empresa`
- `ORG_SUCURSALES` → `menu_id` `E3010002-0000-4000-8000-000000000002` → `/app/org/sucursales`
- `ORG_DEPARTAMENTOS` → `menu_id` `E3010003-0000-4000-8000-000000000003` → `/app/org/departamentos`
- `ORG_CARGOS` → `menu_id` `E3010004-0000-4000-8000-000000000004` → `/app/org/cargos`
- `ORG_CENTROS_COSTO` → `menu_id` `E3010005-0000-4000-8000-000000000005` → `/app/org/centros-costo`
- `ORG_PARAMETROS` → `menu_id` `E3010006-0000-4000-8000-000000000006` → `/app/org/parametros`

### INV (9 menús; Kardex sin permiso de catálogo)

- `INV_CATEGORIAS` → `menu_id` `E3020002-0000-4000-8000-000000000001` → `/app/inv/categorias`
- `INV_PRODUCTOS` → `menu_id` `E3020001-0000-4000-8000-000000000002` → `/app/inv/productos`
- `INV_UNIDADES` → `menu_id` `E3020003-0000-4000-8000-000000000003` → `/app/inv/unidades-medida`
- `INV_ALMACENES` → `menu_id` `E3020004-0000-4000-8000-000000000004` → `/app/inv/almacenes`
- `INV_STOCK` → `menu_id` `E3020005-0000-4000-8000-000000000005` → `/app/inv/stock`
- `INV_TIPOS_MOV` → `menu_id` `E3020006-0000-4000-8000-000000000006` → `/app/inv/tipos-movimiento`
- `INV_MOVIMIENTOS` → `menu_id` `E3020007-0000-4000-8000-000000000007` → `/app/inv/movimientos`
- `INV_INV_FISICO` → `menu_id` `E3020008-0000-4000-8000-000000000008` → `/app/inv/inventario-fisico`
- `INV_INV_KARDEX` → `menu_id` `E3020009-0000-4000-8000-000000000009` → `/app/inv/kardex`

**Gap conocido:** no existe `inv.kardex.leer` (catálogo `permiso`), por lo que el menú `INV_INV_KARDEX` no tiene `required_permission` inferible.  
Este bundle “cerrado” **excluye Kardex** (igual que T2).

---

## Definición del bundle `USER_STANDARD`

### 1) Menús visibles (`rol_menu_permiso`)

**Incluidos (14)**: ORG (6) + INV (8) **sin Kardex**.

**Política UI (predominantemente lectura):**

- `puede_ver = 1`
- `puede_crear = 0`
- `puede_editar = 0`
- `puede_eliminar = 0` (restricción)
- `puede_exportar = 1` (opcional, recomendado para perfiles de lectura)
- `puede_imprimir = 0` (conservador)
- `puede_aprobar = 0` (conservador)

**Total `rol_menu_permiso` esperado:** **14 filas** con `puede_ver=1`.

#### SQL esperado (plantilla idempotente)

> Nota: la tabla real usa PK `permiso_id` (no `rol_menu_permiso_id`).

```sql
INSERT INTO rol_menu_permiso (
  permiso_id, cliente_id, rol_id, menu_id,
  puede_ver, puede_crear, puede_editar, puede_eliminar,
  puede_exportar, puede_imprimir, puede_aprobar,
  fecha_creacion
)
SELECT
  NEWID(), :cliente_id, :user_rol_id, x.menu_id,
  1, 0, 0, 0,
  1, 0, 0,
  GETDATE()
FROM (
  -- ORG (6)
  SELECT CAST('E3010001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER) AS menu_id
  UNION ALL SELECT CAST('E3010002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3010003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3010004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3010005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3010006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER)

  -- INV (8; sin Kardex)
  UNION ALL SELECT CAST('E3020002-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020001-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER)
  UNION ALL SELECT CAST('E3020008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER)
) AS x
WHERE NOT EXISTS (
  SELECT 1 FROM rol_menu_permiso rmp
  WHERE rmp.cliente_id = :cliente_id
    AND rmp.rol_id = :user_rol_id
    AND rmp.menu_id = x.menu_id
);
```

### 2) Permisos API (`rol_permiso`)

**Regla principal:** `USER_STANDARD` incluye solo permisos `*.leer` para ORG/INV (más BASE_OPERATIVE).

Incluye:

- **BASE_OPERATIVE (T1)**:
  - `core.app.acceder`
  - `tenant.branding.leer`
  - `org.empresa.leer`

- **ORG lectura (5 pantallas adicionales)**:
  - `org.sucursal.leer`
  - `org.departamento.leer`
  - `org.cargo.leer`
  - `org.centro_costo.leer`
  - `org.parametro.leer`

- **INV lectura (8 pantallas; sin Kardex)**:
  - `inv.categoria.leer`
  - `inv.producto.leer`
  - `inv.unidad_medida.leer`
  - `inv.almacen.leer`
  - `inv.stock.leer`
  - `inv.tipo_movimiento.leer`
  - `inv.movimiento.leer`
  - `inv.inventario_fisico.leer`

**Total `rol_permiso` esperado:** \(3 + 5 + 8 = 16\) códigos.

#### SQL esperado (plantilla idempotente)

```sql
INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)
SELECT NEWID(), :cliente_id, :user_rol_id, p.permiso_id, GETDATE()
FROM permiso p
WHERE p.es_activo = 1
  AND p.codigo IN (
    'core.app.acceder','tenant.branding.leer','org.empresa.leer',
    'org.sucursal.leer','org.departamento.leer','org.cargo.leer','org.centro_costo.leer','org.parametro.leer',
    'inv.categoria.leer','inv.producto.leer','inv.unidad_medida.leer','inv.almacen.leer',
    'inv.stock.leer','inv.tipo_movimiento.leer','inv.movimiento.leer','inv.inventario_fisico.leer'
  )
  AND NOT EXISTS (
    SELECT 1 FROM rol_permiso rp
    WHERE rp.cliente_id = :cliente_id
      AND rp.rol_id = :user_rol_id
      AND rp.permiso_id = p.permiso_id
  );
```

---

## Diferencias clave: `USER_STANDARD` vs `MANAGER_STANDARD`

- **`rol_permiso`**
  - **USER_STANDARD**: solo `*.leer` (16 códigos).
  - **MANAGER_STANDARD**: lectura + crear + actualizar (y acciones operativas en INV), sin eliminar, empresa solo leer (47 códigos).

- **`rol_menu_permiso` (UI)**
  - **USER_STANDARD**: `ver=1` y resto 0 (opcional exportar=1).
  - **MANAGER_STANDARD**: `ver=1`, `crear/editar` habilitados en varias pantallas; operativo con imprimir/aprobar en flujos INV; siempre `eliminar=0`.

- **Alcance funcional**
  - **USER_STANDARD**: consumo/consulta (operación de lectura).
  - **MANAGER_STANDARD**: operación estándar (mantención + flujos operativos INV).

---

## Conteos esperados (resumen)

- **`rol_menu_permiso`**: 14 filas (`puede_ver=1`)
- **`rol_permiso`**: 16 códigos

---

## Validaciones SQL sugeridas (para futura implementación)

```sql
-- Menús visibles
SELECT COUNT(*) AS total
FROM rol_menu_permiso
WHERE cliente_id = :cliente_id
  AND rol_id = :user_rol_id
  AND puede_ver = 1;
-- esperado: 14
```

```sql
-- Conteo de permisos del bundle
SELECT COUNT(DISTINCT p.codigo) AS c
FROM rol_permiso rp
INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE rp.cliente_id = :cliente_id
  AND rp.rol_id = :user_rol_id
  AND p.codigo IN (/* lista de 16 códigos */);
-- esperado: 16
```

