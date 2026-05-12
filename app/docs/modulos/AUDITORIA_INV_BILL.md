# Auditoría — Módulo INV_BILL (Facturación electrónica)

Documento generado en **Fase 2** del prompt maestro (solo lectura y análisis).  
Prefijo de tablas en BD: `invbill_`. Carpeta de código: `app/modules/invbill/`.  
Rutas API: `{API_V1_STR}/inv-bill` (p. ej. `/api/v1/inv-bill`) según `app/api/v1/api.py`.

---

## 1. Tablas detectadas y tipo

| Tabla | Tipo |
|-------|------|
| `invbill_serie_comprobante` | Maestro (series y numeración) |
| `invbill_comprobante` | Transaccional (cabecera de comprobante fiscal) |
| `invbill_comprobante_detalle` | Transaccional (líneas; en diseño objetivo va embebido en cabecera) |

**Nota de modelo físico:** En `docs/bd/INV_BILL_TABLAS.sql` y `app/docs/database/3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql`, `invbill_comprobante` usa `moneda_id` (FK `cat_moneda`) y columna calculada persistida `numero_completo`. `invbill_comprobante_detalle` define columnas calculadas persistidas: `precio_venta_unitario`, `valor_venta`, `igv`, `total_item`. En código, `app/infrastructure/database/tables_erp/tables_invbill.py` define `moneda` como `String(3)` (no `moneda_id`) y **no** modela `numero_completo` ni las columnas calculadas del detalle. La implementación actual está alineada con **tables_invbill.py**, no con los scripts documentados FASE4 / `INV_BILL_TABLAS.sql` en esos puntos (riesgo de desincronización si la BD real sigue el script documentado).

---

## 2. Inventario de código (Fase 2.1)

No existe carpeta `repositories` dedicada: la persistencia está en `app/infrastructure/database/queries/invbill/*.py` (patrón queries + `execute_query` / `execute_insert` / `execute_update`).

Archivos relevantes:

- **Presentation:** `app/modules/invbill/presentation/endpoints.py`, `endpoints_series.py`, `endpoints_comprobantes.py`, `endpoints_comprobante_detalles.py`, `schemas.py`
- **Application:** `app/modules/invbill/application/services/*.py`
- **Infrastructure:** `app/infrastructure/database/queries/invbill/*.py`, `app/infrastructure/database/tables_erp/tables_invbill.py`

### 2.1 Endpoints existentes

Base: `/inv-bill` + subprefijos de `endpoints.py`.

| Ruta | Método | Entidad | Tenant (`cliente_id`) | RBAC (`require_permission`) |
|------|--------|---------|------------------------|-----------------------------|
| `/inv-bill/series` | GET | Serie comprobante | Sí | **No** |
| `/inv-bill/series/{serie_id}` | GET | Serie comprobante | Sí | Sí (`inv_bill.serie.leer`) |
| `/inv-bill/series` | POST | Serie comprobante | Sí | **No** |
| `/inv-bill/series/{serie_id}` | PUT | Serie comprobante | Sí | Sí (`inv_bill.serie.actualizar`) |
| `/inv-bill/comprobantes` | GET | Comprobante | Sí | Sí (`inv_bill.comprobante.leer`) |
| `/inv-bill/comprobantes/{comprobante_id}` | GET | Comprobante | Sí | Sí (`inv_bill.comprobante.leer`) |
| `/inv-bill/comprobantes` | POST | Comprobante | Sí | Sí (`inv_bill.comprobante.crear`) |
| `/inv-bill/comprobantes/{comprobante_id}` | PUT | Comprobante | Sí | Sí (`inv_bill.comprobante.actualizar`) |
| `/inv-bill/comprobantes-detalles` | GET | Comprobante detalle | Sí | Sí (`inv_bill.comprobante_detalle.leer`) |
| `/inv-bill/comprobantes-detalles/{comprobante_detalle_id}` | GET | Comprobante detalle | Sí | Sí (`inv_bill.comprobante_detalle.leer`) |
| `/inv-bill/comprobantes-detalles` | POST | Comprobante detalle | Sí | Sí (`inv_bill.comprobante_detalle.crear`) |
| `/inv-bill/comprobantes-detalles/{comprobante_detalle_id}` | PUT | Comprobante detalle | Sí | Sí (`inv_bill.comprobante_detalle.actualizar`) |

**Tenant `empresa_id`:** Los listados de series y comprobantes aceptan `empresa_id` opcional en query. Creación de serie y comprobante incluye `empresa_id` en body. Los **GET por ID** y los **PUT** filtran por `cliente_id` + clave en queries; no exigen `empresa_id` en la ruta. El listado de detalles no expone filtro `empresa_id` (solo `comprobante_id` opcional); el `empresa_id` de línea se rellena al crear desde la cabecera en query.

**Código de módulo en permisos:** Los endpoints usan `MODULE_CODE = "inv_bill"` (con guión bajo), no `invbill`.

---

## 3. Brechas funcionales (Fase 2.2)

Criterio del prompt maestro: maestro → crear, listar, detalle, actualizar, activar/desactivar; transaccional → crear (borrador), actualizar (solo borrador), aprobar, procesar, anular, listar, detalle; detalle embebido en cabecera.

### `invbill_serie_comprobante` (maestro)

| Requisito | Estado |
|-----------|--------|
| Crear | Cubierto (POST), **sin** `require_permission` |
| Listar | Cubierto (GET), **sin** `require_permission` |
| Detalle | Cubierto (GET `/{serie_id}`), con RBAC |
| Actualizar | Cubierto (PUT), con RBAC |
| Activar / desactivar | **Parcial:** `es_activo` en Create/Update; no hay rutas dedicadas; no hay permisos explícitos `activar` / `desactivar` |

### `invbill_comprobante` (transaccional)

| Requisito | Estado |
|-----------|--------|
| Crear (borrador) | **Parcial:** existe POST; valores por defecto en BD/schema tienden a `estado` = `emitido` y `estado_sunat` = `pendiente`, no a un flujo explícito “solo borrador al crear” |
| Listar / detalle | Cubierto |
| Actualizar (solo en borrador) | **No:** el servicio no valida `estado == 'borrador'` antes de actualizar |
| Aprobar | **Falta** endpoint o acción semántica (p. ej. alineado a aceptación SUNAT / registro interno) |
| Procesar | **Falta** (p. ej. envío a SUNAT, generación XML/firma, transición de estado) |
| Anular | **Falta** endpoint dedicado; existen campos `fecha_anulacion` / `motivo_anulacion` / `estado` en tabla y schemas, pero solo vía PUT genérico |

### `invbill_comprobante_detalle`

| Requisito | Estado |
|-----------|--------|
| Lectura | Cubierto (lista + por id) |
| Escritura pública separada (POST/PUT línea) | **Presente** |
| Alineación con prompt maestro (detalle embebido en cabecera) | **Desalineado:** CRUD de líneas por API separada bajo `/comprobantes-detalles` |

---

## 4. Campos en BD no cubiertos o divergentes en schemas (Fase 2.3)

Comparación principal contra **`docs/bd/INV_BILL_TABLAS.sql`** (y FASE4 donde coincide). Donde `tables_invbill.py` difiere, se indica.

### Serie (`SerieComprobanteRead` / Create / Update)

- Cobertura razonable respecto al script de referencia; no se detectan columnas de negocio faltantes en Read frente a `invbill_serie_comprobante`.

### Comprobante (`ComprobanteCreate` / `ComprobanteUpdate` / `ComprobanteRead`)

| En BD (`INV_BILL_TABLAS.sql` / FASE4) | En schemas actuales |
|--------------------------------------|----------------------|
| `moneda_id` (UUID, NOT NULL, FK `cat_moneda`) | Se usa `moneda` como `str` opcional (código), no `moneda_id` |
| `numero_completo` (columna calculada persistida) | No expuesto en `ComprobanteRead` |

### Comprobante detalle (`ComprobanteDetalleCreate` / Update / Read)

| En BD | En schemas actuales |
|-------|---------------------|
| `empresa_id` | Presente en BD y en ORM; **no** está en `ComprobanteDetalleRead` ni en Create (se deriva en insert vía cabecera, coherente con no repetir en body) |
| `precio_venta_unitario`, `valor_venta`, `igv`, `total_item` (calculadas persistidas en script) | **No** en `ComprobanteDetalleRead` ni en `tables_invbill.py` como columnas |

**Advertencia:** Si la base de datos desplegada ya tiene `moneda_id` y columnas calculadas del script oficial, los inserts/updates actuales (basados en `tables_invbill.py`) pueden fallar o quedar inconsistentes hasta alinear ORM + schemas + queries.

---

## 5. Problemas de tenant o RBAC

1. **Series — RBAC incompleto:** `GET /inv-bill/series` y `POST /inv-bill/series` no declaran `require_permission`; el resto de acciones de serie sí (parcialmente).
2. **Permisos en seeds:** No se encontró en el repositorio (búsqueda por término `inv_bill`) un archivo **SEED** de permisos RBAC para `inv_bill.serie.*`, `inv_bill.comprobante.*`, `inv_bill.comprobante_detalle.*`. Sin filas en BD de permisos, los endpoints que sí exigen RBAC pueden responder **403** de forma sistemática para todos los usuarios.
3. **Patrón de código de módulo:** El proyecto suele usar código corto sin guión extra en permisos (p. ej. `sls.pedido.leer`). Aquí se usa `inv_bill` con guión bajo; debe ser **consistente** con lo que se inserte en seeds y con la convención global del ERP (no es un bug por sí solo, pero es punto de revisión al sembrar permisos).
4. **`empresa_id` en lecturas por ID:** Igual que en otros módulos, no se valida explícitamente que el recurso pertenezca a una empresa concreta del contexto; solo `cliente_id` + PK.

---

## 6. Código o documentación obsoleta / incorrecta (no eliminar en esta fase)

| Elemento | Observación |
|----------|-------------|
| `app/docs/database/ESTRUCTURA_MODULOS_ERP.md` | Describe rutas/carpetas `inv_bill/` y `tables_inv_bill.py`; el código real usa `invbill` y `tables_invbill.py`. Documentación desalineada con el repo. |
| `endpoints_comprobante_detalles.py` | CRUD REST de líneas en conflicto con la regla del prompt maestro (detalle embebido). No marcar para borrado sin decisión de producto: puede ser intencional temporalmente. |
| `tables_invbill.py` + `schemas.py` | Modelo `moneda` vs `moneda_id` y ausencia de columnas calculadas del detalle frente a scripts SQL oficiales documentados. |

---

## 7. Endpoints faltantes sugeridos (Fase 2.4 resumido)

> Rutas relativas a `/inv-bill`. Métodos y nombres orientativos; la implementación debe respetar contratos existentes y no romper rutas actuales.

| Ruta sugerida | Método | Propósito |
|---------------|--------|-----------|
| `/series` (GET/POST existentes) | — | Añadir `require_permission` alineado a `inv_bill.serie.leer` / `.crear` |
| `/series/{serie_id}/activar` o política única PUT | POST o PATCH | Activar lógicamente (`es_activo = 1`) con permiso dedicado si se desea simetría con otros maestros |
| `/series/{serie_id}/desactivar` | POST o PATCH | Baja lógica (`es_activo = 0`, motivo/fecha) |
| `/comprobantes/{id}/anular` | POST | Anulación con body (`motivo`) y reglas de negocio |
| `/comprobantes/{id}/enviar-sunat` o `/procesar` | POST | Transición / envío (procesar en sentido prompt maestro) |
| `/comprobantes/{id}/aprobar` o equivalente interno | POST | Si el flujo de negocio separa “aprobar” de “emitir a SUNAT” |
| `/comprobantes` (POST) + cabecera anidada | POST | Evolución futura: crear cabecera con `detalles[]` embebidos y transacción única (sin romper POST actual hasta acordar deprecación) |

---

## 8. Cierre Fase 2

- **Implementación parcial** del módulo INV_BILL en FastAPI con tres entidades y persistencia por queries.
- **Principales brechas:** RBAC en series (listado/crear), seeds de permisos no localizados, flujo transaccional incompleto (borrador / anular / procesar), detalle como recurso REST separado vs diseño embebido, desalineación **BD documentada ↔ ORM/schemas** en moneda y columnas calculadas del detalle.

⛔ **Detener aquí (Fase 2).** Esperar confirmación antes de Fase 3 (implementación).
