# INV_BILL — Facturación electrónica — Implementación cerrada

Documento de cierre **Fase 4** del ciclo prompt maestro (lectura → auditoría → implementación → verificación).  
Código del módulo: **INV_BILL**. Prefijo de API: **`{API_V1_STR}/inv-bill`** (p. ej. `/api/v1/inv-bill`), definido en `app/api/v1/api.py`. Carpeta de código: `app/modules/invbill/`.

---

## 1. Alcance y tablas

| Tabla | Rol |
|-------|-----|
| `invbill_serie_comprobante` | Maestro (series y numeración) |
| `invbill_comprobante` | Transaccional (cabecera) |
| `invbill_comprobante_detalle` | Transaccional (líneas; API REST separada conservada) |

No se modificó la estructura física de la base de datos en este ciclo. El ORM `tables_invbill.py` se amplió con **`numero_completo`**, **`moneda_id`** (coexistente con **`moneda`**), índice `IDX_comp_numero`, y columnas de detalle alineadas con `docs/bd/INV_BILL_TABLAS.sql` (`precio_venta_unitario`, `valor_venta`, `igv`, `total_item`).

---

## 2. Archivos creados o modificados

| Archivo | Rol |
|---------|-----|
| `app/docs/modulos/AUDITORIA_INV_BILL.md` | Auditoría Fase 2 (referencia) |
| `app/docs/database/SEED_PERMISOS_RBAC_INV_BILL.sql` | Seeds RBAC INV_BILL (MERGE idempotente) |
| `app/docs/modulos/INV_BILL_IMPLEMENTACION.md` | Este documento de cierre |
| `app/modules/invbill/presentation/schemas.py` | `numero_completo`, `moneda_id`; totales línea en Read; `ComprobanteAnularBody`; `SerieComprobanteDesactivarBody`; default `estado` borrador en creación |
| `app/modules/invbill/presentation/endpoints_series.py` | RBAC lista/crear; `activar` / `desactivar`; `empresa_id` opcional en GET/PUT por id |
| `app/modules/invbill/presentation/endpoints_comprobantes.py` | `anular` / `procesar`; `empresa_id` opcional; `ServiceError` en PUT |
| `app/modules/invbill/presentation/endpoints_comprobante_detalles.py` | `ServiceError` en POST/PUT detalle |
| `app/modules/invbill/application/services/serie_service.py` | `empresa_id` en get/update; `activar_serie` / `desactivar_serie` |
| `app/modules/invbill/application/services/comprobante_service.py` | Validación borrador en PUT; `anular_comprobante` / `procesar_comprobante`; `empresa_id` opcional |
| `app/modules/invbill/application/services/comprobante_detalle_service.py` | Cabecera en borrador para crear/actualizar líneas |
| `app/modules/invbill/application/services/__init__.py` | Exportes públicos |
| `app/infrastructure/database/tables_erp/tables_invbill.py` | Columnas e índice alineados a BD documentada |
| `app/infrastructure/database/queries/invbill/serie_queries.py` | `get_serie_by_id` con filtro opcional `empresa_id` |
| `app/infrastructure/database/queries/invbill/comprobante_queries.py` | `empresa_id` en get/update; exclusión `numero_completo` en insert; `anular_comprobante` / `procesar_comprobante` |
| `app/infrastructure/database/queries/invbill/comprobante_detalle_queries.py` | Exclusión columnas calculadas en insert/update |
| `app/infrastructure/database/queries/invbill/__init__.py` | Exportes de queries |

`app/modules/invbill/presentation/endpoints.py` y `app/api/v1/api.py`: sin cambio de prefijos ni agregado de routers.

---

## 3. Endpoints y contratos

### 3.1 Rutas y métodos existentes (conservados)

Los endpoints **GET/POST/PUT** previos conservan la misma **ruta relativa** y **método HTTP** respecto al cierre de esta fase. El **`response_model`** sigue siendo el mismo tipo Pydantic; los modelos de lectura incorporan **campos adicionales opcionales** (`numero_completo`, `moneda_id`, totales de línea, `empresa_id` en detalle), compatibles hacia atrás para clientes que ignoren propiedades extra en JSON.

| Ruta relativa (bajo `/inv-bill`) | Método | `response_model` |
|----------------------------------|--------|-------------------|
| `/series` | GET | `list[SerieComprobanteRead]` |
| `/series/{serie_id}` | GET | `SerieComprobanteRead` |
| `/series` | POST | `SerieComprobanteRead` |
| `/series/{serie_id}` | PUT | `SerieComprobanteRead` |
| `/comprobantes` | GET | `list[ComprobanteRead]` |
| `/comprobantes/{comprobante_id}` | GET | `ComprobanteRead` |
| `/comprobantes` | POST | `ComprobanteRead` |
| `/comprobantes/{comprobante_id}` | PUT | `ComprobanteRead` |
| `/comprobantes-detalles` | GET | `list[ComprobanteDetalleRead]` |
| `/comprobantes-detalles/{comprobante_detalle_id}` | GET | `ComprobanteDetalleRead` |
| `/comprobantes-detalles` | POST | `ComprobanteDetalleRead` |
| `/comprobantes-detalles/{comprobante_detalle_id}` | PUT | `ComprobanteDetalleRead` |

**Extensiones no rompedoras de contrato**

- Query opcional **`empresa_id`** en **GET** y **PUT** de `/series/{serie_id}` y `/comprobantes/{comprobante_id}`: si no se envía, el comportamiento equivale al filtrado solo por `cliente_id` + PK.
- **RBAC** añadido en **GET** y **POST** de `/series` (lista y creación).
- **Reglas de negocio** en PUT comprobante y POST/PUT detalle: pueden responder **400** con `detail` cuando el estado no es **borrador** (respuesta estándar `HTTPException`, no cambia la forma del cuerpo de éxito).

**Comportamiento por defecto al crear comprobante:** el schema fija **`estado` por defecto `borrador`** para alinear con **`POST .../procesar`** (borrador → emitido). Los clientes que envíen explícitamente otro `estado` siguen pudiendo hacerlo.

### 3.2 Endpoints nuevos — `cliente_id`, `empresa_id` y RBAC

En todos los casos **`cliente_id`** proviene de **`current_user.cliente_id`** en servicios y queries (inserciones fuerzan `cliente_id` desde contexto).

| Ruta relativa | Método | `cliente_id` | `empresa_id` | RBAC |
|---------------|--------|--------------|--------------|------|
| `/series/{serie_id}/activar` | POST | Sí (queries) | Query opcional (filtro coherencia) | `inv_bill.serie.activar` |
| `/series/{serie_id}/desactivar` | POST | Sí | Query opcional | `inv_bill.serie.desactivar` |
| `/comprobantes/{comprobante_id}/anular` | POST | Sí | Query opcional en servicio/query | `inv_bill.comprobante.anular` |
| `/comprobantes/{comprobante_id}/procesar` | POST | Sí | Query opcional | `inv_bill.comprobante.procesar` |

**Integración SUNAT:** no implementada en esta fase; **`procesar`** solo transiciona **`borrador` → `emitido`** en base a reglas de servicio/query.

---

## 4. Seeds RBAC

Script: **`app/docs/database/SEED_PERMISOS_RBAC_INV_BILL.sql`**

- **`modulo_id`:** `E100000E-0000-4000-8000-00000000000E` (módulo INV_BILL en seeds de menú).
- MERGE idempotente por **`codigo`**; reactiva permisos con `es_activo = 0`.
- Permisos: **`inv_bill.serie.*`** (leer, crear, actualizar, activar, desactivar), **`inv_bill.comprobante.*`** (leer, crear, actualizar, anular, procesar), **`inv_bill.comprobante_detalle.*`** (leer, crear, actualizar).

Ejecutar en la BD RBAC central y asignar a roles (`rol_permiso` u otro mecanismo del proyecto) según política del tenant.

---

## 5. Reglas de negocio implementadas (servicios / queries)

- **PUT comprobante:** solo si **`estado`** normalizado es **`borrador`**; caso contrario **`ServiceError`** 400.
- **POST/PUT comprobante detalle:** la cabecera asociada debe estar en **`borrador`**.
- **POST anular:** rechaza si ya **`anulado`**; en caso contrario pasa a **`anulado`** con **`motivo_anulacion`** obligatorio en body.
- **POST procesar:** solo desde **`borrador`** a **`emitido`** (condición en query + validación en servicio).
- **Series activar / desactivar:** actualización lógica de **`es_activo`**, fechas y motivo de baja según operación.

---

## 6. Verificación final (checklist)

| Criterio | Estado |
|----------|--------|
| Endpoints nuevos con `cliente_id` en capa servicio/query | Cumplido |
| Filtro opcional `empresa_id` en GET/PUT por id (serie y comprobante) y en anular/procesar | Cumplido |
| RBAC en rutas nuevas y en GET/POST lista-creación de series | Cumplido |
| Rutas y métodos de los endpoints ya listados en §3.1 sin cambio | Cumplido |
| Cuerpo de respuesta de éxito: mismos `response_model` con campos extra opcionales en lecturas | Cumplido |
| Sin scripts de migración física de BD en este repositorio | Cumplido |

---

## 7. Cierre del módulo

El ciclo **Fase 1–4** para **INV_BILL / invbill** queda cerrado con documentación en **`AUDITORIA_INV_BILL.md`**, implementación en código y seeds en **`SEED_PERMISOS_RBAC_INV_BILL.sql`**. Pendientes típicos fuera de este cierre: asignación de permisos a roles por tenant, pruebas de integración con BD real (`moneda_id` / columnas calculadas según versión desplegada), e integración **SUNAT** cuando corresponda un ciclo posterior.
