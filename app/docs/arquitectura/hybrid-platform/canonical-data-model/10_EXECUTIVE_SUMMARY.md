# 10 — Resumen Ejecutivo: Modelo Canónico de Datos

**Etapa:** 3 — Canonical Data Model & Data Ownership  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión y aprobación  
**Audiencia:** Arquitecto Principal, Tech Lead, Producto, Compliance

---

## 1. Objetivo cumplido

Se definió el **modelo canónico de datos** de la plataforma híbrida: inventario de datos de negocio, ownership único, SSOT, clasificación Control Plane / Data Plane / Transversal, lifecycle, dependencias y riesgos.

**Sin tablas. Sin SQL. Sin implementación.**

---

## 2. Modelo en una vista

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE (Platform)                  │
│  Tenant Registry · Installation Mode · Storage Metadata      │
│  Product Catalog · License · Platform Audit · Reference      │
└──────────────────────────┬──────────────────────────────────┘
                           │ autoriza / define
┌──────────────────────────▼──────────────────────────────────┐
│              TRANSVERSAL (IAM)                                 │
│  User Identity · Session · Tokens · IAM Audit                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ protege acceso
┌──────────────────────────▼──────────────────────────────────┐
│              DATA PLANE (Tenant / ERP)                         │
│  Company · Roles · Grants · Branding · Auth Config             │
│  ERP Masters · Documents · Derived · Sequences · ERP Audit     │
└─────────────────────────────────────────────────────────────┘
```

**Principio rector:** Shared y Dedicated cambian **dónde persiste** el Data Plane; **nunca quién es dueño**.

---

## 3. Ownership completamente definido

| Dominio | Dueño | SSOT | Claridad |
|---------|-------|------|----------|
| Tenant Registry, License, Installation | Platform | Platform | ✅ Total |
| Product Module, Menu, Permission | Platform | Platform | ✅ Total |
| Storage Endpoint Metadata | Platform | Platform | ✅ Total |
| Platform Audit | Platform | Platform | ✅ Total |
| Reference Catalogs (Country, Currency) | Platform | Platform (+ réplica read) | ✅ Total |
| Role (Tenant), Grants, Assignments | Tenant | Tenant Data Plane | ✅ Total |
| Company, Org Structure | Tenant / ERP | Tenant Data Plane | ✅ Total |
| Document Sequence | ERP | Tenant Data Plane | ✅ Total |
| All ERP operational data | ERP | Tenant Data Plane | ✅ Total |
| ERP Audit | ERP | Tenant Data Plane | ✅ Total |
| User Identity | IAM (+ TNT admin) | Tenant Data Plane | ✅ Total |
| Authentication Configuration | Tenant | Tenant Data Plane | ✅ Total |
| Product Permission → Grant reference | Platform → Tenant | Split SSOT | ✅ Total |
| Effective Permission Set | IAM (derived) | Derived | ✅ Total |
| Tenant Branding | Tenant | Tenant Data Plane | ✅ Total |
| Module Activation (assignment) | Tenant | Tenant Data Plane | ✅ Total |

**Total: ~45 familias de datos con dueño único definido.**

---

## 4. Ownership con ambigüedad residual

| Dato | Qué está claro | Qué permanece abierto |
|------|----------------|----------------------|
| **User Session / Refresh Token / Token Family** | Dueño: **IAM**. Plano: **Transversal**. SSOT lógico: **IAM** | **Ubicación física de persistencia** (central vs tenant store) |
| **Geographic Catalog (dedicated)** | SSOT: **Platform** | Política réplica read-only obligatoria vs on-demand |
| **Module Activation** | SSOT: Tenant DP; Platform autoriza | Mecanismo autorización comercial (técnico) |

**Solo 1 ambigüedad de ownership real:** ninguna — la sesión tiene dueño IAM claro. La ambigüedad es **persistencia**, no **ownership**.

---

## 5. Preguntas P0 — estado

| ID | Pregunta | Resultado Etapa 3 |
|----|----------|-------------------|
| Q-001 | Control plane data | ✅ **Resuelta** |
| Q-002 | Data plane data | ✅ **Resuelta** |
| Q-020 | Roles/grants en dedicated | ✅ **Resuelta** (ownership) |
| Q-032 | Seed empresa | ✅ **Resuelta** |
| Q-010 | Sesiones IAM persistencia | 🟡 **Parcial** (dueño sí; store no) |
| Q-030 | Saga onboarding | 🟡 **Parcial** (datos sí; mechanics no) |
| Q-031 | Metadata cuándo | 🟡 **Parcial** (dueño sí; timing no) |

**4 de 7 P0 resueltas completamente.** 3 requieren etapa técnica (no redefinen ownership).

---

## 6. Preguntas que requieren decisión técnica posterior

| Tema | Tipo decisión | Bloquea |
|------|---------------|---------|
| Persistencia Session/Token (Q-010) | ADR-002 técnico | IAM dedicated auth |
| Saga idempotencia/compensación (Q-030) | Orquestación | Onboarding |
| Timing metadata en saga (Q-031) | Orquestación | Provisioning |
| Servicio resolución permisos (Q-021) | Infra IAM | RBAC cross-store |
| Réplica catálogos geo (Q-041) | Provisioning policy | Forms dedicated |
| Alineación física AS-IS → canónico | Migración persistencia | Dedicated MVP |

**Ninguna requiere redefinir el modelo canónico.**

---

## 7. Gap AS-IS → Canónico (principal hallazgo)

| AS-IS hoy | Canónico | Acción futura |
|-----------|----------|---------------|
| CP + DP en mismo almacén | Separación lógica clara | Alinear persistencia |
| Grants en central | Grants en tenant DP | Mover con data plane |
| Company seed vía onboarding central | Company en tenant DP | Seed en tenant store |
| Session en central | IAM dueño (store TBD) | Decidir persistencia |
| Secuencias en central | ERP tenant DP | Seed en tenant store |

**El modelo no invalida AS-IS Shared** — define target state para Dedicated y alineación progresiva.

---

## 8. Riesgos críticos

| # | Riesgo | Mitigación conceptual |
|---|--------|----------------------|
| 1 | Onboarding TX cross-plane | Saga; orden en `06_DATA_DEPENDENCIES` |
| 2 | RBAC join CP→DP | Referencia por ID + servicio resolución |
| 3 | Session/User split stores | Decidir Q-010 antes de implementar |
| 4 | Dedicated sin réplica catálogo | Provisioning seed read-only |
| 5 | Confundir ownership con ubicación | Este modelo como referencia |
| 6 | Modificar ERP por modo | Prohibido — guardrails Etapa 2 |

---

## 9. Documentación entregada

| # | Documento |
|---|-----------|
| 01 | [CANONICAL_DATA_MODEL.md](./01_CANONICAL_DATA_MODEL.md) |
| 02 | [DATA_OWNERSHIP.md](./02_DATA_OWNERSHIP.md) |
| 03 | [SINGLE_SOURCE_OF_TRUTH.md](./03_SINGLE_SOURCE_OF_TRUTH.md) |
| 04 | [CONTROL_PLANE_DATA_PLANE.md](./04_CONTROL_PLANE_DATA_PLANE.md) |
| 05 | [DATA_LIFECYCLE.md](./05_DATA_LIFECYCLE.md) |
| 06 | [DATA_DEPENDENCIES.md](./06_DATA_DEPENDENCIES.md) |
| 07 | [DATA_OWNERSHIP_MATRIX.md](./07_DATA_OWNERSHIP_MATRIX.md) |
| 08 | [DATA_RISKS.md](./08_DATA_RISKS.md) |
| 09 | [P0_QUESTION_RESOLUTION.md](./09_P0_QUESTION_RESOLUTION.md) |
| 10 | [EXECUTIVE_SUMMARY.md](./10_EXECUTIVE_SUMMARY.md) |

---

## 10. Conformidad con principios Etapa 3

| Principio | Cumplido |
|-----------|----------|
| D1 Single SSOT | ✅ |
| D2 Platform ≠ ERP | ✅ |
| D3 IAM = identidad/acceso | ✅ |
| D4 Modo no cambia dueño | ✅ |
| D5 Agnóstico SQL Server | ✅ |
| D6 Extensible modos | ✅ |
| Impact Assessment G-01..G-10 | ✅ Compatible |

---

## 11. Criterios de aprobación

- [ ] Aprobación formal modelo canónico
- [ ] Validación Producto: frontera CP/DP
- [ ] Validación Compliance: data plane dedicated
- [ ] Cierre ADR-002 (persistencia sesiones) — etapa técnica
- [ ] Confirmación: grants en tenant data plane

---

## 12. Próximo paso (Etapa 4 — fuera de alcance)

Tras aprobación:

1. Diseño técnico alineación persistencia AS-IS → canónico
2. ADR-002 definitivo (session store)
3. Diseño saga onboarding (datos ya definidos)
4. Mapeo dato → almacén (primera vez que se nombran ubicaciones físicas)

---

## 13. Conclusión

El **modelo canónico de datos está completo** a nivel conceptual. La tríada **Platform (CP) — IAM (TR) — Tenant/ERP (DP)** es estable para Shared, Dedicated, On-Premise y Cloud privada.

**~95% de ownership definido.** La incertidumbre restante es **dónde persistir sesiones IAM** y **cómo orquestar físicamente** el onboarding — decisiones de Etapa 4, no de ownership.

**Recomendación:** Aprobar este modelo antes de cualquier diseño técnico de conexión, saga o SQLAlchemy.

---

## 14. Estimación cualitativa esfuerzo post-aprobación

| Trabajo | Esfuerzo | Depende de |
|---------|----------|------------|
| Alinear persistencia grants/company/sequences | M | Aprobación modelo |
| Decidir + implementar session store | M–L | ADR-002 |
| Permission resolution service | S–M | Q-021 |
| Reference catalog replica policy | S | Q-041 |
| Saga onboarding (datos conocidos) | L | Q-030 |
| **Redefinir ownership** | **Nulo** | — |

El modelo canónico **no añade** trabajo de rediseño de dominio — **reduce** ambigüedad y previene forks.
