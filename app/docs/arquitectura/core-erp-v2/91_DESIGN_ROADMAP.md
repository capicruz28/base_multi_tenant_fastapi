# Roadmap de diseño (sin SQL)

**Documento:** 91  
**Serie:** CORE ERP V2  
**Nota:** Este roadmap ordena el **diseño del modelo de datos**. No es plan de migración ni de scripts.

---

## Fase D0 — Cierre arquitectónico (auditoría)

- [x] Inventario V010
- [x] Comparación A/B
- [x] ADRs 01–10
- [x] Definición CORE V2
- [x] Auditorías por módulo

**Gate:** aprobación humana de `00_EXECUTIVE_SUMMARY.md` + `90_CORE_V2_DEFINITION.md`. — **Cumplido.**

---

## Fase D0.5 — Modelo conceptual (sin tablas)

- [x] Dominios del Core
- [x] Bounded Contexts
- [x] Aggregate Roots
- [x] Domain Events (catálogo de negocio)
- [x] Lenguaje ubicuo
- [x] Puntos de extensión Verticales

Documentación: `conceptual/`.

**Gate:** modelo conceptual congelado. — **Cumplido.** Autoriza D1.

---

## Fase D1 — Auditoría de evolución V1→V2 (sin columnas)

**Principio nuevo:** CORE V2 = evolución mínima del CORE V1. Extender primero; tabla nueva solo con C1–C4.

- [x] Principios y criterios C1–C4
- [x] Mapa ejecutivo por módulo
- [x] Tablas nuevas obligatorias justificadas
- [x] Impacto en código V1
- [x] Prioridades P0/P1/P2

Documentación: `evolution/`.

**Gate:** mapa de evolución aprobado. — **Listo para revisión humana.**  
**No autorizado aún:** diseño de columnas ni SQL.

---

## Fase D1.1 — Diseño físico P0 (columnas / FKs / CHECKs)

Solo tras aprobar `evolution/`. Orden:

1. `inv_lote` (AR) + impacto en `inv_stock` (extensión/rediseño)
2. Extensiones `lote_id` en INV/WMS/QMS/PUR/MFG/INV_BILL/(POS)
3. Estrategia de salida almacén/ubicación
4. Variante: preferir extensión `inv_producto`; tabla nueva solo si D-EVO-03 lo exige

**Entregable:** spec de columnas — aún sin script bootstrap.

---

## Fase D2 — Modelo de datos P1

1. `wms_oleada` + `oleada_id` en `wms_tarea`
2. MES (ejecución, parada, motivo)
3. PLN calendario capacidad
4. `cfg_vertical_empresa`
5. EVT (outbox mínimo) + ALR
6. Corrección MRP `empresa_id`

---

## Fase D3 — ADRs de extensión (sin tablas)

1. APS futuro (inputs, restricciones tipadas, escenarios)
2. RPT semántica (AST de filtros, métricas/dimensiones)
3. WMS V2.1/V2.2
4. QMS CAPA/SPC
5. Series como AR (si se prioriza)

---

## Fase D4 — Deuda Core no industrial (backlog)

FIN subledgers, CST capas, WFL runtime, TAX, formalización MNT repuestos.

---

## Fase I0 — Implementación schema (solo tras D1–D2 aprobados)

- Regenerar bootstrap desde cero (permitido por restricción del proyecto).
- Un solo script canónico CORE V2 — **no** merge ciego de A+B.

---

## Prohibiciones hasta nuevo aviso

- No generar SQL de A/B “tal cual”.
- No crear tablas `aps_*` / `rpt_*` en D1.1–D2.
- No introducir JSON de vertical en CFG.
- No eliminar tablas Core V010 sin ADR específico de eliminación.
- **No crear tablas nuevas solo por limpieza conceptual** (principio evolución V1→V2).
- No modificar documentos congelados de D0 ni Etapa 0.5.
