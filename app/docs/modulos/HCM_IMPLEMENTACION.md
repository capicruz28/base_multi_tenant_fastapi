# IMPLEMENTACIÓN — HCM (Human Capital Management / Planillas y RRHH)

**Fecha:** 2026-05-07  
**Módulo:** **HCM** (`E1000010-0000-4000-8000-000000000010`)

Este documento cierra la implementación del módulo **HCM** según el prompt maestro y la auditoría (`app/docs/modulos/AUDITORIA_HCM.md`). **No se modificó la estructura física de la base de datos.** Los endpoints existentes conservan **ruta, método y forma de response**; solo se **añadieron** rutas y campos en schemas donde se indicó.

---

## 1) Alcance — tablas `hcm_*`

Referencia de campos clave: `docs/bd/HCM_TABLAS.sql`.

| Tabla | Tipo | `cliente_id` | `empresa_id` | `es_activo` |
|-------|------|--------------|--------------|-------------|
| `hcm_empleado` | Maestro | Sí | Sí | Sí |
| `hcm_contrato` | Transaccional | Sí | Sí | — (`estado_contrato`) |
| `hcm_concepto_planilla` | Maestro / catálogo | Sí | Sí | Sí |
| `hcm_planilla` | Transaccional (cabecera) | Sí | Sí | — (`estado`) |
| `hcm_planilla_empleado` | Transaccional | Sí | Sí | — |
| `hcm_planilla_detalle` | Transaccional | Sí | Sí | — |
| `hcm_asistencia` | Transaccional | Sí | Sí | — |
| `hcm_vacaciones` | Transaccional | Sí | Sí | — |
| `hcm_prestamo` | Transaccional | Sí | Sí | — |

---

## 2) Arquitectura aplicada

| Capa | Ubicación |
|------|-----------|
| Routers | `app/modules/hcm/presentation/endpoints*.py`, agregador `endpoints.py` |
| Servicios | `app/modules/hcm/application/services/*_service.py` |
| Queries SQLAlchemy Core | `app/infrastructure/database/queries/hcm/*_queries.py` |
| Tablas Core | `app/infrastructure/database/tables_erp/tables_hcm.py` |
| Schemas Pydantic | `app/modules/hcm/presentation/schemas.py` |

- **Tenant:** `cliente_id` en todas las queries vía `current_user.cliente_id` → `client_id` en servicios.
- **Empresa:** `empresa_id` en body (create) o query opcional en listados donde el router ya lo exponía; en líneas de planilla se **deriva** en queries desde cabecera cuando aplica.
- **RBAC:** `require_permission("hcm.<recurso>.<accion>")`.
- **Maestros:** baja lógica con `es_activo` (empleado, concepto); activación explícita vía PATCH dedicados en empleados.
- **Planilla:** edición de cabecera y de líneas/detalle **solo con planilla en estado `borrador`** (`ConflictError` 409 si no).
- **Workflow planilla:** transiciones validadas en servicio (ver §4).
- **Contrato:** rescisión vía servicio dedicado (`fecha_rescision`, `fecha_fin`, `estado_contrato`, `es_contrato_vigente`).

---

## 3) Archivos tocados en esta implementación

### Modificados

| Archivo |
|---------|
| `app/modules/hcm/presentation/schemas.py` |
| `app/modules/hcm/application/services/planilla_service.py` |
| `app/modules/hcm/application/services/planilla_empleado_service.py` |
| `app/modules/hcm/application/services/planilla_detalle_service.py` |
| `app/modules/hcm/application/services/contrato_service.py` |
| `app/modules/hcm/application/services/empleado_service.py` |
| `app/modules/hcm/application/services/__init__.py` |
| `app/modules/hcm/presentation/endpoints_empleados.py` |
| `app/modules/hcm/presentation/endpoints_planillas.py` |
| `app/modules/hcm/presentation/endpoints_contratos.py` |

### Creados

| Archivo |
|---------|
| `app/docs/database/SEED_PERMISOS_RBAC_HCM.sql` |

---

## 4) Resumen funcional por bloque

### Bloque 1 — Schemas

- **Read:** campos calculados / enriquecidos expuestos: `nombre_completo` (empleado), `total_planilla` (planilla), `empresa_id` + `neto_pagar` (planilla empleado), `empresa_id` (planilla detalle), `dia_semana` (asistencia), `dias_pendientes` (vacaciones), `cuotas_pendientes` (préstamo).
- **`ConceptoPlanillaUpdate`:** `es_concepto_sistema` opcional.
- **Contrato / préstamo:** `moneda_id` opcional **además** del campo `moneda` legacy.
- **Planilla Create/Update/Read:** `moneda_id`, `tipo_cambio` donde correspondía.

### Bloque 2 — Servicios

- **PUT planilla:** solo si estado actual es **borrador**.
- **PUT/Crear planilla_empleado y planilla_detalle:** exigen planilla padre en **borrador**.
- **Workflow planilla:**

  | Función | Estado origen | Estado destino |
  |---------|---------------|----------------|
  | `calcular_planilla` | borrador | calculada |
  | `aprobar_planilla` | calculada | aprobada (+ `fecha_aprobacion`, opcional `aprobado_por_usuario_id`) |
  | `marcar_pagada_planilla` | aprobada | pagada (+ `fecha_pago` si estaba vacía) |
  | `cerrar_planilla` | pagada | cerrada |

- **`rescindir_contrato`:** si ya está rescindido → `ConflictError`. Si no: `rescindido`, `fecha_rescision`, `fecha_fin`, `es_contrato_vigente = false`, `motivo_rescision` opcional.

### Bloque 3 — Routers (solo rutas nuevas)

| Ruta (prefijo API: `{API_V1_STR}/hcm`) | Método | RBAC |
|----------------------------------------|--------|------|
| `/empleados/{id}/desactivar` | PATCH | `hcm.empleado.desactivar` |
| `/empleados/{id}/activar` | PATCH | `hcm.empleado.activar` |
| `/planillas/{id}/calcular` | POST | `hcm.planilla.calcular` |
| `/planillas/{id}/aprobar` | POST | `hcm.planilla.aprobar` |
| `/planillas/{id}/marcar-pagada` | POST | `hcm.planilla.marcar-pagada` |
| `/planillas/{id}/cerrar` | POST | `hcm.planilla.cerrar` |
| `/contratos/{id}/rescindir` | POST | `hcm.contrato.rescindir` |

Body opcional en rescindir: `ContratoRescindirRequest` (`fecha_rescision`, `motivo_rescision`).

### Bloque 4 — RBAC

Script idempotente: **`app/docs/database/SEED_PERMISOS_RBAC_HCM.sql`** — **MERGE** por `codigo` sobre tabla `permiso`, `modulo_id` HCM.

Incluye todos los permisos usados por los routers actuales (CRUD por recurso + workflow planilla + activar/desactivar empleado + rescindir contrato).

---

## 5) Verificación — endpoints nuevos

Para cada endpoint **nuevo**, se cumple:

| Endpoint | `cliente_id` | `empresa_id` | RBAC |
|----------|--------------|--------------|------|
| `PATCH .../empleados/{id}/desactivar` | Sí (`current_user.cliente_id` → servicio → queries) | En lectura/respuesta según fila; create/update empleado ya llevaba `empresa_id` en body donde aplica | `hcm.empleado.desactivar` |
| `PATCH .../empleados/{id}/activar` | Sí | Igual | `hcm.empleado.activar` |
| `POST .../planillas/{id}/calcular` | Sí | Cabecera filtrada por tenant; `empresa_id` en fila | `hcm.planilla.calcular` |
| `POST .../planillas/{id}/aprobar` | Sí | Igual | `hcm.planilla.aprobar` |
| `POST .../planillas/{id}/marcar-pagada` | Sí | Igual | `hcm.planilla.marcar-pagada` |
| `POST .../planillas/{id}/cerrar` | Sí | Igual | `hcm.planilla.cerrar` |
| `POST .../contratos/{id}/rescindir` | Sí | Contrato con `empresa_id` en fila | `hcm.contrato.rescindir` |

- **`ConflictError`** (estado inválido, planilla no borrador, contrato ya rescindido): respuesta **409** vía manejador global de `CustomException`.
- **`NotFoundError`** en rutas nuevas: donde el endpoint envuelve explícitamente, **404**; el resto delega en el mismo patrón que los endpoints legacy del módulo.

---

## 6) Verificación — endpoints legacy

Los endpoints existentes **antes de esta entrega** mantienen:

- Misma **ruta** y **método** (GET/POST/PUT por recurso).
- Mismo **tipo de response** (`*_Read`); los schemas Read **añaden** campos opcionales sin romper clientes que ignoren campos extra en JSON.

No se eliminó ningún endpoint ni se cambió el contrato de los bodies existentes de forma incompatible (solo extensiones opcionales).

---

## 7) Pendientes operativos (fuera de código)

1. Ejecutar **`SEED_PERMISOS_RBAC_HCM.sql`** en el entorno correspondiente y asignar permisos a roles según política del tenant.
2. Si la BD física aún no tiene columnas documentadas en `HCM_TABLAS.sql` (p. ej. `moneda_id` / `tipo_cambio` en planilla), alinear modelo SQLAlchemy y despliegue **solo cuando** la migración/DDL oficial exista (regla de proyecto: no alterar BD desde esta base de código sin proceso acordado).

---

## 8) Cierre del módulo

El módulo **HCM** queda **cerrado** respecto al alcance acordado: schemas extendidos, validaciones de estado y workflow en servicios, rutas nuevas sin romper las anteriores, y seed RBAC idempotente documentado.

**Referencias:** `AUDITORIA_HCM.md`, `docs/bd/HCM_TABLAS.sql`, `docs/prompts/PROMPT_MODULO_MAESTRO.md`.
