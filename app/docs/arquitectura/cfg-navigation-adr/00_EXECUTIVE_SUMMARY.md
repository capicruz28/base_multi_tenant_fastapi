# ADR — Plano de navegación CFG — Resumen ejecutivo

**Tipo:** Architectural Decision Record (navegación / shell)  
**Fecha:** 2026-07-18  
**Alcance:** Solo decisión documental. Sin código, sin seeds, sin cambio de rutas en runtime.  
**Pregunta:** ¿CFG navega bajo `/app/cfg/*` (Modelo A) o bajo Tenant Administration `/admin/...` (Modelo B)?

---

## 1. Decisión

| Dimensión | Decisión |
|-----------|----------|
| **Dominio funcional** | Sin cambio: módulo ERP transversal **`cfg`** |
| **API** | Sin cambio: **`/api/v1/cfg`** |
| **Contrato OpenAPI / permisos** | Sin cambio: `cfg.secuencias.*` |
| **Catálogo comercial** | Sin cambio de patrón: módulo propio `CFG` + `cliente_modulo` |
| **Plano de navegación FE (ADR)** | **Modelo B — Tenant Administration (`/admin/...`)** |
| **Platform (`/super-admin`)** | **Fuera de alcance / rechazado** (ya decidido en platform-architecture) |

> **Veredicto:** CFG permanece dominio ERP independiente con API propia; su **shell de navegación** correcto es **Administración del Tenant**, no el ERP operativo diario.

---

## 2. Respuestas cortas a las preguntas clave

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 2 | ¿Hay restricción técnica que obligue `/app` si hay API propia? | **No.** El Backend trata `ruta` de menú como string libre con prefijos reservados; no acopla `modulo.codigo` → `/app`. |
| 5 | ¿Qué shell representa mejor CFG? | **`/admin` (Tenant Administration)** |
| 7 | ¿El código de módulo Backend puede quedar igual? | **Sí.** `/api/v1/cfg` y `modules/cfg` no dependen del shell FE. |
| 8 | ¿Mover `/app` → `/admin` qué tipo de cambio es? | **Únicamente cambio de navegación / Information Architecture FE** (no de dominio ni de arquitectura Backend del módulo). |

---

## 3. Por qué no se contradice la arquitectura aprobada

La decisión `cfg-platform-architecture` rechazó **Platform Administration** (`/super-admin`, datos ADMIN, LBAC).  
Eso **no** equivale a imponer el prefijo FE `/app`.

“Tenant shell ERP” en esa documentación significa: **experiencia del tenant que parametriza el ERP**, no la consola SuperAdmin.  
En el modelo SaaS AS-IS del producto existen **dos shells tenant**:

| Shell | Prefijo | Contenido típico |
|-------|---------|------------------|
| ERP operativo | `/app` | ORG, INV, WMS, … |
| Tenant Administration | `/admin` | Usuarios, roles, sesiones (IAM UI) |

CFG es **parametrización / gobernanza de numeración**, no transacción operativa diaria → encaja en **`/admin`**.

---

## 4. Índice del paquete

| Doc | Contenido |
|-----|-----------|
| [`01_DOMAIN_VS_NAVIGATION.md`](01_DOMAIN_VS_NAVIGATION.md) | Desacoplamiento de conceptos + restricción técnica `/app` |
| [`02_MODEL_A_VS_MODEL_B.md`](02_MODEL_A_VS_MODEL_B.md) | Comparación de modelos |
| [`03_IMPACT_ANALYSIS.md`](03_IMPACT_ANALYSIS.md) | Impacto menú, RBAC, FE, onboarding |
| [`04_ARCHITECTURAL_DECISION.md`](04_ARCHITECTURAL_DECISION.md) | ADR formal (contexto, decisión, consecuencias) |
| [`05_FINAL_RECOMMENDATION.md`](05_FINAL_RECOMMENDATION.md) | Recomendación ejecutiva y criterios de aceptación |

---

## 5. Relación con auditorías previas

| Paquete | Qué quedó firme | Qué este ADR corrige / precisas |
|---------|-----------------|----------------------------------|
| `cfg-menu-audit` | Mecánica `/auth/menu` | — |
| `cfg-menu-registration-audit` | CFG = **módulo propio** en catálogo (no embebido solo como IAM sin `modulo CFG`) | **No** implica obligatoriamente rutas `/app/cfg/*` |
| `cfg-platform-architecture` | Dominio ERP `cfg`, no Platform | Shell FE: Tenant Admin `/admin`, no SuperAdmin |

**Aclaración normativa de este ADR:**  
*Módulo propio (`CFG`) + API `/cfg`* y *plano de navegación `/admin`* son **compatibles** y constituyen el Modelo B definido por el negocio.
