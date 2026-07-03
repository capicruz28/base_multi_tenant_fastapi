# F16A — Familias de secuencia (sequence_family)

**Fase:** F16A  
**Fecha:** 2026-07-03  
**Base:** F16 familias F1–F5; alternativas MASTER/DOCUMENT/FISCAL/EXTERNAL/MANUAL

---

## 1. Dos ejes ortogonales

El motor opera con **dos clasificaciones independientes** que no deben mezclarse:

| Eje | Campo | Propósito | Valores |
|-----|-------|-----------|---------|
| **Negocio (política)** | `policy` | Quién provee el código | AUTO_REQUIRED, AUTO_DEFAULT, MANUAL_ONLY, EXTERNAL |
| **Técnico (familia)** | `sequence_family` | Cómo se enruta y formatea | F1–F5 |

**Decisión SC-FAM-01:** EXTERNAL y MANUAL_ONLY son **políticas**, no familias. Las entidades EXTERNAL/MANUAL_ONLY excluidas del motor **no tienen** `sequence_family`.

---

## 2. Alternativas evaluadas

### 2.1 Propuesta A — F1–F5 (F16)

| Código | Nombre F16 | Enfoque |
|--------|------------|---------|
| F1 | Maestro | cfg, prefijo+numérico |
| F2 | Documento | cfg, correlativo |
| F3 | Fiscal | store fiscal |
| F4 | WMS | cfg, scope almacén |
| F5 | POS | cfg, scope punto venta |

### 2.2 Propuesta B — MASTER / DOCUMENT / FISCAL / EXTERNAL / MANUAL

| Código | Enfoque |
|--------|---------|
| MASTER | Maestros |
| DOCUMENT | Transacciones |
| FISCAL | Legal |
| EXTERNAL | Fuera motor |
| MANUAL | Sin secuencia |

### 2.3 Comparación

| Criterio | F1–F5 | MASTER/DOCUMENT/… |
|----------|-------|-------------------|
| Alineación F16 congelado | ✅ Directa | ❌ Replanteamiento |
| Separa scope WMS/POS | ✅ F4, F5 | ❌ Todo MASTER/DOCUMENT |
| EXTERNAL/MANUAL en familia | ❌ Mezcla ejes | ⚠️ Confunde con policy |
| Extensibilidad store | ✅ F3 aislado | ✅ FISCAL aislado |
| Claridad negocio | Media | Alta para negocio |
| Claridad técnica | Alta | Media |

---

## 3. Decisión oficial

**Se adopta F1–F5 como `sequence_family` estándar**, con nombres canónicos bilingües documentales:

| Código oficial | Nombre canónico | Alias legado F16 |
|----------------|-----------------|------------------|
| **F1** | `MASTER` | Maestro |
| **F2** | `DOCUMENT` | Documento |
| **F3** | `FISCAL` | Fiscal |
| **F4** | `WAREHOUSE` | WMS / Almacén |
| **F5** | `POS` | Punto de venta |

**Decisión SC-FAM-02:** En artefactos técnicos se usa el código **F1–F5**; en documentación funcional puede usarse el nombre canónico entre paréntesis.

**Decisión SC-FAM-03:** No se usa familia `EXTERNAL` ni `MANUAL` en catálogo activo.

---

## 4. Mapeo familia → comportamiento técnico

| Familia | store_type | scope típico | Formatter | Parser | Preview |
|---------|------------|--------------|-----------|--------|---------|
| **F1 MASTER** | CFG | TENANT, EMPRESA | FMT_STANDARD | PAR_PREFIX_NUM | Sí |
| **F2 DOCUMENT** | CFG | EMPRESA | FMT_STANDARD | PAR_PREFIX_NUM o PAR_NUM_ONLY | No |
| **F3 FISCAL** | FISCAL | SERIE_FISCAL | FMT_FISCAL_8 | PAR_NONE | No |
| **F4 WAREHOUSE** | CFG | ALMACEN | FMT_STANDARD | PAR_PREFIX_NUM | Sí |
| **F5 POS** | CFG | PUNTO_VENTA, EMPRESA | FMT_STANDARD | PAR_PREFIX_NUM | No* |

\* `pos_punto_venta` (F1) preview sí; `pos_turno_caja` (F5) preview no.

---

## 5. Ventajas de F1–F5

1. **Ya aprobado en F16** — sin replantear arquitectura.
2. **Distingue scope operativo** (almacén, PV) sin duplicar política.
3. **Fiscal aislado** — obligatorio por SUNAT.
4. **Olas de implementación** alineadas (`16` roadmap).
5. **Extensible** — F6+ reservado (ej. `PROYECTO` si aparece scope nuevo).

---

## 6. Desventajas y mitigaciones

| Desventaja | Mitigación |
|------------|------------|
| Códigos opacos (F1, F2) | Nombre canónico en documentación y matriz |
| Solapamiento F1/F2 (mismo formatter) | Perfiles compartidos en `20` |
| F4 y F1 ambos maestros | F4 marca scope ALMACEN obligatorio |
| No expresa política | Campo `policy` separado |

---

## 7. Relación policy × family (matriz permitida)

| policy | Familias permitidas |
|--------|---------------------|
| AUTO_REQUIRED | F2, F3, F5 |
| AUTO_DEFAULT | F1, F4 |
| MANUAL_ONLY | — (sin entrada catálogo) |
| EXTERNAL | — (sin entrada catálogo) |

---

## 8. Evolución futura

| Necesidad | Acción |
|-----------|--------|
| Nueva familia técnica | Agregar F6+ con ADR; no reciclar EXTERNAL |
| Mismo formatter nuevo dominio | Nueva familia solo si cambia store o scope |
| Unificar F1 y F2 | **No recomendado** — políticas y preview difieren |

---

*Matriz por entidad en `21`. Perfiles en `20`.*
