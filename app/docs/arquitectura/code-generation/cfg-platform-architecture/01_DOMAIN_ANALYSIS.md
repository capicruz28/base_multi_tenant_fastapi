# Análisis de dominio — Motor vs Administrador

**Paquete:** `cfg-platform-architecture`  
**Fecha:** 2026-07-17

---

## 1. Responsabilidad del Motor de Códigos

| Aspecto | Definición |
|---------|------------|
| Ubicación | `app/core/codigo/` (infraestructura compartida, no módulo ERP) |
| Qué es | Motor de generación/asignación/validación de códigos |
| Qué no es | Pantalla de configuración; API de administración tenant |
| Consumidores | Services ORG, INV y futuros ERP vía `CodigoGeneracionGateway` |
| Persistencia que usa | `cfg_codigo_secuencia` (store CFG) + series fiscales (store FISCAL) |
| Gobernanza normativa | `SequenceCatalog` (inmutable en runtime tenant) |

**Clasificación:** **infraestructura de plataforma de aplicación** (shared kernel), no dominio de negocio ORG/INV ni control plane SaaS.

---

## 2. Responsabilidad del Administrador del Motor

| Aspecto | Definición |
|---------|------------|
| Qué es | Capacidad de **consultar y parametrizar** filas `cfg_codigo_secuencia` del tenant |
| Qué permite | Ver secuencias, ajustar formato/activo, preview; (post-MVP) align/diagnóstico |
| Qué prohíbe | Mutar Catalog; PATCH libre de `ultimo_numero`; cambiar scope/key/policy desde UI |
| Relación con Motor | **Cliente** del Gateway para preview/align/validate — no reimplementa formato |
| Relación con negocio | No crea cargos ni productos; solo afecta **cómo** se numerarán futuros códigos |

**Clasificación candidata evaluada:** configuración **operativa del tenant** sobre datos ERP → dominio **ERP**, no Platform Admin.

---

## 3. Diferencia infraestructura vs negocio

| Capa | Ejemplo | Dueño |
|------|---------|-------|
| Infraestructura de generación | Gateway, Catalog, Formatter, Store | `core/codigo` |
| Dato de configuración/runtime | Filas cfg (prefijo, contador, activo) | BD tenant |
| Dominio de negocio | Cargo, Producto, Movimiento | ORG / INV / … |
| Control plane SaaS | Cliente, plan, módulos suscritos, conexiones | Platform (`tenant`, `modulos`, …) |
| **Admin del Motor** | API sobre filas cfg | **ERP módulo `cfg`** (orquesta; no es el Motor) |

Confundir “administrar el Motor” con “pertenece a Platform” es un error de categoría: se administra un **dato tenant**, no el **catálogo SaaS** ni el **código del Motor**.

---

## 4. Relación con Tenant / Cliente / Empresa

| Entidad | Rol respecto al admin |
|---------|------------------------|
| **Tenant (`cliente_id`)** | Ámbito de aislamiento y autorización primaria. Toda query filtra por cliente operativo de sesión. |
| **Cliente (tabla `cliente`)** | Identidad SaaS en ADMIN. Onboarding **crea** el tenant y **siembra** cfg; no almacena las secuencias. |
| **Empresa (`org_empresa`)** | Dimensión de scope EMPRESA en filas cfg; filtro de listado; **no** sustituye al tenant como dueño del recurso. |

El Administrador opera **dentro de un tenant ya provisionado**, no crea tenants.

---

## 5. Relación con ORG / INV / futuros ERP

| Módulo | Relación |
|--------|----------|
| **ORG** | Consumidor del Motor. Beneficiario de cambios de formato en keys `org_*`. No es dueño del admin. |
| **INV** | Idem para keys `inv_*` y scopes ALMACEN. |
| **Futuros (PUR, SLS, POS, …)** | Nuevas keys en Catalog → filas cfg seed/lazy → visibles en el mismo admin transversal. |

**Conclusión de acoplamiento:** el admin debe ser **independiente** de services ORG/INV. Dependencia permitida: metadatos read-only de `SequenceCatalog` (`modulo_codigo`).

---

## 6. Usuarios de la funcionalidad

| Perfil | ¿Usa el Admin del Motor? | ¿Es usuario Platform? |
|--------|--------------------------|------------------------|
| **ADMIN_TENANT** | **Sí** — usuario primario | No (es tenant) |
| Responsable parametrización / implantación en el tenant | Sí (actualizar / mantener) | No |
| MANAGER / USER operativo | Consulta limitada o ninguna | No |
| **SuperAdmin / platform_admin** | No en flujo normal; soporte vía **impersonación** al tenant | Sí |
| Onboarding automatizado | Escribe seed (Platform) — no es “uso” del admin UI | Sí (sistema) |

Si el usuario primario es Tenant Admin y el dato es tenant-scoped, el producto es **ERP de configuración**, no consola Platform.

---

## 7. ERP operativo vs Platform Admin

| Criterio | Platform Administration | ERP operativo | Admin Motor |
|----------|-------------------------|---------------|-------------|
| Dato en ADMIN central | Sí | No | **No** (cfg en tenant) |
| Dato en DEFAULT tenant | No (salvo excepciones IAM mixtas) | Sí | **Sí** |
| LBAC + SuperAdmin | Sí | No | **No** |
| `require_erp_session` | No | Sí | **Sí** |
| Cross-tenant nativo | Sí (SA) | No | **No** |
| Persona diaria | Platform ops | Tenant users | **Tenant Admin** |

**Veredicto de dominio:** encaja en **ERP operativo** (recurso de configuración transversal), no en Platform Administration.

---

## 8. Módulo independiente vs capacidad Platform

| Opción | Evaluación |
|--------|------------|
| Capacidad dentro de `tenant` (como Branding) | **Rechazada** — Branding vive en `cliente` (ADMIN); cfg no |
| Capacidad dentro de `modulos` | **Rechazada** — `modulos` gobierna suscripción SaaS, no contadores |
| Extensión de `org` (parámetros) | **Rechazada** — sesga el Motor a un solo dominio |
| **Módulo ERP independiente `cfg`** | **Elegida** — transversal, checklist V4, RBAC propio, sin contaminar Platform |

“Capacidad de Plataforma” en sentido SaaS (control plane) ≠ “capacidad de la plataforma de aplicación” (`core/codigo`). El admin es lo segundo expuesto como **módulo ERP**.
