# Impacto en código existente (V1)

**Documento:** Fase D1 · 03  
**Serie:** CORE ERP V2 — Auditoría de evolución  
**Base:** módulos en `app/modules/*` + madurez declarada del proyecto

---

## 1. Principio de impacto

> Preferir cambios **aditivos** (campos nuevos, endpoints nuevos, servicios nuevos) sobre reescritura de flujos ya probados.

Especialmente en **INV / ORG / CFG / IAM**.

---

## 2. Matriz de impacto por área

| Área | Madurez V1 | Cambios V2 esperados | Riesgo | Estrategia de preservación |
|------|------------|----------------------|--------|----------------------------|
| `auth` / `rbac` / `users` / `tenant` | Muy alta | Ninguno estructural | Bajo | No tocar |
| `cfg` | ~99% | + vertical empresa; secuencias intactas | Bajo | Endpoint nuevo; no romper `cfg_codigo_secuencia` |
| `org` / `catalogos` | ~99% | Ninguno / cosmético | Bajo | Conservar session scope |
| `inv` | ~99% | Lote AR, stock, variantes, `lote_id` | **Alto** | Aditivo: `lote_id` junto a `lote` hasta enforcement; no reescribir estorno/movimientos de golpe |
| `wms` | Media | Oleada, estrategia, `lote_id` | Medio | Extender schemas/endpoints tarea |
| `qms` | Media | `lote_id` | Medio | Extender inspección/NC |
| `pur` | Alta | `lote_id` en recepción | Medio | Extender detalle recepción; pipeline OC intacto |
| `mfg` | Media | `lote_id` consumo; no OEE | Medio | Conservar BOM/OP; MES aparte |
| `invbill` / `pos` | Media | `lote_id` en detalle | Medio–bajo | Extender schemas |
| `sls` / `prc` / `crm` | Media | SKU/variante lectura | Bajo | Sin rediseño de pedido |
| `log` | Media | Consumir eventos / refs | Bajo | Conservar guías |
| `mrp` / `mps` | Media | `empresa_id` en MRP | Medio | Fix de integridad; queries |
| `hcm` / `mnt` / `fin` / otros | Variable | Integración posterior | Bajo | Conservar |
| MES / PLN / EVT / ALR | Ausente o mínimo | Módulos nuevos | N/A (código nuevo) | No reescribe V1 |

---

## 3. Hotspots INV (detalle)

Archivos/contratos sensibles detectados:

- `app/modules/inv/presentation/schemas.py` — `lote`, `color`, `talla`, `maneja_lotes`
- `movimiento_service.py` / `inv_estorno_proceso.py` — propagan `lote` string
- `inventario_fisico_*` — `lote` en detalles
- Endpoints de stock — asumen unicidad producto+almacén

**Plan de evolución de código (conceptual, no implementación):**

1. Introducir `lote_id` en schemas Create/Update/Read (opcional).
2. Servicios: si viene `lote_id`, usarlo; si solo `lote` texto, compatibilidad temporal o rechazo según flag de enforcement.
3. Stock service: evolucionar clave a producto+almacén(+lote).
4. `color`/`talla`: deprecar semánticamente hacia ejes de variante; no borrar de inmediato.

---

## 4. Qué no se reescribe

- Saga/onboarding tenant (salvo seed CFG vertical si aplica)
- Motor de secuencias CFG
- Session scope ORG/INV
- Pipeline PUR solicitud→OC
- Contabilidad FIN básica
- HCM planilla

---

## 5. Módulos nuevos (código a crear, no a reescribir)

| Módulo código | Origen |
|---------------|--------|
| `mes` (nuevo) | BC MES |
| `pln` (nuevo) o servicios bajo namespace PLN | BC PLN |
| `alr` (nuevo) | BC ALR |
| infraestructura `evt` / outbox en `app/core` o módulo | BC EVT |

Recomendación: **no** meter MES dentro de `app/modules/mfg/` como subcarpeta eterna; respetar BC (puede compartir package monorepo pero bounded).

---

## 6. Criterio de aceptación de un cambio de código V2

1. ¿Es aditivo sobre un flujo V1 en prueba?  
2. ¿Evita tabla nueva injustificada?  
3. ¿Respeta BC dueño?  
4. ¿Emite/consumirá eventos del catálogo 0.5 sin acoplar UI?  

Si falla (1) en INV/ORG/CFG/IAM → requiere justificación explícita en D1.1.
