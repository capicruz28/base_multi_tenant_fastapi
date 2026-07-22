# F15A — Buenas prácticas ERP y patrones de mercado

**Fase:** F15A — Política funcional  
**Fecha:** 2026-07-02  
**Propósito:** Benchmark conceptual (no copia de implementación) para validar las políticas CAXIS frente a ERP modernos.

---

## 1. Patrón dominante: Number Series / Document Sequences

Todos los ERP analizados separan **tres conceptos** que CAXIS F15/F15A ya adoptan:

| Concepto | Descripción | Equivalente CAXIS |
|----------|-------------|-------------------|
| **Number Series** | Tabla de configuración por tipo de documento/maestro, empresa y periodo | `cfg_codigo_secuencia` (+ extensiones scope F15) |
| **Master Data Code** | Identificador de artículo, cliente, proveedor | Maestros AUTO_DEFAULT |
| **Legal Numbering** | Series fiscales aisladas con reglas estrictas | `invbill_serie_comprobante` + AUTO_REQUIRED emisión |

**Conclusión:** el estándar CAXIS de familias F1–F5 (`05_PROPOSED_ARCHITECTURE.md`) está alineado con el mercado.

---

## 2. SAP Business One

### 2.1 Patrones observados

- **Series de numeración** por tipo de documento (Marketing Documents, Inventory, Production).
- Cada serie define: primer número, último número, prefijo, tipo de documento.
- Los maestros (ítem, socio de negocio) tienen **código alfanumérico** asignado manualmente o por serie dedicada.
- La numeración fiscal en localizaciones (Perú/Latam vía localización) respeta autoridad tributaria; series bloqueadas tras emisión.

### 2.2 Comparación CAXIS

| Aspecto | SAP B1 | CAXIS F15A |
|---------|--------|------------|
| Documentos | Serie obligatoria; usuario no tipea correlativo en venta estándar | AUTO_REQUIRED — alineado |
| Maestros | Manual o serie; común en migraciones | AUTO_DEFAULT — alineado |
| Multiempresa | Series por empresa | Scope empresa — alineado |
| Huecos en numeración | Aceptados salvo requisito legal estricto | BR-S-01 — alineado |
| Reinicio anual | Configurable por serie | No por defecto — alineado |

### 2.3 Lección para CAXIS

No mezclar series de inventario con series fiscales. Mantener submotor fiscal (F3) separado de `cfg` genérica.

---

## 3. Microsoft Dynamics 365 Business Central

### 3.1 Patrones observados

- **No. Series** por línea de documento (Sales, Purchase, Warehouse, GL).
- Asignación automática al crear documento; campos visibles pero no editables en flujo estándar.
- **Nos.** en maestros (Item No., Vendor No.) con política configurable: manual, secuencia o específica por plantilla.
- Fuerte énfasis en **inmutabilidad** del número de documento publicado; correcciones vía documentos de cancelación/abono.

### 3.2 Comparación CAXIS

| Aspecto | Business Central | CAXIS F15A |
|---------|------------------|------------|
| Correlativo en borrador | Asignado al crear | BR-D-02 — alineado |
| Cancelación | Nuevo documento de reversión | BR-D-04 — alineado |
| Preview | Muestra próximo sin confirmar en algunos flujos | Opcional con advertencia — alineado |
| Dimensiones | Company + serie | empresa_id + serie — alineado |

### 3.3 Lección para CAXIS

La política de **documento compensatorio con nuevo número** es estándar de mercado; refuerza BR-D-04 y prohibición de concatenación entre módulos.

---

## 4. Oracle NetSuite

### 4.1 Patrones observados

- **Auto-Generated Numbering** en transacciones (Sales Order, Invoice, PO) por subsidiaria (multi-subsidiary ≈ multiempresa).
- **Numbering Sequence** configurable por tipo de registro y subsidiaria.
- Maestros: SKU/ID con autonumeración opcional o entrada manual.
- Registros publicados (Posted) bloquean cambios de identificadores clave.

### 4.2 Comparación CAXIS

| Aspecto | NetSuite | CAXIS F15A |
|---------|----------|------------|
| Scope | Subsidiary | empresa_id — alineado |
| SaaS multi-tenant | Aislamiento por cuenta | cliente_id — alineado |
| Edición código | Bloqueada **desde CREATE** | **BR-IMM-01** — alineado (más estricto que “post-uso”) |
| Import CSV | Permite External ID + número | Reglas importación §7 `07` — alineado |

### 4.3 Lección para CAXIS

En importaciones masivas, distinguir **identificador externo de migración** (puede ser UUID o código legado) del **código operativo** que ve el usuario — sin mezclarlos en la misma política.

---

## 5. Odoo

### 5.1 Patrones observados

- **Secuencias** (`ir.sequence`) por tipo de documento con prefijo, padding y próximo número.
- Secuencias por **diario** (journal) en contabilidad — análogo a serie fiscal/contable.
- Productos: `default_code` (referencia interna) manual o automatizada vía secuencia dedicada.
- El usuario puede ver el próximo número en configuración técnica; en UI de usuario final el flujo es automático.

### 5.2 Comparación CAXIS

| Aspecto | Odoo | CAXIS F15A |
|---------|------|------------|
| Configuración secuencias | Admin técnico | Futuro rol `cfg.secuencias` — pendiente Fase 2 |
| Documentos | Automático | AUTO_REQUIRED — alineado |
| Multi-company | Secuencias por company | Scope empresa — alineado |
| Flexibilidad | Alta; riesgo de desconfiguración | Prefijos editables con BR-P — equilibrio |

### 5.3 Lección para CAXIS

Odoo demuestra que la **flexibilidad excesiva** en secuencias genera deuda operativa. CAXIS debe permitir configurar prefijos pero **no** políticas base (AUTO_REQUIRED en documentos).

---

## 6. Tabla comparativa transversal

| Patrón | SAP B1 | Dynamics BC | NetSuite | Odoo | **CAXIS F15A** |
|--------|--------|-------------|----------|------|----------------|
| Secuencias por empresa | ✅ | ✅ | ✅ | ✅ | ✅ |
| Documento auto-numerado | ✅ | ✅ | ✅ | ✅ | ✅ AUTO_REQUIRED |
| Maestro auto opcional | ✅ | ✅ | ✅ | ✅ | ✅ AUTO_DEFAULT |
| Series fiscales aisladas | ✅ | ✅ | ✅ | ✅ | ✅ F3 |
| Inmutabilidad post-CREATE | ✅* | ✅* | ✅* | ○ | ✅ **BR-IMM-01** |
| Reversión = nuevo número | ✅ | ✅ | ✅ | ✅ | ✅ BR-D-04 |
| Huecos permitidos | Generalmente sí | Sí | Sí | Sí | Sí (no fiscal arbitrario) |
| Preview próximo | Limitado | Limitado | Limitado | Admin | Opcional maestros |
| Reinicio secuencia | Excepcional | Excepcional | Excepcional | Posible | Excepcional BR-S |

\* En SAP / Dynamics / NetSuite la práctica dominante es identificador de negocio estable; el umbral exacto (create vs posted) varía. CAXIS adopta el umbral más estricto y uniforme: **post-CREATE** (**BR-IMM-01**).

---

## 7. Patrones que CAXIS NO debe adoptar

| Anti-patrón en mercado | Por qué evitarlo en CAXIS |
|------------------------|---------------------------|
| Correlativo manual en factura estándar | Riesgo fiscal y duplicados |
| Un solo contador global para todos los documentos | Imposible auditar por módulo |
| Reutilizar número anulado sin norma | Problema legal y de auditoría |
| Código de producto = correlativo de documento | Confusión operativa |
| Concatenar números entre módulos (`PED-{cot}`) | Ya identificado como deuda en F15 AS-IS |

---

## 8. Patrones recomendados explícitamente para CAXIS

1. **Number Series por entidad lógica y scope** (empresa, almacén, PV, serie fiscal).
2. **AUTO_REQUIRED universal** en documentos de proceso.
3. **AUTO_DEFAULT** en maestros con validación de unicidad en manual.
4. **EXTERNAL** estricto para legales y catálogos globales.
5. **Inmutabilidad** del código tras primer uso operativo.
6. **Importación con preservación** de históricos + alineación de contador.
7. **Separación fiscal** de secuencia operativa interna.

---

## 9. Posicionamiento CAXIS

CAXIS adopta el **consenso de mercado** (secuencias por empresa, documentos automáticos, fiscal aislado) con énfasis en:

- **Multi-tenant SaaS** (aislamiento `cliente_id`) — igual que NetSuite a nivel cuenta.
- **Hybrid platform** (shared/dedicated) sin cambiar reglas de negocio — igual que BC cloud con múltiples entornos.
- **Convivencia migración** vía AUTO_DEFAULT + importación — práctica común en implantaciones SAP/Odoo.

---

## 10. Referencias internas

| Documento | Uso |
|-----------|-----|
| `07_BUSINESS_RULES.md` | Reglas operativas |
| `08_CODE_POLICIES.md` | Matriz AUTO_* / MANUAL / EXTERNAL |
| `10_FINAL_RECOMMENDATION.md` | Estándar oficial consolidado |

---

*Benchmark conceptual. No constituye decisión de licenciamiento ni copia de diseño de terceros.*
