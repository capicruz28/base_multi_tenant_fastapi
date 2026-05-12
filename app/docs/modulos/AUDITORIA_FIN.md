# Auditoría — Módulo FIN (Finanzas y Contabilidad)

Documento generado en **Fase 2** del prompt maestro (solo lectura y análisis).  
Prefijo de tablas: `fin_`. Rutas API bajo `{API_V1_STR}/fin` (p. ej. `/api/v1/fin`).

---

## 1. Tablas detectadas y tipo

| Tabla | Tipo |
|-------|------|
| `fin_plan_cuentas` | Maestro |
| `fin_periodo_contable` | Maestro / configuración |
| `fin_asiento_contable` | Transaccional (cabecera) |
| `fin_asiento_detalle` | Transaccional (detalle; en diseño objetivo va embebido en cabecera) |

**Nota de modelo físico:** En `docs/bd/FIN_TABLAS.sql` y `app/docs/database/3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql`, `fin_asiento_contable` usa `moneda_id` (FK `cat_moneda`) y columnas calculadas `diferencia` / `esta_cuadrado`. En código, `app/infrastructure/database/tables_erp/tables_fin.py` define `moneda` como `String(3)` y no refleja `moneda_id` ni las columnas persistidas. La implementación actual está alineada con **tables_fin.py**, no con el script FASE4/FIN_TABLAS en ese punto (riesgo de desincronización si la BD real sigue el script documentado).

---

## 2. Inventario de código (Fase 2.1)

No existe carpeta `repositories` dedicada: la persistencia está en `app/infrastructure/database/queries/fin/*.py` (patrón queries + `execute_query` / `execute_insert` / `execute_update`).

### 2.1 Endpoints existentes

Base: `/fin` + subprefijos de `app/modules/fin/presentation/endpoints.py`.

| Ruta | Método | Entidad | Tenant (`cliente_id`) | RBAC (`require_permission`) |
|------|--------|---------|-------------------------|-------------------------------|
| `/fin/plan-cuentas` | GET | Plan de cuentas | Sí (`current_user.cliente_id`) | Sí (`fin.plan_cuenta.leer`) |
| `/fin/plan-cuentas/{cuenta_id}` | GET | Plan de cuentas | Sí | Sí (`fin.plan_cuenta.leer`) |
| `/fin/plan-cuentas` | POST | Plan de cuentas | Sí | Sí (`fin.plan_cuenta.crear`) |
| `/fin/plan-cuentas/{cuenta_id}` | PUT | Plan de cuentas | Sí | Sí (`fin.plan_cuenta.actualizar`) |
| `/fin/periodos` | GET | Periodo contable | Sí | Sí (`fin.periodo.leer`) |
| `/fin/periodos/{periodo_id}` | GET | Periodo contable | Sí | Sí (`fin.periodo.leer`) |
| `/fin/periodos` | POST | Periodo contable | Sí | Sí (`fin.periodo.crear`) |
| `/fin/periodos/{periodo_id}` | PUT | Periodo contable | Sí | Sí (`fin.periodo.actualizar`) |
| `/fin/asientos` | GET | Asiento contable | Sí | **No** |
| `/fin/asientos/{asiento_id}` | GET | Asiento contable | Sí | Sí (`fin.asiento.leer`) |
| `/fin/asientos` | POST | Asiento contable | Sí | **No** |
| `/fin/asientos/{asiento_id}` | PUT | Asiento contable | Sí | Sí (`fin.asiento.actualizar`) |
| `/fin/asientos/{asiento_id}/detalles` | GET | Asiento detalle | Sí | Sí (`fin.asiento_detalle.leer`) |
| `/fin/asientos/{asiento_id}/detalles` | POST | Asiento detalle | Sí | Sí (`fin.asiento_detalle.crear`) |
| `/fin/asientos/detalles/{asiento_detalle_id}` | GET | Asiento detalle | Sí | Sí (`fin.asiento_detalle.leer`) |
| `/fin/asientos/detalles/{asiento_detalle_id}` | PUT | Asiento detalle | Sí | Sí (`fin.asiento_detalle.actualizar`) |

**Tenant `empresa_id`:** Los listados aceptan `empresa_id` opcional en query y el body de creación incluye `empresa_id` donde aplica. Los **GET por ID** y updates filtran principalmente por `cliente_id` + clave técnica en queries; no exigen `empresa_id` en la ruta. Si la política del ERP exige acotar siempre por empresa en lecturas/escrituras, habría que endurecer validación (query obligatorio, claim de empresa, etc.).

---

## 3. Brechas funcionales (Fase 2.2)

Criterio: maestro → crear, listar, detalle, actualizar, activar/desactivar; transaccional → crear (borrador), actualizar (borrador), aprobar, procesar, anular, listar, detalle; detalle embebido según prompt maestro.

### `fin_plan_cuentas` (maestro)

| Requisito | Estado |
|-----------|--------|
| Crear | Cubierto (POST) |
| Listar | Cubierto (GET lista) |
| Detalle | Cubierto (GET por id) |
| Actualizar | Cubierto (PUT) |
| Activar / desactivar | **Parcial:** `es_activo` en `PlanCuentaUpdate`; no hay rutas dedicadas tipo `DELETE` lógico / `POST .../reactivar` como en INV (`categorias`) |

### `fin_periodo_contable` (maestro)

| Requisito | Estado |
|-----------|--------|
| Crear / listar / detalle / actualizar | Cubierto |
| Activar/desactivar | N/A (tabla sin `es_activo`; control por `estado` / fechas) |
| Cerrar / bloquear periodo | **Parcial:** campos en `PeriodoContableUpdate` y tabla; sin endpoints semánticos dedicados (ej. “cerrar periodo”) |

### `fin_asiento_contable` (transaccional)

| Requisito | Estado |
|-----------|--------|
| Crear (borrador) | Cubierto (POST) |
| Listar / detalle | Cubierto |
| Actualizar | Cubierto (PUT) |
| Solo actualizar en borrador | **No verificado** en servicio (no hay regla explícita en capa aplicación revisada) |
| Aprobar | **Falta** endpoint o acción dedicada (solo campos en update) |
| Procesar / registrar | **Falta** flujo explícito (p. ej. transición a `registrado`) |
| Anular | **Falta** endpoint dedicado; campos de anulación vía PUT genérico |

### `fin_asiento_detalle`

| Requisito | Estado |
|-----------|--------|
| Lectura como parte del documento | Cubierto (GET por asiento) |
| Escritura pública separada (POST/PUT línea) | **Presente en código** |
| Alineación con prompt maestro (detalle embebido en cabecera) | **Desalineado:** existe CRUD de líneas por API separada |

---

## 4. Campos en BD no cubiertos o divergentes en schemas (Fase 2.3)

Comparación principal contra **`docs/bd/FIN_TABLAS.sql`** (y FASE4 donde coincide). Donde el ORM `tables_fin.py` difiere, se indica.

### Plan de cuentas (`PlanCuentaRead` / Create / Update)

- Cobertura razonable respecto a columnas no calculadas de `fin_plan_cuentas`.

### Periodo (`PeriodoContableRead`)

| Campo en BD | En schema Read |
|-------------|-----------------|
| `nombre_periodo` (columna persistida calculada) | **Ausente** |

### Asiento cabecera (`AsientoContableRead` / Create / Update)

| Origen | Observación |
|--------|-------------|
| `docs/bd/FIN_TABLAS.sql` | `moneda_id` (UUID, FK `cat_moneda`), `diferencia`, `esta_cuadrado` (calculadas) no están en `AsientoContableRead`; Create/Update usan `moneda` (string) alineado con **tables_fin.py**, no con FIN_TABLAS FASE4 |
| `tables_fin.py` (app) | Coincide con uso de `moneda` string; igualmente faltan en Read las magnitudes `diferencia` / `esta_cuadrado` si existieran en BD |

### Asiento detalle (`AsientoDetalleRead`)

| Campo en BD | En schema Read |
|-------------|-----------------|
| `empresa_id` | **Ausente** (existe en tabla y en INSERT derivado en queries) |

### Cuerpos Create/Update vs tabla

- `AsientoDetalleCreate` no incluye `empresa_id`: aceptable si siempre se deriva de cabecera (ya hay lógica en `create_asiento_detalle`), pero el **Read** debería exponer `empresa_id` para coherencia con la BD.

---

## 5. Problemas de tenant y RBAC

1. **RBAC ausente:** `GET /fin/asientos` y `POST /fin/asientos` no declaran `Depends(require_permission(...))` mientras otros endpoints del mismo recurso sí (`fin.asiento.leer` / acciones). Inconsistente y posible brecha de autorización.
2. **`empresa_id` en GET por ID:** operaciones `get_*_by_id` filtran por `cliente_id` + PK; no cruzan tenant, pero tampoco restringen por empresa si el producto lo exige.
3. **Permisos en seeds SQL:** en el repositorio, `grep` de seeds muestra entradas explícitas para `fin.asiento_detalle.*` en `SEED_PERMISOS_RBAC_FASE4_CANDIDATOS.sql`; **no** aparecen en esos archivos listados `fin.plan_cuenta.*`, `fin.periodo.*`, `fin.asiento.*`. Si no están cargados en otro script, `require_permission` podría fallar en despliegues que solo apliquen seeds versionados.

---

## 6. Código marcado como obsoleto o incorrecto (no eliminar)

| Ubicación | Observación |
|-----------|---------------|
| `endpoints_asientos.py` | Listado y creación de asientos sin `require_permission`. |
| `endpoints_asientos.py` + servicios/queries de detalle | CRUD de líneas expuesto aparte; el prompt maestro recomienda detalle embebido en cabecera (no borrar en Fase 2; revisar en Fase 3). |
| `tables_fin.py` vs `FIN_TABLAS.sql` / FASE4 | Posible modelo distinto (`moneda` vs `moneda_id` + columnas calculadas). No es “obsoleto” por sí solo, pero es **inconsistencia documentación ↔ código** a resolver sin cambiar BD salvo que el proyecto alinee scripts. |

---

## 7. Endpoints faltantes (sugerencia, sin implementar aún)

Respetar prefijos y convenciones actuales (`/fin/plan-cuentas`, `/fin/periodos`, `/fin/asientos`).

| Sugerencia | Método | Notas |
|------------|--------|--------|
| `/fin/plan-cuentas/{cuenta_id}` baja lógica | DELETE | Patrón INV: `es_activo = 0` + permiso `eliminar` o `actualizar` según estándar del proyecto |
| `/fin/plan-cuentas/{cuenta_id}/reactivar` | POST | Opcional si se separa de PUT |
| `/fin/periodos/{periodo_id}/cerrar` (o similar) | POST | Semántica de negocio para cierre controlado |
| `/fin/asientos/{asiento_id}/aprobar` | POST | RBAC `fin.asiento.aprobar` (seed) |
| `/fin/asientos/{asiento_id}/registrar` o `/procesar` | POST | Transición de estado |
| `/fin/asientos/{asiento_id}/anular` | POST | Body con `motivo_anulacion`; validar periodo no cerrado, etc. |
| Inclusión de detalles en POST/PUT cabecera | POST/PUT | Alternativa a POST/PUT separados en `/detalles` si se adopta modelo embebido |

---

## 8. Checklist Fase 3 (referencia)

Implementar solo lo acordado tras confirmación: priorizar RBAC en list/create asientos, seeds RBAC completos para recursos `plan_cuenta`, `periodo`, `asiento`, alinear schemas con BD de referencia (o documentar decisión `moneda` vs `moneda_id`), campos Read faltantes, rutas maestro/transaccional según auditoría, y transacciones SQL en cabecera+detalle si se unifica el flujo.

---

**Fin Fase 2.** Esperar confirmación antes de Fase 3 (implementación).
