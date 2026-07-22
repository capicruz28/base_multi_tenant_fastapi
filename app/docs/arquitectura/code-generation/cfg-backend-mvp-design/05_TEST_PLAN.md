# Plan de pruebas (MVP Backend)

**Paquete:** `cfg-backend-mvp-design`  
**Fecha:** 2026-07-17

---

## 1. Estrategia general

| Tipo | Objetivo | Herramientas típicas |
|------|----------|----------------------|
| **Unitarias** | Services, validator, enricher, context builder, queries con session mock | pytest + AsyncMock |
| **Integración** | Endpoints FastAPI + RBAC + UoW (si hay harness tenant) | TestClient / async client + fixtures ORG-like |
| **Contrato** | OpenAPI paths/schemas presentes | snapshot diff / schema checks |
| **No regresión Motor** | Suite `core/codigo` y ORG/INV existentes en verde | CI existente |

**Principio:** no mockear el Gateway de forma que oculte side-effects; para preview, mockear `CodigoGeneracionGateway.preview` **o** usar fake session que aserte que no se llama `increment_and_get`.

---

## 2. Pruebas unitarias (obligatorias MVP)

### 2.1 Validator

| ID | Caso | Esperado |
|----|------|----------|
| U-V01 | PATCH org_empresa | `ORG_EMPRESA_CFG_LOCKED` |
| U-V02 | desactivar org_empresa | `ORG_EMPRESA_CFG_LOCKED` |
| U-V03 | prefijo inválido | `CFG_PREFIX_INVALID` |
| U-V04 | padding inválido | `CFG_PADDING_INVALID` |
| U-V05 | separador no permitido | `CFG_SEPARATOR_INVALID` |
| U-V06 | numero_inicial conflict | `CFG_NUMERO_INICIAL_CONFLICT` |
| U-V07 | colisión formato otra key | `CFG_FORMAT_COLLISION` |

### 2.2 Enricher

| ID | Caso | Esperado |
|----|------|----------|
| U-E01 | key conocida | campos catalog poblados |
| U-E02 | policy drift | `policy_drift=true` |
| U-E03 | org_empresa | `config_locked=true` |
| U-E04 | key desconocida | no exception; enrich null |

### 2.3 Services lectura

| ID | Caso | Esperado |
|----|------|----------|
| U-L01 | list filtra cliente_id | no filas de otro tenant |
| U-L02 | get id otro cliente | NotFoundError |
| U-L03 | paginación con page | envelope |
| U-L04 | sin page | list plana |
| U-L05 | sort_by inválido | INVALID_SORT_COLUMN |

### 2.4 Services mutación

| ID | Caso | Esperado |
|----|------|----------|
| U-M01 | PATCH OK | campos B actualizados + audit set |
| U-M02 | PATCH con ultimo_numero en body | 422 forbid |
| U-M03 | activar idempotente | 200 es_activo true |
| U-M04 | desactivar OK | es_activo false |
| U-M05 | write usa get_connection_for_tenant | mock assert called |
| U-M06 | nunca llama update_ultimo_numero | assert not called |

### 2.5 Preview

| ID | Caso | Esperado |
|----|------|----------|
| U-P01 | preview mapea codigo_estimado | desde PreviewResult.code |
| U-P02 | consume_contador false | siempre |
| U-P03 | ultimo_numero igual antes/después | sin increment |
| U-P04 | context usa empresa_id de la fila | builder test |
| U-P05 | llama Gateway.preview no allocate | assert |

### 2.6 Deps

| ID | Caso | Esperado |
|----|------|----------|
| U-D01 | impersonación | cliente_id JWT tenant no SYSTEM |

---

## 3. Pruebas de integración (recomendadas MVP)

| ID | Caso | Esperado |
|----|------|----------|
| I-01 | GET list 403 sin permiso | |
| I-02 | GET list 200 con consultar | |
| I-03 | PATCH 403 solo consultar | |
| I-04 | PATCH 200 con actualizar | |
| I-05 | preview 200 disclaimer presente | |
| I-06 | OpenAPI contiene operationIds MVP | |
| I-07 | Dedicated path: session passed to update | si hay fixture Dedicated |

Si el harness de integración tenant es costoso, priorizar unitarias U-* + un smoke I-02/I-04/I-05.

---

## 4. Archivos de test sugeridos

```text
tests/unit/test_cfg_secuencia_validator.py
tests/unit/test_cfg_catalog_enricher.py
tests/unit/test_cfg_codigo_secuencia_admin_servicio.py
tests/unit/test_cfg_preview_context_builder.py
tests/unit/test_cfg_deps_session_client_id.py
tests/api/test_cfg_secuencias_endpoints.py   # si aplica convención api/
```

---

## 5. Qué no probar en MVP

- Align / diagnóstico  
- validate_manual admin  
- Frontend  
- Series fiscales  
- Performance a escala (volumen bajo)  
- Reescritura de suites ORG/INV (solo no-regresión CI)

---

## 6. Criterio de salida de pruebas

MVP Backend listo para certificación cuando:

1. Todos los U-V, U-E, U-L, U-M, U-P, U-D01 pasan.  
2. Al menos smoke I-02, I-04, I-05 (o equivalentes).  
3. Suites Motor + ORG + INV sin fallos nuevos.  
4. OpenAPI actualizado alineado a `02_OPENAPI_DESIGN.md`.
