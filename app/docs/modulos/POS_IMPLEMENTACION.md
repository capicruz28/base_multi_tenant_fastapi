# IMPLEMENTACIÓN — POS (Punto de Venta)

Fecha: 2026-05-07

Este documento cierra el ciclo del módulo **POS** según el prompt maestro (`docs/prompts/PROMPT_MODULO_MAESTRO.md`): implementación alineada a `docs/bd/POS_TABLAS.sql`, **sin modificar DDL**, sin eliminar rutas previas y añadiendo solo contratos complementarios donde se indicó en auditoría.

---

## Alcance de datos

Tablas `pos_*` documentadas en **`docs/bd/POS_TABLAS.sql`**:

| Tabla | Rol |
|-------|-----|
| `pos_punto_venta` | Maestro (terminales/cajas; `es_activo`) |
| `pos_turno_caja` | Transaccional (apertura/cierre) |
| `pos_venta` | Transaccional (cabecera) |
| `pos_venta_detalle` | Transaccional (líneas) |

---

## Arquitectura aplicada

- **Routers**: `app/modules/pos/presentation/endpoints_*.py` + `endpoints.py`
- **Servicios**: `app/modules/pos/application/services/*_service.py`
- **Acceso datos**: `app/infrastructure/database/queries/pos/*_queries.py` (patrón queries del repo, sin carpeta `repositories` en el módulo)
- **Tablas Core**: `app/infrastructure/database/tables_erp/tables_pos.py`
- **Montaje API**: `app/api/v1/api.py` → prefijo `{API_V1_STR}/pos`
- **Tenant**: `cliente_id` desde `current_user.cliente_id` en todas las operaciones
- **Empresa**: `empresa_id` opcional en listados y en GET/PUT por ID (validación de pertenencia cuando se envía)
- **RBAC**: `require_permission("pos.<recurso>.<accion>")`

---

## Resumen de cambios

### Schemas y ORM

- Lecturas con columnas calculadas / adicionales: **Turno** (`diferencia`, `total_ingresos`), **Venta** (`total_cobrar`, `monto_cambio`, `moneda_id` sin quitar `moneda`), **Detalle** (`empresa_id`, importes calc. cuando la BD los expone).
- **VentaCreate / VentaRead**: `moneda_id` opcional en paralelo a `moneda`.
- **TurnoCajaUpdate**: retirados campos de totales agregados editables manualmente (el cierre los fija).
- **Nuevos bodies**: `VentaAnularRequest`, `TurnoCajaCerrarRequest`.
- **ORM** (`tables_pos.py`): columnas alineadas a la documentación (incl. `moneda_id`, calculadas en cabecera/detalle donde aplica).

### Multi-tenant por empresa

- Filtro opcional `empresa_id` en listados de **turnos de caja**, **ventas** y **detalle de ventas**.
- GET/PUT y operaciones de negocio por ID aceptan `empresa_id` opcional; si no coincide con la fila → **404**.

### Reglas de negocio

- **PUT `pos_venta`**: solo si estado **borrador** o **pendiente**. La anulación no va por PUT; usar **POST …/anular**.
- **PUT `pos_venta_detalle`**: solo si la cabecera está en **borrador** o **pendiente**; bloqueado si la venta está **anulada** o en estado “cerrado” contable (**completada** u otro no editable).
- **Anulación**: `POST /ventas/{id}/anular` con motivo; estados previos admitidos **borrador**, **pendiente**, **completada** (no **anulada**).
- **Cierre de turno**: `POST /turnos-caja/{id}/cerrar` recalcula totales desde ventas del turno (no anuladas) y fija montos/cierres; el PUT de turno no permite fijar totales de sistema.

### Endpoints nuevos (aditivos)

| Método | Ruta (relativa a `/pos`) | Permiso |
|--------|--------------------------|---------|
| DELETE | `/puntos-venta/{id}` | `pos.punto_venta.eliminar` |
| POST | `/puntos-venta/{id}/reactivar` | `pos.punto_venta.actualizar` |
| POST | `/ventas/{id}/anular` | `pos.venta.anular` |
| POST | `/turnos-caja/{id}/cerrar` | `pos.turno_caja.cerrar` |

### RBAC — seed

Script idempotente: **`app/docs/database/SEED_PERMISOS_RBAC_POS.sql`**

Incluye:

- `pos.punto_venta.{leer,crear,actualizar,eliminar}`
- `pos.turno_caja.{leer,crear,actualizar,cerrar}`
- `pos.venta.{leer,crear,actualizar,anular}`
- `pos.venta_detalle.{leer,crear,actualizar}`

---

## Verificación Fase 4

### 1) Archivos modificados o creados

**Documentación**

- `app/docs/modulos/AUDITORIA_POS.md`
- `app/docs/modulos/POS_IMPLEMENTACION.md` (este archivo)
- `app/docs/database/SEED_PERMISOS_RBAC_POS.sql` (**nuevo**)

**Presentación**

- `app/modules/pos/presentation/schemas.py`
- `app/modules/pos/presentation/endpoints_puntos_venta.py`
- `app/modules/pos/presentation/endpoints_turnos_caja.py`
- `app/modules/pos/presentation/endpoints_ventas.py`
- `app/modules/pos/presentation/endpoints_ventas_detalle.py`

**Aplicación**

- `app/modules/pos/application/services/__init__.py`
- `app/modules/pos/application/services/punto_venta_service.py`
- `app/modules/pos/application/services/turno_caja_service.py`
- `app/modules/pos/application/services/venta_service.py`
- `app/modules/pos/application/services/venta_detalle_service.py`

**Infraestructura**

- `app/infrastructure/database/tables_erp/tables_pos.py`
- `app/infrastructure/database/queries/pos/__init__.py`
- `app/infrastructure/database/queries/pos/punto_venta_queries.py`
- `app/infrastructure/database/queries/pos/turno_caja_queries.py`
- `app/infrastructure/database/queries/pos/venta_queries.py`
- `app/infrastructure/database/queries/pos/venta_detalle_queries.py`

### 2) Endpoints nuevos — tenant, empresa, RBAC

Todos usan `current_user.cliente_id` en servicios/queries. **Empresa**: query opcional `empresa_id` donde la tabla lo lleva y el endpoint lo expone.

| Endpoint nuevo | `cliente_id` | `empresa_id` (scope) | RBAC |
|----------------|--------------|----------------------|------|
| `DELETE …/puntos-venta/{id}` | Sí | Opcional en query | `pos.punto_venta.eliminar` |
| `POST …/puntos-venta/{id}/reactivar` | Sí | Opcional en query | `pos.punto_venta.actualizar` |
| `POST …/ventas/{id}/anular` | Sí | Opcional en query | `pos.venta.anular` |
| `POST …/turnos-caja/{id}/cerrar` | Sí | Opcional en query | `pos.turno_caja.cerrar` |

### 3) Compatibilidad de endpoints existentes

- **Rutas y métodos** de los endpoints que ya existían (`GET/POST/PUT` en cada recurso) se mantienen en los mismos paths relativos al router POS.
- Se añadieron **parámetros de query opcionales** (`empresa_id` y, en listados donde faltaba, el mismo) y **campos opcionales adicionales** en los `*Read` (extensión compatible hacia delante; los clientes que solo consuman campos previos siguen válidos).
- La semántica de **PUT** de venta y de **TurnoCajaUpdate** se endureció (validaciones de estado / totales); si un cliente dependía del comportamiento anterior laxo, debe ajustarse a las reglas documentadas aquí.

### 4) Dependencias y despliegue

- Ejecutar en BD el seed **`SEED_PERMISOS_RBAC_POS.sql`** (tras existir el módulo POS en catálogo).
- El modelo SQLAlchemy asume columnas coherentes con **`docs/bd/POS_TABLAS.sql`**; si alguna base no tiene aún columnas como `moneda_id` o columnas calculadas, la capa ORM y las consultas deben alinearse al DDL real del entorno **sin confundir con “migración” aplicada desde este backend** (regla de proyecto: no alterar BD desde aquí).

---

## Cierre del módulo

El módulo **POS** queda cubierto por: auditoría (`AUDITORIA_POS.md`), implementación descrita en este documento, permisos seed y reglas de negocio operativas en routers/servicios/queries. Para trabajo futuro (p. ej. cabecera con detalle embebido en una sola transacción, series SUNAT más finas en cierre de turno, u otros estados), conviene abrir una nueva iteración explicitando contratos y alcance.
