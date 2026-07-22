# ADR — Ubicación del Administrador del Motor de Códigos

**Paquete:** `cfg-platform-architecture`  
**ID:** ADR-CFG-ADMIN-LOC-001  
**Fecha:** 2026-07-17  
**Estado:** **Propuesto / pendiente de aprobación ejecutiva** (documentación; sin implementación)

---

## 1. Contexto

La auditoría `cfg-admin-audit/` demostró que:

- Existe fundación de datos y Motor (`cfg_codigo_secuencia`, Store, Gateway, Catalog).
- **No** existe módulo funcional de administración.
- El diseño previo `codigo-generation-admin/` asumió un módulo ERP `cfg`.

Antes de diseñar endpoints, debe consolidarse si esa asunción es correcta frente a la arquitectura SaaS (Platform vs ERP), comparando Branding, Onboarding, Tenant Management e IAM.

---

## 2. Decisión

**Se decide implementar el Administrador del Motor de Códigos como módulo ERP operativo transversal `cfg`**, bajo checklist V4 (DEFAULT, `require_erp_session`, RBAC `cfg.secuencias.*`, impersonación-safe deps).

**No** se implementa como capacidad de Platform Administration (`tenant`, `superadmin`, `modulos`).

**No** se implementa como sub-recurso de ORG ni INV.

**El Motor** permanece en `app/core/codigo/` (shared kernel); el módulo `cfg` es orquestación administrativa, no reubicación del Motor.

---

## 3. Opciones consideradas

### Opción A — Módulo ERP `cfg` (**elegida**)

| Pros | Contras |
|------|---------|
| Alineado a localidad del dato (DEFAULT) | Nuevo código de módulo a construir (~70% producto) |
| Persona correcta (Tenant Admin) | Requiere seed RBAC/menú |
| Compatible Dedicated/Shared (ADJ-03) | Nombre `cfg` puede confundirse con “config platform” — mitigar en docs/UX |
| Transversal a ORG/INV/futuros | — |
| Ratifica diseño `codigo-generation-admin/` | — |
| Checklist ERP V4 ya probado en Ola 1 | — |

### Opción B — Capacidad Platform (`tenant` / `/clientes`)

| Pros | Contras |
|------|---------|
| Reutiliza módulo tenant existente | **Viola §15** (ADMIN vs datos ERP) |
| Agrupa “configuración” junto a branding | Branding ≠ cfg (distinto store) |
| SA podría ver todos los tenants | Cross-tenant indeseable; Dedicated broken |

**Rechazada.**

### Opción C — Capacidad SuperAdmin / soporte L2 en Platform

| Pros | Contras |
|------|---------|
| Útil para implantación multi-tenant | Persona equivocada para uso diario |
| | Contadores no son catálogo global |
| | Impersonación + RBAC `mantener` en ERP cubre soporte sin mover el dominio |

**Rechazada** como ubicación primaria. Soporte = impersonación + permisos elevados en `cfg`, no consola Platform.

### Opción D — Extender ORG (p. ej. bajo parámetros)

| Pros | Contras |
|------|---------|
| Menos módulos nuevos | Acopla Motor a ORG; INV/POS quedan huérfanos |
| | Rompe transversalidad del Catalog |

**Rechazada.**

### Opción E — Solo `core/codigo` sin módulo (APIs internas)

| Pros | Contras |
|------|---------|
| Cero superficie HTTP nueva | Tenant Admin sin canal oficial |
| | No cumple objetivo de administración |

**Rechazada** como producto admin (el Motor sí permanece en core).

---

## 4. Consecuencias

### Positivas

1. Frontera clara: Platform provisiona; ERP `cfg` parametriza; Motor ejecuta.
2. Sin regresión de aislamiento multi-tenant / Dedicated.
3. OpenAPI y Frontend seguirán el mismo patrón que ORG/INV (sesión ERP + RBAC).
4. Futuros módulos ERP heredan el admin sin trabajo de Platform.

### Negativas / costos

1. Hay que crear `app/modules/cfg/` completo (hoy 0%).
2. Hay que sembrar permisos y entrada de menú.
3. Debe documentarse en UX que “CFG” = configuración de códigos ERP, no consola SaaS.

### Invariantes (no negociables post-decisión)

- No ADMIN para mutaciones de `cfg_codigo_secuencia` operacionales.
- No LBAC como gate primario del admin.
- No PATCH de `ultimo_numero` fuera de Gateway.align.
- No modificar Catalog/Gateway/ORG/INV como parte del admin (salvo autorización explícita futura).

---

## 5. Relación con documentos

| Documento | Efecto |
|-----------|--------|
| `cfg-admin-audit/` | AS-IS y gaps — **sigue válido**; el MVP allí descrito se ejecuta **dentro** de módulo ERP `cfg` |
| `codigo-generation-admin/` | Diseño API/RBAC — **ratificado** en ubicación de dominio |
| STANDARDS V4 §15/§21 | Norma que obliga la decisión A |

---

## 6. Respuesta canónica (cita)

> **¿Módulo ERP (CFG) o capacidad Platform Administration?**  
> **Módulo ERP (`cfg`).** Platform Administration no es el dueño del Administrador del Motor; solo participa en el seed de onboarding.
