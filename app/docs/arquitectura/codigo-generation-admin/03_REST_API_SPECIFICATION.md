# Especificación REST (diseño — sin implementación)

**Prefijo propuesto:** `/cfg/secuencias`  
**Router padre:** ERP con `dependencies=[Depends(require_erp_session)]`  
**Scope datos:** `cliente_id` desde `get_cfg_session_client_id` (patrón ORG tenant)  
**Paginación:** contrato v1 ERP (`page`, `limit`, `buscar`, `sort_by`) en listado

---

## 1. Endpoints permitidos

### 1.1 Consulta

| Método | Ruta | Operación | RBAC |
|--------|------|-----------|------|
| GET | `/cfg/secuencias` | Listar secuencias tenant | `cfg.secuencias.consultar` |
| GET | `/cfg/secuencias/{secuencia_id}` | Detalle + metadatos catálogo | `cfg.secuencias.consultar` |
| GET | `/cfg/secuencias/{secuencia_id}/diagnostico` | DGN-01..06 agregado | `cfg.secuencias.diagnosticar` |

**Query params listado (propuestos):**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `empresa_id` | UUID | Filtrar scope EMPRESA |
| `scope_type` | enum | TENANT / EMPRESA / ALMACEN / PUNTO_VENTA |
| `sequence_key` | string | Filtro exacto o `buscar` parcial |
| `es_activo` | bool | Solo activas/inactivas |
| `modulo_codigo` | string | Filtro vía catálogo (post-join lógico) |
| `page`, `limit`, `sort_by`, `sort_dir` | paginación v1 | |

**Response Read enriquecido (campos adicionales catálogo):**

```text
sequence_key, scope_type, scope_fingerprint,
empresa_id?, almacen_id?, punto_venta_id?,
prefijo, separador, longitud_numero, numero_inicial, ultimo_numero,
es_activo, generation_policy,
fecha_creacion, fecha_actualizacion,
— enriquecimiento —
entity_table, code_column, modulo_codigo, catalog_policy,
supports_preview, allow_manual, sequence_family (read-only)
```

### 1.2 Configuración

| Método | Ruta | Operación | RBAC |
|--------|------|-----------|------|
| PATCH | `/cfg/secuencias/{secuencia_id}` | Actualizar B-configurables | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/activar` | `es_activo=true` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/desactivar` | `es_activo=false` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/validar-config` | MNT-02 simulación | `cfg.secuencias.actualizar` |

**PATCH body (propuesto):**

```json
{
  "prefijo": "CLI",
  "separador": "",
  "longitud_numero": 4,
  "numero_inicial": 1
}
```

Todos optional; validación BR-CUST-01 antes de commit.

### 1.3 Operativas

| Método | Ruta | Operación | RBAC |
|--------|------|-----------|------|
| POST | `/cfg/secuencias/{secuencia_id}/preview` | OPS-01 próximo código | `cfg.secuencias.consultar` |
| POST | `/cfg/secuencias/validar-manual` | OPS-02 (sequence_key + scope + code) | `cfg.secuencias.consultar` |

**Preview request:** resuelve `GenerationContext` desde sesión ERP (empresa_id operativa si scope EMPRESA).

**Preview response:**

```json
{
  "sequence_key": "org_sucursal",
  "codigo_estimado": "SUC042",
  "ultimo_numero_actual": 41,
  "consume_contador": false
}
```

### 1.4 Mantenimiento

| Método | Ruta | Operación | RBAC |
|--------|------|-----------|------|
| POST | `/cfg/secuencias/{secuencia_id}/align` | MNT-01 align counter | `cfg.secuencias.mantener` |

**Align body:**

```json
{
  "candidate_code": "CLI999",
  "motivo": "Importación lote 2026-03-15"
}
```

Delegación: `CodigoGeneracionGateway.align_counter` en UoW tenant.

**Align response:**

```json
{
  "ultimo_numero_anterior": 20,
  "ultimo_numero_nuevo": 999,
  "aligned": true
}
```

---

## 2. Endpoints explícitamente prohibidos

| Operación prohibida | Motivo |
|---------------------|--------|
| POST `/cfg/secuencias` (crear fila libre) | Solo bootstrap/lazy; admin no inventa scopes |
| DELETE `/cfg/secuencias/{id}` | Soft-disable únicamente |
| PATCH `ultimo_numero` | Bypass motor; usar `/align` |
| PATCH `sequence_key` | Rompe UQ y catálogo |
| PATCH `scope_type`, `scope_fingerprint` | Identidad fila |
| PATCH `cliente_id` | Seguridad tenant |
| PATCH `empresa_id` / `almacen_id` / `punto_venta_id` | Requiere nueva fila lazy |
| PATCH `generation_policy` | BR-UPD-02 gobernanza catálogo |
| PUT reemplazo total | PATCH parcial únicamente |
| POST «reiniciar contador a 0» | BR-S-02; usar align con evidencia MAX |

**Errores esperados:** 422 `IMMUTABLE_FIELD`, 409 anti-colisión, 403 RBAC.

---

## 3. Endpoints no incluidos en v1 (evaluar v2)

| Idea | Decisión v1 |
|------|-------------|
| Historial cambios | Fase F — sin tabla audit hoy |
| Align masivo tenant | Fase D — script implantación primero |
| CRUD fiscal series | Módulo **fiscal admin** separado (`invbill_serie_comprobante`) |
| Export CSV cfg | Nice-to-have |
| Sincronizar catálogo → cfg | Job plataforma; no REST tenant |

---

## 4. Códigos de error HTTP (mapeo)

| Situación | HTTP | internal_code |
|-----------|------|---------------|
| Secuencia no encontrada / cross-tenant | 404 | — |
| Campo inmutable en PATCH | 422 | `IMMUTABLE_FIELD` |
| Anti-colisión prefijo/pad/inicial | 409 | `CFG_COLLISION_RISK` |
| Secuencia inactiva en preview | 422 | `SEQUENCE_INACTIVE` |
| Preview no soportado catálogo | 422 | `PREVIEW_NOT_ALLOWED` |
| Align candidate no parseable | 422 | `ALIGN_NOT_PARSEABLE` |
| Sin permiso mantenimiento | 403 | — |

Usar clases existentes `ConflictError`, `ValidationError`, `NotFoundError`, `AuthorizationError` (`app/core/exceptions.py`).

---

## 5. Convenciones ERP V4

| Regla | Aplicación |
|-------|------------|
| UUID v4 paths | `{secuencia_id}` |
| Sin DELETE físico | POST desactivar |
| Session scope | TENANT-wide list; gate empresa si mezcla scopes |
| Dedicated | Misma API; routing tenant_data |
| OpenAPI | Tags `CFG - Secuencias`; operationId únicos |

---

*Políticas: [`04_GENERATION_POLICY_ADMIN.md`](04_GENERATION_POLICY_ADMIN.md)*
