# F17B — Matriz de responsabilidades: Bootstrap vs Motor

**Fase:** F17B (documentación). Complementa `28` y `29`.
**Objetivo:** delimitar sin ambigüedad qué pertenece al **Bootstrap existente** y qué al **Motor de Generación de Códigos**, para evitar solapamientos futuros (ORG/INV).

Leyenda: **O** = owner (responsable) · **C** = colabora/invoca · **—** = no participa

---

## 1. Matriz por responsabilidad

| # | Responsabilidad | Bootstrap (onboarding) | Motor (`app/core/codigo`) | Notas |
|---|-----------------|:---------------------:|:-------------------------:|-------|
| R1 | Crear `cliente` | **O** | — | Control-plane |
| R2 | Crear `org_empresa` sede | **O** | — | `MinimalErpTenantBootstrapService` |
| R3 | Crear usuario admin / roles / RBAC | **O** | — | onboarding + RBAC service |
| R4 | Crear `cliente_auth_config` | **O** | — | Shared paso 7 |
| R5 | Gestionar TX / rollback / markers | **O** | — | Shared TX; Dedicated markers |
| R6 | Aportar `empresa_id` de contexto al seed | **O** | **C** | Motor lo recibe, no lo crea |
| R7 | **Definir metadatos de secuencia** (prefijo, padding, scope, policy, family) | — | **O** | `SequenceCatalog` = fuente única |
| R8 | **Decidir subconjunto eager** (qué sembrar en onboarding) | **C** | **O** | F17D: el eager se **deriva** del catálogo (store CFG + scope TENANT/EMPRESA = 57); sin lista manual (ADJ-01/05 ✅) |
| R9 | **Insertar filas cfg iniciales** (seed) | **O** | **C** | `_insertar_secuencias_codigo` (bootstrap) usando datos del motor |
| R10 | Computar `scope_fingerprint` | — | **O** | `compute_scope_fingerprint` |
| R11 | **Lazy creation** en runtime | — | **O** | `CfgSequenceStore.ensure_row` |
| R12 | Incrementar contador (allocate) | — | **O** | `AllocationCoordinator` + UPDLOCK |
| R13 | Formatear / parsear / validar código | — | **O** | Formatter/Parser/Validator |
| R14 | Preview / alineación high-water | — | **O** | `PreviewReader` / `CounterAlignmentService` |
| R15 | Verificación de conteo (`row_expectations`) | **O** | **C** | Dedicated; el conteo esperado lo fija el eager del motor |
| R16 | Enrutamiento de conexión (Shared/Dedicated) | **O** | — | Motor es agnóstico: usa la sesión recibida |
| R17 | Punto único de consumo por ERP | — | **O** | `CodigoGeneracionGateway` |

---

## 2. Frontera crítica (dónde suele romperse)

> **El Bootstrap decide CUÁNDO y DÓNDE sembrar. El Motor decide QUÉ y CÓMO.**

- El bootstrap **no** debe hardcodear prefijos/padding ni conteos → resuelto en F17C/F17D: `onboarding_seed.py` deriva **todo** del `SequenceCatalog` (ADJ-01), incluida la selección de keys (F17D: store CFG + scope TENANT/EMPRESA); `EAGER_SEQUENCE_KEYS` es una vista derivada.
- El motor **no** debe abrir conexiones propias ni conocer Shared/Dedicated → hoy cumple (session-driven).
- ORG/INV **no** deben insertar filas cfg ni conocer prefijos → deben usar el Gateway.

---

## 3. Ownership de artefactos (archivos)

| Artefacto | Owner | Consumidores |
|-----------|-------|--------------|
| `sequence_catalog.py` | Motor | onboarding_seed (debería), stores, coordinator |
| `onboarding_seed.py` | Motor (contrato eager) | `cliente_onboarding_service`, `dedicated_*_adapters`, `tenant_seed_profiles` |
| `cfg_codigo_secuencia_repository.py` | Infra/Bootstrap | seed onboarding (con `session=`) |
| `cfg_sequence_store.py` | Motor | coordinator/gateway (runtime) |
| `cliente_onboarding_service.py` | Bootstrap | onboarding Shared + adapters Dedicated |
| `dedicated_tenant_seed_*` | Bootstrap/Provisioning | orquestador Dedicated |
| `codigo_generacion_gateway.py` | Motor | módulos ERP (ORG/INV, futuro) |

---

## 4. Doble vía de escritura a `cfg_codigo_secuencia` (a converger)

| Vía | Componente | Contexto | Sesión | Fingerprint |
|-----|-----------|----------|--------|-------------|
| Seed inicial | `CfgCodigoSecuenciaRepository.insert_secuencia` | Onboarding | recibida (`session=`) | computa |
| Lazy runtime | `CfgSequenceStore.ensure_row` | Runtime ERP | UoW ERP | computa |

Ambas computan `scope_fingerprint` y respetan `UQ_cfg_scope`, por lo que son **consistentes**. La convergencia recomendada (que el seed delegue en `ensure_row`) es un ajuste de robustez, no un requisito arquitectónico (ADJ-02).

---

## 5. Invariantes que ORG/INV deben respetar

1. **Nunca** insertar/actualizar `cfg_codigo_secuencia` directamente. Usar `CodigoGeneracionGateway`.
2. **Nunca** derivar prefijos/padding localmente. Provienen del `SequenceCatalog`.
3. `allocate` siempre dentro del **mismo UoW** que la operación transaccional (atomicidad código↔documento).
4. El motor hereda el store del servicio ERP (Shared/Dedicated) → **no** forzar conexión.

---

*Ajustes de implementación en `31`. Aprobación en `32`.*
