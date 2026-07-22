# Etapa 0.5 — Modelo Conceptual del Core (cerrado)

**Estado:** Definitivo · congelado a nivel conceptual  
**Fecha:** 2026-07-22  
**Próxima fase:** Diseño físico de tablas (D1) — aún sin SQL

Esta carpeta **no** modifica la auditoría aprobada (`../00`–`../91`, `../modules/*`). La complementa.

---

## Documentos

| Doc | Contenido |
|-----|-----------|
| [01_CORE_DOMAIN_MODEL.md](./01_CORE_DOMAIN_MODEL.md) | Dominios, responsabilidades, límites Core vs nunca-Core |
| [02_BOUNDED_CONTEXTS.md](./02_BOUNDED_CONTEXTS.md) | Bounded Contexts oficiales |
| [03_AGGREGATE_ROOTS.md](./03_AGGREGATE_ROOTS.md) | Aggregate Roots y ciclos de vida |
| [04_DOMAIN_EVENTS.md](./04_DOMAIN_EVENTS.md) | Catálogo de eventos de negocio |
| [05_UBIQUITOUS_LANGUAGE.md](./05_UBIQUITOUS_LANGUAGE.md) | Lenguaje ubicuo (una definición por término) |
| [06_EXTENSION_POINTS.md](./06_EXTENSION_POINTS.md) | Contrato de extensión para Verticales |

---

## Decisiones fuera de discusión (heredadas)

Core vs Vertical · PLN · MES · Event Bus · Lote · Variantes · APS · JSON · ALR  
→ Ver `../03_PRELIMINARY_ADR_DECISIONS.md` y `../90_CORE_V2_DEFINITION.md`.

---

## Definition of Done de la Etapa 0.5

- [x] Dominios y fronteras definidos
- [x] Bounded Contexts definidos
- [x] Aggregate Roots definidos (sin tablas)
- [x] Eventos de dominio catalogados (sin diseño de bus)
- [x] Lenguaje ubicuo sin ambigüedades
- [x] Puntos de extensión para Verticales

**Gate:** con esta etapa cerrada, se autoriza iniciar **Fase D1** (especificación física de tablas P0), todavía sin scripts SQL de bootstrap.
