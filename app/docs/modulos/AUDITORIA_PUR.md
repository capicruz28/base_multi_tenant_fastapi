# Auditoría — Módulo PUR (Compras y Abastecimiento)

**Código:** PUR  
**Fuente de modelo de datos:** `docs/bd/PUR_TABLAS.sql` (tablas `pur_*`).  
**Metodología:** `docs/prompts/PROMPT_MODULO_MAESTRO.md` — Fase 2.

**Inventario de código PUR**

| Capa | Ubicación |
|------|-----------|
| Routers (presentation) | `app/modules/pur/presentation/endpoints.py` (agregador), `endpoints_proveedores.py`, `endpoints_contactos.py`, `endpoints_productos_proveedor.py`, `endpoints_solicitudes.py`, `endpoints_solicitudes_detalle.py`, `endpoints_solicitudes_transaccional.py`, `endpoints_cotizaciones.py`, `endpoints_cotizaciones_detalle.py`, `endpoints_cotizaciones_transaccional.py`, `endpoints_ordenes_compra.py`, `endpoints_ordenes_compra_detalle.py`, `endpoints_ordenes_compra_transaccional.py`, `endpoints_recepciones.py`, `endpoints_recepciones_detalle.py`, `endpoints_recepciones_transaccional.py` |
| Schemas | `app/modules/pur/presentation/schemas.py` |
| Servicios (application) | `app/modules/pur/application/services/*.py` (incl. `pur_transaccional_creacion_service.py`) |
| Consultas SQL (infraestructura) | `app/infrastructure/database/queries/pur/*.py` |
| Repositories dedicados en `app/modules/pur/` | No hay carpeta `repositories`; persistencia vía queries en infraestructura |

Prefijo API: **`{API_V1_STR}/pur`** (p. ej. `/api/v1/pur` si `API_V1_STR=/api/v1`), registro en `app/api/v1/api.py`.

---

## 1. Tablas detectadas y su tipo

| Tabla | Tipo (prompt) |
|-------|----------------|
| `pur_proveedor` | Maestro |
| `pur_proveedor_contacto` | Maestro (dependiente de proveedor) |
| `pur_producto_proveedor` | Maestro (relación INV–PUR) |
| `pur_solicitud_compra` | Transaccional |
| `pur_solicitud_compra_detalle` | Transaccional (detalle) |
| `pur_cotizacion` | Transaccional |
| `pur_cotizacion_detalle` | Transaccional (detalle) |
| `pur_orden_compra` | Transaccional |
| `pur_orden_compra_detalle` | Transaccional (detalle) |
| `pur_recepcion` | Transaccional |
| `pur_recepcion_detalle` | Transaccional (detalle) |

No hay tablas `pur_*` puramente derivadas/analíticas (solo columnas calculadas persistidas dentro de detalles).

---

## 2. Endpoints existentes

Criterios: **tenant** = uso de `cliente_id` desde `current_user.cliente_id` hacia servicios/queries (y, cuando la tabla lo tiene, `empresa_id` en filtros o body). **RBAC** = `Depends(require_permission(...))` en la ruta.

Rutas relativas a **`/pur`** (más el prefijo global de la API).

### 2.1 Proveedores (`/pur/proveedores`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/proveedores` | GET | `pur_proveedor` | Sí | `pur.proveedor.leer` |
| `/proveedores/{proveedor_id}` | GET | `pur_proveedor` | Sí | `pur.proveedor.leer` |
| `/proveedores` | POST | `pur_proveedor` | Sí | `pur.proveedor.crear` |
| `/proveedores/{proveedor_id}` | PUT | `pur_proveedor` | Sí | `pur.proveedor.actualizar` |

### 2.2 Contactos de proveedor (`/pur/contactos`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/contactos` | GET | `pur_proveedor_contacto` | Sí | `pur.contacto.leer` |
| `/contactos/{contacto_id}` | GET | `pur_proveedor_contacto` | Sí | `pur.contacto.leer` |
| `/contactos` | POST | `pur_proveedor_contacto` | Sí | `pur.contacto.crear` |
| `/contactos/{contacto_id}` | PUT | `pur_proveedor_contacto` | Sí | `pur.contacto.actualizar` |

### 2.3 Productos por proveedor (`/pur/productos-proveedor`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/productos-proveedor` | GET | `pur_producto_proveedor` | Sí | `pur.producto_proveedor.leer` |
| `/productos-proveedor/{producto_proveedor_id}` | GET | `pur_producto_proveedor` | Sí | `pur.producto_proveedor.leer` |
| `/productos-proveedor` | POST | `pur_producto_proveedor` | Sí | `pur.producto_proveedor.crear` |
| `/productos-proveedor/{producto_proveedor_id}` | PUT | `pur_producto_proveedor` | Sí | `pur.producto_proveedor.actualizar` |

### 2.4 Solicitudes de compra (`/pur/solicitudes`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/solicitudes` | GET | `pur_solicitud_compra` | Sí | `pur.solicitud.leer` |
| `/solicitudes/{solicitud_id}` | GET | `pur_solicitud_compra` | Sí | `pur.solicitud.leer` |
| `/solicitudes` | POST | `pur_solicitud_compra` | Sí | `pur.solicitud.crear` |
| `/solicitudes/{solicitud_id}` | PUT | `pur_solicitud_compra` | Sí | `pur.solicitud.actualizar` |
| `/solicitudes/{solicitud_id}/aprobar` | POST | `pur_solicitud_compra` | Sí | `pur.solicitud.actualizar` |
| `/solicitudes/{solicitud_id}/rechazar` | POST | `pur_solicitud_compra` | Sí | `pur.solicitud.actualizar` |
| `/solicitudes/{solicitud_id}/marcar-procesada` | POST | `pur_solicitud_compra` | Sí | `pur.solicitud.actualizar` |
| `/solicitudes/transaccional` | POST | `pur_solicitud_compra` + detalle | Sí | `pur.solicitud.crear` |

### 2.5 Solicitudes — detalle (`/pur/solicitudes-detalle`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/solicitudes-detalle` | GET | `pur_solicitud_compra_detalle` | Sí | `pur.solicitud.leer` |
| `/solicitudes-detalle/{solicitud_detalle_id}` | GET | `pur_solicitud_compra_detalle` | Sí | `pur.solicitud.leer` |
| `/solicitudes-detalle` | POST | `pur_solicitud_compra_detalle` | Sí | `pur.solicitud.crear` |
| `/solicitudes-detalle/{solicitud_detalle_id}` | PUT | `pur_solicitud_compra_detalle` | Sí | `pur.solicitud.actualizar` |

### 2.6 Cotizaciones (`/pur/cotizaciones`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/cotizaciones` | GET | `pur_cotizacion` | Sí | `pur.cotizacion.leer` |
| `/cotizaciones/{cotizacion_id}` | GET | `pur_cotizacion` | Sí | `pur.cotizacion.leer` |
| `/cotizaciones` | POST | `pur_cotizacion` | Sí | `pur.cotizacion.crear` |
| `/cotizaciones/{cotizacion_id}` | PUT | `pur_cotizacion` | Sí | `pur.cotizacion.actualizar` |
| `/cotizaciones/{cotizacion_id}/marcar-ganadora` | POST | `pur_cotizacion` | Sí | `pur.cotizacion.actualizar` |
| `/cotizaciones/transaccional` | POST | `pur_cotizacion` + detalle | Sí | `pur.cotizacion.crear` |

### 2.7 Cotizaciones — detalle (`/pur/cotizaciones-detalle`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/cotizaciones-detalle` | GET | `pur_cotizacion_detalle` | Sí | `pur.cotizacion.leer` |
| `/cotizaciones-detalle/{cotizacion_detalle_id}` | GET | `pur_cotizacion_detalle` | Sí | `pur.cotizacion.leer` |
| `/cotizaciones-detalle` | POST | `pur_cotizacion_detalle` | Sí | `pur.cotizacion.crear` |
| `/cotizaciones-detalle/{cotizacion_detalle_id}` | PUT | `pur_cotizacion_detalle` | Sí | `pur.cotizacion.actualizar` |

### 2.8 Órdenes de compra (`/pur/ordenes-compra`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/ordenes-compra` | GET | `pur_orden_compra` | Sí | `pur.orden_compra.leer` |
| `/ordenes-compra/{orden_compra_id}` | GET | `pur_orden_compra` | Sí | `pur.orden_compra.leer` |
| `/ordenes-compra` | POST | `pur_orden_compra` | Sí | `pur.orden_compra.crear` |
| `/ordenes-compra/{orden_compra_id}` | PUT | `pur_orden_compra` | Sí | `pur.orden_compra.actualizar` |
| `/ordenes-compra/{orden_compra_id}/aprobar` | POST | `pur_orden_compra` | Sí | `pur.orden_compra.actualizar` |
| `/ordenes-compra/{orden_compra_id}/anular` | POST | `pur_orden_compra` | Sí | `pur.orden_compra.actualizar` |
| `/ordenes-compra/transaccional` | POST | `pur_orden_compra` + detalle | Sí | `pur.orden_compra.crear` |

### 2.9 Órdenes de compra — detalle (`/pur/ordenes-compra-detalle`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/ordenes-compra-detalle` | GET | `pur_orden_compra_detalle` | Sí | `pur.orden_compra.leer` |
| `/ordenes-compra-detalle/{orden_compra_detalle_id}` | GET | `pur_orden_compra_detalle` | Sí | `pur.orden_compra.leer` |
| `/ordenes-compra-detalle` | POST | `pur_orden_compra_detalle` | Sí | `pur.orden_compra.crear` |
| `/ordenes-compra-detalle/{orden_compra_detalle_id}` | PUT | `pur_orden_compra_detalle` | Sí | `pur.orden_compra.actualizar` |

### 2.10 Recepciones (`/pur/recepciones`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/recepciones` | GET | `pur_recepcion` | Sí | `pur.recepcion.leer` |
| `/recepciones/{recepcion_id}` | GET | `pur_recepcion` | Sí | `pur.recepcion.leer` |
| `/recepciones` | POST | `pur_recepcion` | Sí | `pur.recepcion.crear` |
| `/recepciones/{recepcion_id}` | PUT | `pur_recepcion` | Sí | `pur.recepcion.actualizar` |
| `/recepciones/{recepcion_id}/procesar` | POST | `pur_recepcion` | Sí | `pur.recepcion.actualizar` |
| `/recepciones/transaccional` | POST | `pur_recepcion` + detalle | Sí | `pur.recepcion.crear` |

### 2.11 Recepciones — detalle (`/pur/recepciones-detalle`)

| Ruta | Método | Entidad (tabla) | Tenant | RBAC |
|------|--------|-----------------|--------|------|
| `/recepciones-detalle` | GET | `pur_recepcion_detalle` | Sí | `pur.recepcion.leer` |
| `/recepciones-detalle/{recepcion_detalle_id}` | GET | `pur_recepcion_detalle` | Sí | `pur.recepcion.leer` |
| `/recepciones-detalle` | POST | `pur_recepcion_detalle` | Sí | `pur.recepcion.crear` |
| `/recepciones-detalle/{recepcion_detalle_id}` | PUT | `pur_recepcion_detalle` | Sí | `pur.recepcion.actualizar` |

**Observación:** Todos los routers revisados combinan `get_current_active_user` con `require_permission`. No se detectaron rutas PUR públicas sin RBAC.

---

## 3. Brechas frente al estándar del prompt

### 3.1 Maestros (crear, listar, detalle, actualizar, activar/desactivar)

| Tabla | Crear | Listar | Detalle | Actualizar | Activar/desactivar explícito |
|-------|-------|--------|---------|------------|------------------------------|
| `pur_proveedor` | Sí | Sí | Sí | Sí | **Parcial:** `es_activo` vía `PUT`; sin ruta dedicada tipo `POST …/reactivar` (patrón ORG) |
| `pur_proveedor_contacto` | Sí | Sí | Sí | Sí | **Parcial:** mismo criterio (`es_activo` en `PUT`) |
| `pur_producto_proveedor` | Sí | Sí | Sí | Sí | **Parcial:** mismo criterio |

### 3.2 Transaccional (cabecera): crear (borrador), actualizar (solo borrador / editable), aprobar, procesar, anular, listar, detalle

Estándar interpretado según `PUR_TABLAS.sql` y comentarios de estado.

#### `pur_solicitud_compra`

| Requisito | Estado |
|-----------|--------|
| Crear (borrador) | **Sí** (`POST`, estado por defecto en BD/schema) |
| Listar / detalle | **Sí** |
| Actualizar solo en fase editable | **Brecha:** `update_solicitud_servicio` no valida `estado` antes de persistir |
| Aprobar | **Sí** (`/aprobar`, con validación de estado) |
| Procesar | **Parcial:** `POST …/marcar-procesada` existe pero **no valida** que la solicitud esté en estado coherente (p. ej. aprobada) antes de marcar procesada |
| Anular | **Brecha:** la BD admite `anulada` en comentarios de flujo; **no hay** endpoint dedicado análogo a OC/rechazo unificado |
| Rechazar | **Sí** (cubre parte del ciclo; no es anulación genérica) |

#### `pur_cotizacion`

| Requisito | Estado |
|-----------|--------|
| Crear / listar / detalle / PUT | **Sí** |
| Actualizar solo borrador/editable | **Brecha:** sin validación de estado en actualización |
| Aprobar / procesar / anular como flujo explícito | **Brecha:** no hay `aprobar` / `procesar` / `anular` dedicados; existe `marcar-ganadora`. Transiciones (`recibida`, `evaluada`, `aceptada`, `rechazada`, `vencida`) dependen de `PUT` genérico |

#### `pur_orden_compra`

| Requisito | Estado |
|-----------|--------|
| Crear / listar / detalle | **Sí** |
| Actualizar solo borrador | **Brecha:** `update_orden_compra_servicio` no restringe por `estado` |
| Aprobar | **Sí**, pero pasa a **`aprobada`**; el modelo SQL incluye también **`emitida`** — **posible hueco** si el negocio exige estado intermedio “emitida” vía API |
| Procesar | **Parcial:** avance hacia `parcial`/`completa` ocurre vía **recepción** (`recepcion_service`), no un endpoint “procesar OC” |
| Anular | **Sí** (`/anular`); **brecha:** el servicio **no valida** estados previos permitidos (p. ej. impedir anular ya `completa` o ya `anulada`) |

#### `pur_recepcion`

| Requisito | Estado |
|-----------|--------|
| Crear / listar / detalle | **Sí** |
| Actualizar solo borrador | **Brecha:** `update_recepcion_servicio` sin chequeo de estado editable |
| Procesar | **Sí** (`/procesar`; lógica adicional en servicio) |
| Aprobar (p. ej. tras inspección) | **Brecha:** estados `inspeccion` / `aprobada` en BD **sin** endpoints dedicados de transición |
| Anular | **Brecha:** estado `anulada` en BD **sin** endpoint dedicado |

### 3.3 Detalles transaccionales (CRUD separado + creación transaccional)

Existe **doble vía**: líneas por `*-detalle` y creación agrupada `POST …/transaccional`. Respecto al prompt maestro (“detalle embebido”), el diseño actual es **más expuesto** de lo mínimo; no es incorrecto por sí solo, pero **incrementa** la necesidad de validar estado en PUT/POST de líneas para no desalinear cabecera.

| Tabla detalle | PUT sin validar cabecera en borrador (riesgo) |
|---------------|-----------------------------------------------|
| `pur_solicitud_compra_detalle` | A confirmar en servicio; patrón general mismo gap que cabecera |
| `pur_cotizacion_detalle` | Idem |
| `pur_orden_compra_detalle` | Idem |
| `pur_recepcion_detalle` | Idem |

---

## 4. Campos en BD no expuestos (o no expuestos del todo) en schemas de lectura / API

Contraste principal: columnas **persistidas calculadas** en SQL vs `*Read` en `schemas.py`.

| Tabla | Columnas en BD ausentes en schema `*Read` típico |
|-------|--------------------------------------------------|
| `pur_solicitud_compra_detalle` | `total_referencial`, `cantidad_pendiente` (computadas) |
| `pur_cotizacion_detalle` | `precio_neto`, `total` (computadas) |
| `pur_orden_compra_detalle` | `precio_neto`, `subtotal`, `igv`, `total`, `cantidad_pendiente` (computadas) |
| `pur_recepcion_detalle` | `diferencia`, `total` (computadas) |

**Nota:** Si las consultas SQL ya devuelven esas columnas, Pydantic puede ignorarlas o fallar según configuración; conviene **alinear** `*Read` con el SELECT o excluir columnas en query de forma explícita.

**Cabeceras:** Los modelos `*Read` de cabeceras están en general alineados con `PUR_TABLAS.sql` para uso estándar. Detalle menor: `pur_solicitud_compra` no define `usuario_actualizacion_id` en SQL; el schema no lo exige.

**Cuerpos `rechazar` / `anular`:** uso de `Body(Optional[dict])` en lugar de schema Pydantic tipado; no es campo de BD, pero es **deuda de contrato** documentable en Fase 3 si se desea tipar sin romper compatibilidad.

---

## 5. Tenant y RBAC — observaciones

- **RBAC:** Recursos usados: `proveedor`, `contacto`, `producto_proveedor`, `solicitud`, `cotizacion`, `orden_compra`, `recepcion`. Los detalles reutilizan el permiso de la cabecera (`solicitud`, `cotizacion`, `orden_compra`, `recepcion`), coherente con listar/editar líneas del mismo documento.
- **Tenant (`cliente_id`):** Consistente en endpoints revisados.
- **`empresa_id` en GET por ID:** En maestros como proveedor, el detalle **no** exige `empresa_id` en query (filtra por `cliente_id` + id). La tabla `pur_proveedor` sí tiene `empresa_id`; si el requisito de negocio es restringir lectura por empresa, habría que alinear con patrón ORG opcional `empresa_id` en query (mejora opcional, no necesariamente bug).

---

## 6. Endpoints sugeridos (sin implementar aquí)

Solo propuesta para cerrar brechas del apartado 3; **no modifica** contratos hasta decisión de Fase 3.

| Brecha | Ruta sugerida (bajo `/pur`) | Método |
|--------|----------------------------|--------|
| Anular solicitud | `/solicitudes/{id}/anular` | POST |
| Validación estricta “solo editable en borrador” | Misma ruta `PUT` existente reforzada en servicio (sin nueva ruta) | PUT |
| Transiciones cotización | `/cotizaciones/{id}/aceptar`, `…/rechazar`, `…/marcar-recibida`, etc. (o una acción genérica con body tipado) | POST |
| Emitir OC | `/ordenes-compra/{id}/emitir` | POST |
| Anular recepción | `/recepciones/{id}/anular` | POST |
| Aprobar recepción post-inspección | `/recepciones/{id}/aprobar` | POST |
| Reactivar maestro | `/proveedores/{id}/reactivar`, análogos contacto/producto-proveedor | POST |

---

## 7. Código marcado como revisable (no eliminar en auditoría)

- `Optional[dict]` en bodies de `rechazar` (solicitud) y `anular` (orden de compra): contrato débil; mejorar con schema dedicado en una evolución controlada.
- `marcar_procesada_solicitud_servicio`: conviene auditar reglas de negocio en Fase 3 sin borrar el endpoint.

---

## 8. Resumen ejecutivo

| Área | Conclusión |
|------|------------|
| Cobertura CRUD | Alta: las 11 tablas tienen al menos lectura/escritura vía API o líneas + transaccional |
| Maestros PUR | Cumplen CRUD básico; falta simetría con patrón ORG de reactivación explícita si se desea uniformidad |
| Transaccional | Huecos en **validación de estado** en `PUT` de cabeceras/detalle y en **anular** solicitud/recepción; cotización sin **máquina de estados** explícita; OC **emitida** vs **aprobada** a revisar con negocio |
| Schemas vs BD | Añadir computadas en `*Read` de detalles o filtrar en SQL de forma explícita |
| RBAC / tenant | Presente en todas las rutas inventariadas |

⛔ **Fase 2 completa.** Esperar confirmación antes de **Fase 3** (implementación acotada al reporte).
