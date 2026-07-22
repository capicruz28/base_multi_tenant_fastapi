# Guía de pruebas — especificación oficial v1.0

**Paquete:** `cfg-implementation-spec`  
**Versión:** 1.0

---

## 1. Alcance

Cubrir MVP Backend `cfg` según `02_API_SPEC` y `03_BUSINESS_RULES`.  
No probar align/diagnóstico/Frontend.  
Mantener verdes suites Motor + ORG + INV (no regresión).

---

## 2. Unitarias obligatorias

### Validator / reglas

| ID | Caso | Esperado |
|----|------|----------|
| T-V01 | PATCH `org_empresa` | `ORG_EMPRESA_CFG_LOCKED` |
| T-V02 | DELETE soft `org_empresa` | `ORG_EMPRESA_CFG_LOCKED` |
| T-V03 | prefijo inválido | `CFG_PREFIX_INVALID` |
| T-V04 | separador inválido | `CFG_SEPARATOR_INVALID` |
| T-V05 | padding &lt; 1 | `CFG_PADDING_INVALID` |
| T-V06 | `numero_inicial &lt; 1` | `CFG_NUMERO_INICIAL_INVALID` |
| T-V07 | `numero_inicial` ≤ `ultimo_numero` | **aceptado** (no error) |

### Enrich

| ID | Caso | Esperado |
|----|------|----------|
| T-E01 | key Catalog | enrich poblado |
| T-E02 | drift policy | `policy_drift=true` |
| T-E03 | `org_empresa` | `config_locked=true` |

### Lectura

| ID | Caso | Esperado |
|----|------|----------|
| T-L01 | filtro `cliente_id` | aislamiento |
| T-L02 | id otro tenant | NotFound |
| T-L03 | con `page` | envelope; total = filtrados post-enrich |
| T-L04 | `modulo_codigo` + page | totales coherentes (G-04) |
| T-L05 | sort_by inválido | `INVALID_SORT_COLUMN` |

### Mutación

| ID | Caso | Esperado |
|----|------|----------|
| T-M01 | PATCH OK + audit | campos B + usuario/fecha |
| T-M02 | body con `ultimo_numero` | 422 forbid |
| T-M03 | DELETE soft | `es_activo=false` |
| T-M04 | reactivar | `es_activo=true` |
| T-M05 | idempotencia soft/reactivar | 200 |
| T-M06 | UoW `get_connection_for_tenant` | llamado |
| T-M07 | no `update_ultimo_numero` | no llamado |

### Preview

| ID | Caso | Esperado |
|----|------|----------|
| T-P01 | mapeo `codigo_estimado` | desde Gateway |
| T-P02 | `consume_contador=false` | |
| T-P03 | `ultimo_numero` invariante | |
| T-P04 | llama `preview` no `allocate` | |
| T-P05 | fila inactiva | 200 + `es_activo=false` |
| T-P06 | context desde fila | empresa/almacén/PV |

### Deps

| ID | Caso | Esperado |
|----|------|----------|
| T-D01 | impersonación | cliente JWT tenant |

---

## 3. Integración / smoke (mínimo)

| ID | Caso |
|----|------|
| T-I01 | GET list 403 sin consultar |
| T-I02 | GET list 200 con consultar |
| T-I03 | PATCH 403 solo consultar |
| T-I04 | PATCH 200 con actualizar |
| T-I05 | DELETE + reactivar 200 |
| T-I06 | preview 200 + disclaimer |
| T-I07 | OpenAPI: 6 operationIds presentes |

---

## 4. Archivos sugeridos

```text
tests/unit/test_cfg_codigo_secuencia_admin_servicio.py
tests/unit/test_cfg_deps_session_client_id.py
tests/api/test_cfg_secuencias_endpoints.py   # según convención repo
```

---

## 5. Criterio de salida de pruebas

1. Todas las T-V, T-E, T-L, T-M, T-P, T-D01 en verde.  
2. Smoke T-I02, T-I04, T-I05, T-I06 (mínimo).  
3. CI Motor + ORG + INV sin regresiones nuevas.  
4. OpenAPI alineado a `02_API_SPEC.md`.
