# 06 — Bootstrap V2: Resumen ejecutivo y decisiones oficiales

**Etapa:** Diseño arquitectónico TO-BE  
**Fecha:** 2026-07-09  
**Estado:** Diseño corregido post-revisión ARB — **sin implementación**

---

## 1. Decisión principal

Se adopta oficialmente **Bootstrap V2** como reorganización interna en tres capas:

| Capa | Rol |
|------|-----|
| **Platform Bootstrap** | Instalación global + identidad CP |
| **Tenant Bootstrap** | **Orquestador único** del onboarding cliente |
| **Empresa Bootstrap** | Componente **interno reutilizable** por empresa |

**El comportamiento observable del sistema no cambia.** `POST /clientes` produce el mismo resultado que hoy.

---

## 2. Respuestas consolidadas (preguntas 1–14)

### 1. División Platform Bootstrap
P-SCH, P-CAT, P-SYNC, P-ID, P-RBAC, P-AUD — ver `03` §1. Aislado del onboarding tenant.

### 2. División Tenant Bootstrap
T-REG, T-ROL, T-USR, T-RBAC, T-AUTH, T-CFG-T, T-ORCH, T-DED — ver `03` §2. Orquesta e invoca Empresa Bootstrap.

### 3. División Empresa Bootstrap
E-ORG, E-LNK, E-CFG, E-IDEM — ver `03` §3. Interno; no expuesto en onboarding UX.

### 4. Responsabilidades por capa
Matriz R01–R16 en `03` §4.

### 5. Qué pasa de Tenant → Empresa
`ensure_empresa_inicial`, `vincular_admin_empresa`, 56 cfg EMPRESA — `03` §5.

### 6. Exclusivo Tenant Bootstrap
Registro cliente, roles, admin, RBAC, auth config, 1 cfg TENANT, orquestación, saga Dedicated — `03` §6.

### 7. Comunicación Tenant ↔ Empresa
Tenant posee session/TX; invoca `EmpresaBootstrapService` con contrato interno; retorna `empresa_id` — `02` §4.

### 8. Orden oficial ejecución
1→8 idéntico AS-IS; pasos 3, 5, 56 cfg delegados internamente a Empresa Bootstrap — `02` §5.

### 9. Reutilizables sin modificación (fase 1)
Platform services, RBAC, AuthConfigGateway, SequenceCatalog, repository con session, Dedicated saga infra — `03` §7.

### 10. Orquestadores
`crear_cliente_con_onboarding`, `DedicatedTenantSeedService`, adapters S7, `PlatformBootstrapService` — `03` §8.

### 11. Servicios nuevos (conceptuales)
`EmpresaBootstrapService`, Tenant orchestrators (Shared/Dedicated), `BootstrapExtensionRegistry` (futuro) — `03` §9.

### 12. Multi-empresa sin re-modificar Tenant Bootstrap
ORG invoca Empresa Bootstrap modo `ADDITIONAL`; Tenant solo en onboarding inicial — `04` §1.

### 13. Bootstraps futuros (Warehouse, PV, etc.)
Plug-in vía `BootstrapExtensionRegistry`; invocados por módulo ERP owner; no tocan Tenant/Empresa core — `04` §2.

### 14. Principios oficiales
P1–P12 en `04` §3 (orquestación, session-driven, idempotencia, atomicidad, SSOT motor, scope, no observable change, paridad, plug-in, CP/DP, fail-closed, verificabilidad).

---

## 3. Decisiones arquitectónicas oficiales (DA-01 – DA-07)

| ID | Decisión | Estado |
|----|----------|--------|
| DA-01 | Tenant Bootstrap = orquestador único onboarding | **Aprobado diseño** |
| DA-02 | Empresa Bootstrap = interno; EMP001 automática | **Aprobado diseño** |
| DA-03 | Cero cambio contratos API / UX | **Aprobado diseño** |
| DA-04 | Platform Bootstrap aislado | **Aprobado diseño** (ver excepción DA-04-E1 en `01` §3.1) |
| DA-05 | Separación organizacional, no funcional | **Aprobado diseño** |
| DA-06 | Multi-empresa vía Empresa Bootstrap + ORG | **Aprobado diseño** |
| DA-07 | Dominio bootstraps = extensiones plug-in | **Aprobado diseño** |

---

## 4. Criterios de éxito — verificación diseño

| Criterio | Cumple diseño V2 |
|----------|------------------|
| Cero cambio comportamiento observable (UX/API) | ✓ DA-03, `01` §4 |
| Compatibilidad Shared | ✓ `02` §2, `05` §4.1 |
| Compatibilidad Dedicated (seed ERP S7) | ✓ `02` §3, `05` §4.2 |
| Onboarding actual conservado | ✓ secuencia 1–8 |
| Primera empresa automática | ✓ DA-02, `02` §5 paso 3 |
| Contratos API conservados | ✓ DA-03 |
| Bootstrap actual durante migración | ✓ Strangler `05` |
| Separación Platform/Tenant/Empresa | ✓ `01` §2 |
| Multi-empresa preparado | ✓ `04` §1 |
| Bootstraps especializados futuros | ✓ `04` §2 |

### 4.1 Definiciones normativas: compatibilidad vs paridad (Dedicated)

| Término | Significado en Bootstrap V2 |
|---------|----------------------------|
| **Compatibilidad** | El refactor V2 **no altera** el comportamiento AS-IS existente. Misma secuencia, mismos artefactos ERP en BD tenant, mismos contratos saga/API. |
| **Paridad Shared/Dedicated** | Misma **semántica de seed tenant** (roles, empresa, admin, RBAC, cfg×57 en BD operativa). Distinta **ruta física** (TX ADMIN vs saga S7 + markers). |
| **Paridad artefactual CP** | Presencia idéntica de artefactos en Control Plane (`cliente_auth_config`, provisioning metadata). |
| **Deuda técnica AS-IS (fuera V2 core)** | Gaps documentados antes de V2 que V2 **no introduce** ni **resuelve** en Fases 1–4 salvo decisión explícita. |

### 4.2 Dedicated — estado explícito

| Aspecto | Shared | Dedicated AS-IS | Bootstrap V2 Fases 1–4 |
|---------|--------|-----------------|------------------------|
| Seed ERP S7 (roles, EMP001, admin, RBAC, cfg×57) | TX única | Markers S7 | **Paridad semántica** — sin cambio |
| `cliente_auth_config` en CP | Paso 7 onboarding | **No en S7** (ADJ-07) | **Deuda AS-IS** — no bloquea V2 core |
| Atomicidad onboarding | Strong (1 TX) | Eventual (markers) | Preservado AS-IS |
| Saga S1–S10 | N/A | Contrato público | Sin cambio |

**ADJ-07** (`cliente_auth_config` Dedicated): clasificado como **deuda técnica preexistente**, no como requisito de Bootstrap V2 Fases 1–4. Si se cierra, es **fix de paridad CP** independiente del refactor de facades (ver `05` Fase 3 nota ADJ-07); altera artefactos CP y requiere gate de tests propio — **no** forma parte del criterio "cero cambio observable UX".

**Conclusión Dedicated:** Bootstrap V2 garantiza **compatibilidad** y **paridad semántica seed ERP**. No garantiza **paridad artefactual CP** hasta cierre ADJ-07 (deuda AS-IS).

---

## 5. Entregables diseño

| Documento | Ubicación |
|-----------|-----------|
| Arquitectura objetivo | `design/01_BOOTSTRAP_V2_ARCHITECTURE.md` |
| Flujo ejecución | `design/02_BOOTSTRAP_EXECUTION_FLOW.md` |
| Mapa responsabilidades | `design/03_BOOTSTRAP_RESPONSIBILITY_MAP.md` |
| Modelo extensión | `design/04_BOOTSTRAP_EXTENSION_MODEL.md` |
| Estrategia incremental | `design/05_IMPLEMENTATION_STRATEGY.md` |
| Resumen ejecutivo | `design/06_EXECUTIVE_SUMMARY.md` |

**Base AS-IS:** `app/docs/arquitectura/bootstrap-v2/01`–`06` (no modificados).

---

## 6. Próximo paso

Iniciar **Fase 1** de implementación incremental (`05` §2) tras esta corrección documental.

---

## 7. Confirmaciones

- ✓ No se modificó código, SQL, tests ni contratos API.
- ✓ Documentación AS-IS (`bootstrap-v2/01`–`06`) no modificada.
- ✓ Arquitectura V2 (tres capas, flujo 1–8, orquestación Tenant) **sin cambios**.
- ✓ Correcciones documentales P0–P2 aplicadas en `design/`.
- ✓ Diseño listo para Fase 1 (`05` §2, §8 gates).
