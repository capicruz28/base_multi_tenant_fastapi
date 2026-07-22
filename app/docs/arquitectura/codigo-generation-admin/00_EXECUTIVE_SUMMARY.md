# Módulo administrativo del Motor de Códigos — Resumen ejecutivo

**Etapa:** Auditoría funcional y arquitectónica — **sin implementación**  
**Fecha:** 2026-07-12  
**Alcance:** Administración oficial de `cfg_codigo_secuencia` para **todo el ERP** (ORG, INV, LOG, COM, POS, …)  
**Base normativa:** `code-generation/` (F15–F17), `07_BUSINESS_RULES.md`, `12_GATEWAY_DESIGN.md`, `bootstrap/03_BOOTSTRAP_RULES.md`

---

## 1. Objetivo

Diseñar el **módulo administrativo del Motor de Códigos**: capa Backend (y contrato para Frontend React) que permita **consultar, configurar, mantener y diagnosticar** las filas `cfg_codigo_secuencia` **sin bypass del motor** ni mutaciones peligrosas.

El runtime ERP seguirá consumiendo códigos **exclusivamente** vía `CodigoGeneracionGateway`. El módulo admin es **cliente del Gateway** para preview, align y validación — no reimplementa lógica de formato, scope ni política.

---

## 2. Veredicto arquitectónico

| Decisión | Valor |
|----------|-------|
| **Tipo de módulo** | Nuevo módulo ERP transversal: código **`cfg`** (configuración tenant) |
| **Tabla gobernada** | `cfg_codigo_secuencia` (store CFG; **excluye** fiscal `invbill_serie_comprobante`) |
| **Scope de sesión** | TENANT (`cliente_id` operativo ERP); filtros adicionales por `empresa_id` / almacén / PV según listado |
| **Mutaciones cfg** | Solo campos **configurables** (BR-CUST); contador solo vía **align** o motor |
| **Política `generation_policy`** | **Solo lectura** en admin; fuente normativa = `SequenceCatalog` (BR-UPD-02) |
| **API REST** | Bajo `/cfg/secuencias` (propuesto); RBAC `cfg.secuencias.{consultar\|actualizar\|mantener\|diagnosticar}` |
| **Dedicated / Shared** | Misma semántica; escrituras **siempre** con `get_connection_for_tenant` + `session` (ADJ-03) |

**Principio rector:** *El admin configura el entorno; el motor consume el contador.*

---

## 3. Operaciones en una frase

| Clase | Ejemplos |
|-------|----------|
| **Configuración** | Editar prefijo, separador, padding, numero_inicial, activar/desactivar |
| **Operativas** | Preview próximo código (sin consumo) |
| **Mantenimiento** | Align counter post-importación; validación anti-colisión |
| **Diagnóstico** | Drift cfg vs catálogo; secuencias lazy pendientes; contador vs MAX negocio |

**Prohibido:** CRUD libre de `ultimo_numero`, cambio de `sequence_key`/scope/fingerprint/cliente, DELETE físico.

---

## 4. Documentos de esta etapa

| # | Documento | Contenido |
|---|-----------|-----------|
| 00 | Este archivo | Resumen, veredicto, plan por fases |
| 01 | [`01_ADMIN_OPERATIONS_TAXONOMY.md`](01_ADMIN_OPERATIONS_TAXONOMY.md) | Taxonomía operaciones (§1) |
| 02 | [`02_CFG_COLUMN_REFERENCE.md`](02_CFG_COLUMN_REFERENCE.md) | Columnas, clasificación A/B/C/D (§2–§3) |
| 03 | [`03_REST_API_SPECIFICATION.md`](03_REST_API_SPECIFICATION.md) | Endpoints permitidos y prohibidos (§4–§5) |
| 04 | [`04_GENERATION_POLICY_ADMIN.md`](04_GENERATION_POLICY_ADMIN.md) | Políticas AUTO_* / MANUAL / EXTERNAL (§6) |
| 05 | [`05_ORG_EMPRESA_AND_SPECIAL_CASES.md`](05_ORG_EMPRESA_AND_SPECIAL_CASES.md) | org_empresa, preview, align (§7–§9) |
| 06 | [`06_SECURITY_RBAC_AND_FRONTEND.md`](06_SECURITY_RBAC_AND_FRONTEND.md) | Permisos y contrato React (§10–§11) |
| 07 | [`07_MODULE_ARCHITECTURE.md`](07_MODULE_ARCHITECTURE.md) | Componentes, flujos, riesgos, estrategia (§12) |

---

## 5. Plan de implementación recomendado (por fases)

### Fase A — Fundación (solo lectura)

| Entregable | Detalle |
|------------|---------|
| Módulo `cfg` | `presentation/`, `application/services/`, `infrastructure/database/queries/cfg/` |
| GET list + GET detail | Enriquecido con metadatos `SequenceCatalog` (read-only) |
| RBAC | `cfg.secuencias.consultar` |
| Tests | Listado tenant-scoped; Dedicated session path |

**Gate:** OpenAPI estable; sin mutaciones.

### Fase B — Configuración

| Entregable | Detalle |
|------------|---------|
| PATCH configuración | `prefijo`, `separador`, `longitud_numero`, `numero_inicial` |
| POST activar / desactivar | Soft-disable `es_activo` (BR-CUST-02) |
| Validación | BR-CUST-01 anti-colisión; reglas org_empresa |
| RBAC | `cfg.secuencias.actualizar` |

**Gate:** Cambio prefijo no altera códigos históricos (BR-P-01).

### Fase C — Operativas y diagnóstico

| Entregable | Detalle |
|------------|---------|
| POST preview | Delegación `CodigoGeneracionGateway.preview` |
| GET diagnóstico | Drift catálogo, lazy pending, agotamiento padding |
| RBAC | consultar + `cfg.secuencias.diagnosticar` |

### Fase D — Mantenimiento (restringido)

| Entregable | Detalle |
|------------|---------|
| POST align | `CodigoGeneracionGateway.align_counter` con auditoría |
| POST validar-config | Simulación pre-cambio |
| RBAC | `cfg.secuencias.mantener` (rol implantación / admin tenant elevado) |

### Fase E — Frontend React

| Entregable | Detalle |
|------------|---------|
| Pantallas | Listado, detalle, edición config, preview, mantenimiento |
| Sin diseño UI en esta etapa | Solo contrato API documentado en `06` |

### Fase F — Evolución (opcional)

| Entregable | Detalle |
|------------|---------|
| Historial | Tabla audit o eventos si se exige trazabilidad admin |
| Import batch align | Integración pipeline migración (BR-M-41) |

---

## 6. Relación con olas previas

| Ola | Estado | Relación admin |
|-----|--------|----------------|
| Ola 0 Motor core | ✅ | Gateway/Preview/Align **congelados** — admin los invoca |
| Ola 1 ORG motor | ✅ Cerrada | org_empresa: reglas especiales documentadas en `05` |
| **Admin (nueva etapa)** | Diseño | No bloquea runtime; paralelizable tras Fase A |

---

*Siguiente paso implementación: Fase A tras aprobación explícita de este diseño.*
