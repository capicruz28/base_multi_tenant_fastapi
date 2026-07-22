# Administrador del Motor — Consolidación arquitectónica (Platform vs ERP)

**Etapa:** Decisión de ubicación de dominio — **sin implementación**  
**Fecha:** 2026-07-17  
**Precondición:** auditoría AS-IS `cfg-admin-audit/` **cerrada**  
**Pregunta decisoria:** ¿módulo ERP (`cfg`) o capacidad de Platform Administration?

---

## 1. Dictamen ejecutivo

### Respuesta explícita

> **El Administrador del Motor de Códigos debe implementarse como un módulo ERP operativo transversal (`cfg`), no como una capacidad del dominio Platform Administration.**

| Dimensión | Decisión |
|-----------|----------|
| Dominio | **ERP operativo** (configuración tenant) |
| Código de módulo | **`cfg`** |
| Usuario primario | **ADMIN_TENANT** / roles de parametrización del tenant |
| Conexión BD | **`DatabaseConnection.DEFAULT`** + `get_connection_for_tenant` / session UoW |
| Autorización | **RBAC solo** (`cfg.secuencias.*`) — sin LBAC platform |
| Session gate | **`require_erp_session`** + `cfg_deps` (impersonación-safe) |
| Dato gobernado | `cfg_codigo_secuencia` (schema tenant / ERP) |
| Relación con Platform | Platform **siembra** en onboarding; ERP **administra** en operación |

### Qué no es

| Opción descartada | Motivo breve |
|-------------------|--------------|
| Capacidad bajo `tenant` / `/clientes` | Patrón Branding: datos en tabla `cliente` (ADMIN). cfg vive en BD tenant. |
| Capacidad `superadmin` cross-tenant | Viola aislamiento; ADMIN no es para datos ERP operacionales (STANDARDS §15). |
| Extensión de ORG o INV | El Motor es transversal a todo el ERP; no es dominio ORG/INV. |
| Mutación del Motor (`app/core/codigo`) | El admin es cliente del Gateway; el Motor permanece infraestructura compartida. |

---

## 2. Separación de ciclos de vida

```text
Platform (onboarding)
  → crea tenant + EMP001 + RBAC + seed cfg_codigo_secuencia
       ↓
ERP módulo cfg (operación)
  → Tenant Admin consulta / configura formato / preview
       ↓
Motor core/codigo (runtime)
  → ORG/INV/… allocate vía Gateway
```

**Regla de frontera:** *Platform provisiona; ERP parametriza; Motor ejecuta.*

---

## 3. Por qué no Platform Administration

1. **Localidad del dato:** `cfg_codigo_secuencia` está en el schema ERP (V010), no en el control plane (`cliente`, `cliente_modulo`, …).
2. **STANDARDS §15:** ADMIN = SaaS central; DEFAULT = datos operativos tenant. Usar ADMIN para cfg operacional está **prohibido**.
3. **STANDARDS §21:** Platform (tenant, superadmin, modulos) no sigue checklist ERP; cfg admin **sí** debe seguirlo (session scope, RBAC, pagination).
4. **Persona:** Tenant Admin parametriza su ERP; SuperAdmin no opera contadores por tenant en el día a día.
5. **Dedicated Database:** writes deben ir a la BD dedicada del tenant vía session; un CRUD platform sobre ADMIN/CP rompería ADJ-03.

La analogía con **Branding** es **incorrecta**: branding es metadata del `cliente` en ADMIN; cfg es contadores/formato por secuencia en DEFAULT.

---

## 4. Compatibilidad con decisión documental previa

El paquete `codigo-generation-admin/` (2026-07-12) ya concluyó **módulo ERP `cfg`**.  
Esta consolidación **ratifica** esa decisión tras contrastarla con Branding, Onboarding, Tenant Management e IAM — y **corrige** cualquier tentación de reclasificarlo como Platform solo porque “aún no existe el módulo”.

---

## 5. Índice del paquete

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento — dictamen |
| `01_DOMAIN_ANALYSIS.md` | Responsabilidades, usuarios, relaciones |
| `02_PLATFORM_BOUNDARIES.md` | Comparación Branding / Onboarding / Tenant / IAM |
| `03_ARCHITECTURE_DECISION.md` | ADR formal (opción elegida y descartadas) |
| `04_RECOMMENDED_STRUCTURE.md` | Estructura de módulo y fronteras |
| `05_IMPLEMENTATION_GUIDELINES.md` | Guías cuando se autorice implementar (sin código ahora) |

---

*Sin cambios de código. Siguiente paso: aprobación del ADR antes de diseñar endpoints detallados o MVP.*
