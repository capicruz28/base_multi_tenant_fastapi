# Análisis de configuración de secuencias

**Paquete:** `cfg-admin-audit`  
**Fecha:** 2026-07-17

---

## 1. SequenceCatalog (normativo)

| Atributo | Hallazgo |
|----------|----------|
| Ubicación | `app/core/codigo/sequence_catalog.py` |
| Rol | Única fuente de verdad de `sequence_key`, policy nominal, defaults, perfiles, scope |
| Tamaño | Validación interna: **63** entradas |
| Mutabilidad tenant | **Ninguna** — admin no crea keys ni cambia catálogo |
| Relación cfg | Seed copia defaults; runtime puede override formato en fila cfg |

**Implicación admin:** Read enriquecido con catálogo; Update **nunca** altera Catalog.

---

## 2. GenerationPolicy

### 2.1 Enum `CodePolicy`

| Valor | En Catalog | En CK BD cfg | Editable admin |
|-------|------------|--------------|----------------|
| `AUTO_REQUIRED` | ✅ | ✅ | **No** (clase C) |
| `AUTO_DEFAULT` | ✅ | ✅ | **No** |
| `MANUAL_ONLY` | ✅ | ✅ | **No** |
| `EXTERNAL` | ✅ (casos especiales) | ❌ no en CK | N/A en cfg |

### 2.2 Resolución runtime

- `CodigoGeneracionGateway._resolve_generation_policy`: lee policy de fila cfg (store CFG) o definición fiscal.
- `PolicyResolver.resolve`: traduce policy + `GenerationContext` → `PolicyMode` (AUTO_GENERATE / ACCEPT_MANUAL / REJECT_MANUAL / IMPORT_HISTORICAL).

**Diseño admin confirmado:** `generation_policy` se **muestra**; cambio solo vía gobernanza de Catalog + re-seed/migración controlada (fuera de MVP tenant).

**Diagnóstico futuro (DGN-01):** alertar drift `cfg.generation_policy` ≠ `Catalog.policy`.

---

## 3. Format / Prefix / Suffix / Number “Strategies”

### Hallazgo crítico de nomenclatura

**No existen** clases `FormatStrategy`, `PrefixStrategy`, `SuffixStrategy` ni `NumberStrategy` en el código.

El Motor usa **perfiles + formatter único**:

| Concepto de diseño | Implementación AS-IS |
|--------------------|----------------------|
| Format strategy | `FormatterProfile` + `CodeFormatter.format` |
| Prefix | `SequenceDefinition.default_prefix` / override `cfg.prefijo` |
| Separator | `default_separator` / `cfg.separador` |
| Number / padding | `default_padding` / `cfg.longitud_numero` + `ultimo_numero` / `numero_inicial` |
| Suffix | **No modelado** como columna ni perfil dedicado |
| Parser | `ParserProfile` + `CodeParser` |
| Validator | `ValidatorProfile` + `CodeValidator` |

### `CodeFormatter` (comportamiento)

1. `FMT_FISCAL_8` → número 8 dígitos (store fiscal; no cfg admin).
2. `FMT_NUMERIC_ONLY` → solo número con padding.
3. `FMT_STANDARD` (default) → `{prefijo}{separador}{numero_padded}`.
4. `NormalizeCase.UPPER` si aplica.
5. Tope `max_output_length` → `ConflictError` CODE_LENGTH_EXCEEDED.

**Implicación admin:** editar B-fields cambia el ensamblaje futuro; no hay API de “strategies” que implementar — solo columnas cfg + perfiles de catálogo read-only.

---

## 4. Scope por empresa / tenant / almacén / PV

| `ScopeType` | Dimensiones | Creación fila |
|-------------|-------------|---------------|
| `TENANT` | `cliente_id` | Eager onboarding |
| `EMPRESA` | + `empresa_id` | Eager (empresa sede) / por empresa |
| `ALMACEN` | + `almacen_id` | Lazy `ensure_row` |
| `PUNTO_VENTA` | + `punto_venta_id` | Lazy |
| `SERIE_FISCAL` | Store FISCAL | **Fuera** de cfg admin |

Unicidad: `(cliente_id, sequence_key, scope_fingerprint)`.

**Admin listados:** filtro opcional por `empresa_id` / scope; autorización siempre por `cliente_id` de sesión ERP (impersonación-safe). Cross-tenant → 404.

**Relación empresa:** FK a `org_empresa`; filas EMPRESA no se “mueven” de empresa (campo A). Caso especial `org_empresa` (BR-BOOT-04): correlativo bootstrap; diseño admin recomienda lock de edición agresiva.

---

## 5. Validaciones existentes (Motor)

| Capa | Qué valida |
|------|------------|
| `CodeValidator` | Formato / reglas por `ValidatorProfile` |
| `CodeParser` | Extracción numérica para align/manual |
| `PolicyResolver` | Manual vs auto |
| Store | Secuencia inactiva → conflicto en allocate |
| Gateway | Orquesta allocate/preview/validate/align |

**Validaciones admin (BR-CUST, anti-colisión prefijo, org_empresa lock):** documentadas en `codigo-generation-admin`; **no implementadas** en código de módulo.

---

## 6. Compatibilidad Shared vs Dedicated Database

| Aspecto | AS-IS |
|---------|-------|
| Tabla cfg | En BD tenant (DEFAULT connection) |
| Motor allocate | Sesión UoW pasada al Gateway/Store |
| Repo bootstrap | **Session obligatoria** en writes (ADJ-03) |
| Admin futuro | Misma regla: `get_connection_for_tenant` + `session.begin()`; **prohibido** escribir vía connection pool CP en Dedicated |

Semántica funcional idéntica Shared/Dedicated; solo cambia el binding de conexión.

---

## 7. Dependencias con módulos ERP

| Consumidor | sequence_keys (ejemplos Ola 1) | Impacto si admin cambia prefijo |
|------------|--------------------------------|----------------------------------|
| ORG | `org_cargo`, `org_sucursal`, `org_empresa`, … | Códigos **nuevos**; históricos inmutables (BR-IMM) |
| INV | `inv_categoria_producto`, `inv_producto`, movimientos, … | Igual |
| Futuros | Keys nuevas en Catalog | Aparecen en listado cfg tras seed/lazy |

Cambiar formato **no** reescribe códigos ya emitidos; solo afecta generación futura y preview.

---

## 8. Conclusión de configuración

La “configuración del Motor” para un Tenant Admin se reduce a:

1. **Ver** filas cfg + metadatos Catalog.
2. **Editar** overrides de formato y activo (clase B).
3. **Previsualizar** vía Gateway.
4. **No** editar policy, scope, key, contador (salvo align post-MVP).

No hay capa Strategy pluggable que administrar: hay **perfiles congelados** + **overrides de fila**.
