# 02 — Data Ownership

**Etapa:** 3 — Canonical Data Model  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión

---

## 1. Leyenda de dueños

| Dueño | Sigla | Alcance |
|-------|-------|---------|
| **Platform** | PLT | Control plane; gobierno del SaaS |
| **IAM** | IAM | Identidad, sesión, acceso |
| **Tenant** | TNT | Administración del suscriptor |
| **ERP** | ERP | Operaciones de negocio |
| **Product Reference** | REF | Catálogos de referencia del producto |

**Regla:** Un dato tiene **exactamente un** dueño primario (SSOT). Otros dominios **consumen** o **derivan**.

---

## 2. Platform (Control Plane)

### P-01 Tenant Registry

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | IAM (login routing), Tenant Admin, Provisioning, FE |
| **Modifica** | Platform (superadmin), Provisioning |
| **Solo lectura** | Tenant Admin (parcial), IAM, ERP (ninguno directo) |
| **Ciclo de vida** | Create: Provisioning → Update: Platform → Suspend/Retire: Platform |
| **Dependencias** | Ninguna (raíz) |
| **Riesgo** | Crítico — corrupción afecta todo el tenant |

### P-02 Installation Mode

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | Infraestructura (persistencia), Provisioning, Monitoreo |
| **Modifica** | Platform (comercial/migración) |
| **Solo lectura** | Tenant Admin (consulta), IAM, ERP |
| **Ciclo de vida** | Asignado en alta; cambio solo vía migración gobernada |
| **Dependencias** | Tenant Registry |
| **Riesgo** | Crítico — modo incorrecto = almacén incorrecto |

### P-03 Storage Endpoint Metadata

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | Infraestructura resolución |
| **Modifica** | Platform / Provisioning |
| **Solo lectura** | Ningún módulo de negocio |
| **Ciclo de vida** | Create: Provisioning dedicated → Update: migración → Delete: retiro tenant |
| **Dependencias** | Tenant Registry, Installation Mode |
| **Riesgo** | Crítico — seguridad y conectividad |

### P-04 Subscription / License

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | Module Activation, Feature gates, Facturación |
| **Modifica** | Platform |
| **Solo lectura** | Tenant Admin (consulta plan) |
| **Ciclo de vida** | Vinculado a Tenant Registry |
| **Dependencias** | Tenant Registry |
| **Riesgo** | Medio — acceso a features |

### P-05 Product Module / P-06 Product Menu / P-07 Product Permission

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform (Product Catalog) |
| **Consumidores** | IAM (RBAC), Tenant Admin, Menu resolver, Onboarding |
| **Modifica** | Platform (release producto) |
| **Solo lectura** | Tenant, IAM, ERP |
| **Ciclo de vida** | Versionado con releases; nunca eliminado (deprecated) |
| **Dependencias** | Ninguna entre tenants |
| **Riesgo** | Alto — inconsistencia de producto |

### P-08 Role Template

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | Onboarding (seed grants) |
| **Modifica** | Platform |
| **Solo lectura** | Tenant Admin |
| **Ciclo de vida** | Versionado producto |
| **Dependencias** | Product Permission, Product Module |

### P-09 Platform Operator Identity

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | IAM |
| **Modifica** | Platform |
| **Solo lectura** | — |
| **Ciclo de vida** | CRUD Platform |
| **Dependencias** | Tenant Registry (cliente SYSTEM) |

### P-10 Platform Audit Record

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | Platform |
| **Consumidores** | Compliance, Superadmin UI |
| **Modifica** | Append-only Platform/IAM |
| **Solo lectura** | Superadmin |
| **Dependencias** | Tenant Registry |

---

## 3. IAM (Transversal)

### I-01 User Identity

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **IAM** (gobierno) + **Tenant Admin** (administración delegada) |
| **Nota ownership** | IAM es dueño funcional de integridad de identidad; Tenant Admin opera CRUD dentro de políticas |
| **Consumidores** | IAM, ERP (audit user id), Platform (onboarding) |
| **Modifica** | Tenant Admin, IAM (password reset), Onboarding |
| **Solo lectura** | ERP (referencia usuario_creacion_id) |
| **Ciclo de vida** | Create: onboarding/admin → Update: admin/user → Deactivate: soft (es_activo) |
| **Dependencias** | Tenant Registry |
| **Riesgo** | Crítico |

### I-02 Authentication Configuration

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **Tenant** (políticas) bajo gobierno **IAM** (validación) |
| **Consumidores** | IAM login, SSO |
| **Modifica** | Tenant Admin |
| **Solo lectura** | IAM |
| **Ciclo de vida** | Create: onboarding → Update: tenant admin |
| **Dependencias** | Tenant Registry |
| **Riesgo** | Alto — auth roto |

### I-03 User Session / I-04 Refresh Token / I-05 Token Family

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **IAM** |
| **Consumidores** | IAM (refresh, probe, revoke), Redis cache |
| **Modifica** | IAM exclusivamente |
| **Solo lectura** | Tenant Admin (listado sesiones activas) |
| **Ciclo de vida** | Create: login → Rotate: refresh → Revoke: logout/admin |
| **Dependencias** | User Identity, Tenant Registry |
| **Riesgo** | Crítico — **persistencia física: decisión técnica pendiente** |

### I-06 Access Token State (blacklist)

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | IAM |
| **Consumidores** | IAM deps |
| **Modifica** | IAM (revocación) |
| **Ciclo de vida** | TTL-bound |
| **Dependencias** | Session |
| **Riesgo** | Medio — cache volátil aceptable |

### I-07 Federated Identity Link

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | IAM |
| **Modifica** | IAM / SSO flow |
| **Dependencias** | User Identity |

### I-08 Impersonation Context

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | IAM + Platform Audit |
| **Modifica** | IAM (start/end impersonation) |
| **Dependencias** | Platform Operator, Tenant Registry |

### I-09 IAM Audit Record

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | IAM |
| **Modifica** | Append-only IAM |
| **Consumidores** | Security, Platform |

### I-10 Effective Permission Set (derivado)

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **IAM** (derivación) — fuentes: Product Permission + Grants |
| **Modifica** | Recalculado ante cambio grants; cache IAM |
| **No es SSOT** | Derivado |

---

## 4. Tenant Administration (Data Plane — no ERP)

### T-01 Tenant Branding

| Dueño | Tenant Admin | Modifica: Tenant Admin | Dep: Tenant Registry |

### T-02 Module Activation

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **Platform** autoriza; **Tenant** recibe asignación |
| **SSOT funcional** | Platform (qué módulos existen) + Assignment (qué tiene el tenant) |
| **Modifica** | Platform (plan), Superadmin, Onboarding |
| **Consumidores** | ERP (feature gate), Menu resolver |

### T-03 Role (Tenant)

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **Tenant** |
| **Modifica** | Tenant Admin, Onboarding (roles sistema seed) |
| **Consumidores** | IAM, RBAC endpoints |
| **Dependencias** | Tenant Registry |

### T-04 Role-Permission Grant / T-05 Role-Menu Grant

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **Tenant** |
| **Modifica** | Tenant Admin, Onboarding |
| **Referencia** | Product Permission / Product Menu (Platform, read-only) |
| **Dependencias** | Role, Product Permission |

### T-06 User-Role Assignment

| Dueño | Tenant (admin) + IAM enforcement | Modifica: Tenant Admin |

### T-07 Company (Empresa)

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **Tenant** (administración) / **ERP-ORG** (operación) |
| **Resolución** | Dueño funcional único: **Tenant** — ERP consume como maestro estructural |
| **Modifica** | Tenant Admin, Onboarding (seed) |
| **Consumidores** | Todo ERP (scope empresa) |
| **Dependencias** | Tenant Registry |

### T-09 Document Sequence

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **ERP** (dominio codificación documentos) |
| **Modifica** | ERP services internos, Onboarding (seed inicial) |
| **Consumidores** | ERP document creation |
| **Dependencias** | Tenant Registry, Company (scope) |

---

## 5. ERP Operational Data

**Dueño unificado: ERP** (en nombre del Tenant como titular de datos).

| Categoría | Datos | Modifica | Lee |
|-----------|-------|----------|-----|
| Maestros | Product, Supplier, Customer, Warehouse, … | Usuario ERP autorizado | Usuarios ERP |
| Documentos | Movement, Order, Journal Entry, … | Workflow ERP | Usuarios ERP |
| Derivados | Stock, Kardex, Balances | Solo pipeline ERP | Usuarios ERP |
| Config operativa | Org Parameter | Tenant Admin / ERP admin | ERP |

**Platform:** solo lectura **prohibida** salvo soporte auditado.  
**IAM:** no modifica; solo verifica permiso.

---

## 6. Reference Catalogs

### R-01..R-03 Geographic / Currency

| Aspecto | Detalle |
|---------|---------|
| **Dueño** | **Product Reference (Platform)** |
| **Consumidores** | ERP, Tenant forms |
| **Modifica** | Platform (releases) |
| **Réplica** | Permitida read-only en data plane (ver SSOT doc) |

---

## 7. Auditoría

| Dato | Dueño | Append por |
|------|-------|------------|
| ERP Audit | Tenant/ERP | ERP services |
| Platform Audit | Platform | Platform/IAM superadmin |
| IAM Audit | IAM | IAM services |

---

## 8. Reglas de ownership cruzado (prohibiciones)

| Prohibición | Motivo |
|-------------|--------|
| Platform dueño de Stock | Viola D2 |
| ERP dueño de Product Permission | Viola D2 |
| IAM dueño de Purchase Order | Viola D3 |
| Tenant dueño de Product Module definition | Viola catálogo producto |
| Company dueño de Installation Mode | Confunde scope |

---

## 9. Resumen ownership por dominio

| Dominio | Dueño primario |
|---------|----------------|
| Tenant Registry, License, Installation | Platform |
| Product Catalog | Platform |
| User Identity | IAM (+ admin delegado Tenant) |
| Session, Tokens | IAM |
| Roles, Grants, Module Activation | Tenant (grants) / Platform (catálogo) |
| Company, Org structure | Tenant / ERP-ORG |
| ERP transaccional | ERP |
| Reference catalogs | Platform (REF) |
| Audit | Dominio emisor |
