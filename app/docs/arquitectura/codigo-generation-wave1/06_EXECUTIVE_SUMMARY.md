# Motor de Códigos — Resumen ejecutivo: política en cfg_codigo_secuencia

**Proyecto:** Policy Runtime Migration  
**Fecha:** 2026-07-11  
**Estado:** Diseño para aprobación — **sin implementación**  
**Audiencia:** Arquitectura, backend, provisioning

---

## 1. Decisión en una frase

La **política de generación** (`AUTO_REQUIRED`, `AUTO_DEFAULT`, `MANUAL_ONLY`) pasa de **`SequenceCatalog`** a **`cfg_codigo_secuencia.generation_policy`**, manteniendo el catálogo como metadata técnica y defaults de semilla — **sin nueva tabla**.

---

## 2. Respuestas a las 12 preguntas de auditoría

### 2.1 ¿Qué componentes leen PolicyResolver hoy?

Solo **`CodigoGeneracionGateway`** en tres métodos: `allocate`, `preview`, `validate_manual`.  
Tests unitarios en `test_codigo_engine_ola0.py`. **Ningún módulo ERP** (ORG, INV) lo invoca directamente.

### 2.2 ¿Qué partes dependen de SequenceCatalog.policy?

| Dependencia | Tipo |
|-------------|------|
| `PolicyResolver.resolve(defn, …)` | **Runtime — directa** |
| `SequenceDefinition.consumes_counter_on_allocate` | Property derivada |
| `sequence_catalog._def()` → `allow_manual`, `supports_import` | Derivados estáticos |
| Documentación / matriz catálogo | Referencia |

**No dependen hoy:** bootstrap seed, `CfgSequenceStore`, `AllocationCoordinator`, `OrgCodigoGenerationService`.

### 2.3 ¿Cuáles deben seguir dependiendo del catálogo?

| Consumidor | Campos catálogo |
|------------|-----------------|
| Gateway / Coordinator | `sequence_key`, `store_type`, perfiles format/parse/validate |
| ScopeResolver | `scope_type` |
| Bootstrap / lazy ensure | `default_prefix`, padding, separator, **`default_generation_policy`** |
| CounterAlignment | `alignment_mode`, `align_on_manual` |
| PreviewReader | `supports_preview` |

### 2.4 ¿Cuáles deben pasar a cfg_codigo_secuencia?

| Decisión runtime | Campo cfg |
|------------------|-----------|
| AUTO vs manual vs import | **`generation_policy`** |
| Formato efectivo | `prefijo`, `separador`, `longitud_numero` (ya en cfg) |
| Contador | `ultimo_numero`, `numero_inicial` (ya en cfg) |
| Activación | `es_activo` (ya en cfg) |

Derivados runtime (`allow_manual`, `consumes_counter_on_allocate`) se calculan desde **cfg policy**, no catálogo.

### 2.5 ¿Cambios conceptuales en CodigoGeneracionGateway?

1. Resolver `scope_key` (sin cambio).
2. **Cargar fila cfg** por scope (`CfgSequenceStore.get_by_scope`).
3. Rechazar allocate si cfg ausente/inactiva (steady-state).
4. Invocar `PolicyResolver.resolve(cfg_row.generation_policy, context)`.
5. Ramas AUTO / manual sin cambio de semántica.

**Firma pública:** sin cambio. ORG sigue usando `OrgCodigoGenerationService` → gateway.

### 2.6 ¿Cambios conceptuales en AllocationCoordinator?

**Mínimos.** Policy se resuelve **antes** de llamar al coordinator. Coordinator mantiene `allocate_next`, `accept_manual`, incremento contador. Opcional: pasar `cfg_row` para claridad — no obligatorio.

### 2.7 ¿PolicyResolver desaparece, transforma o delega?

| Opción | Veredicto |
|--------|-----------|
| Desaparecer | **No** — lógica F15A centralizada |
| Transformar | **Sí** — input `CodePolicy` desde cfg, no `SequenceDefinition` |
| Delegar | Gateway carga cfg y delega; resolver permanece puro sin I/O |

### 2.8 ¿Fallback en SequenceCatalog?

| Contexto | Fallback catálogo |
|----------|-------------------|
| Bootstrap / lazy `ensure_row` | **Sí** — copiar `default_generation_policy` |
| Repair backfill | **Sí** — fuente para filas legacy |
| Runtime allocate steady-state | **No** — solo cfg; NULL = error |

### 2.9 Ventajas y desventajas

**Ventajas:** configuración tenant unificada; policy auditable por fila; alineación ERP cfg=operativo; habilita UI admin futura; Ola 1 ORG usa policy real del tenant.

**Desventajas:** migración DDL + backfill; riesgo drift catálogo vs cfg; más superficie en seed (63 keys × scopes); cambio policy en caliente requiere gobernanza (especialmente F2).

### 2.10 Riesgos de compatibilidad

| Riesgo | Severidad |
|--------|-----------|
| Filas legacy sin policy | Alta |
| F2 con AUTO_DEFAULT por seed bug | Alta |
| Drift catálogo vs cfg antiguo | Media |
| Lazy row sin policy | Alta |
| Ola 1.1 ya implementada | Baja (gateway opaco) |

Mitigación: repair idempotente + tests por familia + gate pre-Ola 1.2.

### 2.11 Impacto por área

| Área | Impacto |
|------|---------|
| **Bootstrap Tenant** | Seed explícito policy en 57 filas |
| **Bootstrap Empresa / EBS V1** | 56 filas EMPRESA con policy |
| **Dedicated provisioning** | Mismo seed path |
| **ORG futuro** | Beneficiario — policy tenant real vía gateway |
| **INV futuro** | Mismo patrón; F2 AUTO_REQUIRED en cfg |
| **SequenceCatalog** | Rename `policy` → `default_generation_policy` |
| **Tests** | PolicyResolver, seed F17D, gateway+cfg |
| **Repair scripts** | Nuevo backfill cfg policy |

### 2.12 Nuevo flujo oficial del motor

```
ERP → OrgCodigoGenerationService → CodigoGeneracionGateway.allocate
  → SequenceCatalog.get (metadata)
  → ScopeResolver → scope_key
  → CfgSequenceStore.get_by_scope → cfg_row
  → PolicyResolver(cfg_row.generation_policy, context) → PolicyMode
  → AllocationCoordinator (AUTO o manual)
  → AllocationResult
```

Catálogo: **qué** secuencia y **cómo** técnicamente.  
Cfg: **política + formato + contador** del cliente.

---

## 3. Columna `generation_policy`

| Atributo | Valor |
|----------|-------|
| Nombre | **`generation_policy`** (recomendado) |
| CHECK | `AUTO_REQUIRED`, `AUTO_DEFAULT`, `MANUAL_ONLY` |
| EXTERNAL | **No en cfg** — identificadores externos sin fila |

Bootstrap debe sembrar **explícitamente** desde `default_generation_policy` del catálogo — **no** depender de DEFAULT SQL para distinguir F1 vs F2.

---

## 4. Veredictos clave

| Tema | Veredicto |
|------|-----------|
| Nueva tabla | **Rechazada** |
| PolicyResolver | **Transformar**, no eliminar |
| AllocationCoordinator | **Estable** |
| OrgCodigoGenerationService (Ola 1.1) | **Sin cambio** |
| Orden vs Ola 1 ORG | **Policy migration antes de org_cargo** |
| Nombre columna | **`generation_policy`** |
| Semilla bootstrap | **Explícita en Python** |

---

## 5. Entregables de diseño

| # | Documento | Contenido |
|---|-----------|-----------|
| 01 | `01_POLICY_ARCHITECTURE.md` | Decisión, columna, split catálogo/cfg, ventajas/riesgos |
| 02 | `02_POLICY_FLOW.md` | Flujos AS-IS / TO-BE, diagramas |
| 03 | `03_COMPONENT_IMPACT.md` | Matriz impacto por componente |
| 04 | `04_BOOTSTRAP_IMPACT.md` | Seed, backfill, flujos tenant/empresa |
| 05 | `05_IMPLEMENTATION_STRATEGY.md` | Fases P0–P2, gates, DoD |
| 06 | `06_EXECUTIVE_SUMMARY.md` | Este documento |

---

## 6. Próximo paso

**Aprobación explícita** de este paquete de diseño → iniciar **Fase P0** (DDL + ORM) → P1 (seed + backfill) → P2 (gateway) → **después** Ola 1.2 piloto `org_cargo`.

**Hasta entonces:** motor congelado; sin cambios en código, SQL, tests ni bootstrap.

---

## 7. Estado de aprobación

| Rol | Estado |
|-----|--------|
| Diseño arquitectura | **Pendiente aprobación** |
| Implementación | **Bloqueada** |
