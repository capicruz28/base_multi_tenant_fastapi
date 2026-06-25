# 09 — Resolución de Preguntas P0

**Etapa:** 3 — Canonical Data Model  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Referencia:** `hybrid-platform/05_OPEN_QUESTIONS.md`

---

## 1. Propósito

Indicar qué preguntas P0 de Etapa 1 quedan **resueltas por ownership**, cuáles **parcialmente resueltas**, y cuáles **requieren decisión técnica posterior**.

**Importante:** Resolución de ownership ≠ decisión de implementación.

---

## 2. Resumen

| Estado | Count P0 |
|--------|----------|
| ✅ Resueltas (ownership) | 4 |
| 🟡 Parcialmente resueltas | 3 |
| ❌ Abiertas (técnica/ops) | 3 |

---

## 3. P0 resueltas por modelo canónico

### Q-001 ✅ ¿Qué datos pertenecen exclusivamente al Control Plane?

**Resuelta** — Ver `04_CONTROL_PLANE_DATA_PLANE.md` §5.

**Respuesta ownership:**

Tenant Registry, Installation Mode, Storage Metadata, Subscription, Product Catalog (Module, Menu, Permission, Role Template), Platform Operator, Platform Audit, Global Config, Product Reference maestros.

**Excluidos:** Sesiones, User Identity, Grants, Company, ERP.

**Documento:** `03_SINGLE_SOURCE_OF_TRUTH.md`, `07_DATA_OWNERSHIP_MATRIX.md`

---

### Q-002 ✅ ¿Qué datos pertenecen exclusivamente al Data Plane?

**Resuelta** — Ver `04_CONTROL_PLANE_DATA_PLANE.md` §5.

**Respuesta ownership:**

Company, Org structure, Roles tenant, Grants, User-Role assignments, Module Activation (assignment), Branding, Auth Config (tenant), Document Sequences, 100% ERP operacional, ERP Audit.

**Excluidos:** Catálogo producto (CP), Sesiones (Transversal).

---

### Q-020 ✅ ¿Dónde viven Role, Role-Permission Grant, User-Role Assignment en Dedicated?

**Resuelta a nivel ownership** (no persistencia física).

**Respuesta:**

| Dato | Dueño | Plano | SSOT |
|------|-------|-------|------|
| Role (Tenant) | Tenant | Data Plane | Tenant store |
| Role-Permission Grant | Tenant | Data Plane | Tenant store |
| User-Role Assignment | Tenant | Data Plane | Tenant store |
| Product Permission (referenciado) | Platform | Control Plane | Platform central |

**Implicación:** Grants viven en **data plane del tenant** (mismo almacén que Company y ERP). Product Permission permanece **central read-only reference**.

**Gap AS-IS:** Hoy en almacén central compartido — requiere alineación física en etapa técnica, no cambio de ownership.

---

### Q-032 ✅ ¿Seed empresa inicial es ERP o Platform?

**Resuelta.**

**Respuesta ownership:**

- **Dueño del dato Company:** Tenant (Data Plane)
- **Responsable del seed:** Onboarding (orquestado Platform) ejecutando **ERP-ORG seed**
- **Platform:** orquesta, no posee
- **ERP-ORG:** define estructura mínima

**Implicación:** Seed en **almacén data plane del tenant**, no en Control Plane.

---

## 4. P0 parcialmente resueltas

### Q-010 🟡 ¿Dónde persisten sesiones IAM en Dedicated?

**Parcial.**

| Aspecto | Estado |
|---------|--------|
| Dueño funcional | ✅ IAM (cerrado) |
| Plano | ✅ Transversal (cerrado) |
| SSOT lógico | ✅ IAM |
| **Ubicación física persistencia** | ❌ Abierta |

**Opciones restantes (técnica, no ownership):**

- A) Persistencia Control Plane / central (IAM SSOT centralizado)
- B) Persistencia Data Plane tenant (co-localizado con Identity)

**Ownership no cambia** en ninguna opción.

---

### Q-030 🟡 ¿Contrato saga onboarding?

**Parcial.**

| Aspecto | Resuelto por modelo |
|---------|---------------------|
| Orden creación datos | ✅ `06_DATA_DEPENDENCIES.md` §8 |
| Qué datos en CP vs DP | ✅ `05_DATA_LIFECYCLE.md` §4 |
| Dependencias fuertes | ✅ |
| Pasos idempotentes | ❌ Técnica |
| Compensación fallos | ❌ Técnica |
| Estado mínimo Activo | 🟡 Tenant Registry Activo + Identity + Company + Grants mínimos |

---

### Q-031 🟡 ¿Cuándo se crea metadata instalación?

**Parcial.**

| Aspecto | Resuelto |
|---------|----------|
| Dueño metadata | ✅ Platform |
| Creación en dedicated onboarding | ✅ Antes/durante provisioning data plane |
| Creación en shared onboarding | ✅ Implícito default (mode=Shared) |
| **Momento exacto en saga** | ❌ Técnica |
| **Shared existente sin metadata** | ✅ Fallback Shared (compat AS-IS) |

---

## 5. P0 abiertas (requieren etapa técnica)

### Q-010 (persistencia) ❌

Sub-decisión física de almacén para Session/Token. Ownership IAM ya definido.

**Bloquea:** Diseño técnico conexión IAM.

---

### Q-030 (saga mechanics) ❌

Idempotencia, compensación, estados intermedios — diseño de orquestación, no ownership.

**Bloquea:** Implementación onboarding.

---

### Q-021 derivada de Q-020 🟡→❌

**Q-021 [P1 pero relacionada]:** ¿Cómo resolver permiso sin join cross-almacén?

**Ownership responde:** Product Permission es referencia read-only por ID; resolución vía **servicio abstracto** (no join en ERP).

**Implementación:** Etapa técnica.

---

## 6. P1/P2 relevantes actualizadas

| ID | Estado post-Etapa 3 | Nota |
|----|----------------------|------|
| Q-003 | ✅ Resuelta | Catálogo solo Platform; réplica read optional |
| Q-004 | ✅ Resuelta | Auth Config = Tenant DP |
| Q-040 | 🟡 Parcial | Ownership: tenant identifier en DP; redundancia física = técnica |
| Q-041 | 🟡 Parcial | SSOT Platform; réplica read DP permitida |
| Q-042 | ✅ Resuelta | Document Sequence = ERP / Tenant DP |
| Q-080 | ✅ Confirmada | Shared default |
| Q-081 | ✅ Confirmada | Tenants shared sin cambio ownership |

---

## 7. Tabla consolidada P0

| ID | Pregunta | Estado | Próxima etapa |
|----|----------|--------|---------------|
| Q-001 | Control plane data | ✅ Ownership | — |
| Q-002 | Data plane data | ✅ Ownership | — |
| Q-010 | Sesiones dedicated | 🟡 | Decisión persistencia |
| Q-020 | Roles/grants ubicación | ✅ Ownership | Alineación física |
| Q-030 | Saga onboarding | 🟡 | Diseño orquestación |
| Q-031 | Metadata cuándo | 🟡 | Diseño saga timing |
| Q-032 | Seed empresa | ✅ Ownership | — |

---

## 8. Criterio de cierre actualizado

| Pregunta | Cierre ownership | Cierre técnico |
|----------|------------------|----------------|
| Q-001, Q-002, Q-020, Q-032 | ✅ Esta etapa | N/A |
| Q-010 | ✅ Dueño IAM | ❌ Store location |
| Q-030, Q-031 | 🟡 Datos orden | ❌ Saga mechanics |
| Q-021 | 🟡 Modelo refs | ❌ Servicio resolución |

**Etapa técnica puede iniciar** para ownership-resueltas; **no** para MVP dedicated hasta cerrar Q-010 persistencia y Q-030 saga.

---

## 9. Decisiones explícitamente NO tomadas

| Tema | Motivo |
|------|--------|
| Tabla física por dato | Fuera alcance Etapa 3 |
| SQLAlchemy routing | Fuera alcance |
| Session central vs tenant store | Requiere ADR-002 aprobado + análisis latencia |
| Saga compensación steps | Requiere diseño técnico |
| Réplica obligatoria vs on-demand catálogos | Q-041 parcial |

---

## 10. Conclusión

El modelo canónico **resuelve la frontera CP/DP** (Q-001, Q-002) y **ownership RBAC** (Q-020, Q-032) — bloqueadores conceptuales principales.

Permanece **1 eje P0 técnico**: persistencia sesiones IAM (Q-010), y **2 ejes orquestación**: saga onboarding (Q-030, Q-031).

Estos no requieren redefinir ownership; requieren **diseño técnico** en Etapa 4.
