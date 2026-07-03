# F16B — Análisis de excepciones reales

**Fase:** F16B — Auditoría final de validación  
**Fecha:** 2026-07-03  
**Alcance:** Solo excepciones **documentadas y verificables** en F15–F16A o V010. Sin escenarios inventados.

---

## 1. Criterio de inclusión

Se documenta una excepción solo si:

1. Está explícita en reglas de negocio o diseño congelado, **o**
2. Es impuesta por el DDL V010 actual de forma que el motor no puede tratarla como caso estándar.

---

## 2. Excepciones de negocio (confirmadas)

### EX-01 — Primera empresa bootstrap `EMP001`

| Atributo | Valor |
|----------|-------|
| **Entidad** | `org_empresa` |
| **Regla** | BR-M-02 (F15A `07`) |
| **Comportamiento** | La primera empresa puede crearse con código fijo de onboarding sin allocate |
| **Scope** | TENANT |
| **Tratamiento motor** | Servicio ORG puede omitir `allocate` en bootstrap; empresas subsecuentes usan motor |
| **Riesgo si ignorada** | Bajo; caso único por tenant |

---

### EX-02 — Importación histórica con correlativo explícito

| Atributo | Valor |
|----------|-------|
| **Entidades** | Documentos AUTO_REQUIRED (grupo C) |
| **Regla** | F15A `08` §1.1, BR-M-40/41 |
| **Comportamiento** | Rol implantación puede persistir `numero_*` histórico sin consumir contador en allocate normal |
| **Tratamiento motor** | Modo `IMPORT_HISTORICAL`; `align_on_manual` / high-water al cierre de lote (`align=import` en matriz `21`) |
| **Riesgo si ignorada** | Alto — colisiones post-migración |

---

### EX-03 — Manual alto sin consumo (high-water)

| Atributo | Valor |
|----------|-------|
| **Entidades** | Maestros AUTO_DEFAULT |
| **Regla** | TD-MAN-01/02 (F16 `15`) |
| **Escenario canónico** | Contador 20, usuario crea `CLI999` |
| **Tratamiento** | `CounterAlignmentService` + `CodeParser` PAR_PREFIX_NUM |
| **Riesgo si ignorada** | Alto — siguiente auto generaría duplicado lógico |

---

### EX-04 — `wms_ubicacion` códigos semánticos no estándar

| Atributo | Valor |
|----------|-------|
| **Entidad** | `wms_ubicacion` |
| **Regla** | F16A `21` nota; `align=partial` |
| **Comportamiento** | Códigos tipo `A-01-03` predominan; high-water solo si parseable |
| **Tratamiento** | `VAL_UBICACION`; parser partial; manual libre predominante |
| **Riesgo si ignorada** | Medio — align incorrecto en ubicaciones semánticas |

---

### EX-05 — `fin_plan_cuentas` jerárquico sin prefijo

| Atributo | Valor |
|----------|-------|
| **Entidad** | `fin_plan_cuentas` |
| **Regla** | BR-M-03; `default_prefix` vacío en `21` |
| **Comportamiento** | Códigos contables tipo `101`, `60111` sin prefijo alfanumérico |
| **Tratamiento** | AUTO_DEFAULT con manual frecuente en implantación; high-water solo si parte numérica final parseable |
| **Riesgo si ignorada** | Medio en migraciones contables; bajo en operación estándar autogenerada |

---

### EX-06 — Alta de serie fiscal MANUAL_ONLY

| Atributo | Valor |
|----------|-------|
| **Entidad** | `invbill_serie_comprobante.serie` |
| **Regla** | BR-M-05; F15A MANUAL_ONLY |
| **Comportamiento** | Usuario registra serie autorizada SUNAT; motor no allocate en alta |
| **Tratamiento** | Fuera del catálogo; emisión `invbill_comprobante.numero` sí usa motor F3 |
| **Riesgo si ignorada** | Alto legal/fiscal |

---

### EX-07 — Estorno / patrones legacy INV

| Atributo | Valor |
|----------|-------|
| **Entidad** | `inv_movimiento` (AS-IS) |
| **Regla** | F15 `04`, F16 `16` INC-07 |
| **Comportamiento actual** | `INV-EST-{timestamp}` en runtime |
| **Tratamiento objetivo** | Allocate compensatorio AUTO_REQUIRED (Ola 1) |
| **Riesgo si ignorada** | Medio operativo; no arquitectónico |

---

## 3. Excepciones técnicas impuestas por V010

### EX-08 — `log_guia_remision` sin store serie dedicado

| Atributo | Valor |
|----------|-------|
| **Entidad** | `log_guia_remision` |
| **Hecho V010** | `serie NVARCHAR(4)` en cabecera; UNIQUE `(cliente_id, empresa_id, serie, numero)`; **no** existe tabla serie guía ni `serie_id` |
| **Diseño F16A** | F3, SERIE_FISCAL, FISCAL store |
| **Contraste** | `invbill_comprobante` tiene tabla contador `invbill_serie_comprobante` |
| **Tratamiento requerido** | Decisión Ola 4 (INC-10): extensión tabla serie guía, adaptador FiscalSeriesStore sobre cfg por `(empresa_id, serie)`, o contador en servicio hasta DDL |
| **Clasificación** | Excepción real; **no** caso estándar F3 |

---

### EX-09 — Resolución `serie_id` en emisión fiscal comprobante

| Atributo | Valor |
|----------|-------|
| **Entidad** | `invbill_comprobante` |
| **Hecho V010** | Cabecera almacena `serie` texto; contador en `invbill_serie_comprobante` por `serie_id` |
| **Diseño** | `GenerationContext.serie_id` obligatorio en SERIE_FISCAL |
| **Tratamiento** | Servicio emisión resuelve `serie_id` desde selección UI antes de gateway; no es excepción de catálogo sino de capa servicio |
| **Riesgo si ignorada** | Alto en emisión |

---

### EX-10 — Seed onboarding cfg desalineado

| Atributo | Valor |
|----------|-------|
| **Ámbito** | `cfg_codigo_secuencia` AS-IS |
| **Hecho** | INC-01, INC-02 (F16 `16`) |
| **Comportamiento** | `empresa_id=NULL` en seeds empresa-scoped; nombre `inv_categoria` obsoleto |
| **Tratamiento** | Migración Ola 0; no excepción permanente del motor |
| **Riesgo si ignorada** | P0 en implementación |

---

## 4. Excepciones explícitamente NO aplicables

| Escenario evaluado | Veredicto | Motivo |
|--------------------|-----------|--------|
| Preview como reserva | No aplica | Prohibido por F15A y F16 `15` |
| Override política por tenant | No aplica | Prohibido TA-11 / D-11 |
| Secuencia anual automática | No aplica | Fuera V1; excluido en `14` |
| `pos_venta` mismo número en distintos PV | No excepción | V010 UNIQUE por PV lo permite; motor empresa-scoped evita colisión numérica global |
| Dual-write cfg central + dedicated | No aplica | Prohibido R-08 |

---

## 5. Matriz excepción × componente

| ID | Gateway | Parser | Align | FiscalStore | Servicio ERP |
|----|---------|--------|-------|-------------|--------------|
| EX-01 | Omisión bootstrap | — | — | — | ORG onboarding |
| EX-02 | `IMPORT_HISTORICAL` | ✓ | ✓ | — | Rol implantación |
| EX-03 | allocate manual | ✓ | ✓ | — | — |
| EX-04 | estándar | partial | partial | — | — |
| EX-05 | estándar | limitado | limitado | — | Implantación FIN |
| EX-06 | excluido catálogo | — | — | — | Alta serie manual |
| EX-07 | allocate | — | — | — | Sustitución legacy |
| EX-08 | rama F3 | PAR_NONE | no | **pendiente diseño store** | Ola 4 |
| EX-09 | allocate | — | — | ✓ | Resuelve serie_id |
| EX-10 | — | — | align MAX | — | Migración Ola 0 |

---

## 6. Conclusión

Existen **10 excepciones reales** documentadas. Ninguna invalida el contrato del catálogo en su totalidad. **EX-08** es la única excepción técnica que requiere decisión de store antes de Ola 4; las demás tienen tratamiento definido en F16/F16A.

---

*Gaps clasificados en `26`. Veredicto en `27`.*
