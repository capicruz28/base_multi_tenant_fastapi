# 01 — Bootstrap V2: Arquitectura objetivo (TO-BE)

**Etapa:** Diseño arquitectónico oficial  
**Base:** Auditoría AS-IS (`app/docs/arquitectura/bootstrap-v2/01`–`06`)  
**Estado:** Solo diseño. Sin implementación. Sin cambio de comportamiento observable.

---

## 1. Propósito

Bootstrap V2 es una **reorganización interna de responsabilidades** en tres capas nombradas y extensibles:

| Capa | Rol | Alcance temporal |
|------|-----|------------------|
| **Platform Bootstrap** | Instalación y operación del Control Plane global | Una vez por instalación |
| **Tenant Bootstrap** | Orquestador del onboarding completo de un cliente | Una vez por tenant |
| **Empresa Bootstrap** | Materialización de una `org_empresa` y sus artefactos derivados | Una vez por empresa (1ª invocada automáticamente en onboarding) |

**Principio rector:** el usuario y los contratos API **no perciben** la separación. `POST /clientes` sigue produciendo el mismo resultado observable que hoy.

---

## 2. Modelo de capas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PLATFORM BOOTSTRAP                               │
│  Instalación · Catálogos globales · Identidad superadmin · RBAC CP   │
│  Frecuencia: 1× por instalación                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ prerequisito
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         TENANT BOOTSTRAP                                │
│  ORQUESTADOR — invoca automáticamente Empresa Bootstrap para EMP001     │
│  Frecuencia: 1× por cliente (Shared TX / Dedicated S7)                 │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ invocación interna automática (paso 3)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EMPRESA BOOTSTRAP                                │
│  org_empresa · cfg EMPRESA · preferencias admin (1ª empresa)             │
│  Frecuencia: 1× por org_empresa · reutilizable para empresa N            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ extensión futura (plug-in)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              DOMINIO BOOTSTRAPS (futuro — extensión V2)                   │
│  Warehouse · PuntoVenta · CentroCostos · Producción · Contabilidad       │
│  Frecuencia: por entidad de dominio · invocados desde ORG/runtime       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fronteras normativas

### 3.1 Platform Bootstrap

**Qué es:** todo lo que ocurre **antes** de existir tenants operativos y **sin** `cliente_id` de tenant de negocio (excepto el cliente platform fijo).

**Qué NO es:** onboarding de clientes SaaS, seed ERP por tenant, provisioning Dedicated.

**Componentes AS-IS que permanecen en esta capa (sin mover comportamiento):**
- SQL `bootstrap_v2` (schema + catálogos globales)
- Startup `permission_sync`
- CLI `PlatformBootstrapService` + identidad/RBAC platform

**Excepción DA-04-E1 — RBAC compartido:** `OnboardingRbacService`, catálogo `permiso`/`modulo_menu` y `permission_sync` son **leídos/consumidos** por Tenant Bootstrap (T-RBAC) pero **inicializados** por Platform (P-CAT, P-SYNC). Platform no orquesta onboarding; Tenant no escribe catálogos globales. Ver `03` §1.

### 3.2 Tenant Bootstrap

**Qué es:** el **único orquestador** del onboarding de un cliente. Coordina pasos tenant-scoped e **invoca** Empresa Bootstrap como sub-rutina interna.

**Qué NO es:** lógica de creación de `org_empresa` ni seed cfg EMPRESA (delegado a Empresa Bootstrap).

**Invariante UX:** un solo proceso, un solo endpoint, un solo resultado — igual que hoy.

**Componentes AS-IS que evolucionan a orquestación:**
- `ClienteOnboardingService.crear_cliente_con_onboarding` (Shared)
- `DedicatedTenantSeedService` + adapters (Dedicated S7)

### 3.3 Empresa Bootstrap

**Qué es:** componente **interno reutilizable** que, dado `(session, cliente_id, datos_empresa)`, materializa una empresa y sus artefactos de bootstrap asociados.

**Qué NO es:** un endpoint público ni un paso visible para el usuario en onboarding inicial.

**Componentes AS-IS que consolidan esta capa (conceptualmente):**
- `MinimalErpTenantBootstrapService.ensure_empresa_inicial`
- `MinimalErpTenantBootstrapService.vincular_admin_empresa`
- Subset EMPRESA de `_insertar_secuencias_codigo`

---

## 4. Contrato de observabilidad (sin cambios)

Al finalizar `POST /clientes` (Shared) o la saga Dedicated exitosa, el sistema debe contener **exactamente** los mismos artefactos que hoy:

| # | Artefacto | Scope |
|---|-----------|-------|
| 1 | `cliente` | Tenant |
| 2 | Roles base (×3) | Tenant |
| 3 | `org_empresa` EMP001 | Empresa |
| 4 | Usuario admin | Tenant |
| 5 | Vínculo admin ↔ empresa default | Empresa (preferencia) |
| 6 | RBAC plan + bundles | Tenant |
| 7 | `cliente_auth_config` | Tenant (CP) — Shared sí; Dedicated ADJ-07 deuda AS-IS |
| 8 | `cfg_codigo_secuencia` ×57 | 1 TENANT + 56 EMPRESA |

**Orden observable:** idéntico al AS-IS (ver `02`).

---

## 5. Ubicación física (Shared vs Dedicated)

Bootstrap V2 **no cambia** dónde viven los datos:

| Modo | Tenant Bootstrap | Empresa Bootstrap | Platform |
|------|------------------|-------------------|----------|
| **Shared** | TX ADMIN única | Misma TX (sub-rutina) | CP preexistente |
| **Dedicated** | S7 sobre BD dedicada | Misma sesión S7 (sub-rutina) | CP + S4/S5/S6 |

---

## 6. Relación con el Motor de Códigos

| Responsabilidad | Owner V2 |
|-----------------|----------|
| Metadatos secuencia (`SequenceCatalog`) | Motor (sin cambio) |
| Subconjunto eager (TENANT/EMPRESA) | Motor / `onboarding_seed` (sin cambio) |
| **Cuándo** sembrar TENANT scope | Tenant Bootstrap |
| **Cuándo** sembrar EMPRESA scope | Empresa Bootstrap |
| Lazy ALMACEN/PV | Motor runtime (`ensure_row`) — fuera bootstrap |

---

## 7. Servicios conceptuales nuevos (solo diseño)

| Servicio conceptual | Rol |
|-------------------|-----|
| `EmpresaBootstrapService` | Facade interna: `bootstrap_empresa(...)` |
| `TenantBootstrapOrchestrator` (nombre conceptual) | Coordina pasos tenant + invoca Empresa Bootstrap |
| `BootstrapExtensionRegistry` (futuro) | Registro plug-in para dominio bootstraps |

Los nombres son **conceptuales**. La implementación puede evolucionar métodos existentes sin renombrar en esta etapa.

---

## 8. Decisiones arquitectónicas oficiales (DA)

| ID | Decisión |
|----|----------|
| DA-01 | Tenant Bootstrap permanece **orquestador único** del onboarding |
| DA-02 | Empresa Bootstrap es **interno**; primera empresa **automática** en onboarding |
| DA-03 | **Cero** cambio en contratos API y UX |
| DA-04 | Platform Bootstrap permanece **aislado** del onboarding tenant (excepción DA-04-E1: RBAC compartido lectura) |
| DA-05 | Separación es **organizacional**, no funcional |
| DA-06 | Multi-empresa futura invoca Empresa Bootstrap desde ORG, no reabre Tenant Bootstrap |
| DA-07 | Dominio bootstraps futuros son **extensiones**, no modifican Tenant/Empresa core |

---

*Flujo de ejecución: `02`. Mapa de responsabilidades: `03`. Extensiones: `04`. Estrategia incremental: `05`.*
