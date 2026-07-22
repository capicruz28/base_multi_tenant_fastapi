# F17B — Aprobación ejecutiva de la integración Motor ↔ Bootstrap

**Fase:** F17B (cierre documental). Consolida `28`–`31`.
**Fecha:** 2026-07-03
**Decisión requerida:** aprobar la integración del Motor de Generación de Códigos con el Bootstrap oficial y habilitar el inicio de ORG e INV.

---

## 1. Pregunta de negocio

> ¿El Motor de Generación de Códigos está correctamente integrado al Bootstrap oficial (Shared y Dedicated), formando **un único flujo de onboarding**, sin flujos paralelos ni duplicación de responsabilidades de flujo?

**Respuesta: SÍ.**

---

## 2. Evidencia (resumen ejecutivo)

| Verificación | Resultado |
|--------------|-----------|
| El motor es una **etapa** del bootstrap (Shared paso 8 / Dedicated paso 6) | ✅ |
| Shared y Dedicated **reutilizan** la misma función de seed (`_insertar_secuencias_codigo`) | ✅ |
| El seed corre en la **misma TX/BD** del onboarding (session-driven) | ✅ |
| Orden correcto (secuencias **después** de crear empresa sede) | ✅ |
| Rollback Shared total; Dedicated resumible por markers + `row_expectations` | ✅ |
| Lazy creation runtime usa el **UoW ERP** y defaults del `SequenceCatalog` | ✅ |
| Ubicación física consistente (Shared BD única / Dedicated BD tenant) | ✅ |
| Duplicación de **flujo** | ❌ (no existe) |
| Duplicación de **datos de config** (catálogo↔onboarding_seed) | ⚠️ (ADJ-01) |
| Riesgo repo ADMIN sin sesión en Dedicated (INC-09) | ⚠️ (ADJ-03) |

---

## 3. Condiciones de la aprobación

La integración de **flujo** se aprueba **sin cambios**. Se recomienda ejecutar como primer sub-paso de la integración ORG los ajustes **P1** (no bloqueantes arquitectónicos):

- **ADJ-01** — `onboarding_seed` derivado del `SequenceCatalog` (una sola fuente de verdad).
- **ADJ-03** — blindar `CfgCodigoSecuenciaRepository` (solo onboarding / `session=` obligatoria).
- **ADJ-05 / ADJ-06** — centralizar la lista eager y su verificación de conteo.

Ajustes **P2** (ADJ-02, ADJ-04, ADJ-07) durante la implementación ORG/INV.

---

## 4. Lo que queda definido

1. **Un único flujo de onboarding** para Shared y Dedicated, con el motor como etapa final del seed.
2. **Frontera clara** (`30`): el Bootstrap decide *cuándo/dónde* sembrar; el Motor decide *qué/cómo* (catálogo, fingerprint, formato, lazy, allocate).
3. **Contrato para ORG/INV:** consumir exclusivamente `CodigoGeneracionGateway`; nunca insertar cfg ni derivar prefijos localmente; `allocate` en el mismo UoW del documento.
4. **Backlog de robustez** priorizado (`31`), sin impacto arquitectónico.

---

## 5. Riesgos residuales (aceptados)

| Riesgo | Severidad | Estado |
|--------|-----------|--------|
| Drift catálogo↔onboarding_seed | Media | Mitigado por ADJ-01 (P1) |
| Repo ADMIN sin sesión (Dedicated) | Media | Mitigado por ADJ-03 (P1) |
| Multi-empresa posterior (solo lazy) | Baja | Cubierto por lazy; ADJ-04 opcional |
| Paridad auth_config Dedicated | Baja | Fuera del motor; ADJ-07 |

---

## 6. Veredicto

> **APROBADO.** La incorporación del Motor de Generación de Códigos respeta la arquitectura del Bootstrap existente y constituye un flujo único de onboarding para Shared y Dedicated.
>
> **Se habilita el inicio de la integración ORG e INV**, recomendando ejecutar los ajustes P1 (`31`) como primer sub-paso.

---

## 7. Firmas (rol)

| Rol | Decisión |
|-----|----------|
| Arquitectura de Motor | Aprobado con ADJ-01/05/06 |
| Arquitectura de Bootstrap/Provisioning | Aprobado con ADJ-03 |
| Product Owner ERP | Habilita ORG/INV |

---

*Documentos de soporte: `28_BOOTSTRAP_INTEGRATION_AUDIT.md`, `29_BOOTSTRAP_EXECUTION_FLOW.md`, `30_BOOTSTRAP_RESPONSIBILITY_MATRIX.md`, `31_IMPLEMENTATION_ADJUSTMENTS.md`.*
