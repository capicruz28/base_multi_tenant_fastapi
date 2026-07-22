# Análisis de impacto — Modelo B (navegación `/admin`)

> Alcance: impacto **si** se adopta el ADR (Modelo B).  
> **No** implementa cambios. Inventario de superficies afectadas.

---

## 1. Lo que no cambia (Backend de dominio)

| Superficie | Impacto Modelo B |
|------------|------------------|
| `app/modules/cfg/` | **Ninguno** |
| Prefijo API `/api/v1/cfg` | **Ninguno** |
| OpenAPI / `frontend-contracts/cfg` (API) | **Ninguno** en paths HTTP |
| `require_erp_session` / `cfg_deps` | **Ninguno** |
| `cfg_codigo_secuencia` / Motor | **Ninguno** |
| Permisos `cfg.secuencias.*` | **Ninguno** (siguen siendo el gate de negocio) |

**Respuesta §7:** el código de módulo Backend CFG puede permanecer **exactamente igual** aunque cambie el shell Frontend.

---

## 2. Menú dinámico (`GET /auth/menu`)

| Aspecto | Impacto |
|---------|---------|
| Mecánica Q1/Q2 | Sin cambio |
| Campo afectado | `modulo_menu.ruta` → valor bajo `/admin/...` |
| Normalizer | Respeta `/admin/` (prefijo reservado); no reescribe a `/app` |
| Forma del árbol | Módulo `CFG` aparece como nodo propio; la ruta determina el shell FE |
| Separación de sidebars FE | FE ya parte por prefijo de ruta; CFG caería en sidebar **admin** |

---

## 3. `PermissionGuard` / `usePermission()` / `/auth/permissions/me`

| Aspecto | Impacto |
|---------|---------|
| Códigos de negocio | Siguen siendo `cfg.secuencias.consultar` / `actualizar` |
| Gate de menú FE | Contrato ya exige `consultar` para entrada |
| Gate de shell (opcional) | FE puede además exigir `admin.tenant.access` para rutas `/admin/*` (precedente S020) |
| Conflicto | No: plano (`admin.tenant.access`) ⊥ dominio (`cfg.*`) |

---

## 4. React Router / shell FE

| Aspecto | Impacto |
|---------|---------|
| Rutas React | Declarar pantallas CFG bajo árbol `/admin/...` (no `/app/cfg`) |
| Layout | Layout Tenant Admin (mismo que usuarios/roles) |
| Deep links | Prefijo `/admin` |
| `ERP_MODULES` | Si hoy asume “módulo = ruta `/app/{cod}`”, CFG **no** debe forzar esa convención; mapear shell admin o mantener CFG fuera de la lista operativa |

---

## 5. `ERP_MODULES` (Frontend)

| Aspecto | Impacto |
|---------|---------|
| Backend | No conoce `ERP_MODULES` |
| Riesgo | Acoplar “módulo certificado” ⇒ entrada automática en mapa `/app` |
| Mitigación documental | Tratar `ERP_MODULES` como mapa del **shell operativo**; CFG es módulo de **configuración** en shell admin |

---

## 6. `cliente_modulo`

| Aspecto | Impacto Modelo B |
|---------|------------------|
| ¿Sigue existiendo fila CFG? | **Sí** (Modelo B no elimina contrato comercial) |
| ¿Se reutiliza solo SYS_ADMIN? | **No** — contradiría módulo propio |
| Onboarding trial | Habrá que incluir `CFG` en activación cuando se registre (futuro; fuera de este ADR) |

---

## 7. `rol_menu_permiso` / Owner sync / onboarding

| Aspecto | Impacto |
|---------|---------|
| RMP | Grants sobre `menu_id` de menús del módulo **CFG** |
| OwnerSync | Sync por `modulo_codigo="CFG"` (todos los menús visibles del módulo); **no** requiere filtro `SYS_ADMIN.TENANT.%` |
| Diferencia vs IAM | IAM filtra prefijos dentro de SYS_ADMIN; CFG es módulo completo propio |
| Onboarding menú | Incluir CFG en lista de módulos a sincronizar cuando exista catálogo |

---

## 8. Matriz de impacto resumida

| Componente | ¿Cambia en Modelo B? | Tipo de cambio |
|------------|----------------------|----------------|
| Dominio / API Backend | No | — |
| Permisos `cfg.*` | No | — |
| `modulo` CFG | Sí (futuro registro) | Catálogo — independiente del shell |
| `modulo_menu.ruta` | Sí | **Navegación** → `/admin/...` |
| `cliente_modulo` | Sí (futuro) | Comercial |
| `rol_menu_permiso` | Sí (futuro) | UI visibility |
| React Router shell | Sí | **Navegación FE** |
| PermissionGuard códigos | No (mismos códigos) | Posible gate adicional de plano |
| Platform `/super-admin` | No | Sigue excluido |

---

## 9. Clasificación del cambio `/app` → `/admin` (§8)

| Hipótesis | ¿Aplica? | Justificación técnica |
|-----------|----------|------------------------|
| Cambio de **dominio** | **No** | Dominio sigue siendo ERP `cfg`; dato en DEFAULT; API `/cfg`; no pasa a Platform |
| Cambio de **arquitectura Backend** | **No** | Capas, session scope, RBAC de negocio, stores — intactos |
| Cambio de **arquitectura de navegación FE / IA** | **Sí** | Shell y rutas de menú |
| Cambio **únicamente de navegación** | **Sí (definición correcta)** | Variable = `modulo_menu.ruta` + router FE; resto del sistema de módulo permanece |

Evidencia de independencia: el Backend no deriva el shell desde `modulo.codigo`; solo publica `ruta`. Cambiar la ruta no muta el grafo de dependencias del módulo HTTP.
