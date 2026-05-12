# AUDITORIA — Módulo POS (Punto de Venta)

Fecha: 2026-05-07

Este documento audita **implementación backend** del módulo `POS` contra las tablas documentadas en `docs/bd/POS_TABLAS.sql` (prefijo `pos_` / `POS_`).

Reglas auditadas (prompt maestro / reglas de proyecto):

- Multi-tenant: validar `cliente_id` siempre; validar `empresa_id` cuando la tabla lo tiene.
- RBAC: permiso con patrón `pos.<recurso>.<accion>`.
- Maestros: crear / listar / detalle / actualizar / activar-desactivar (baja lógica `es_activo = 0`).
- Transaccionales: crear (borrador), actualizar (solo borrador donde aplique), aprobar / procesar / anular (según aplique), listar / detalle; detalle de cabecera **preferentemente embebido** en la cabecera.

**Nota de consistencia modelo ↔ BD:** El ORM del repo (`app/infrastructure/database/tables_erp/tables_pos.py`) **no replica literalmente** todo lo definido en `docs/bd/POS_TABLAS.sql` (p. ej. `pos_venta.moneda` código ISO frente a `moneda_id` UUID en el SQL adjunto; columnas calculadas `PERSISTED` en SQL no están declaradas en la tabla Core). La comparación de schemas en §5 contrasta primero con el **SQL documentado**; las desviaciones del modelo interno se mencionan en §6–§7.

---

## 1) Tablas detectadas y tipo

Fuente: `docs/bd/POS_TABLAS.sql`

| Tabla | Tipo |
|-------|------|
| `pos_punto_venta` | Maestro (`es_activo`, `cliente_id`, `empresa_id`) |
| `pos_turno_caja` | Transaccional (apertura/cierre; `cliente_id`, `empresa_id`; sin `es_activo`) |
| `pos_venta` | Transaccional (cabecera; `cliente_id`, `empresa_id`; sin `es_activo`; estados) |
| `pos_venta_detalle` | Transaccional (detalle; `cliente_id`, `empresa_id`; sin `es_activo`) |

---

## 2) Inventario de implementación

No existe carpeta `repositories` en el módulo: el acceso a datos sigue el patrón **queries** en `app/infrastructure/database/queries/pos/` (SQLAlchemy Core + `execute_*`).

| Capa | Ubicación |
|------|-----------|
| Routers | `app/modules/pos/presentation/endpoints*.py`, agregador `endpoints.py` |
| Servicios | `app/modules/pos/application/services/*.py` |
| “Repositorio” / queries | `app/infrastructure/database/queries/pos/*.py` |
| Tablas Core | `app/infrastructure/database/tables_erp/tables_pos.py` |
| Mount API | `app/api/v1/api.py` → `prefix="/pos"` sobre `{API_V1_STR}` |

---

## 3) Endpoints existentes

Prefijo público: `{API_V1_STR}/pos` (típicamente `/api/v1/pos`). Rutas relativas al router POS:

### Puntos de venta — `/puntos-venta`

Archivo: `app/modules/pos/presentation/endpoints_puntos_venta.py`

| Ruta | Método | Entidad | Tenant (`cliente_id`) | Empresa (`empresa_id`) | RBAC |
|------|--------|---------|----------------------|-------------------------|------|
| `/puntos-venta` | GET | `pos_punto_venta` | Sí | Lista: opcional query | `pos.punto_venta.leer` |
| `/puntos-venta/{punto_venta_id}` | GET | `pos_punto_venta` | Sí | No validado en path/query | `pos.punto_venta.leer` |
| `/puntos-venta` | POST | `pos_punto_venta` | Sí (contexto) | Body obligatorio | `pos.punto_venta.crear` |
| `/puntos-venta/{punto_venta_id}` | PUT | `pos_punto_venta` | Sí | No validado en path/query | `pos.punto_venta.actualizar` |

### Turnos de caja — `/turnos-caja`

Archivo: `app/modules/pos/presentation/endpoints_turnos_caja.py`

| Ruta | Método | Entidad | Tenant | Empresa | RBAC |
|------|--------|---------|--------|---------|------|
| `/turnos-caja` | GET | `pos_turno_caja` | Sí | Sin filtro query | `pos.turno_caja.leer` |
| `/turnos-caja/{turno_id}` | GET | `pos_turno_caja` | Sí | Sin validación | `pos.turno_caja.leer` |
| `/turnos-caja` | POST | `pos_turno_caja` | Sí | Body (`empresa_id`) | `pos.turno_caja.crear` |
| `/turnos-caja/{turno_id}` | PUT | `pos_turno_caja` | Sí | Sin validación | `pos.turno_caja.actualizar` |

### Ventas — `/ventas`

Archivo: `app/modules/pos/presentation/endpoints_ventas.py`

| Ruta | Método | Entidad | Tenant | Empresa | RBAC |
|------|--------|---------|--------|---------|------|
| `/ventas` | GET | `pos_venta` | Sí | Sin filtro query | `pos.venta.leer` |
| `/ventas/{venta_id}` | GET | `pos_venta` | Sí | Sin validación | `pos.venta.leer` |
| `/ventas` | POST | `pos_venta` | Sí | Body (`empresa_id`) | `pos.venta.crear` |
| `/ventas/{venta_id}` | PUT | `pos_venta` | Sí | Sin validación | `pos.venta.actualizar` |

### Detalle de ventas — `/ventas-detalle`

Archivo: `app/modules/pos/presentation/endpoints_ventas_detalle.py`

| Ruta | Método | Entidad | Tenant | Empresa | RBAC |
|------|--------|---------|--------|---------|------|
| `/ventas-detalle` | GET | `pos_venta_detalle` | Sí | Sin filtro query | `pos.venta_detalle.leer` |
| `/ventas-detalle/{venta_detalle_id}` | GET | `pos_venta_detalle` | Sí | Sin validación | `pos.venta_detalle.leer` |
| `/ventas-detalle` | POST | `pos_venta_detalle` | Sí | Derivado en query desde cabecera | `pos.venta_detalle.crear` |
| `/ventas-detalle/{venta_detalle_id}` | PUT | `pos_venta_detalle` | Sí | Sin validación explícita | `pos.venta_detalle.actualizar` |

---

## 4) Brechas frente al patrón maestro

### 4.1 `pos_punto_venta` (maestro)

| Requisito | Estado |
|-----------|--------|
| Crear | Cubierto (`POST`) |
| Listar | Cubierto (`GET`; opcional `empresa_id`) |
| Detalle | Cubierto (`GET /{id}`) |
| Actualizar | Cubierto (`PUT`) |
| Activar / desactivar (baja lógica) | Parcial: solo vía `PUT` con `es_activo`; **no** hay `DELETE` ni `POST …/reactivar` dedicados ni permiso `eliminar` como en ORG |

### 4.2 `pos_turno_caja` (transaccional)

| Requisito | Estado |
|-----------|--------|
| Crear | Cubierto (apertura) |
| Actualizar | Cubierto (incl. campos de cierre vía `PUT`) |
| Listar / detalle | Cubierto |
| Reglas de estado (solo borrador editable, etc.) | No aplicado en servicio/query: `TurnoCajaUpdate` permite mutar totales y estado sin máquina de estados explícita |
| Aprobar / procesar / anular | No hay endpoints dedicados (puede ser aceptable para turnos; evaluar negocio) |

### 4.3 `pos_venta` + `pos_venta_detalle` (transaccional)

| Requisito | Estado |
|-----------|--------|
| Crear cabecera | Cubierto |
| Listar / detalle cabecera | Cubierto |
| Actualizar cabecera | Cubierto (`PUT`; incluye anulación por campos en `VentaUpdate`) |
| Crear / actualizar detalle | Cubierto en **router aparte** `/ventas-detalle` |
| Detalle embebido en cabecera | No hay `POST/PUT /ventas` con arreglo de líneas en una sola operación transaccional |
| Actualizar solo en borrador | No verificado en código (no hay gate por `estado == 'borrador'` en updates) |
| Aprobar / procesar / anular dedicados | No hay `POST …/anular` separado; anulación vía `PUT` genérico |

### 4.4 Tablas derivadas (solo lectura)

No hay tablas POS solo-analíticas en `POS_TABLAS.sql`. Las columnas calculadas del SQL documentado son **columnas persistidas** dentro de tablas transaccionales; deben exponerse en lectura si la BD las materializa (ver §5–§6).

---

## 5) Campos en BD (`docs/bd/POS_TABLAS.sql`) ausentes o mal alineados en schemas de lectura/escritura

### 5.1 `pos_punto_venta`

- Lectura (`PuntoVentaRead`): alineado con columnas “normales” del SQL.
- Escritura: ok respecto al modelo Core actual.

### 5.2 `pos_turno_caja`

En el SQL documentado existen columnas computadas **`diferencia`** y **`total_ingresos`** (`PERSISTED`).  
**No** están en `TurnoCajaRead` ni en `tables_pos.py`; la API no puede devolverlas vía el modelo Core actual.

### 5.3 `pos_venta`

- SQL documentado: **`moneda_id`** (FK `cat_moneda`). El schema y el Core del repo usan **`moneda`** como `String(3)` — **desalineación documentación ↔ código**.
- Columnas computadas **`total_cobrar`**, **`monto_cambio`** en SQL: **no** en `VentaRead` ni en `tables_pos.py`.

### 5.4 `pos_venta_detalle`

- **`empresa_id`**: existe en BD; **no** aparece en `VentaDetalleRead` (el insert lo rellena desde cabecera en query).
- Columnas computadas en SQL: **`descuento_monto`**, **`precio_neto`**, **`subtotal`**, **`igv`**, **`total`** — **no** en `VentaDetalleRead` ni en `tables_pos.py` (coincide con auditoría previa en `scripts/erp_columns_audit_missing_extra.txt` para columnas faltantes en modelo).

---

## 6) Tenant y RBAC — problemas detectados

### Empresa (`empresa_id`)

- **Listados** de turnos, ventas y detalles: **no** aceptan filtro opcional `empresa_id` (a diferencia de puntos de venta).
- **GET por id** (punto de venta, turno, venta, detalle): **no** exigen ni validan `empresa_id` opcional; solo `cliente_id` + PK. Riesgo menor por UUID, pero **incoherente** con la regla “validar `empresa_id` cuando la tabla lo tiene” y con patrones de otros módulos (p. ej. ORG).

### RBAC

- Endpoints declaran permisos `pos.<recurso>.<accion>` con acciones `leer`, `crear`, `actualizar`.
- **No** se encontró en `app/docs/database` un seed dedicado tipo `SEED_PERMISOS_RBAC_POS.sql` que registre estos códigos (búsqueda por prefijo POS / `pos.` en seeds). **Riesgo:** permisos no existentes en BD → usuarios sin acceso o solo admins según política global.

### Permiso `eliminar` (maestro)

- No hay endpoint que use `pos.punto_venta.eliminar`; la baja lógica dependería de `actualizar`.

---

## 7) Código u orientación incorrecta / deuda (no eliminar)

| Ítem | Observación |
|------|-------------|
| Detalle en router propio | Funciona, pero se aleja del prompt “detalle embebido en cabecera” y complica transacciones cabecera-detalle atómicas. |
| `TurnoCajaUpdate` | Expone campos agregados (`total_ventas`, montos, conteos) editables por API; en muchos diseños son **solo sistema** al cerrar turno o al registrar ventas. |
| `VentaUpdate` | Permite cambiar `estado`, comprobante y anulación sin validaciones centralizadas de negocio visibles en servicio. |
| Modelo Core vs `POS_TABLAS.sql` | Divergencias (`moneda` vs `moneda_id`; sin columnas calculadas) impiden exponer campos reales de BD si esta siguiera el SQL documentado al pie de la letra. |

---

## 8) Endpoints faltantes sugeridos (sin cambiar contratos actuales)

Los siguientes son **añadidos opcionales** para alinear con el prompt maestro sin romper rutas existentes:

| Ruta sugerida | Método | Objetivo |
|---------------|--------|----------|
| `/puntos-venta/{id}` | DELETE | Baja lógica (`es_activo = 0`) + permiso `pos.punto_venta.eliminar` |
| `/puntos-venta/{id}/reactivar` | POST | Reactivar maestro |
| `/turnos-caja`, `/ventas`, `/ventas-detalle` | GET | Query opcional `empresa_id` |
| `GET` por id en todas las entidades POS | GET | Query opcional `empresa_id` para validar pertenencia |
| `/ventas/{venta_id}/detalles` | GET/POST/PUT | Detalle anidado (alternativa a `/ventas-detalle`) |
| `/ventas/{venta_id}/anular` | POST | Anulación con body de motivo (delegación desde `PUT` si se desea mantener compatibilidad) |

---

## 9) Seeds RBAC sugeridos

- Crear `app/docs/database/SEED_PERMISOS_RBAC_POS.sql` (o incorporar en el seed maestro de permisos) con al menos:

  `pos.punto_venta.{leer,crear,actualizar,eliminar}`  
  `pos.turno_caja.{leer,crear,actualizar}`  
  `pos.venta.{leer,crear,actualizar}` (+ acciones de negocio si se añaden endpoints dedicados)  
  `pos.venta_detalle.{leer,crear,actualizar}`  

---

## 10) Resumen ejecutivo

| Área | Conclusión |
|------|------------|
| Cobertura CRUD básica | Presente para las 4 tablas vía 4 grupos de endpoints |
| Maestro POS | Falta patrón explícito eliminar/reactivar y permiso `eliminar` |
| Transaccional | Falta rigor de estados (borrador), atomicidad cabecera-detalle y endpoints de negocio explícitos |
| Multi-tenant `empresa_id` | Débil en GET por id y listados de turno/venta/detalle |
| Schemas vs BD documentada | Faltan columnas computadas y `empresa_id` en lectura de detalle; desajuste `moneda_id` vs `moneda` |
| Seeds permisos POS | No localizados en `app/docs/database` |

---

⛔ **Fin Fase 2 (auditoría).** Esperar confirmación antes de Fase 3 (implementación).
