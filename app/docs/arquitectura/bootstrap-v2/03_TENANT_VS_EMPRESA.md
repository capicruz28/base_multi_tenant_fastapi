# 03 — Tenant vs Empresa (separación conceptual vs AS-IS)

**Etapa:** Auditoría bootstrap-v2  
**Objetivo:** Delimitar qué es tenant-scoped vs empresa-scoped hoy y qué debería moverse.

---

## 1. Definiciones operativas (derivadas del código)

| Concepto | Identificador | Persistencia | Evidencia |
|----------|---------------|--------------|-----------|
| **Tenant** | `cliente_id` | CP (`cliente`) + datos ERP filtrados por `cliente_id` | `cliente_onboarding_service._insertar_cliente` |
| **Empresa** | `empresa_id` | `org_empresa` bajo un `cliente_id` | `MinimalErpTenantBootstrapService.ensure_empresa_inicial` |
| **Platform** | `SUPERADMIN_CLIENTE_ID` fijo | Mismo CP, rol distinto | `PlatformRbacBootstrapService.resolve_platform_cliente_id` |

**Regla ERP V4:** todo dato operativo filtra `cliente_id`; muchas tablas además filtran `empresa_id` cuando aplica scope COMPANY.

---

## 2. Qué ejecuta hoy el Tenant Bootstrap (y no debería, según objetivo de separación)

| Paso AS-IS | Por qué es Tenant | Por qué es Empresa | Ubicación |
|------------|-------------------|--------------------|-----------|
| `ensure_empresa_inicial` | Se invoca en onboarding tenant | Crea **una** `org_empresa` (EMP001) | `minimal_erp_tenant_bootstrap_service.py:39-115` |
| `vincular_admin_empresa` | Parte del onboarding admin | Setea `usuario.empresa_default_id` para **una** empresa | `:118-193` |
| 56 filas `cfg_codigo_secuencia` EMPRESA | Iteración en onboarding tenant | Cada fila lleva `empresa_id` concreto | `_insertar_secuencias_codigo:408-422` |

**Conclusión:** el Tenant Bootstrap **asume y materializa la primera empresa** como efecto colateral obligatorio, no como fase separada invocable al crear empresas adicionales.

---

## 3. Qué debería ser exclusivo de Empresa Bootstrap (target conceptual, no implementado)

| Responsabilidad | Trigger natural | Componente actual a reutilizar |
|-----------------|-----------------|--------------------------------|
| Crear `org_empresa` | Alta de empresa (1ª o N-ésima) | `ensure_empresa_inicial` (generalizar más allá de EMP001) |
| Secuencias CFG scope EMPRESA | Por cada `empresa_id` nuevo | `_insertar_secuencias_codigo` (subset EMPRESA) |
| Preferencia login por empresa | Asignación rol/usuario por empresa | `vincular_admin_empresa` / `empresa_preference.py` |
| Lazy ALMACEN/PV secuencias | Creación almacén/PV | `AllocationCoordinator.ensure_row` (runtime, ya fuera onboarding) |

**Nota:** hoy **no existe** un `EmpresaBootstrapService` ni endpoint de "crear empresa" que dispare seed dedicado; la única creación de empresa en bootstrap es EMP001 en tenant onboarding.

---

## 4. Qué debería ejecutarse una sola vez por Tenant

| # | Responsabilidad | Evidencia | Shared | Dedicated |
|---|-----------------|-----------|--------|-----------|
| T1 | Registro `cliente` | `_insertar_cliente` | ✓ paso 1 | ✓ CP only |
| T2 | Roles sistema tenant | `_insertar_roles_base` | ✓ paso 2 | ✓ S7-1 |
| T3 | Usuario admin inicial | `_insertar_usuario_admin` | ✓ paso 4 | ✓ S7-3 |
| T4 | RBAC plan + bundles | `bootstrap_cliente_rbac` | ✓ paso 6 | ✓ S7-5 |
| T5 | Auth config CP | `_insertar_auth_config_si_no_existe` | ✓ paso 7 | **✗ gap** |
| T6 | Secuencia CFG TENANT (1 fila) | `_insertar_secuencias_codigo` TENANT scope | ✓ paso 8 | ✓ S7-6 |
| T7 | Provisioning Dedicated | saga S1–S10 | N/A | ✓ |

---

## 5. Qué debería ejecutarse por Empresa (cada `empresa_id`)

| # | Responsabilidad | Hoy | Gap multi-empresa |
|---|-----------------|-----|-------------------|
| E1 | INSERT `org_empresa` | Solo EMP001 en onboarding | No hay bootstrap para empresa #2 |
| E2 | 56 filas CFG EMPRESA | Solo para empresa sede | Nuevas empresas: sin seed automático documentado |
| E3 | `usuario.empresa_default_id` | Solo admin en onboarding | `UserService._maybe_set_empresa_default_after_role_assign` (runtime) |

---

## 6. Código que asume una única empresa (pregunta 11)

| Patrón | Archivo | Evidencia |
|--------|---------|-----------|
| Código fijo `EMP001` | `minimal_erp_tenant_bootstrap_service.py:21,80` | `CODIGO_EMPRESA_INICIAL = "EMP001"` |
| Idempotencia "primera empresa" | `:49-51` | `_get_primera_empresa_activa` — si existe cualquiera, no crea otra |
| Lookup `TOP 1 ORDER BY fecha_creacion` | `:224-230` | `_get_primera_empresa_activa` — no distingue sede vs adicional |
| Onboarding pasa un solo `empresa_id` | `cliente_onboarding_service.py:116,143-144` | Variable única tras `ensure_empresa_inicial` |
| Dedicated hydrate | `dedicated_tenant_seed_adapters.py:86-91` | Rehidrata `state.empresa_id` desde primera activa |
| Seed secuencias | `_insertar_secuencias_codigo:409-410` | Un `empresa_id` para todas las filas EMPRESA |
| Docstring servicio | `minimal_erp_tenant_bootstrap_service.py:2-4` | "una org_empresa" explícito |
| Row expectation | `tenant_seed_profiles.py:84` | `org_empresa ≥ 1` (no N empresas) |

**Matiz:** RBAC onboarding usa `empresa_id=NULL` en grants (tenant-wide) — **no** asume single-company para permisos. La asunción está en **ERP seed** y **secuencias EMPRESA**.

---

## 7. Diagrama target conceptual (solo documentación, no implementado)

```
                    ┌─────────────────────┐
                    │  Platform Bootstrap │  (1× instalación)
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
    ┌─────────▼─────────┐             ┌─────────▼─────────┐
    │  Tenant Bootstrap │             │  Tenant Bootstrap │
    │  (Shared / CP+ERP)│             │  (Dedicated saga) │
    └─────────┬─────────┘             └─────────┬─────────┘
              │                                 │
              │    ┌──────────────────────────┘
              │    │
    ┌─────────▼────▼─────────┐
    │  Empresa Bootstrap     │  (1× por org_empresa — HOY solo EMP001 en tenant flow)
    │  org_empresa + CFG×56 │
    └────────────────────────┘
```

---

## 8. Paridad Shared vs Dedicated (gaps tenant-level)

| Aspecto | Shared | Dedicated | Referencia |
|---------|--------|-----------|------------|
| Auth config CP | Sí paso 7 | No en S7 | ADJ-07 `31_IMPLEMENTATION_ADJUSTMENTS.md` |
| TX atómica completa | Una TX ADMIN | S7 markers por paso | `dedicated_tenant_seed_service.py:118` |
| Catálogos permiso/menu | Preexistentes (BD única) | S6 replica SQL | `DedicatedCatalogSeedService` |
| Mismos métodos seed | Directo | Vía adapters | `dedicated_tenant_seed_adapters.py:195` |

---

*Resumen ejecutivo y riesgos: `05`, `06`.*
