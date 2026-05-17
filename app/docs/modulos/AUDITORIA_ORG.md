# AUDITORÍA MÓDULO ORG — Organización (CORE - Obligatorio)

**Fecha:** 2026-05-12  
**Módulo:** ORG — Organización  
**Tipo:** CORE — Prerequisito para todos los módulos  
**Stack:** FastAPI + SQL Server + SQLAlchemy Core  

---

## DIAGNÓSTICO GENERAL

🟢 **SALUDABLE**

El módulo ORG cubre sus 6 flujos principales de organización empresarial con CRUD completo
(listar, detalle, crear, actualizar, desactivar, reactivar) para cada una de las 6 entidades
confirmadas en BD. Tenant validado en todos los endpoints mediante `client_id = current_user.cliente_id`.
RBAC aplicado consistentemente con el patrón `org.recurso.accion`. Los schemas están exactamente
alineados con la BD — todos los campos NOT NULL sin default están presentes en los schemas de creación.
Los catálogos globales (`cat_*`) están correctamente segregados en módulos separados.

**El módulo cubre 6 de 6 flujos principales de organización SaaS.**

Ajuste menor detectado: `empresa_id` se declara como `Optional` en los Query params de las
operaciones by-ID (detalle, actualizar, eliminar, reactivar) para sucursal, centro_costo, departamento
y cargo, pero el servicio de `org_cargo` lo exige obligatoriamente mediante `_require_empresa_id()`.
Inconsistencia de contrato que puede causar `ValidationError` inesperado si el frontend no provee
el parámetro. No impide el funcionamiento del módulo, pero debe corregirse.

---

## TABLAS CRÍTICAS FALTANTES

Ninguna. La BD cubre todos los flujos principales.

---

## ENTIDADES Y CLASIFICACIÓN

| Entidad | Tipo | Tabla BD | Endpoints propios |
|---|---|---|---|
| Empresa | maestro | `org_empresa` | Sí — `/org/empresa` |
| Sucursal | maestro | `org_sucursal` | Sí — `/org/sucursales` |
| Centro de Costo | maestro | `org_centro_costo` | Sí — `/org/centros-costo` |
| Departamento Org. | maestro | `org_departamento` | Sí — `/org/departamentos` |
| Cargo / Puesto | maestro | `org_cargo` | Sí — `/org/cargos` |
| Parámetro Sistema | maestro-config | `org_parametro_sistema` | Sí — `/org/parametros` |
| Moneda | maestro global | `cat_moneda` | Sí — `/catalogos/monedas` (tenant read) + `/catalogos-globales/monedas` (superadmin write) |
| País | maestro global | `cat_pais` | Sí — `/catalogos/paises` (tenant read) + `/catalogos-globales/paises` (superadmin write) |
| Dpto. Geográfico | maestro global | `cat_departamento` | Sí — `/catalogos/departamentos` (tenant read) + `/catalogos-globales/departamentos` (superadmin write) |
| Provincia | maestro global | `cat_provincia` | Sí — `/catalogos/provincias` (tenant read) + `/catalogos-globales/provincias` (superadmin write) |
| Distrito | maestro global | `cat_distrito` | Sí — `/catalogos/distritos` (tenant read) + `/catalogos-globales/distritos` (superadmin write) |

---

## ENDPOINTS EXISTENTES

### org_empresa — `/org/empresa`

| Ruta | Método | Tenant | RBAC | Clasificación |
|---|---|---|---|---|
| `/org/empresa` | GET | ✅ | ✅ org.empresa.leer | ✅ CORRECTO |
| `/org/empresa/{empresa_id}` | GET | ✅ | ✅ org.empresa.leer | ✅ CORRECTO |
| `/org/empresa` | POST | ✅ | ✅ org.empresa.crear | ✅ CORRECTO |
| `/org/empresa/{empresa_id}` | PUT | ✅ | ✅ org.empresa.actualizar | ✅ CORRECTO |
| `/org/empresa/{empresa_id}` | DELETE | ✅ | ✅ org.empresa.eliminar | ✅ CORRECTO |
| `/org/empresa/{empresa_id}/reactivar` | POST | ✅ | ✅ org.empresa.actualizar | ✅ CORRECTO |

### org_sucursal — `/org/sucursales`

| Ruta | Método | Tenant | RBAC | Clasificación | Motivo |
|---|---|---|---|---|---|
| `/org/sucursales` | GET | ✅ | ✅ org.sucursal.leer | ✅ CORRECTO | |
| `/org/sucursales/{sucursal_id}` | GET | ✅ | ✅ org.sucursal.leer | ⚠ INCOMPLETO | empresa_id declarado Optional; comportamiento del servicio no confirmado |
| `/org/sucursales` | POST | ✅ | ✅ org.sucursal.crear | ✅ CORRECTO | |
| `/org/sucursales/{sucursal_id}` | PUT | ✅ | ✅ org.sucursal.actualizar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/sucursales/{sucursal_id}` | DELETE | ✅ | ✅ org.sucursal.eliminar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/sucursales/{sucursal_id}/reactivar` | POST | ✅ | ✅ org.sucursal.actualizar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |

### org_centro_costo — `/org/centros-costo`

| Ruta | Método | Tenant | RBAC | Clasificación | Motivo |
|---|---|---|---|---|---|
| `/org/centros-costo` | GET | ✅ | ✅ org.centro_costo.leer | ✅ CORRECTO | |
| `/org/centros-costo/{centro_costo_id}` | GET | ✅ | ✅ org.centro_costo.leer | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/centros-costo` | POST | ✅ | ✅ org.centro_costo.crear | ✅ CORRECTO | |
| `/org/centros-costo/{centro_costo_id}` | PUT | ✅ | ✅ org.centro_costo.actualizar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/centros-costo/{centro_costo_id}` | DELETE | ✅ | ✅ org.centro_costo.eliminar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/centros-costo/{centro_costo_id}/reactivar` | POST | ✅ | ✅ org.centro_costo.actualizar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |

### org_departamento — `/org/departamentos`

| Ruta | Método | Tenant | RBAC | Clasificación | Motivo |
|---|---|---|---|---|---|
| `/org/departamentos` | GET | ✅ | ✅ org.departamento.leer | ✅ CORRECTO | |
| `/org/departamentos/{departamento_id}` | GET | ✅ | ✅ org.departamento.leer | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/departamentos` | POST | ✅ | ✅ org.departamento.crear | ✅ CORRECTO | |
| `/org/departamentos/{departamento_id}` | PUT | ✅ | ✅ org.departamento.actualizar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/departamentos/{departamento_id}` | DELETE | ✅ | ✅ org.departamento.eliminar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |
| `/org/departamentos/{departamento_id}/reactivar` | POST | ✅ | ✅ org.departamento.actualizar | ⚠ INCOMPLETO | empresa_id contrato ambiguo |

### org_cargo — `/org/cargos`

| Ruta | Método | Tenant | RBAC | Clasificación | Motivo |
|---|---|---|---|---|---|
| `/org/cargos` | GET | ✅ | ✅ org.cargo.leer | ✅ CORRECTO | |
| `/org/cargos/{cargo_id}` | GET | ✅ | ✅ org.cargo.leer | ⚠ INCOMPLETO | empresa_id Optional en endpoint pero `_require_empresa_id()` lo fuerza en servicio → ValidationError si no se provee (CONFIRMADO) |
| `/org/cargos` | POST | ✅ | ✅ org.cargo.crear | ✅ CORRECTO | |
| `/org/cargos/{cargo_id}` | PUT | ✅ | ✅ org.cargo.actualizar | ⚠ INCOMPLETO | mismo problema empresa_id (CONFIRMADO en cargo_service) |
| `/org/cargos/{cargo_id}` | DELETE | ✅ | ✅ org.cargo.eliminar | ⚠ INCOMPLETO | mismo problema empresa_id (CONFIRMADO) |
| `/org/cargos/{cargo_id}/reactivar` | POST | ✅ | ✅ org.cargo.actualizar | ⚠ INCOMPLETO | mismo problema empresa_id (CONFIRMADO) |

### org_parametro_sistema — `/org/parametros`

| Ruta | Método | Tenant | RBAC | Clasificación |
|---|---|---|---|---|
| `/org/parametros` | GET | ✅ | ✅ org.parametro.leer | ✅ CORRECTO |
| `/org/parametros/{parametro_id}` | GET | ✅ | ✅ org.parametro.leer | ✅ CORRECTO |
| `/org/parametros` | POST | ✅ | ✅ org.parametro.crear | ✅ CORRECTO |
| `/org/parametros/{parametro_id}` | PUT | ✅ | ✅ org.parametro.actualizar | ✅ CORRECTO |
| `/org/parametros/{parametro_id}` | DELETE | ✅ | ✅ org.parametro.eliminar | ✅ CORRECTO |
| `/org/parametros/{parametro_id}/reactivar` | POST | ✅ | ✅ org.parametro.actualizar | ✅ CORRECTO |

**Resumen:** 18 ✅ CORRECTO · 16 ⚠ INCOMPLETO · 0 🔴 DEPRECATED · 0 🔁 REEMPLAZAR

---

## ENDPOINTS A DEPRECAR

Ninguno. Todos los endpoints existentes tienen diseño arquitectónicamente válido para un SaaS ERP.

---

## ENDPOINTS FALTANTES A IMPLEMENTAR

Ninguno. Todas las operaciones del tipo maestro están implementadas para las 6 entidades `org_*`.

Los catálogos globales (`cat_*`) ya tienen cobertura completa en módulos separados:
- Lectura tenant: `GET /catalogos/monedas|paises|departamentos|provincias|distritos`
- Escritura superadmin: CRUD completo en `GET|POST|PUT|DELETE /catalogos-globales/monedas|paises|...`

---

## CAMPOS FALTANTES EN SCHEMAS

No hay campos faltantes en ningún schema del módulo ORG. Todos los schemas están completamente
alineados con la BD real:

| Entidad | Schema Create | Schema Read | Estado |
|---|---|---|---|
| org_empresa | EmpresaCreate | EmpresaRead | ✅ Completo |
| org_sucursal | SucursalCreate | SucursalRead | ✅ Completo |
| org_centro_costo | CentroCostoCreate | CentroCostoRead | ✅ Completo |
| org_departamento | DepartamentoCreate | DepartamentoRead | ✅ Completo |
| org_cargo | CargoCreate (moneda_salarial NOT NULL ✅) | CargoRead | ✅ Completo |
| org_parametro_sistema | ParametroCreate | ParametroRead | ✅ Completo |

---

## PROBLEMAS DE TENANT O RBAC

### Problema detectado: empresa_id — inconsistencia de contrato en operaciones by-ID

**Afecta:** `org_cargo` (CONFIRMADO), potencialmente `org_sucursal`, `org_centro_costo`, `org_departamento` (pendiente verificar a nivel de servicio)

**Descripción:**
En las operaciones por ID (detalle, actualizar, eliminar, reactivar), `empresa_id` se declara
como `Optional[UUID] = Query(None)` en el endpoint, pero en `cargo_service.py` se llama a
`_require_empresa_id(empresa_id)` que lanza un `ValidationError` si el valor es `None`.

Esto genera una inconsistencia entre el contrato declarado del endpoint (empresa_id es opcional)
y el comportamiento real del servicio (empresa_id es obligatorio para operaciones by-ID).

**Corrección en Fase 3:**
Estandarizar el comportamiento. Opciones:
1. Hacer `empresa_id` explícitamente requerido en los Query params de operaciones by-ID
   (más honesto con el cliente)
2. Eliminar `_require_empresa_id` y permitir que las queries funcionen solo con `cliente_id`
   (empresa_id como scope restrictor opcional real)

> Opción recomendada: **1** — ya que las entidades `org_sucursal`, `org_cargo`, `org_departamento`,
> `org_centro_costo` pertenecen a una empresa específica y el frontend siempre debería conocer
> el `empresa_id` en contexto.

**Archivos afectados:**
- `app/modules/org/presentation/endpoints_cargos.py` — GET/{id}, PUT/{id}, DELETE/{id}, POST/{id}/reactivar
- `app/modules/org/application/services/cargo_service.py` — `_require_empresa_id`
- Verificar también: `endpoints_sucursales.py`, `endpoints_centros_costo.py`, `endpoints_departamentos.py`
  y sus respectivos servicios

---

## SEEDS RBAC FALTANTES

No se encontró un archivo de seeds específico para el módulo ORG. Los siguientes 24 permisos
deben existir en la tabla `permiso` (catálogo RBAC) para que los endpoints funcionen correctamente:

| Código permiso | Recurso | Acción | Endpoint que lo requiere |
|---|---|---|---|
| `org.empresa.leer` | empresa | leer | GET /org/empresa, GET /org/empresa/{id} |
| `org.empresa.crear` | empresa | crear | POST /org/empresa |
| `org.empresa.actualizar` | empresa | actualizar | PUT /org/empresa/{id}, POST /org/empresa/{id}/reactivar |
| `org.empresa.eliminar` | empresa | eliminar | DELETE /org/empresa/{id} |
| `org.sucursal.leer` | sucursal | leer | GET /org/sucursales, GET /org/sucursales/{id} |
| `org.sucursal.crear` | sucursal | crear | POST /org/sucursales |
| `org.sucursal.actualizar` | sucursal | actualizar | PUT /org/sucursales/{id}, POST /org/sucursales/{id}/reactivar |
| `org.sucursal.eliminar` | sucursal | eliminar | DELETE /org/sucursales/{id} |
| `org.centro_costo.leer` | centro_costo | leer | GET /org/centros-costo, GET /org/centros-costo/{id} |
| `org.centro_costo.crear` | centro_costo | crear | POST /org/centros-costo |
| `org.centro_costo.actualizar` | centro_costo | actualizar | PUT /org/centros-costo/{id}, POST /org/centros-costo/{id}/reactivar |
| `org.centro_costo.eliminar` | centro_costo | eliminar | DELETE /org/centros-costo/{id} |
| `org.departamento.leer` | departamento | leer | GET /org/departamentos, GET /org/departamentos/{id} |
| `org.departamento.crear` | departamento | crear | POST /org/departamentos |
| `org.departamento.actualizar` | departamento | actualizar | PUT /org/departamentos/{id}, POST /org/departamentos/{id}/reactivar |
| `org.departamento.eliminar` | departamento | eliminar | DELETE /org/departamentos/{id} |
| `org.cargo.leer` | cargo | leer | GET /org/cargos, GET /org/cargos/{id} |
| `org.cargo.crear` | cargo | crear | POST /org/cargos |
| `org.cargo.actualizar` | cargo | actualizar | PUT /org/cargos/{id}, POST /org/cargos/{id}/reactivar |
| `org.cargo.eliminar` | cargo | eliminar | DELETE /org/cargos/{id} |
| `org.parametro.leer` | parametro | leer | GET /org/parametros, GET /org/parametros/{id} |
| `org.parametro.crear` | parametro | crear | POST /org/parametros |
| `org.parametro.actualizar` | parametro | actualizar | PUT /org/parametros/{id}, POST /org/parametros/{id}/reactivar |
| `org.parametro.eliminar` | parametro | eliminar | DELETE /org/parametros/{id} |

> Si estos permisos no existen en la tabla `permiso`, todos los endpoints del módulo ORG
> devolverán 403 para usuarios normales. Un SuperAdmin o AdministradorTenant puede acceder
> independientemente de la existencia del seed.

---

## RESUMEN EJECUTIVO

| Categoría | Cantidad | Estado |
|---|---|---|
| Entidades `org_*` implementadas | 6/6 | ✅ Completo |
| Endpoints totales | 36 | — |
| Endpoints ✅ CORRECTO | 18 | ✅ |
| Endpoints ⚠ INCOMPLETO | 16 | Corrección requerida |
| Endpoints 🔴 DEPRECATED | 0 | — |
| Endpoints 🔁 REEMPLAZAR | 0 | — |
| Endpoints faltantes | 0 | ✅ Ninguno |
| Campos faltantes en schemas | 0 | ✅ Ninguno |
| Permisos RBAC a verificar en BD | 24 | ⚠ Verificar seeds |

**Acción Fase 3:** Corregir la inconsistencia `empresa_id` en los 16 endpoints ⚠ INCOMPLETO.
La corrección consiste en marcar `empresa_id` como parámetro requerido (no Optional) en las
operaciones by-ID de `org_cargo`, `org_sucursal`, `org_centro_costo` y `org_departamento`,
alineando el contrato del endpoint con el comportamiento real del servicio.
