# Reglas de negocio — especificación oficial v1.0

**Paquete:** `cfg-implementation-spec`  
**Versión:** 1.0

---

## 1. Clasificación de campos

| Clase | Campos | Admin MVP |
|-------|--------|-----------|
| **A** Identidad | `secuencia_id`, `cliente_id`, `sequence_key`, `scope_type`, `scope_fingerprint`, `empresa_id`, `almacen_id`, `punto_venta_id` | Solo lectura; no en Update |
| **B** Configurable | `prefijo`, `separador`, `longitud_numero`, `numero_inicial`, `es_activo` | B vía PATCH excepto `es_activo` (DELETE/reactivar) |
| **C** Solo lectura | `generation_policy`, timestamps, enrich Catalog | Solo lectura |
| **D** Operativo | `ultimo_numero` | Solo lectura; Motor/align futuro |

---

## 2. Reglas de mutación

| ID | Regla |
|----|-------|
| BR-01 | PATCH solo campos B de formato (`prefijo`, `separador`, `longitud_numero`, `numero_inicial`) |
| BR-02 | `es_activo` solo vía DELETE soft / POST reactivar |
| BR-03 | Sin create admin ni delete físico de fila |
| BR-04 | Sin mutar `ultimo_numero` desde admin |
| BR-05 | Sin mutar `generation_policy` / identidad / scope |
| BR-06 | Cambios de formato **no** reescriben códigos históricos en ORG/INV |
| BR-07 | Toda mutación setea auditoría (`fecha_actualizacion`, `usuario_actualizacion_id`) |

---

## 3. Lock `org_empresa`

| ID | Regla |
|----|-------|
| BR-ORG-01 | Si `sequence_key == "org_empresa"` → `config_locked=true` en Read |
| BR-ORG-02 | PATCH → 422 `ORG_EMPRESA_CFG_LOCKED` |
| BR-ORG-03 | DELETE soft → 422 `ORG_EMPRESA_CFG_LOCKED` |
| BR-ORG-04 | GET y preview **permitidos** |
| BR-ORG-05 | Reactivar no aplica de forma útil si nunca se desactiva; si se llama sobre activa → 200 idempotente |

---

## 4. Validaciones PATCH

| Campo | Regla | Código |
|-------|-------|--------|
| `prefijo` | Requerido si se envía; max 10; charset alfanumérico razonable; upper | `CFG_PREFIX_INVALID` |
| `separador` | Solo `""` o `"-"` | `CFG_SEPARATOR_INVALID` |
| `longitud_numero` | Entero ≥ 1; no exceder lo razonable vs `max_output_length` del Catalog si existe | `CFG_PADDING_INVALID` |
| `numero_inicial` | Entero ≥ 1 (**G-03**) | `CFG_NUMERO_INICIAL_INVALID` |
| Extra fields | Rechazo schema | 422 Pydantic |
| Body vacío | 422 | al menos un campo |

**No validar en MVP:** colisión de formato entre keys (**G-02**).

---

## 5. Preview

| ID | Regla |
|----|-------|
| BR-PV-01 | Delegar solo a `CodigoGeneracionGateway.preview` |
| BR-PV-02 | No incrementa `ultimo_numero` |
| BR-PV-03 | No reserva correlativo |
| BR-PV-04 | Scope desde fila cfg |
| BR-PV-05 | Secuencia inactiva → **200** con `es_activo=false` (**G-05**) |
| BR-PV-06 | `supports_preview=false` → 422 `PREVIEW_NOT_ALLOWED` |
| BR-PV-07 | `disclaimer` desde `PreviewResult` del Motor |

---

## 6. Soft-disable (G-01)

| ID | Regla |
|----|-------|
| BR-SD-01 | DELETE HTTP = `es_activo=false` |
| BR-SD-02 | POST reactivar = `es_activo=true` |
| BR-SD-03 | Allocate runtime del Motor fallará si inactiva (comportamiento Motor existente); admin preview no |
| BR-SD-04 | Idempotencia: repetir DELETE/reactivar en mismo estado → 200 |

---

## 7. Aislamiento multi-tenant

| ID | Regla |
|----|-------|
| BR-T-01 | Toda query filtra `cliente_id` de sesión |
| BR-T-02 | Cross-tenant → 404 |
| BR-T-03 | Shared y Dedicated: misma semántica de negocio |

---

## 8. Operaciones prohibidas (lista cerrada MVP)

- Crear fila cfg por API  
- Borrar físicamente  
- Align counter  
- Diagnóstico  
- Editar policy / contador / fingerprint  
- Administrar series fiscales  
- Llamar allocate desde admin  
- Path ADMIN sin session tenant  

---

## 9. Enrich Catalog

| ID | Regla |
|----|-------|
| BR-EN-01 | Si `SequenceCatalog.contains(key)` → poblar enrich |
| BR-EN-02 | Si no contiene → enrich null; no 500 |
| BR-EN-03 | `policy_drift = (generation_policy != catalog_policy)` cuando hay catalog |
| BR-EN-04 | Catalog nunca se escribe |
