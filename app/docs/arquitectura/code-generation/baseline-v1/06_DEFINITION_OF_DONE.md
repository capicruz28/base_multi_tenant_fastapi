# Definition of Done — certificación de módulo — Baseline V1

Un módulo ERP se considera **certificado** respecto al Motor de Códigos cuando cumple **todos** los criterios siguientes.

---

## 1. Criterios funcionales

| # | Criterio |
|---|----------|
| D1 | CREATE omite código → allocate correcto (o rechazo si MANUAL_ONLY) |
| D2 | CREATE manual válido → aceptado + UNIQUE + align según catálogo |
| D3 | CREATE manual duplicado → 409 antes o vía Motor, sin fila huérfana |
| D4 | UPDATE no puede cambiar código Motor (schema + service) |
| D5 | UPDATE no invoca Gateway |
| D6 | Read/List siempre exponen el código asignado |
| D7 | Soft-delete / reactivar preservan el código |

---

## 2. Criterios técnicos

| # | Criterio |
|---|----------|
| T1 | Diff de `app/core/codigo/**` vacío en el PR del módulo |
| T2 | Diff Gateway / SequenceCatalog vacío |
| T3 | UoW CREATE: un `session.begin` cubre allocate + insert |
| T4 | Checklist [`04_CHECKLISTS.md`](04_CHECKLISTS.md) §1 completo |
| T5 | OpenAPI vivo alineado; snapshot regenerado si aplica al cierre |
| T6 | Tests unitarios CREATE + BR-IMM verdes |
| T7 | Session scope / RBAC conforme ERP V4 |

---

## 3. Criterios documentales

| # | Criterio |
|---|----------|
| C1 | Matriz entidad ↔ `sequence_key` ↔ campo ↔ policy ↔ scope |
| C2 | Contrato FE (o addendum) actualizado: Create optional / Update read-only código |
| C3 | Referencia explícita a **Baseline V1** + Golden Reference ORG |
| C4 | Sin reivindicar BR-M-31 / “editable sin referencias” |

---

## 4. Gate de certificación

```text
[ ] D1–D7
[ ] T1–T7
[ ] C1–C4
[ ] Revisión arquitectura: “sin desviación de Baseline V1”
```

**Si algún ítem falla → el módulo NO está certificado**, aunque el happy path CREATE funcione.

---

## 5. Estado ORG (Golden Reference)

| Gate | ORG Ola 1 |
|------|-----------|
| D1–D7 | ✅ |
| T1–T7 | ✅ |
| C1–C4 | ✅ |
| Baseline V1 | **Congelado — referencia obligatoria** |

---

## 6. Veredicto para INV

INV se certificará **solo** cuando replique este DoD **sin** modificar Motor/Gateway y **sin** reintroducir UPDATE mutable de códigos Motor.

---

*Inicio del paquete: [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md)*
