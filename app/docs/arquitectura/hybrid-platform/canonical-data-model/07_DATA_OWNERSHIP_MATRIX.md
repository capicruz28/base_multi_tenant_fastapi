# 07 — Matriz de Ownership

**Etapa:** 3 — Canonical Data Model  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión

---

## 1. Leyenda

| Columna | Valores |
|---------|---------|
| **Dueño** | PLT=Platform, IAM, TNT=Tenant, ERP, REF=Reference |
| **CP/DP/TR** | Control Plane / Data Plane / Transversal |
| **SSOT** | Ubicación lógica de verdad |
| **Ambigüedad** | Ninguna / Parcial / Alta |

---

## 2. Matriz completa

| Dato | Dueño | CP | DP | TR | SSOT | Ambigüedad | Observaciones |
|------|-------|:--:|:--:|:--:|------|------------|---------------|
| Tenant Registry | PLT | ● | | | Platform | Ninguna | Raíz del modelo |
| Installation Mode | PLT | ● | | | Platform | Ninguna | |
| Storage Endpoint Metadata | PLT | ● | | | Platform | Ninguna | Secreto infra separado |
| Subscription / License | PLT | ● | | | Platform | Ninguna | |
| Product Module | PLT | ● | | | Platform | Ninguna | |
| Product Menu | PLT | ● | | | Platform | Ninguna | |
| Product Permission | PLT | ● | | | Platform | Ninguna | Nunca tenant-defined |
| Role Template | PLT | ● | | | Platform | Ninguna | |
| Platform Operator Identity | PLT | ● | | | Platform | Ninguna | |
| Platform Audit | PLT | ● | | | Platform | Ninguna | |
| Global System Config | PLT | ● | | | Platform | Ninguna | |
| Provisioning State | PLT | ● | | | Platform | Ninguna | |
| User Identity | IAM | | ● | ● | Tenant DP | Parcial | IAM gobierna; TNT administra |
| Authentication Configuration | TNT | | ● | ● | Tenant DP | Parcial | IAM consume |
| User Session | IAM | | | ● | IAM | **Alta persistencia** | Ownership claro; store TBD |
| Refresh Token | IAM | | | ● | IAM | **Alta persistencia** | Idem |
| Token Family | IAM | | | ● | IAM | **Alta persistencia** | Idem |
| Access Token Blacklist | IAM | | | ● | IAM (cache) | Ninguna | Volátil OK |
| Federated Identity Link | IAM | | | ● | IAM | Ninguna | |
| Impersonation Context | IAM | | | ● | IAM (ephemeral) | Ninguna | |
| IAM Audit | IAM | | | ● | IAM | Ninguna | |
| Effective Permission Set | IAM | | | ● | Derived | Ninguna | Cache |
| Tenant Branding | TNT | | ● | | Tenant DP | Ninguna | |
| Module Activation | TNT/PLT | ● | ● | | Tenant DP | Parcial | PLT autoriza; TNT tiene |
| Role (Tenant) | TNT | | ● | | Tenant DP | Ninguna | |
| Role-Permission Grant | TNT | | ● | | Tenant DP | Ninguna | Ref Product Permission |
| Role-Menu Grant | TNT | | ● | | Tenant DP | Ninguna | |
| User-Role Assignment | TNT | | ● | | Tenant DP | Ninguna | |
| Company | TNT | | ● | | Tenant DP | Ninguna | ERP opera |
| User Default Company | TNT | | ● | | Tenant DP | Ninguna | On User Identity |
| Document Sequence | ERP | | ● | | Tenant DP | Ninguna | |
| Branch, Department, Cargo | ERP | | ● | | Tenant DP | Ninguna | Org maestros |
| Cost Center | ERP | | ● | | Tenant DP | Ninguna | |
| Org Parameter | ERP | | ● | | Tenant DP | Ninguna | |
| Product (INV) | ERP | | ● | | Tenant DP | Ninguna | |
| Stock / Kardex | ERP | | ● | | Derived | Ninguna | Solo pipeline |
| Inventory Movement | ERP | | ● | | Tenant DP | Ninguna | |
| Supplier, Customer (SLS) | ERP | | ● | | Tenant DP | Ninguna | |
| Purchase / Sales Documents | ERP | | ● | | Tenant DP | Ninguna | |
| All other ERP masters/docs | ERP | | ● | | Tenant DP | Ninguna | Patrón uniforme |
| ERP Audit | ERP | | ● | | Tenant DP | Ninguna | |
| Country / Region | REF/PLT | ● | ○ | | Platform | Parcial | Réplica read DP opcional |
| Currency | REF/PLT | ● | ○ | | Platform | Parcial | Idem |
| Geographic Read Replica | REF | | ○ | | Platform | Parcial | Read-only copy |

**Leyenda columnas CP/DP/TR:** ● = primario; ○ = secundario/réplica

---

## 3. Matriz resumida por dueño

| Dueño | # Datos | CP | DP | TR |
|-------|---------|----|----|-----|
| Platform | 12 | 12 | 0 | 0 |
| IAM | 10 | 0 | 1 | 9 |
| Tenant | 8 | 0 | 8 | 0 |
| ERP | 30+ | 0 | 30+ | 0 |
| Reference | 3 | 3 | réplica | 0 |

---

## 4. Datos con ambigüedad residual

| Dato | Ambigüedad | Resolución ownership | Pendiente técnico |
|------|------------|------------------------|-------------------|
| User Session | Alta (persistencia) | IAM es dueño | Q-010 store location |
| Refresh Token / Token Family | Alta (persistencia) | IAM es dueño | Q-010 |
| Module Activation | Parcial (autorización) | SSOT: Tenant DP; PLT autoriza | Ninguno |
| User Identity | Parcial (admin vs IAM) | IAM dueño funcional | Ninguno |
| Auth Configuration | Parcial | Tenant dueño | Ninguno |
| Geographic Catalog | Parcial (réplica) | Platform SSOT | Q-041 réplica policy |
| Role-Permission Grant | Parcial AS-IS | Canónico: Tenant DP | Migración física |

---

## 5. Matriz Shared vs Dedicated (ownership invariante)

| Dato | Shared ownership | Dedicated ownership | ¿Cambia? |
|------|------------------|---------------------|----------|
| Todos P-* | PLT | PLT | No |
| Todos I-* (session) | IAM | IAM | No |
| Todos T-* / E-* | TNT/ERP | TNT/ERP | No |
| SSOT Platform | Central | Central | No |
| SSOT Tenant DP | Shared store lógico | Dedicated store | Solo ubicación |

---

## 6. Quick reference — ¿Quién es dueño?

| Pregunta | Respuesta |
|----------|-----------|
| ¿Quién define permisos? | Platform (Product Permission) |
| ¿Quién asigna permisos? | Tenant (Grant) |
| ¿Quién posee stock? | ERP (derivado) |
| ¿Quién posee sesiones? | IAM |
| ¿Quién posee empresa? | Tenant (Company) |
| ¿Quién posee tenant? | Platform (Registry) |
| ¿Quién posee movimiento inventario? | ERP |
| ¿Quién define módulos? | Platform |
| ¿Quién activa módulos? | Tenant (assignment) |
| ¿Quién define modo instalación? | Platform |

---

## 7. Conformidad con principios D1–D7

| Principio | Cumplimiento en matriz |
|-----------|---------------------|
| D1 Single SSOT | ✅ Cada fila tiene dueño único |
| D2 Platform ≠ ERP | ✅ Filas separadas; sin overlap |
| D3 IAM = identidad/acceso | ✅ Session/Identity IAM |
| D4 Modo no cambia dueño | ✅ Columna Shared/Dedicated |
| D5 Agnóstico SQL | ✅ Sin tablas |
| D6 Extensible modos | ✅ Installation Mode en PLT |
| D7 (impact) | ✅ ERP 100% DP |

---

## 8. Observaciones para etapa técnica

1. **AS-IS** coloca muchos datos DP en almacén central — ownership canónico ≠ ubicación actual
2. Migración canónica es **alinear persistencia con ownership**, no cambiar dueños
3. Sesiones IAM: ownership **cerrado**; persistencia **abierta**
4. Grants RBAC: ownership **cerrado** en Tenant DP
