# Motor de Códigos — Arquitectura de política en cfg_codigo_secuencia

**Proyecto:** Policy Runtime Migration (pre-Ola 1)  
**Fecha:** 2026-07-11  
**Estado:** Diseño aprobado para revisión — sin implementación  
**Restricción:** Una sola tabla de configuración — `cfg_codigo_secuencia`

---

## 1. Decisión arquitectónica

### 1.1 Problema AS-IS

Hoy la **política de generación** (`AUTO_REQUIRED` / `AUTO_DEFAULT`) vive en **`SequenceCatalog`** (`SequenceDefinition.policy`). La fila **`cfg_codigo_secuencia`** almacena prefijo, contador y scope, pero **no** la política efectiva del tenant.

Consecuencia: un tenant **no puede** endurecer o relajar política por secuencia sin desplegar código. La configuración operativa está partida entre catálogo estático (política) y BD (formato/contador).

### 1.2 Decisión TO-BE

| Capa | Responsabilidad |
|------|-----------------|
| **`SequenceCatalog`** | Metadata de sistema: `sequence_key`, tabla/columna, scope_type, store_type, perfiles formatter/parser/validator, alignment, defaults técnicos, **`default_generation_policy`** (semilla) |
| **`cfg_codigo_secuencia`** | Configuración **efectiva por cliente/scope**: prefijo, separador, longitud, contadores, `es_activo`, **`generation_policy`** |

**Prohibido:** tabla `cfg_codigo_policy`, duplicar filas, duplicar prefijos/contadores fuera de cfg.

### 1.3 Principio rector

> En runtime, **`generation_policy` de la fila cfg** es la fuente de verdad para decidir AUTO vs manual.  
> El catálogo provee **defaults de bootstrap** y **metadata técnica** no negociable por tenant.

---

## 2. Nueva columna: `generation_policy`

### 2.1 Definición propuesta

| Atributo | Valor |
|----------|-------|
| **Nombre** | `generation_policy` |
| **Tipo** | `NVARCHAR(20) NOT NULL` |
| **CHECK** | `IN ('AUTO_REQUIRED', 'AUTO_DEFAULT', 'MANUAL_ONLY')` |
| **Default SQL** | **No usar** como fuente de negocio — ver §4 |

### 2.2 ¿Es el nombre correcto?

| Alternativa | Veredicto |
|-------------|-----------|
| **`generation_policy`** | **Recomendado** — semántica de negocio clara; alinea con contrato funcional Ola 1A |
| `code_policy` | Aceptable — coincide con enum `CodePolicy` en Python |
| `policy` | Rechazado — ambiguo en SQL |
| `modo_generacion` | Rechazado — inconsistente con docs F15A en inglés técnico |

**Mapeo código:** columna BD `generation_policy` ↔ enum Python `CodePolicy` (mismos literales).

### 2.3 Valores CHECK vs enum completo

| Valor CHECK | En cfg | Motivo |
|-------------|--------|--------|
| `AUTO_REQUIRED` | Sí | Documentos F2, correlativos obligatorios |
| `AUTO_DEFAULT` | Sí | Maestros F1 |
| `MANUAL_ONLY` | Sí | Secuencia cfg donde el tenant exige siempre manual (implantación avanzada) |
| `EXTERNAL` | **No** | No aplica a secuencias cfg — identificadores externos (RUC, ISO) no tienen fila cfg |

**Nota:** hoy el catálogo solo define `AUTO_REQUIRED` y `AUTO_DEFAULT` (63 entradas CFG). `MANUAL_ONLY` en cfg es **capacidad futura** sin entrada catálogo obligatoria.

---

## 3. Split catálogo vs cfg

### 3.1 Permanece en SequenceCatalog

| Campo / concepto | Razón |
|------------------|-------|
| `sequence_key` | Identidad global del motor |
| `table_name`, `code_column` | Binding técnico ERP |
| `scope_type`, `store_type`, `sequence_family` | Estrategia de allocation |
| `formatter_profile`, `parser_profile`, `validator_profile` | Algoritmos congelados |
| `alignment_mode`, `normalize_case` | Comportamiento técnico alineación |
| `supports_preview` | Capacidad de sistema (no negocio tenant) |
| `default_prefix`, `default_padding`, `default_separator`, `numero_inicial` | **Defaults de semilla** bootstrap/lazy |
| `default_generation_policy` (rename de `policy`) | **Semilla** — no runtime authority |
| `catalog_version`, `modulo_codigo` | Gobierno y trazabilidad |

### 3.2 Pasa a cfg_codigo_secuencia (runtime)

| Campo | Ya existe | Nuevo |
|-------|-----------|-------|
| `prefijo`, `separador`, `longitud_numero` | Sí | — |
| `numero_inicial`, `ultimo_numero` | Sí | — |
| `es_activo` | Sí | — |
| `scope_type`, `scope_fingerprint`, dimensiones | Sí | — |
| **`generation_policy`** | **No** | **Sí** |

### 3.3 Campos derivados que dejan de depender solo del catálogo

| Campo catálogo | Hoy | TO-BE |
|----------------|-----|-------|
| `allow_manual` | Derivado de `policy` en `_def()` | **Derivado de `generation_policy` cfg** en runtime |
| `supports_import` | Derivado de policy + alignment | Derivado de **cfg policy** + alignment catálogo |
| `consumes_counter_on_allocate` | `defn.policy == AUTO_REQUIRED` | **`cfg.generation_policy == AUTO_REQUIRED`** |

---

## 4. Modelo de resolución (EffectiveConfig)

Concepto nuevo — **no requiere tabla adicional**:

```
EffectiveSequenceConfig = SequenceDefinition (catálogo)
                        + CfgSequenceRow (BD)
                        → effective_policy = row.generation_policy
                        → effective_prefix = row.prefijo
                        → ...
```

El motor **combina** ambas fuentes en memoria por operación `allocate`.

---

## 5. PolicyResolver — veredicto

| Opción | Veredicto |
|--------|-----------|
| Desaparecer | **No** |
| Transformarse | **Sí** — firma desacoplada de `SequenceDefinition` |
| Delegar | **Sí** — desde gateway/store |

**Diseño:**

```text
PolicyResolver.resolve(
    generation_policy: CodePolicy,  # desde cfg (obligatorio en runtime)
    context: GenerationContext,
) -> PolicyMode
```

El catálogo **no** participa en `resolve()` salvo fallback controlado en bootstrap/repair.

---

## 6. Fallback catálogo — veredicto

| Estrategia | Veredicto |
|------------|-----------|
| Fallback `default_generation_policy` del catálogo si cfg NULL | **Solo migración/repair/lazy-create** — ventana finita |
| Runtime allocate con cfg NULL | **Rechazado** post-backfill — error 422/500 explícito |
| Toda decisión solo desde cfg | **Objetivo steady-state** |

**Lazy `ensure_row`:** al crear fila ALMACEN/PV, copiar `generation_policy` desde `catalog.default_generation_policy`.

---

## 7. Ventajas y desventajas

### Ventajas

| # | Ventaja |
|---|---------|
| A1 | Configuración tenant completa en **un solo lugar** (cfg) |
| A2 | Política modificable por implantación **sin deploy** (futuro UI admin) |
| A3 | Alineación con modelo mental ERP: cfg = operativo, catálogo = sistema |
| A4 | Bootstrap puede sembrar política explícita por fila (auditable) |
| A5 | Ola 1 ORG consume política real del tenant, no hardcode catálogo |

### Desventajas

| # | Desventaja |
|---|------------|
| D1 | Migración DDL + backfill obligatoria |
| D2 | Doble fuente durante transición (riesgo drift catálogo vs cfg) |
| D3 | Tests y docs deben actualizarse (63×N filas por tenant) |
| D4 | `ensure_row` y seed deben mantener paridad con catálogo |
| D5 | Cambio de política en cfg sin validación de negocio puede romper integraciones |

---

## 8. Riesgos de compatibilidad

| ID | Riesgo | Severidad |
|----|--------|-----------|
| R-PC-01 | Filas legacy sin `generation_policy` | Alta — requiere backfill |
| R-PC-02 | Drift: catálogo cambia default, cfg antigua no | Media — gobernanza catálogo |
| R-PC-03 | Tenant cambia AUTO_REQUIRED → AUTO_DEFAULT en caliente | Alta — impacto legal F2 |
| R-PC-04 | Lazy row sin policy copiada | Alta — bloquear en ensure_row |
| R-PC-05 | Dedicated vs Shared seed paths divergen | Media |
| R-PC-06 | Ola 1.1 OrgCodigoGenerationService asume catálogo policy | Baja — aún no wired |

---

## 9. Relación con documentos Ola 1 ORG

| Documento | Impacto |
|-----------|---------|
| `04_FUNCTIONAL_CONTRACT.md` | Sigue válido — políticas AUTO_DEFAULT por entidad ORG |
| `OrgCodigoGenerationService` | Sin cambio en Ola 1.1 — consume gateway opaco |
| Implementación Ola 1.2+ cargo | **Debe** usar cfg policy post-migración |

**Orden recomendado:** cerrar policy migration **antes** de migrar primera entidad ORG al motor.

---

## 10. Veredicto arquitectura

**APROBADO CONDICIONAL:** incorporar `generation_policy` en `cfg_codigo_secuencia` como autoridad runtime; renombrar `SequenceDefinition.policy` → `default_generation_policy` (semántica semilla); transformar `PolicyResolver` para leer policy desde cfg.
