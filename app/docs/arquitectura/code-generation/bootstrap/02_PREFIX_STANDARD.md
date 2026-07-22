# F17A — Estándar oficial de prefijos y nomenclatura

**Fase:** F17A — Bootstrap oficial
**Fecha:** 2026-07-03
**Base:** `01_SEQUENCE_DEFAULT_CONFIGURATION.md`, `SequenceCatalog` v1.0.0

> Documento normativo de convenciones. **No modifica** el catálogo. Explica *por qué* los prefijos por defecto son intuitivos y cómo el cliente puede personalizarlos sin romper la arquitectura.

---

## 1. Principios de nomenclatura

| ID | Regla | Motivo |
|----|-------|--------|
| **PFX-01** | Prefijo en **MAYÚSCULAS**, alfanumérico ASCII (`A–Z`, `0–9`) | Consistencia con `normalize_upper` de schemas ORG/INV; legibilidad |
| **PFX-02** | Longitud recomendada **2–4 caracteres** | Códigos compactos y escaneables; margen NVARCHAR(10) |
| **PFX-03** | Derivado de la **entidad de negocio**, no de la tabla técnica | Intuitivo para el usuario final (`OC` = orden de compra) |
| **PFX-04** | **Sin separador** por defecto (`∅`) | Código contiguo tipo `MOV000001`; menos ruido visual |
| **PFX-05** | Prefijo **vacío** permitido solo en códigos numéricos por norma (contable/fiscal/semántico) | `fin_plan_cuentas`, `wms_ubicacion`, fiscal |
| **PFX-06** | El prefijo **no** codifica empresa/almacén/PV | El scope ya aísla la secuencia; duplicar la dimensión en el prefijo es redundante |
| **PFX-07** | El prefijo **no** incluye año ni periodo | Reinicio por periodo excluido en V1 (F16 `14`) |

---

## 2. Convención de derivación del prefijo

| Patrón | Aplicación | Ejemplos |
|--------|------------|----------|
| **Sigla de proceso** (documentos) | Acrónimo del tipo de documento | `OC` orden compra, `PED` pedido, `MOV` movimiento, `OT` orden trabajo |
| **Sigla de maestro** | Acrónimo de la entidad maestra | `PROV` proveedor, `CLI` cliente, `ALM` almacén, `CAT` categoría |
| **Inicial + numérico** | Maestros de alta cardinalidad | `P` producto (SKU) |
| **Sin prefijo** | Norma externa/semántica | plan de cuentas, ubicación WMS, número fiscal |

**Longitud numérica (padding) por tipo:**

| Tipo | Padding estándar | Capacidad antes de expandir |
|------|------------------|-----------------------------|
| Maestros baja cardinalidad (ORG, config) | 3 | 999 |
| Maestros media cardinalidad | 4 | 9 999 |
| Maestro producto (SKU) | 5 | 99 999 |
| Documentos | 6 | 999 999 |
| POS turno | 4 | 9 999 por PV |
| Fiscal (legal) | 8 | 99 999 999 (norma SUNAT) |

---

## 3. Referencia conceptual a ERP comerciales

*Solo comparación de convenciones; no se copia implementación.*

| ERP | Convención observada | Alineación CAXIS |
|-----|----------------------|------------------|
| **SAP B1** | Series por documento y sucursal; numeración configurable con prefijo | Scope EMPRESA + prefijo por `sequence_key` ✅ |
| **Dynamics 365 BC** | "No. Series" con código, descripción y último usado | `cfg_codigo_secuencia` (prefijo + `ultimo_numero`) ✅ |
| **Oracle / NetSuite** | Auto-numbering por tipo con prefijo + relleno de ceros | FMT_STANDARD `{prefijo}{num:0pad}` ✅ |
| **Odoo** | `ir.sequence` con `prefix`, `padding`, `number_next` | Equivalencia directa: prefijo/padding/numero_inicial ✅ |

**Conclusión:** los prefijos por defecto (`OC`, `PED`, `MOV`, `CLI`, `PROV`, …) coinciden con las siglas que un usuario ERP reconoce; el formato `{PFX}{ceros}{N}` es el patrón universal.

---

## 4. Solapamientos de prefijo (transparencia)

Existen prefijos por defecto repetidos entre entidades **distintas**. Son **técnicamente correctos** (la unicidad es por `tabla + scope + fingerprint`, nunca por prefijo global) y ya fueron aceptados en F16B GAP-P2-03.

| Prefijo | Entidades | Diferenciador |
|---------|-----------|---------------|
| `EMP` | `org_empresa` (TENANT, pad 3), `hcm_empleado` (EMPRESA, pad 4) | Longitud (`EMP001` vs `EMP0001`) + scope |
| `OP` | `mfg_operacion` (maestro, pad 3), `mfg_orden_produccion` (documento, pad 6) | Longitud (`OP001` vs `OP000001`) + familia |
| `CC` | `org_centro_costo` (pad 3), `pur_cotizacion` (pad 6) | Longitud + módulo |
| `PRE` | `bdg_presupuesto` (pad 4), `hcm_prestamo` (pad 6) | Longitud + módulo |

**Regla oficial (PFX-08):** los solapamientos son **aceptables en el estándar por defecto**. Si un cliente desea eliminarlos por preferencia visual, puede personalizar el prefijo del maestro o documento afectado (§5). CAXIS **no** modifica el catálogo por este motivo.

**Sugerencias opcionales de desambiguación** (a criterio del cliente, no obligatorias):

| Entidad | Prefijo alternativo sugerido |
|---------|------------------------------|
| `hcm_empleado` | `COL` (colaborador) |
| `pur_cotizacion` | `COC` (cotización compra) |
| `hcm_prestamo` | `PRT` (préstamo) |
| `mfg_orden_produccion` | `OPR` (orden producción) |

---

## 5. Personalización por cliente

| Aspecto | ¿Personalizable? | Cómo |
|---------|------------------|------|
| `prefijo` | ✅ Sí | Admin de secuencias (Ola 6) o pre-carga de seed dedicada |
| `longitud_numero` | ✅ Sí | Solo si no reduce por debajo de códigos ya emitidos |
| `separador` | ✅ Sí | `∅` → `-` u otro de 1 carácter |
| `numero_inicial` | ✅ Sí | Solo antes del primer consumo o vía migración validada |
| `policy` / `scope` / `family` | ❌ No | Propiedad del catálogo (inmutable por tenant) |

**Restricción de personalización (PFX-09):** cambiar prefijo/padding **no** reescribe códigos ya emitidos; aplica solo a asignaciones futuras. La coherencia histórica se preserva (**BR-IMM-01**, inmutabilidad desde CREATE).

---

## 6. Reglas de validación del prefijo

Heredadas de los perfiles Validator (`20`), no se redefinen aquí:

| Perfil | Charset código | Nota prefijo |
|--------|----------------|--------------|
| `VAL_MASTER` | `[A-Z0-9_-]` | Prefijo alfanumérico |
| `VAL_DOCUMENT` | `[A-Z0-9_-]` | Prefijo alfanumérico |
| `VAL_UBICACION` | `[A-Z0-9_-]` | Permite `-` semántico; prefijo puede ser ∅ |
| `VAL_FISCAL_NUM` | `[0-9]` | Sin prefijo; número puro |

---

## 7. Checklist de aprobación de un prefijo nuevo (gobernanza futura)

Al agregar una entidad al catálogo (proceso `22`), el prefijo debe:

- [ ] Estar en MAYÚSCULAS, 2–4 caracteres (o ∅ justificado)
- [ ] Ser mnemotécnico de la entidad de negocio
- [ ] No introducir separador por defecto
- [ ] No codificar scope, empresa ni periodo
- [ ] Documentar cualquier solapamiento aceptado
- [ ] Respetar `max_output_length` de la columna V010

---

*Configuración completa en `01`. Reglas de poblado en `03`. Plan de seed en `04`.*
