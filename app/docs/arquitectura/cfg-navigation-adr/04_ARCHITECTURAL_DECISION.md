# ADR formal — Plano de navegación del módulo CFG

**Status:** Proposed → **Accepted (recomendación arquitectónica)**  
**Date:** 2026-07-18  
**Deciders:** Arquitectura Backend + Frontend ERP  
**Tags:** navigation, shell, cfg, multi-tenant, saas

---

## Context

El módulo CFG (Administrador de secuencias de código) está:

- Certificado como **dominio ERP** con API `/api/v1/cfg`
- Documentado como **no Platform Administration**
- Orientado a **ADMIN_TENANT** / parametrización
- Aún **sin** registro en menú dinámico

Existen dos modelos de navegación FE posibles:

- **A:** `/app/cfg/*` (plano ERP operativo, como ORG/INV/WMS)
- **B:** `/admin/...` (plano Tenant Administration), manteniendo dominio/API/módulo propios

Una auditoría previa de *registro* concluyó correctamente que CFG es **módulo propio** en catálogo.  
Eso **no** decide el prefijo de shell. Este ADR cierra esa dimensión.

---

## Decision

Adoptar el **Modelo B** para el plano de navegación:

1. Mantener dominio, API, OpenAPI, permisos y patrón de módulo propio `CFG`.
2. Ubicar la navegación Frontend y `modulo_menu.ruta` bajo el shell **Tenant Administration** (`/admin/...`).
3. Rechazar ubicar CFG bajo Platform (`/super-admin`).
4. No exigir `/app/cfg` como consecuencia del dominio ERP.

Ruta ilustrativa (no implementación; no fija naming final):

```text
/admin/configuracion/secuencias
```

(o estructura equivalente coherente bajo `/admin`).

---

## Consequences

### Positive

- Shell alineado al perfil real de usuario (Tenant Admin / implantación).
- Separación clara: **operar el ERP** (`/app`) vs **configurar el tenant** (`/admin`).
- Escalabilidad de futuras pantallas de configuración tenant bajo el mismo plano.
- Coherencia con IAM UI existente en `/admin`.
- Cero impacto en Backend certificado `/cfg`.

### Negative / costs

- Rompe la simetría “todo módulo ERP aparece en `/app`” (coste de consistencia visual, no técnico).
- El Frontend debe evitar meter CFG automáticamente en mapas operativos tipo `ERP_MODULES` → `/app`.
- Posible doble permiso de puerta: `admin.tenant.access` + `cfg.secuencias.*` (aceptable y ya modelado).

### Neutral

- Registro futuro de catálogo (`modulo`, `modulo_menu`, `cliente_modulo`, RMP) sigue siendo necesario para `/auth/menu`; solo cambia el **valor de `ruta`**.

---

## Alternatives considered

### Alternative A — `/app/cfg/*`

**Pros:** Simetría con ORG/INV/WMS.  
**Cons:** Desalinea UX con usuario primario; mezcla configuración sensible en sidebar operativo.  
**Rejected** como plano de navegación (no como patrón de módulo).

### Alternative C — Embebido solo en `SYS_ADMIN` sin módulo `CFG`

**Pros:** Reutiliza `cliente_modulo(SYS_ADMIN)`.  
**Cons:** Contradice decisión de módulo propio `cfg` + API independiente.  
**Rejected** (fuera del Modelo B; el Modelo B **conserva** módulo `CFG`).

### Alternative D — `/super-admin`

**Pros:** Ninguno válido.  
**Cons:** Viola platform-architecture (Platform vs ERP).  
**Rejected**.

---

## Compliance with prior ADRs

| ADR / paquete | Cumplimiento |
|---------------|--------------|
| `cfg-platform-architecture` | Cumple: dominio ERP, no Platform |
| `cfg-menu-registration-audit` | Cumple: módulo propio; **precisa** que shell ≠ `/app` obligatorio |
| Frontend contract CFG | Cumple: API y permisos intactos; menú sigue exigiendo `cfg.secuencias.consultar` |

---

## Explicit answers (normative)

### ¿Restricción técnica `/app`?

**No existe.** Evidencia: `menu_route_normalizer`, menú data-driven, permisos de plano ortogonales, precedente `/admin` en el mismo producto.

### ¿Qué tipo de cambio es A→B?

**Únicamente navegación / Information Architecture Frontend** (más el valor de `modulo_menu.ruta`).  
No es cambio de dominio ni de arquitectura Backend del módulo CFG.
