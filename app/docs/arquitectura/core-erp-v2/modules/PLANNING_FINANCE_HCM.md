# Auditoría modular — MRP / MPS / MNT / FIN / TAX / CST / BDG / HCM

**Prioridad global:** P2–P3 (deuda / correcciones)

---

## MRP / MPS

| Campo | Contenido |
|-------|-----------|
| Estado actual | Básico |
| Fortalezas | Esqueleto MRP/MPS clásico |
| Debilidades | `mrp_necesidad_bruta` y `mrp_explosion_materiales` **sin `empresa_id`**; sin pegging rico; capacidad MPS numérica suelta |
| Cambios recomendados | Corregir `empresa_id`; consumir PLN para capacidad; **no** implementar APS aquí |
| Prioridad | P1 (empresa_id) / P2 (profundidad) |
| Impacto | Integridad multiempresa + planeamiento |
| Riesgos | Convertir MRP en APS improvisado |

---

## MNT

| Campo | Contenido |
|-------|-----------|
| Estado actual | Básico CMMS |
| Fortalezas | Activo / plan / OT / historial |
| Debilidades | Repuestos en JSON; acoplamiento prematuro MES→OT (propuesta A) |
| Cambios recomendados | Conservar; formalizar repuestos después; vínculo MES↔MNT vía EVT opcional |
| Prioridad | P2 |
| Impacto | Medio |
| Riesgos | FK dura MES→MNT antes de madurez |

---

## FIN / TAX / CST / BDG

| Campo | Contenido |
|-------|-----------|
| Estado actual | FIN básico (asientos); TAX/CST embrionarios; BDG básico |
| Fortalezas | Núcleo contable presente |
| Debilidades | Sin CxC/CxP/bancos; costeo sin capas; TAX metadata |
| Cambios recomendados | Documentar como **deuda Core** (no Vertical). No bloquean ola industrial P0/P1. Fasear subledgers y costeo por lote después de `inv_lote`. |
| Prioridad | P2–P3 |
| Impacto | Alto a largo plazo; fuera del foco inmediato A/B |
| Riesgos | Ignorar deuda financiera hasta que el Core industrial esté “listo” y luego rehacer |

---

## HCM

| Campo | Contenido |
|-------|-----------|
| Estado actual | Maduro (planilla/RRHH amplio) |
| Fortalezas | Empleado→contrato→planilla |
| Debilidades | Reglas en campos libres; localización |
| Cambios recomendados | Exponer `operario_id` a MES; no rediseñar HCM en esta ola |
| Prioridad | P2 (integración MES) |
| Impacto | Medio (OEE por persona) |
| Riesgos | Acoplar planilla a MES innecesariamente |

---

## Síntesis

Corrección **MRP `empresa_id`** es la única urgencia estructural aquí. El resto es deuda Core real, faseable sin contaminar el diseño industrial P0/P1.
