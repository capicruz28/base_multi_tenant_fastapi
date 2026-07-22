# Referencia de columnas `cfg_codigo_secuencia`

**Fuente BD:** `app/infrastructure/database/tables.py` L742–786  
**Repositorio AS-IS:** `CfgCodigoSecuenciaRepository`  
**Clasificación:** A Inmutable · B Configurable · C Solo lectura · D Operativo (motor)

---

## 1. Tabla completa por columna

| Columna | Significado | Responsabilidad | Clase | Editable admin | Quién modifica | Cuándo | Impacto motor |
|---------|-------------|-----------------|-------|----------------|----------------|--------|---------------|
| `secuencia_id` | PK UUID fila cfg | Identidad persistente | **A** | No | Bootstrap / lazy ensure | Creación fila | ScopeKey lookup interno |
| `cliente_id` | Tenant propietario | Aislamiento multi-tenant | **A** | No | Bootstrap | Onboarding | Filtro obligatorio queries |
| `sequence_key` | Clave catálogo (`org_cargo`, …) | Vincula cfg ↔ `SequenceCatalog` | **A** | No | Bootstrap / lazy | Creación | Gateway resuelve definición |
| `scope_type` | TENANT / EMPRESA / ALMACEN / PUNTO_VENTA | Dimensión unicidad | **A** | No | Bootstrap / lazy | Creación | `ScopeResolver` |
| `scope_fingerprint` | Hash canónico del scope | Unicidad `(cliente, key, fingerprint)` | **A** | No | Sistema al insert | Creación | UQ_cfg_scope |
| `empresa_id` | FK org_empresa (nullable) | Scope EMPRESA+ | **A** | No | Bootstrap / lazy | Creación | Dimension ScopeKey |
| `almacen_id` | FK inv_almacen | Scope ALMACEN | **A** | No | Lazy | Primer uso WMS | Dimension ScopeKey |
| `punto_venta_id` | FK pos_punto_venta | Scope PUNTO_VENTA | **A** | No | Lazy | Primer uso POS | Dimension ScopeKey |
| `prefijo` | Prefijo alfanumérico | Formato código futuro | **B** | **Sí** | Admin / implantación | Post-onboarding | `CodeFormatter` usa cfg |
| `separador` | Entre prefijo y número | Formato (`∅` o `-`) | **B** | **Sí** | Admin | Post-onboarding | Formatter |
| `longitud_numero` | Padding dígitos | Ancho parte numérica | **B** | **Sí** | Admin | Post-onboarding; validar anti-colisión | Formatter + agotamiento |
| `numero_inicial` | Piso lógico correlativo | Primer número si contador bajo | **B** | **Sí** (restringido) | Admin | Sin códigos emitidos bajo nuevo piso | `increment_and_get` fórmula |
| `ultimo_numero` | High-water consumido | Último correlativo emitido/aceptado | **D** | **No** (admin directo) | **Motor** / align mantenimiento | allocate, manual+align, import | Próximo auto = max+1 |
| `es_activo` | Soft-enable secuencia | Bloqueo allocate si false | **B** | **Sí** | Admin | Operación | ConflictError si inactiva |
| `generation_policy` | AUTO_REQUIRED / AUTO_DEFAULT / MANUAL_ONLY | Modo PolicyResolver | **C** | **No** | Bootstrap (copia catálogo) | Creación fila | Gateway `_resolve_generation_policy` |
| `fecha_creacion` | Timestamp alta | Auditoría | **C** | No | BD default | INSERT | — |
| `fecha_actualizacion` | Timestamp última mutación | Auditoría | **C** | No | Sistema | UPDATE admin | — |
| `usuario_actualizacion_id` | Usuario última mutación admin | Auditoría | **C** | No | Servicio admin | UPDATE config | — |

> **Nota EXTERNAL:** `EXTERNAL` no se persiste en cfg (campos fuera del motor secuencial). CK BD: solo 3 políticas motor.

---

## 2. Clasificación detallada A / B / C / D

### A) Inmutables

| Campo | Justificación |
|-------|---------------|
| `secuencia_id` | PK; cambiar = nueva fila |
| `cliente_id` | Seguridad tenant; nunca reasignar |
| `sequence_key` | SC-GOV-01; identidad catálogo |
| `scope_type` | BR-UPD-02; cambio = otra fila |
| `scope_fingerprint` | Derivado; UQ_cfg_scope |
| `empresa_id`, `almacen_id`, `punto_venta_id` | Definen fingerprint; no editables post-creación |

**Regla ADMIN-A1:** mutación de campos A → **404** o **422** (`IMMUTABLE_FIELD`).

### B) Configurables

| Campo | Justificación |
|-------|---------------|
| `prefijo` | BR-CUST, PFX-*; personalización tenant sin tocar catálogo |
| `separador` | BS-CFG-01 editable por tenant |
| `longitud_numero` | Ampliación correlativo futuro (BR-CUST-01) |
| `numero_inicial` | Ajuste piso; validación anti-colisión |
| `es_activo` | BR-CUST-02 soft-disable |

**Regla ADMIN-B1:** PATCH solo estos campos + auditoría.

### C) Solo lectura (admin)

| Campo | Justificación |
|-------|---------------|
| `generation_policy` | BR-UPD-02: cambio = gobernanza catálogo, no UI tenant |
| `fecha_creacion`, `fecha_actualizacion`, `usuario_actualizacion_id` | Sistema |
| Metadatos catálogo enriquecidos | `table_name`, `code_column`, `modulo_codigo` — no están en cfg |

**Exposición API:** incluir en Read; **no** en Update schema.

### D) Operativos (solo motor / mantenimiento Gateway)

| Campo | Justificación |
|-------|---------------|
| `ultimo_numero` | SC-GOV-01: administrable en sentido estricto pero **solo** vía allocate/align; PATCH manual prohibido |

**Regla ADMIN-D1:** lectura permitida; escritura **solo** `Gateway.align_counter` o allocate runtime — nunca `update_ultimo_numero` desde API admin genérica.

---

## 3. Coherencia cfg ↔ catálogo

| Dato | En catálogo | En cfg | Admin |
|------|-------------|--------|-------|
| policy nominal | ✅ autoritativa | Copia al seed | Mostrar drift si difiere |
| prefijo default | ✅ default | Override tenant | Editable |
| scope | ✅ fijo | Persistido | Solo lectura |
| ultimo_numero | ❌ | ✅ runtime | Solo lectura + align |

**Diagnóstico DGN-01:** alertar si `generation_policy` cfg ≠ `SequenceCatalog.get(key).policy`.

---

## 4. Evidencia repositorio AS-IS

| Método repo | Uso admin futuro |
|-------------|------------------|
| `get_by_cliente` | Listado |
| `get_by_sequence_key` | Detalle / scope |
| `update_secuencia` | CFG-03..08 (prefijo, pad, sep, activo) — **extender** para numero_inicial |
| `update_ultimo_numero` | **No exponer REST** — reservado motor/tests |
| `insert_secuencia` | **No admin** — bootstrap/lazy only |

**ADJ-03:** toda escritura exige `session` tenant UoW — admin debe usar `get_connection_for_tenant`, no ADMIN CP en Dedicated.

---

*API REST: [`03_REST_API_SPECIFICATION.md`](03_REST_API_SPECIFICATION.md)*
