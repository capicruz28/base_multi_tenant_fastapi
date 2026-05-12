## SLS — Implementación (Ventas)

Este documento resume la implementación del módulo **SLS** siguiendo el `PROMPT_MODULO_MAESTRO.md` en fases (auditoría → implementación).

---

## Alcance

### Tablas (prefijo SLS_)

- `sls_cliente`
- `sls_cliente_contacto`
- `sls_cliente_direccion`
- `sls_cotizacion`
- `sls_cotizacion_detalle`
- `sls_pedido`
- `sls_pedido_detalle`

---

## Resumen de cambios (Fase 3)

### 1) Schemas + ORM (alineación con BD)

- **Moneda alineada a BD (UUID)**:
  - `sls_cliente.moneda_preferida` → `UUID` (`cat_moneda.moneda_id`)
  - `sls_cotizacion.moneda_id` → `UUID` (`cat_moneda.moneda_id`)
  - `sls_pedido.moneda_id` → `UUID` (`cat_moneda.moneda_id`)
- **Detalle Read expone columnas calculadas (solo lectura)**:
  - `CotizacionDetalleRead`: `empresa_id`, `precio_neto`, `subtotal`, `igv`, `total`
  - `PedidoDetalleRead`: `empresa_id`, `precio_neto`, `subtotal`, `igv`, `total`, `cantidad_pendiente`

Archivos:
- `app/infrastructure/database/tables_erp/tables_sls.py`
- `app/modules/sls/presentation/schemas.py`

### 2) Queries + Services (detalle embebido, estados y transiciones)

- **Detalle embebido** (sin CRUD independiente):
  - `GET detalle`: lectura por documento
  - `PUT detalle`: reemplazo completo (DELETE + INSERT) en **transacción**
- **Regla de edición**:
  - `PUT` cabecera (cotización/pedido) **solo en estado `borrador`**
  - `PUT` detalle (cotización/pedido) **solo en estado `borrador`**
- **Transiciones**:
  - Cotización: `enviar`, `aceptar`, `rechazar`, `convertir-a-pedido`
  - Pedido: `confirmar`, `aprobar`, `anular`

Archivos:
- `app/infrastructure/database/queries/sls/cotizacion_detalle_queries.py`
- `app/infrastructure/database/queries/sls/pedido_detalle_queries.py`
- `app/infrastructure/database/queries/sls/__init__.py`
- `app/modules/sls/application/services/cotizacion_service.py`
- `app/modules/sls/application/services/pedido_service.py`
- `app/modules/sls/application/services/cliente_service.py`
- `app/modules/sls/application/services/__init__.py`

### 3) Routers (endpoints nuevos)

> Importante: **no se cambiaron** rutas/métodos/contratos existentes; solo se agregaron endpoints nuevos.

#### Cotizaciones

- `GET /sls/cotizaciones/{cotizacion_id}/detalle`
- `PUT /sls/cotizaciones/{cotizacion_id}/detalle`
- `POST /sls/cotizaciones/{cotizacion_id}/enviar`
- `POST /sls/cotizaciones/{cotizacion_id}/aceptar`
- `POST /sls/cotizaciones/{cotizacion_id}/rechazar`
- `POST /sls/cotizaciones/{cotizacion_id}/convertir-a-pedido`

#### Pedidos

- `GET /sls/pedidos/{pedido_id}/detalle`
- `PUT /sls/pedidos/{pedido_id}/detalle`
- `POST /sls/pedidos/{pedido_id}/confirmar`
- `POST /sls/pedidos/{pedido_id}/aprobar`
- `POST /sls/pedidos/{pedido_id}/anular`

#### Clientes

- `POST /sls/clientes/{cliente_venta_id}/reactivar` (baja lógica inversa)
- `DELETE /sls/clientes/{cliente_venta_id}` (baja lógica `es_activo=0`)

Archivos:
- `app/modules/sls/presentation/endpoints_cotizaciones.py`
- `app/modules/sls/presentation/endpoints_pedidos.py`
- `app/modules/sls/presentation/endpoints_clientes.py`

---

## RBAC (permisos)

### Permisos usados por endpoints

Patrón: `sls.<recurso>.<accion>`

- Clientes: `sls.cliente.leer|crear|actualizar`
- Contactos: `sls.contacto.leer|crear|actualizar`
- Direcciones: `sls.direccion.leer|crear|actualizar`
- Cotizaciones (incluye detalle + transiciones): `sls.cotizacion.leer|crear|actualizar`
- Pedidos (incluye detalle + transiciones): `sls.pedido.leer|crear|actualizar`

### Seed agregado

- `app/docs/database/SEED_PERMISOS_RBAC_SLS.sql`
  - Idempotente con `MERGE INTO permiso`
  - `modulo_id` SLS: `E100000B-0000-4000-8000-00000000000B`

---

## Verificación final (Fase 4 del prompt maestro)

### 1) Archivos modificados o creados

- **Modificados**
  - `app/infrastructure/database/tables_erp/tables_sls.py`
  - `app/modules/sls/presentation/schemas.py`
  - `app/infrastructure/database/queries/sls/__init__.py`
  - `app/infrastructure/database/queries/sls/cliente_queries.py`
  - `app/infrastructure/database/queries/sls/cotizacion_queries.py`
  - `app/infrastructure/database/queries/sls/pedido_queries.py`
  - `app/modules/sls/application/services/cliente_service.py`
  - `app/modules/sls/application/services/cotizacion_service.py`
  - `app/modules/sls/application/services/pedido_service.py`
  - `app/modules/sls/application/services/__init__.py`
  - `app/modules/sls/presentation/endpoints_clientes.py`
  - `app/modules/sls/presentation/endpoints_cotizaciones.py`
  - `app/modules/sls/presentation/endpoints_pedidos.py`
- **Creados**
  - `app/infrastructure/database/queries/sls/cotizacion_detalle_queries.py`
  - `app/infrastructure/database/queries/sls/pedido_detalle_queries.py`
  - `app/docs/database/SEED_PERMISOS_RBAC_SLS.sql`

### 2) Tenant y empresa_id

- **cliente_id**:
  - Se obtiene desde `current_user.cliente_id` en endpoints.
  - En queries, todas las operaciones usan filtro `cliente_id` (aislamiento multi-tenant).
- **empresa_id**:
  - Para detalle, se fuerza desde la cabecera (`empresa_id`) al hacer `PUT detalle`.
  - En listados, `empresa_id` sigue siendo filtro opcional (sin alterar contratos existentes).

### 3) RBAC

- Todos los endpoints nuevos aplican `Depends(require_permission(...))`.
- Los endpoints nuevos reutilizan permisos `leer`/`actualizar` del recurso correspondiente (sin inventar acciones nuevas).

### 4) Contratos existentes

- No se cambiaron URLs ni métodos de endpoints existentes.
- Las rutas nuevas se agregaron como extensiones (detalle y transiciones).

---

## Documentos relacionados

- Auditoría: `app/docs/modulos/AUDITORIA_SLS.md`

