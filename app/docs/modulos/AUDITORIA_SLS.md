## Auditoría de módulo: SLS (Ventas)

Fuente BD: `docs/bd/SLS_TABLAS.sql` (sección SLS)  
Fuente código: `app/modules/sls/` + `app/infrastructure/database/{tables_erp,queries}/sls/`

---

## Tablas detectadas y su tipo

- **Maestro**
  - `sls_cliente`
- **Derivadas / Detalle de maestro**
  - `sls_cliente_contacto` (detalle de `sls_cliente`)
  - `sls_cliente_direccion` (detalle de `sls_cliente`)
- **Transaccional**
  - `sls_cotizacion` (cabecera)
  - `sls_cotizacion_detalle` (detalle)
  - `sls_pedido` (cabecera)
  - `sls_pedido_detalle` (detalle)

---

## Endpoints existentes

Base router del módulo: `app/api/v1/api.py` incluye `prefix="/sls"` (ver `app/modules/sls/presentation/endpoints.py`).

| Ruta | Método | Entidad | Tiene tenant? | Tiene RBAC? |
|------|--------|---------|---------------|-------------|
| `/sls/clientes` | GET | `sls_cliente` | Sí (`current_user.cliente_id` → queries filtran `cliente_id`) | Sí (`sls.cliente.leer`) |
| `/sls/clientes/{cliente_venta_id}` | GET | `sls_cliente` | Sí | Sí (`sls.cliente.leer`) |
| `/sls/clientes` | POST | `sls_cliente` | Sí (cliente_id forzado en query insert) | Sí (`sls.cliente.crear`) |
| `/sls/clientes/{cliente_venta_id}` | PUT | `sls_cliente` | Sí | Sí (`sls.cliente.actualizar`) |
| `/sls/contactos` | GET | `sls_cliente_contacto` | Sí | Sí (`sls.contacto.leer`) |
| `/sls/contactos/{contacto_id}` | GET | `sls_cliente_contacto` | Sí | Sí (`sls.contacto.leer`) |
| `/sls/contactos` | POST | `sls_cliente_contacto` | Sí | Sí (`sls.contacto.crear`) |
| `/sls/contactos/{contacto_id}` | PUT | `sls_cliente_contacto` | Sí | Sí (`sls.contacto.actualizar`) |
| `/sls/direcciones` | GET | `sls_cliente_direccion` | Sí | Sí (`sls.direccion.leer`) |
| `/sls/direcciones/{direccion_id}` | GET | `sls_cliente_direccion` | Sí | Sí (`sls.direccion.leer`) |
| `/sls/direcciones` | POST | `sls_cliente_direccion` | Sí | Sí (`sls.direccion.crear`) |
| `/sls/direcciones/{direccion_id}` | PUT | `sls_cliente_direccion` | Sí | Sí (`sls.direccion.actualizar`) |
| `/sls/cotizaciones` | GET | `sls_cotizacion` | Sí | Sí (`sls.cotizacion.leer`) |
| `/sls/cotizaciones/{cotizacion_id}` | GET | `sls_cotizacion` | Sí | Sí (`sls.cotizacion.leer`) |
| `/sls/cotizaciones` | POST | `sls_cotizacion` | Sí | Sí (`sls.cotizacion.crear`) |
| `/sls/cotizaciones/{cotizacion_id}` | PUT | `sls_cotizacion` | Sí | Sí (`sls.cotizacion.actualizar`) |
| `/sls/pedidos` | GET | `sls_pedido` | Sí | Sí (`sls.pedido.leer`) |
| `/sls/pedidos/{pedido_id}` | GET | `sls_pedido` | Sí | Sí (`sls.pedido.leer`) |
| `/sls/pedidos` | POST | `sls_pedido` | Sí | Sí (`sls.pedido.crear`) |
| `/sls/pedidos/{pedido_id}` | PUT | `sls_pedido` | Sí | Sí (`sls.pedido.actualizar`) |

---

## Endpoints faltantes (con ruta sugerida y método)

### 1) Brechas vs “MAESTRO” (según prompt maestro)

Para `sls_cliente` se espera patrón maestro: crear, listar, detalle, actualizar, **activar/desactivar**.

- **Falta**: Activar/desactivar (borrado lógico)  
  - **Sugerido**:
    - `POST /sls/clientes/{cliente_venta_id}/desactivar` (permiso `sls.cliente.actualizar`)  
    - `POST /sls/clientes/{cliente_venta_id}/activar` (permiso `sls.cliente.actualizar`)
  - **Motivo**: la tabla tiene `es_activo` y el prompt exige no eliminar físicamente.

Para `sls_cliente_contacto` y `sls_cliente_direccion` (detalles de maestro) hay CRUD básico, pero no hay endpoints explícitos de activar/desactivar:

- **Falta** (opcional según criterio de UX): activar/desactivar por `es_activo`  
  - **Sugerido**:
    - `POST /sls/contactos/{contacto_id}/desactivar` / `activar` (permiso `sls.contacto.actualizar`)
    - `POST /sls/direcciones/{direccion_id}/desactivar` / `activar` (permiso `sls.direccion.actualizar`)

### 2) Brechas vs “TRANSACCIONAL” (según prompt maestro)

Para `sls_cotizacion` y `sls_pedido` el prompt sugiere acciones tipo: crear (borrador), actualizar (solo borrador), aprobar/procesar/anular, etc.

Actualmente existen solo: listar, detalle, crear, actualizar.

- **Faltan** endpoints de transición de estado (mínimo):
  - **Cotización**:
    - `POST /sls/cotizaciones/{cotizacion_id}/enviar` (permiso `sls.cotizacion.actualizar`)
    - `POST /sls/cotizaciones/{cotizacion_id}/aceptar` (permiso `sls.cotizacion.actualizar`)
    - `POST /sls/cotizaciones/{cotizacion_id}/rechazar` (permiso `sls.cotizacion.actualizar`)
    - `POST /sls/cotizaciones/{cotizacion_id}/convertir-a-pedido` (permiso `sls.cotizacion.actualizar`)
  - **Pedido**:
    - `POST /sls/pedidos/{pedido_id}/confirmar` (permiso `sls.pedido.actualizar`)
    - `POST /sls/pedidos/{pedido_id}/aprobar` (permiso `sls.pedido.actualizar`)
    - `POST /sls/pedidos/{pedido_id}/anular` (permiso `sls.pedido.actualizar`)

> Nota: las acciones exactas y reglas (qué estados permiten qué transición) deben alinearse con el catálogo de estados de BD (`estado`) y el patrón de módulos transaccionales ya implementados (referencia técnica: `PUR`).

### 3) Detalles transaccionales embebidos (no deben tener CRUD independiente)

BD tiene tablas de detalle:
- `sls_cotizacion_detalle`
- `sls_pedido_detalle`

En el módulo SLS actual:
- **No existen** endpoints para manejar detalle (ni embebidos ni independientes).
- **No existen** queries/repositories para estas tablas de detalle.

**Sugerencia** (alineada al prompt maestro para transaccionales: “el detalle se maneja embebido en la cabecera”):
- Manejar detalle dentro de `POST/PUT` de cotización y pedido, o endpoints específicos del documento:
  - `GET /sls/cotizaciones/{cotizacion_id}/detalle`
  - `PUT /sls/cotizaciones/{cotizacion_id}/detalle`
  - `GET /sls/pedidos/{pedido_id}/detalle`
  - `PUT /sls/pedidos/{pedido_id}/detalle`

---

## Campos faltantes en schemas (comparación completa BD vs schemas)

### Consideraciones

- La comparación usa BD (`docs/bd/SLS_TABLAS.sql`) como fuente primaria y valida coherencia con `tables_erp/tables_sls.py` y `app/modules/sls/presentation/schemas.py`.
- “Faltante” significa: existe en tabla BD y **no aparece** en el schema Read/Write correspondiente.
- “Inconsistencia” significa: existe, pero con **nombre o tipo no alineado** (ej. `UUID` vs `str(3)`).

### `sls_cliente`

**BD (SLS_TABLAS.sql)**
- `moneda_preferida` es `UNIQUEIDENTIFIER NOT NULL` con FK a `cat_moneda(moneda_id)`.

**Código**
- `tables_sls.py`: `moneda_preferida` es `String(3)` (código ISO) con default `"PEN"`.
- `schemas.py`: `ClienteCreate.moneda_preferida: Optional[str] = "PEN"` y `ClienteRead.moneda_preferida: Optional[str]`.

**Inconsistencias**
- **Crítica**: `moneda_preferida` **UUID (BD)** vs **string(3) (código)** en tablas ORM y schemas.

**Campos BD faltantes en schemas**
- No se detectan faltantes “grandes” en `ClienteRead` vs `tables_sls.py` (la mayoría de campos están presentes).

### `sls_cliente_contacto`

**BD vs schemas**
- `ClienteContactoCreate/Update/Read` cubren todos los campos definidos en `tables_sls.py` y los campos del SQL.

**Faltantes**
- No se detectan faltantes.

### `sls_cliente_direccion`

**BD vs schemas**
- `ClienteDireccionCreate/Update/Read` cubren todos los campos definidos en `tables_sls.py` y los campos del SQL.

**Faltantes**
- No se detectan faltantes.

### `sls_cotizacion`

**BD (SLS_TABLAS.sql)**
- Campo: `moneda_id UNIQUEIDENTIFIER NOT NULL` con FK a `cat_moneda(moneda_id)`.

**Código**
- `tables_sls.py`: columna `moneda` `String(3)` (no `moneda_id`), default `"PEN"`.
- `schemas.py`: usa `moneda: Optional[str] = "PEN"` (en Create/Update/Read).

**Inconsistencias**
- **Crítica**: `moneda_id` (UUID) en BD vs `moneda` (String(3)) en ORM y schemas.

**Campos BD faltantes en schemas**
- No se detectan faltantes relevantes en cabecera (el schema refleja la cabecera definida en `tables_sls.py`).

### `sls_cotizacion_detalle`

**BD (SLS_TABLAS.sql)**
- Incluye `empresa_id UNIQUEIDENTIFIER NOT NULL` (FK a `org_empresa`).
- Incluye columnas calculadas persistidas: `precio_neto`, `subtotal`, `igv`, `total`.

**Código**
- `tables_sls.py`: sí modela `empresa_id`, pero **no** modela columnas calculadas.
- `schemas.py`:
  - `CotizacionDetalleRead` **no incluye `empresa_id`**
  - `CotizacionDetalleRead` **no incluye** `precio_neto`, `subtotal`, `igv`, `total`

**Campos BD faltantes en schemas (detalle)**
- **Falta**: `empresa_id` en `CotizacionDetalleRead`
- **Faltan**: `precio_neto`, `subtotal`, `igv`, `total` (si se desean exponer como lectura)

**Brecha adicional**
- No hay endpoints ni queries para `sls_cotizacion_detalle`, por lo que estos schemas no están actualmente respaldados por repositorios.

### `sls_pedido`

**BD (SLS_TABLAS.sql)**
- Campo: `moneda_id UNIQUEIDENTIFIER NOT NULL` con FK a `cat_moneda(moneda_id)`.

**Código**
- `tables_sls.py`: columna `moneda` `String(3)` (no `moneda_id`), default `"PEN"`.
- `schemas.py`: `moneda: Optional[str] = "PEN"`.

**Inconsistencias**
- **Crítica**: `moneda_id` (UUID) en BD vs `moneda` (String(3)) en ORM y schemas.

### `sls_pedido_detalle`

**BD (SLS_TABLAS.sql)**
- Incluye `empresa_id UNIQUEIDENTIFIER NOT NULL` (FK a `org_empresa`).
- Incluye columnas calculadas persistidas: `precio_neto`, `subtotal`, `igv`, `total`, `cantidad_pendiente`.

**Código**
- `tables_sls.py`: sí modela `empresa_id`, pero **no** modela columnas calculadas.
- `schemas.py`:
  - `PedidoDetalleRead` **no incluye `empresa_id`**
  - `PedidoDetalleRead` **no incluye** `precio_neto`, `subtotal`, `igv`, `total`, `cantidad_pendiente`

**Campos BD faltantes en schemas (detalle)**
- **Falta**: `empresa_id` en `PedidoDetalleRead`
- **Faltan**: `precio_neto`, `subtotal`, `igv`, `total`, `cantidad_pendiente` (si se desean exponer como lectura)

**Brecha adicional**
- No hay endpoints ni queries para `sls_pedido_detalle`, por lo que estos schemas no están actualmente respaldados por repositorios.

---

## Problemas de tenant o RBAC

### Tenant (cliente_id / empresa_id)

- **Tenant OK (cliente_id)**:
  - Endpoints obtienen `cliente_id` desde `current_user.cliente_id`.
  - Queries filtran estrictamente por `cliente_id` en `WHERE` para list/detalle/update.
  - Inserts fuerzan `cliente_id` desde contexto, ignorando `cliente_id` en `data`.
- **Empresa (empresa_id)**:
  - En cabeceras (`sls_cliente`, `sls_cotizacion`, `sls_pedido`) se acepta `empresa_id` desde query/body (según endpoint).
  - La existencia de validación de pertenencia de `empresa_id` al tenant no es visible a nivel de endpoints/queries SLS (no se observan joins/validaciones explícitas en estas queries; solo se filtra por `cliente_id` y opcionalmente `empresa_id` cuando viene como parámetro).

### RBAC

- **RBAC OK**: todos los endpoints revisados usan `Depends(require_permission(...))` con patrón:
  - `sls.<recurso>.<accion>` (ej.: `sls.pedido.leer`, `sls.cliente.crear`, etc.)

---

## Código marcado como obsoleto o incorrecto (NO eliminar)

### Desalineación BD vs ORM/schemas en moneda (crítico)

En BD (`SLS_TABLAS.sql`):
- `sls_cliente.moneda_preferida` = `UNIQUEIDENTIFIER` (FK a `cat_moneda`)
- `sls_cotizacion.moneda_id` = `UNIQUEIDENTIFIER` (FK a `cat_moneda`)
- `sls_pedido.moneda_id` = `UNIQUEIDENTIFIER` (FK a `cat_moneda`)

En código (`tables_sls.py` + `schemas.py`):
- Se usa `String(3)` (código) en `moneda_preferida` y `moneda` (sin `_id`).

Esto debe resolverse en implementación posterior (sin modificar estructura BD), alineando la capa de acceso y schemas con los tipos/columnas reales de BD.

---

## Resumen de brechas prioritarias

1) **Crítico**: Inconsistencia de moneda (`moneda_id`/`moneda_preferida` UUID en BD vs `moneda`/`moneda_preferida` string(3) en código).  
2) **Funcional**: faltan endpoints de “activar/desactivar” para entidades con `es_activo`.  
3) **Transaccional**: faltan acciones de estado para cotizaciones/pedidos (según patrón del prompt maestro).  
4) **Detalle**: existen tablas de detalle (`sls_cotizacion_detalle`, `sls_pedido_detalle`) pero no hay endpoints/queries; además faltan campos en schemas Read (`empresa_id` y calculados si se exponen).

