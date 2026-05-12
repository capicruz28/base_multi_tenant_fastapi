# AUDITORÍA — Módulo HCM (Human Capital Management)

Documento generado en **Fase 2** del prompt maestro (solo lectura de código y BD de referencia).  
**Base de datos de referencia para campos:** `docs/bd/HCM_TABLAS.sql`.  
**Modelo SQLAlchemy en código:** `app/infrastructure/database/tables_erp/tables_hcm.py` (puede diferir del SQL de documentación; ver sección de discrepancias).

---

## 1. Tablas detectadas y tipo

| Tabla | Tipo | Notas |
|-------|------|--------|
| `hcm_empleado` | Maestro | `cliente_id`, `empresa_id`, `es_activo` |
| `hcm_contrato` | Transaccional | Histórico / estados (`estado_contrato`) |
| `hcm_concepto_planilla` | Maestro | Catálogo; `es_activo`, `es_concepto_sistema` |
| `hcm_planilla` | Transaccional (cabecera) | `estado` (borrador → cerrada); totales |
| `hcm_planilla_empleado` | Transaccional | Resumen por empleado en planilla |
| `hcm_planilla_detalle` | Transaccional | Líneas por concepto |
| `hcm_asistencia` | Transaccional | Registro diario |
| `hcm_vacaciones` | Transaccional | Periodos y estados |
| `hcm_prestamo` | Transaccional | Cuotas y saldo |

No hay tablas HCM puramente **derivadas/analíticas** como entidad separada (solo columnas calculadas dentro de tablas anteriores).

---

## 2. Archivos del módulo en el proyecto

| Capa | Ubicación |
|------|-----------|
| Routers | `app/modules/hcm/presentation/endpoints*.py`, agregador `endpoints.py` |
| Servicios | `app/modules/hcm/application/services/*.py` |
| **Repositorios** | No hay carpeta `repositories`; persistencia vía **`app/infrastructure/database/queries/hcm/*.py`** (patrón queries Core) |
| Schemas | `app/modules/hcm/presentation/schemas.py` |
| Tablas ORM/Core | `app/infrastructure/database/tables_erp/tables_hcm.py` |

**Prefijo API global:** `{API_V1_STR}/hcm` (p. ej. `/api/v1/hcm`). Los routers hijos añaden `/empleados`, `/contratos`, etc.

---

## 3. Endpoints existentes

Todos los endpoints listados aplican **`require_permission("hcm.{recurso}.{accion}")`** con `accion` ∈ `leer`, `crear`, `actualizar`.  
**Tenant:** se pasa `current_user.cliente_id` a los servicios como `client_id` en todas las operaciones.

| Ruta | Método | Entidad | Tenant (`cliente_id`) | RBAC |
|------|--------|---------|------------------------|------|
| `/hcm/empleados` | GET | empleado | Sí (lista filtra opc. `empresa_id`) | `hcm.empleado.leer` |
| `/hcm/empleados/{empleado_id}` | GET | empleado | Sí | `hcm.empleado.leer` |
| `/hcm/empleados` | POST | empleado | Sí | `hcm.empleado.crear` |
| `/hcm/empleados/{empleado_id}` | PUT | empleado | Sí | `hcm.empleado.actualizar` |
| `/hcm/contratos` | GET | contrato | Sí (lista opc. `empresa_id`) | `hcm.contrato.leer` |
| `/hcm/contratos/{contrato_id}` | GET | contrato | Sí | `hcm.contrato.leer` |
| `/hcm/contratos` | POST | contrato | Sí | `hcm.contrato.crear` |
| `/hcm/contratos/{contrato_id}` | PUT | contrato | Sí | `hcm.contrato.actualizar` |
| `/hcm/conceptos-planilla` | GET | concepto_planilla | Sí | `hcm.concepto_planilla.leer` |
| `/hcm/conceptos-planilla/{concepto_id}` | GET | concepto_planilla | Sí | `hcm.concepto_planilla.leer` |
| `/hcm/conceptos-planilla` | POST | concepto_planilla | Sí | `hcm.concepto_planilla.crear` |
| `/hcm/conceptos-planilla/{concepto_id}` | PUT | concepto_planilla | Sí | `hcm.concepto_planilla.actualizar` |
| `/hcm/planillas` | GET | planilla | Sí | `hcm.planilla.leer` |
| `/hcm/planillas/{planilla_id}` | GET | planilla | Sí | `hcm.planilla.leer` |
| `/hcm/planillas` | POST | planilla | Sí | `hcm.planilla.crear` |
| `/hcm/planillas/{planilla_id}` | PUT | planilla | Sí | `hcm.planilla.actualizar` |
| `/hcm/planilla-empleados` | GET | planilla_empleado | Sí | `hcm.planilla_empleado.leer` |
| `/hcm/planilla-empleados/{planilla_empleado_id}` | GET | planilla_empleado | Sí | `hcm.planilla_empleado.leer` |
| `/hcm/planilla-empleados` | POST | planilla_empleado | Sí | `hcm.planilla_empleado.crear` |
| `/hcm/planilla-empleados/{planilla_empleado_id}` | PUT | planilla_empleado | Sí | `hcm.planilla_empleado.actualizar` |
| `/hcm/planilla-detalle` | GET | planilla_detalle | Sí | `hcm.planilla_detalle.leer` |
| `/hcm/planilla-detalle/{planilla_detalle_id}` | GET | planilla_detalle | Sí | `hcm.planilla_detalle.leer` |
| `/hcm/planilla-detalle` | POST | planilla_detalle | Sí | `hcm.planilla_detalle.crear` |
| `/hcm/planilla-detalle/{planilla_detalle_id}` | PUT | planilla_detalle | Sí | `hcm.planilla_detalle.actualizar` |
| `/hcm/asistencia` | GET | asistencia | Sí | `hcm.asistencia.leer` |
| `/hcm/asistencia/{asistencia_id}` | GET | asistencia | Sí | `hcm.asistencia.leer` |
| `/hcm/asistencia` | POST | asistencia | Sí | `hcm.asistencia.crear` |
| `/hcm/asistencia/{asistencia_id}` | PUT | asistencia | Sí | `hcm.asistencia.actualizar` |
| `/hcm/vacaciones` | GET | vacaciones | Sí | `hcm.vacaciones.leer` |
| `/hcm/vacaciones/{vacaciones_id}` | GET | vacaciones | Sí | `hcm.vacaciones.leer` |
| `/hcm/vacaciones` | POST | vacaciones | Sí | `hcm.vacaciones.crear` |
| `/hcm/vacaciones/{vacaciones_id}` | PUT | vacaciones | Sí | `hcm.vacaciones.actualizar` |
| `/hcm/prestamos` | GET | prestamo | Sí | `hcm.prestamo.leer` |
| `/hcm/prestamos/{prestamo_id}` | GET | prestamo | Sí | `hcm.prestamo.leer` |
| `/hcm/prestamos` | POST | prestamo | Sí | `hcm.prestamo.crear` |
| `/hcm/prestamos/{prestamo_id}` | PUT | prestamo | Sí | `hcm.prestamo.actualizar` |

---

## 4. Brechas funcionales (vs patrón maestro / transaccional del prompt maestro)

### 4.1 Maestros

| Tabla | crear | listar | detalle | actualizar | activar/desactivar |
|-------|-------|--------|---------|------------|---------------------|
| `hcm_empleado` | OK | OK | OK | OK | Parcial: no hay ruta dedicada; `es_activo` puede ir en **PUT** si el cliente envía el campo |
| `hcm_concepto_planilla` | OK | OK | OK | OK | Parcial: mismo criterio con `es_activo`; **`es_concepto_sistema` no está en `ConceptoPlanillaUpdate`** |

### 4.2 Transaccionales (patrón orientativo: borrador, aprobar, procesar, anular…)

Ningún recurso HCM expone hoy un flujo explícito tipo **aprobar / procesar / anular** como endpoints separados. Predomina **CRUD genérico** con actualización de campos de estado vía **PUT** donde el schema lo permite.

| Área | Observación |
|------|-------------|
| **Planilla** (`hcm_planilla`) | Estados en BD: borrador, calculada, aprobada, pagada, cerrada. Solo CRUD; **faltan** acciones de negocio (calcular, aprobar, registrar pago, cerrar, etc.) si se desea alinear al patrón transaccional estricto. |
| **Planilla empleado / detalle** | Escritura **sin comprobación visible** de que la planilla padre esté en `borrador` (riesgo de inconsistencia si el prompt maestro exige editar solo en borrador). |
| **Contrato** | Estados borrador/vigente/vencido/rescindido; **no hay** endpoints específicos de rescisión o renovación (solo campos en PUT). |
| **Vacaciones / préstamo / asistencia** | CRUD; aprobaciones parciales vía campos en update donde aplica. |

### 4.3 Derivadas / solo lectura

No aplica tabla derivada sin CRUD. La escritura en planilla detalle es **correcta** para modelo transaccional (no marcar como incorrecto por tener escritura).

---

## 5. Campos en BD (`docs/bd/HCM_TABLAS.sql`) no cubiertos o divergentes en schemas

Referencias cruzadas con **`tables_hcm.py`**: donde el modelo en código **no** tiene la columna del SQL de documentación, se indica.

### 5.1 `hcm_empleado`

- **`nombre_completo`**: columna calculada PERSISTED en SQL doc — **no** está en `EmpleadoRead` (opcional exponer como solo lectura).

### 5.2 `hcm_contrato`

- **`moneda_id`** (FK `cat_moneda`) en **HCM_TABLAS.sql**. En **`tables_hcm.py`** y schemas aparece **`moneda`** como código (`String(3)` / campo `moneda` en API). **Discrepancia documentación BD vs código:** alinear con la BD real desplegada antes de cambiar contratos de API.

### 5.3 `hcm_planilla`

- **`moneda_id`**, **`tipo_cambio`**: en HCM_TABLAS.sql — **no** en `PlanillaCreate` / `PlanillaRead` ni en `tables_hcm.py` actual.
- **`total_planilla`**: calculada en SQL doc — **no** en `PlanillaRead`.

### 5.4 `hcm_planilla_empleado`

- **`empresa_id`**: en BD y `tables_hcm.py` — **no** en `PlanillaEmpleadoRead` (las queries lo rellenan al crear).
- **`neto_pagar`**: calculada en SQL doc — **no** en `PlanillaEmpleadoRead`.

### 5.5 `hcm_planilla_detalle`

- **`empresa_id`**: en BD y `tables_hcm.py` — **no** en `PlanillaDetalleRead`.
- **`tipo_concepto` / `concepto_id`**: no están en `PlanillaDetalleUpdate` (solo lectura implícita tras crear); coherente con líneas fijas, pero es una limitación si la BD permite cambiar concepto.

### 5.6 `hcm_asistencia`

- **`dia_semana`**: calculada en SQL doc — **no** en `AsistenciaRead`.

### 5.7 `hcm_vacaciones`

- **`dias_pendientes`**: calculada — **no** en `VacacionesRead`.

### 5.8 `hcm_prestamo`

- **`cuotas_pendientes`**: calculada — **no** en `PrestamoRead`.
- **`moneda_id`** en HCM_TABLAS.sql vs **`moneda`** string en código — misma observación que contratos.

### 5.9 `hcm_concepto_planilla`

- **`es_concepto_sistema`**: presente en BD y `ConceptoPlanillaCreate` / `Read` — **ausente en `ConceptoPlanillaUpdate`**.

### 5.10 `PlanillaUpdate` / periodo

- **`año`**, **`mes`**: existen en BD; **no** están en `PlanillaUpdate` (puede ser decisión de negocio para no romper unicidad de periodo).

---

## 6. Tenant y RBAC — problemas o comprobaciones

| Tema | Estado |
|------|--------|
| Filtro **`cliente_id`** en queries | Correcto en `queries/hcm/*` para list/get/update/insert. |
| **`empresa_id` en listados** | Muchos listados aceptan `empresa_id` opcional en query; los detalles por ID filtran solo `cliente_id` + PK (no exigen `empresa_id` en query). Coherente con aislamiento por tenant; para multi-empresa estricta valorar filtro opcional en GET por id. |
| **RBAC** | Todos los endpoints HCM revisados usan `require_permission`. |
| **Seeds / catálogo de permisos `hcm.*`** | No se localizó archivo tipo `SEED_PERMISOS_RBAC_HCM.sql` en el repositorio; **conviene verificar** que los permisos existan en BD / seeds globales para evitar fallos en runtime. |
| **Registro en código de permisos** | No hay `RegisterPermission` dedicado en el módulo HCM; depender del mecanismo global (BD / sync). |

---

## 7. Endpoints sugeridos (solo si Fase 3 lo aprueba; no romper contratos existentes)

Rutas ilustrativas bajo el mismo prefijo `/hcm`:

| Recurso | Método | Ruta sugerida | Propósito |
|---------|--------|---------------|-----------|
| Empleado | PATCH | `/empleados/{id}/desactivar` | Alinear con patrón ORG (reactivar/desactivar explícito), sin sustituir PUT |
| Concepto planilla | — | Incluir `es_concepto_sistema` en update o documentar solo lectura | Coherencia con BD |
| Planilla | POST | `/planillas/{id}/calcular` | Pasar a calculada |
| Planilla | POST | `/planillas/{id}/aprobar` | Aprobación |
| Planilla | POST | `/planillas/{id}/marcar-pagada` o `/cerrar` | Estados finales |
| Planilla | POST | `/planillas/{id}/generar-plame` | Integración PLAME |
| Contrato | POST | `/contratos/{id}/rescindir` | Cierre formal |

*(Las rutas exactas deben acordarse con OpenAPI y reglas de no cambiar contratos ya publicados.)*

---

## 8. Código obsoleto o incorrecto

- **No se marca código para eliminación** (según reglas del proyecto).
- **Inconsistencias modelo/doc:** priorizar la **BD real** del cliente antes de modificar APIs; el SQL en `docs/bd` y `tables_hcm.py` ya difieren en moneda planilla/contrato/prestamo.

---

## 9. Resumen ejecutivo

- El módulo HCM está **implementado** con servicios + **queries** Core (no repositories), **RBAC** en todos los endpoints auditados y **tenant por `cliente_id`**.
- Entidades principales tienen **CRUD básico**; faltan **flujos transaccionales** típicos de planilla y rutas dedicadas de activación tipo ORG en maestros.
- **Schemas** omiten varias columnas de BD (calculadas, `empresa_id` en líneas de planilla, campos de moneda según versión de BD) y hay **diferencias doc vs código** en moneda (`moneda_id` vs código).
- **Permisos seed** específicos HCM: **verificar** en despliegue.

---

*Fin del informe Fase 2. Continuar solo tras confirmación explícita para Fase 3.*
