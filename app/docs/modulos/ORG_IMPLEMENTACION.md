# ORG — Organización: Reporte de Implementación (Fase 3 + Fase 4)

**Fecha:** 2026-05-12  
**Módulo:** ORG — Organización  
**Tipo:** CORE — Prerequisito para todos los módulos  
**Stack:** FastAPI + SQL Server + SQLAlchemy Core  

---

## 1. ARCHIVOS MODIFICADOS

| Archivo | Operación | Cambio |
|---|---|---|
| `app/modules/org/presentation/endpoints_sucursales.py` | Modificado | `empresa_id` → requerido en 4 endpoints by-ID |
| `app/modules/org/presentation/endpoints_centros_costo.py` | Modificado | `empresa_id` → requerido en 4 endpoints by-ID |
| `app/modules/org/presentation/endpoints_departamentos.py` | Modificado | `empresa_id` → requerido en 4 endpoints by-ID |
| `app/modules/org/presentation/endpoints_cargos.py` | Modificado | `empresa_id` → requerido en 4 endpoints by-ID |

## 2. ARCHIVOS CREADOS

| Archivo | Descripción |
|---|---|
| `app/docs/database/SEED_PERMISOS_RBAC_ORG.sql` | Seeds RBAC — 24 permisos para el módulo ORG |
| `app/docs/modulos/AUDITORIA_ORG.md` | Reporte de auditoría Fase 2 |
| `app/docs/modulos/ORG_IMPLEMENTACION.md` | Este reporte (Fase 4) |

---

## 3. ENDPOINTS MARCADOS COMO DEPRECATED

Ninguno. Todos los endpoints existentes tienen diseño arquitectónicamente válido para un SaaS ERP.

---

## 4. ENDPOINTS NUEVOS

Ninguno. La Fase 3 consistió exclusivamente en correcciones de contrato sobre endpoints existentes
(⚠ INCOMPLETO → ✅ CORRECTO). No se crearon rutas nuevas.

---

## 5. ENDPOINTS CORREGIDOS (⚠ INCOMPLETO → ✅ CORRECTO)

Se aplicó la corrección de `empresa_id` en 16 endpoints by-ID distribuidos en 4 entidades.

### Cambio aplicado (idéntico en los 16 endpoints)

```
# ANTES
empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC)

# DESPUÉS
empresa_id: UUID = Query(..., description="Empresa propietaria del [entidad].")
```

La constante `_EMPRESA_ID_SCOPE_DESC` fue eliminada de los 4 archivos al quedar sin uso.

### org_sucursal — `endpoints_sucursales.py`

| Endpoint | Método | cliente_id | empresa_id | RBAC | Estado |
|---|---|---|---|---|---|
| `/org/sucursales/{id}` | GET | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.sucursal.leer` | ✅ CORRECTO |
| `/org/sucursales/{id}` | PUT | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.sucursal.actualizar` | ✅ CORRECTO |
| `/org/sucursales/{id}` | DELETE | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.sucursal.eliminar` | ✅ CORRECTO |
| `/org/sucursales/{id}/reactivar` | POST | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.sucursal.actualizar` | ✅ CORRECTO |

### org_centro_costo — `endpoints_centros_costo.py`

| Endpoint | Método | cliente_id | empresa_id | RBAC | Estado |
|---|---|---|---|---|---|
| `/org/centros-costo/{id}` | GET | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.centro_costo.leer` | ✅ CORRECTO |
| `/org/centros-costo/{id}` | PUT | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.centro_costo.actualizar` | ✅ CORRECTO |
| `/org/centros-costo/{id}` | DELETE | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.centro_costo.eliminar` | ✅ CORRECTO |
| `/org/centros-costo/{id}/reactivar` | POST | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.centro_costo.actualizar` | ✅ CORRECTO |

### org_departamento — `endpoints_departamentos.py`

| Endpoint | Método | cliente_id | empresa_id | RBAC | Estado |
|---|---|---|---|---|---|
| `/org/departamentos/{id}` | GET | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.departamento.leer` | ✅ CORRECTO |
| `/org/departamentos/{id}` | PUT | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.departamento.actualizar` | ✅ CORRECTO |
| `/org/departamentos/{id}` | DELETE | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.departamento.eliminar` | ✅ CORRECTO |
| `/org/departamentos/{id}/reactivar` | POST | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.departamento.actualizar` | ✅ CORRECTO |

### org_cargo — `endpoints_cargos.py`

| Endpoint | Método | cliente_id | empresa_id | RBAC | Estado |
|---|---|---|---|---|---|
| `/org/cargos/{id}` | GET | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.cargo.leer` | ✅ CORRECTO |
| `/org/cargos/{id}` | PUT | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.cargo.actualizar` | ✅ CORRECTO |
| `/org/cargos/{id}` | DELETE | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.cargo.eliminar` | ✅ CORRECTO |
| `/org/cargos/{id}/reactivar` | POST | ✅ `current_user.cliente_id` | ✅ Requerido | ✅ `org.cargo.actualizar` | ✅ CORRECTO |

---

## 6. ENDPOINTS CORRECTOS NO MODIFICADOS

Todos los endpoints que estaban ✅ CORRECTO en la auditoría permanecen sin cambios:
rutas, métodos, response_model y structure de parámetros son idénticos a la versión auditada.

| Entidad | Endpoints | Estado |
|---|---|---|
| org_empresa | GET / · GET /{id} · POST / · PUT /{id} · DELETE /{id} · POST /{id}/reactivar | ✅ Sin cambios |
| org_sucursal | GET / · POST / | ✅ Sin cambios |
| org_centro_costo | GET / · POST / | ✅ Sin cambios |
| org_departamento | GET / · POST / | ✅ Sin cambios |
| org_cargo | GET / · POST / | ✅ Sin cambios |
| org_parametro_sistema | GET / · GET /{id} · POST / · PUT /{id} · DELETE /{id} · POST /{id}/reactivar | ✅ Sin cambios |

---

## 7. SEEDS RBAC — `SEED_PERMISOS_RBAC_ORG.sql`

Script idempotente (`MERGE ON codigo`). Debe ejecutarse en `bd_hybrid_sistema_central`.

| Código permiso | Recurso | Acción | Endpoints cubiertos |
|---|---|---|---|
| `org.empresa.leer` | empresa | leer | GET /org/empresa · GET /org/empresa/{id} |
| `org.empresa.crear` | empresa | crear | POST /org/empresa |
| `org.empresa.actualizar` | empresa | actualizar | PUT /org/empresa/{id} · POST /org/empresa/{id}/reactivar |
| `org.empresa.eliminar` | empresa | eliminar | DELETE /org/empresa/{id} |
| `org.sucursal.leer` | sucursal | leer | GET /org/sucursales · GET /org/sucursales/{id} |
| `org.sucursal.crear` | sucursal | crear | POST /org/sucursales |
| `org.sucursal.actualizar` | sucursal | actualizar | PUT /org/sucursales/{id} · POST /org/sucursales/{id}/reactivar |
| `org.sucursal.eliminar` | sucursal | eliminar | DELETE /org/sucursales/{id} |
| `org.centro_costo.leer` | centro_costo | leer | GET /org/centros-costo · GET /org/centros-costo/{id} |
| `org.centro_costo.crear` | centro_costo | crear | POST /org/centros-costo |
| `org.centro_costo.actualizar` | centro_costo | actualizar | PUT /org/centros-costo/{id} · POST /org/centros-costo/{id}/reactivar |
| `org.centro_costo.eliminar` | centro_costo | eliminar | DELETE /org/centros-costo/{id} |
| `org.departamento.leer` | departamento | leer | GET /org/departamentos · GET /org/departamentos/{id} |
| `org.departamento.crear` | departamento | crear | POST /org/departamentos |
| `org.departamento.actualizar` | departamento | actualizar | PUT /org/departamentos/{id} · POST /org/departamentos/{id}/reactivar |
| `org.departamento.eliminar` | departamento | eliminar | DELETE /org/departamentos/{id} |
| `org.cargo.leer` | cargo | leer | GET /org/cargos · GET /org/cargos/{id} |
| `org.cargo.crear` | cargo | crear | POST /org/cargos |
| `org.cargo.actualizar` | cargo | actualizar | PUT /org/cargos/{id} · POST /org/cargos/{id}/reactivar |
| `org.cargo.eliminar` | cargo | eliminar | DELETE /org/cargos/{id} |
| `org.parametro.leer` | parametro | leer | GET /org/parametros · GET /org/parametros/{id} |
| `org.parametro.crear` | parametro | crear | POST /org/parametros |
| `org.parametro.actualizar` | parametro | actualizar | PUT /org/parametros/{id} · POST /org/parametros/{id}/reactivar |
| `org.parametro.eliminar` | parametro | eliminar | DELETE /org/parametros/{id} |

**`modulo_id` ORG:** `E1000001-0000-4000-8000-000000000001`

---

## 8. RESUMEN FINAL DEL MÓDULO ORG

| Categoría | Antes de Fase 3 | Después de Fase 3 |
|---|---|---|
| Endpoints ✅ CORRECTO | 18 | **34** |
| Endpoints ⚠ INCOMPLETO | 16 | **0** |
| Endpoints 🔴 DEPRECATED | 0 | 0 |
| Endpoints 🔁 REEMPLAZAR | 0 | 0 |
| Endpoints faltantes | 0 | 0 |
| Seeds RBAC | ❌ No existían | ✅ 24 permisos creados |
| Contrato `empresa_id` by-ID | ⚠ Ambiguo (Optional) | ✅ Explícito (requerido) |

**Estado final:** 🟢 **COMPLETO Y LISTO PARA PRODUCCIÓN**

El módulo ORG cubre sus 6 entidades organizacionales con CRUD completo (36 endpoints),
validación de `client_id` y `empresa_id` en todos los endpoints que aplican, RBAC
consistente con el patrón `org.recurso.accion`, y seeds disponibles para poblar la
tabla `permiso` en la BD central.
