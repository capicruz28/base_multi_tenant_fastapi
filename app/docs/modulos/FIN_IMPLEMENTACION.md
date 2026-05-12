# FIN — Finanzas y Contabilidad — Implementación cerrada

Documento de cierre **Fase 4** del ciclo prompt maestro (lectura → auditoría → implementación → verificación).  
Código del módulo: **FIN**. Prefijo de API: **`{API_V1_STR}/fin`** (p. ej. `/api/v1/fin`), definido en `app/api/v1/api.py`.

---

## 1. Alcance y tablas

| Tabla | Rol |
|-------|-----|
| `fin_plan_cuentas` | Maestro (plan de cuentas) |
| `fin_periodo_contable` | Maestro / control de periodos |
| `fin_asiento_contable` | Transaccional (cabecera) |
| `fin_asiento_detalle` | Transaccional (líneas; API separada conservada) |

No se modificó la estructura física de la base de datos en este ciclo. El ORM `tables_fin.py` incluye **`moneda_id`** (nullable) además de **`moneda`** para alinear con `docs/bd/FIN_TABLAS.sql` y resolución vía `cat_moneda`.

---

## 2. Archivos creados o modificados

| Archivo | Rol |
|---------|-----|
| `app/modules/fin/presentation/schemas.py` | Read/Create/Update; `nombre_periodo`, `moneda_id`, `diferencia`, `esta_cuadrado`, `empresa_id` en detalle; `AsientoAnularBody` |
| `app/modules/fin/presentation/endpoints_plan_cuentas.py` | `DELETE`, `POST .../reactivar` |
| `app/modules/fin/presentation/endpoints_periodos.py` | `POST .../cerrar` |
| `app/modules/fin/presentation/endpoints_asientos.py` | RBAC en list/create; `POST` aprobar/registrar/anular; `ServiceError` en flujos |
| `app/modules/fin/application/services/plan_cuentas_service.py` | `desactivar_cuenta`, `reactivar_cuenta` |
| `app/modules/fin/application/services/periodo_contable_service.py` | `cerrar_periodo_contable` |
| `app/modules/fin/application/services/asiento_contable_service.py` | Moneda, enriquecimiento totales, estados, validaciones borrador |
| `app/modules/fin/application/services/__init__.py` | Exportes públicos |
| `app/infrastructure/database/tables_erp/tables_fin.py` | Columna `moneda_id` en asiento |
| `app/infrastructure/database/queries/fin/periodo_contable_queries.py` | Conteo borradores, `cerrar_periodo_contable` |
| `app/docs/database/SEED_PERMISOS_RBAC_FIN.sql` | Seeds RBAC FIN (MERGE idempotente) |
| `app/docs/modulos/AUDITORIA_FIN.md` | Auditoría Fase 2 (referencia) |

Routers agregados (`endpoints.py`, `main` / `api_router`): sin cambio de prefijo del módulo.

---

## 3. Endpoints y contratos

### 3.1 Rutas y métodos (sin cambio de método ni path en los ya existentes)

Los endpoints **GET/POST/PUT** previos de plan-cuentas, periodos y asientos conservan la misma **ruta relativa**, **método** y **modelo de respuesta** (`response_model`); solo se añadieron dependencias RBAC donde faltaban y handlers de error donde aplica.

| Ruta relativa (bajo `/fin`) | Método | `response_model` / cuerpo |
|----------------------------|--------|---------------------------|
| `/plan-cuentas` | GET | `list[PlanCuentaRead]` |
| `/plan-cuentas/{cuenta_id}` | GET | `PlanCuentaRead` |
| `/plan-cuentas` | POST | `PlanCuentaRead` |
| `/plan-cuentas/{cuenta_id}` | PUT | `PlanCuentaRead` |
| `/plan-cuentas/{cuenta_id}` | DELETE | `204` sin cuerpo |
| `/plan-cuentas/{cuenta_id}/reactivar` | POST | `PlanCuentaRead` |
| `/periodos` | GET | `list[PeriodoContableRead]` |
| `/periodos/{periodo_id}` | GET | `PeriodoContableRead` |
| `/periodos` | POST | `PeriodoContableRead` |
| `/periodos/{periodo_id}` | PUT | `PeriodoContableRead` |
| `/periodos/{periodo_id}/cerrar` | POST | `PeriodoContableRead` |
| `/asientos` | GET | `list[AsientoContableRead]` |
| `/asientos/{asiento_id}` | GET | `AsientoContableRead` |
| `/asientos` | POST | `AsientoContableRead` |
| `/asientos/{asiento_id}` | PUT | `AsientoContableRead` |
| `/asientos/{asiento_id}/aprobar` | POST | `AsientoContableRead` |
| `/asientos/{asiento_id}/registrar` | POST | `AsientoContableRead` |
| `/asientos/{asiento_id}/anular` | POST | `AsientoContableRead` |
| `/asientos/{asiento_id}/detalles` | GET | `list[AsientoDetalleRead]` |
| `/asientos/{asiento_id}/detalles` | POST | `AsientoDetalleRead` |
| `/asientos/detalles/{asiento_detalle_id}` | GET | `AsientoDetalleRead` |
| `/asientos/detalles/{asiento_detalle_id}` | PUT | `AsientoDetalleRead` |

### 3.2 Endpoints nuevos — tenant, empresa y RBAC

En todos los casos **`cliente_id`** proviene de **`current_user.cliente_id`** (no del body salvo diseño explícito de creación con `empresa_id` en maestros).

| Endpoint nuevo | `cliente_id` | `empresa_id` | RBAC |
|----------------|--------------|--------------|------|
| `DELETE /plan-cuentas/{id}` | Sí (servicio/queries) | En filas vía update `PlanCuentaUpdate` implícito | `fin.plan_cuenta.eliminar` |
| `POST /plan-cuentas/{id}/reactivar` | Sí | Igual que actualizar cuenta | `fin.plan_cuenta.actualizar` |
| `POST /periodos/{id}/cerrar` | Sí | Periodo y asientos filtrados por tenant | `fin.periodo.cerrar` |
| `POST /asientos/{id}/aprobar` | Sí | Cabecera mantiene `empresa_id` en BD | `fin.asiento.aprobar` |
| `POST /asientos/{id}/registrar` | Sí | Igual | `fin.asiento.registrar` |
| `POST /asientos/{id}/anular` | Sí | Valida periodo no cerrado/bloqueado | `fin.asiento.anular` |

**Nota `empresa_id`:** Listados y creaciones siguen el patrón existente: query opcional `empresa_id` en listas; creación con `empresa_id` en body donde el schema lo exige. Los **GET por ID** filtran por `cliente_id` + PK en queries (no se añadió `empresa_id` obligatorio en path).

### 3.3 RBAC reforzado en rutas ya existentes

- **`GET /asientos`**: `fin.asiento.leer` (antes ausente).
- **`POST /asientos`**: `fin.asiento.crear` (antes ausente).

Resto de permisos `fin.plan_cuenta.*`, `fin.periodo.*`, `fin.asiento_detalle.*` sin cambio de código de permiso en rutas ya definidas.

---

## 4. Seeds RBAC

Script: **`app/docs/database/SEED_PERMISOS_RBAC_FIN.sql`**

- `modulo_id` FIN: `E1000011-0000-4000-8000-000000000011`
- MERGE idempotente por `codigo`
- Incluye `fin.asiento_detalle.*` (equivalente a la sección FIN de `SEED_PERMISOS_RBAC_FASE4_CANDIDATOS.sql`; re-ejecutar no duplica)

Ejecutar después del seed base de permisos/módulos y asignar permisos a roles según política del tenant.

---

## 5. Reglas de negocio implementadas (servicios)

- **Asiento PUT:** solo si **`estado == borrador`**; no se actualizan por este canal `estado`, aprobación ni anulación (solo acciones POST dedicadas).
- **Detalle POST/PUT:** asiento padre en **borrador**.
- **Aprobar:** `borrador` → `aprobado` (registra `aprobado_por_usuario_id`, `fecha_aprobacion`).
- **Registrar:** `aprobado` → `registrado`.
- **Anular:** no si **`registrado`** ni si ya **`anulado`**; no si periodo **`cerrado`** o **`bloqueado`**; body **`motivo_anulacion`**.
- **Cerrar periodo:** no si ya cerrado/bloqueado; exige **cero asientos en borrador** en ese periodo.
- **Moneda:** resolución de **`moneda_id`** vía `cat_moneda` (`get_moneda_by_codigo`) si falta en creación/actualización.
- **Lectura asiento:** `diferencia` y `esta_cuadrado` calculados en servicio si la fila no los trae.

---

## 6. Verificación Fase 4 (checklist)

1. **Archivos:** listados en §2.
2. **Endpoints nuevos:** tabla §3.2 (`cliente_id` + RBAC; `empresa_id` según tabla/query).
3. **Endpoints existentes:** mismas rutas relativas, métodos y `response_model` principales; cambios acotados a `Depends` (RBAC) y manejo de `ServiceError` sin alterar tipos de respuesta acordados.
4. **Este documento:** `app/docs/modulos/FIN_IMPLEMENTACION.md`.

---

## 7. Cierre

El módulo **FIN** queda documentado para despliegue: ejecutar **`SEED_PERMISOS_RBAC_FIN.sql`**, asignar permisos a roles, y validar en integración que la BD exponga las columnas esperadas (`moneda_id` en asientos si aplica al entorno).

Para evolución futura: valorar detalle de asiento **embebido** en cabecera (solo API) y alineación total ORM ↔ script oficial de tablas (`FIN_TABLAS.sql` / FASE4) sin migraciones no acordadas.

**Estado:** implementación y documentación de cierre **completadas**.
