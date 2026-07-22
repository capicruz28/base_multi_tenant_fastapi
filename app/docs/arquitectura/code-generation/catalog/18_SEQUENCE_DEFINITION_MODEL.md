# F16A — Modelo de SequenceDefinition

**Fase:** F16A — Diseño del SequenceCatalog  
**Fecha:** 2026-07-03  
**Alcance:** Metadatos conceptuales de una entrada. Sin clases, sin código.

---

## 1. Propósito

Una **SequenceDefinition** es la unidad atómica del SequenceCatalog: describe **una** secuencia lógica identificada por `sequence_key` que el motor puede operar (allocate, preview, align).

---

## 2. Identidad y trazabilidad

| Campo | Obligatorio | Descripción | Justificación |
|-------|-------------|-------------|---------------|
| **sequence_key** | Sí | Clave estable; igual a `table_name` salvo excepción documentada | Identificador único en catálogo (F16 D-02) |
| **table_name** | Sí | Nombre tabla V010 | Trazabilidad DDL; puede coincidir con sequence_key |
| **code_column** | Sí | Columna que almacena el código generado/manual | Mapeo persistencia |
| **modulo_codigo** | Sí | Código módulo ERP (`ORG`, `INV`, `PUR`…) | RBAC, documentación, olas implementación |
| **catalog_version** | Sí | Versión del catálogo que introdujo la entrada | Gobernanza (`22`) |
| **documentation** | Recomendado | Texto humano: propósito de negocio, notas | Onboarding desarrolladores |

**Decisión SC-DEF-01:** `sequence_key` y `table_name` son **redundantes por diseño** en V1 (mismo valor). Se mantienen ambos para futura extensión donde una tabla tenga dos secuencias (ej. cabecera con dos columnas secuenciales — hoy no aplica).

---

## 3. Clasificación operativa

| Campo | Obligatorio | Valores | Justificación |
|-------|-------------|---------|---------------|
| **policy** | Sí | `AUTO_REQUIRED`, `AUTO_DEFAULT` | Solo entradas del motor; EXTERNAL/MANUAL_ONLY excluidas del catálogo |
| **sequence_family** | Sí | `F1`…`F5` (ver `19`) | Enrutamiento store y perfiles técnicos |
| **scope_type** | Sí | `TENANT`, `EMPRESA`, `ALMACEN`, `PUNTO_VENTA`, `SERIE_FISCAL` | ScopeResolver (F16 `13`) |
| **store_type** | Sí | `CFG`, `FISCAL` | cfg_codigo_secuencia vs serie fiscal |

**Decisión SC-DEF-02:** `policy` no es editable por tenant; replica F15A congelado.

---

## 4. Perfiles técnicos (referencias, no implementación)

| Campo | Obligatorio | Descripción | Justificación |
|-------|-------------|-------------|---------------|
| **formatter_profile** | Sí | Nombre de perfil de formateo (`FMT_*`) | Reutilización entre entidades |
| **parser_profile** | Sí | Nombre de perfil de parseo (`PAR_*`) | High-water y import |
| **validator_profile** | Sí | Nombre de perfil validación (`VAL_*`) | Formato y longitud |

**Decisión SC-DEF-03:** No se incrustan reglas en la entrada; se referencian perfiles definidos en `20`.

---

## 5. Capacidades (flags)

| Campo | Tipo | Default lógico | Justificación |
|-------|------|----------------|---------------|
| **motor_enabled** | bool | `true` | Entrada activa; `false` solo en deprecación |
| **supports_preview** | bool | `true` si AUTO_DEFAULT; else `false` | F15A STD-P-01 |
| **allow_manual** | bool | `true` si AUTO_DEFAULT; `false` si AUTO_REQUIRED | F15A |
| **align_on_manual** | bool | `true` si AUTO_DEFAULT + parser aplicable | F16 TD-MAN-02 |
| **supports_high_water** | bool | `true` si entra parser numérico | Import + manual |
| **supports_import** | bool | `true` maestros; documentos con rol implantación | F15A STD-I-* |
| **consumes_counter_on_allocate** | bool | `true` AUTO_REQUIRED; AUTO_DEFAULT solo si autogenera | F16 `15` |

**Decisión SC-DEF-04:** Flags derivables de `policy` se **denuncian explícitamente** en catálogo para evitar inferencia en runtime.

---

## 6. Defaults de formato (semilla cfg)

| Campo | Obligatorio | Descripción | Justificación |
|-------|-------------|-------------|---------------|
| **default_prefix** | Sí* | Prefijo seed (*vacío permitido en numérico puro) | Lazy-create cfg |
| **default_separator** | Sí | `''` o `'-'` | Formato humano |
| **default_padding** | Sí | Longitud parte numérica (ej. 3, 6) | Padding |
| **numero_inicial** | Sí | Primer número (típico 1; onboarding usa 0 → primer emitido 1) | F16 `14` |
| **max_output_length** | Sí | Máx. caracteres; = columna V010 | Validator |
| **normalize_case** | Sí | `UPPER` maestros; `AS_IS` fiscal numérico | F15A FP-01 |

---

## 7. Edición y ciclo de vida

| Campo | Valor oficial | Fuente |
|-------|---------------|--------|
| **editable_before_usage** | **`false`** | **BR-IMM-01** (BR-M-31 DEPRECATED) |
| **editable_after_usage** | **`false`** | **BR-IMM-01** (BR-M-30 SUPERSEDED) |
| **immutable_after_allocate** | **`true`** para toda entidad Motor | **BR-IMM-01…05** |

**Decisión SC-DEF-05 (rev. 2026-07-13):** El catálogo documenta expectativa de **inmutabilidad total post-CREATE**. El enforcement runtime está en **servicios ERP + schemas Update** (no en Gateway, no en cfg BD). Ver ADR `code-immutability/`.

---

## 8. Dimensiones de contexto requeridas

| Campo | Descripción |
|-------|-------------|
| **required_context** | Lista: `client_id`, `empresa_id`, `almacen_id`, `punto_venta_id`, `serie_id` |
| **scope_dimensions** | Subconjunto activo según `scope_type` |

Evita duplicar lógica en ScopeResolver: lee `required_context` del catálogo.

---

## 9. Campos evaluados y descartados

| Campo propuesto | Veredicto | Motivo |
|-----------------|-----------|--------|
| `entity` / `entidad` | Deprecado | Reemplazado por `sequence_key` |
| `resource` | Rechazado | Colisión RBAC |
| `formatter` (inline) | Rechazado | Usar `formatter_profile` |
| `parser` (inline) | Rechazado | Usar `parser_profile` |
| `validator` (inline) | Rechazado | Usar `validator_profile` |
| `preview_enabled` | Renombrado | → `supports_preview` |
| `editable_*` en cfg BD | Rechazado en cfg | Solo en catálogo |
| `politica` en cfg BD | Rechazado | Solo catálogo |
| `algorithm` | Fuera F16A | Implementación |
| `rbac_permission` | Fuera catálogo | Servicio ERP |

---

## 10. Plantilla conceptual de una entrada

```
SequenceDefinition
├── Identidad
│   ├── sequence_key
│   ├── table_name
│   ├── code_column
│   ├── modulo_codigo
│   └── documentation
├── Clasificación
│   ├── policy
│   ├── sequence_family
│   ├── scope_type
│   └── store_type
├── Perfiles
│   ├── formatter_profile
│   ├── parser_profile
│   └── validator_profile
├── Capacidades
│   ├── motor_enabled
│   ├── supports_preview
│   ├── allow_manual
│   ├── align_on_manual
│   ├── supports_high_water
│   ├── supports_import
│   └── consumes_counter_on_allocate
├── Defaults
│   ├── default_prefix
│   ├── default_separator
│   ├── default_padding
│   ├── numero_inicial
│   ├── max_output_length
│   └── normalize_case
├── Contexto
│   └── required_context[]
└── Ciclo de vida
    ├── editable_before_usage = false   # BR-IMM-01
    ├── editable_after_usage = false    # BR-IMM-01
    └── immutable_after_allocate = true # BR-IMM-01…05
```

---

## 11. Consistencia entre campos (reglas de validación del catálogo)

| Regla | Validación |
|-------|------------|
| V-01 | `policy=AUTO_REQUIRED` → `allow_manual=false`, `supports_preview=false` |
| V-02 | `policy=AUTO_DEFAULT` → `allow_manual=true` |
| V-03 | `scope_type=SERIE_FISCAL` → `store_type=FISCAL` |
| V-04 | `scope_type≠SERIE_FISCAL` → `store_type=CFG` |
| V-05 | `sequence_family=F3` → `store_type=FISCAL` |
| V-06 | `max_output_length` ≤ longitud columna V010 documentada |
| V-07 | `default_prefix` length ≤ 10 (diseño F16 `14`) |
| V-08 | `supports_preview=true` solo si `policy=AUTO_DEFAULT` |

Estas reglas se automatizan en CI (fase implementación).

---

*Perfiles en `20`. Matriz completa en `21`.*
