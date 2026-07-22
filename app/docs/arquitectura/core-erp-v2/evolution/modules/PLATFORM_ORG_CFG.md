# Evolución modular — IAM / Plataforma / ORG / CFG / CAT

**Fase D1 · modules**

---

## IAM / Auth / RBAC / Users / Tenant / Menus / Modulos

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Muy maduro (en prueba) |
| Conservar sin cambios | Todo el modelo de identidad, sesiones, RBAC, provisioning tenant, menús/módulos de plataforma |
| Extender | Nada obligatorio para ola industrial V2 |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | Fuera del mapa de tablas ERP V010; no es gap industrial P0 |
| Impacto código | Nulo si se respeta frontera IAM↔ERP |
| Prioridad | — (no tocar) |

---

## CFG

| Campo | Contenido |
|-------|-----------|
| Estado V1 | ~99% — `cfg_codigo_secuencia` + código generación |
| Conservar | `cfg_codigo_secuencia` y motor de códigos |
| Extender | — |
| Rediseñar | — |
| Tablas nuevas | **`cfg_vertical_empresa`** (C1+C4) |
| Justificación | Multi-vertical por empresa no cabe en `rubro` ni en parámetros JSON |
| Impacto código | Bajo — servicio/endpoint nuevo; onboarding puede seedar vertical |
| Prioridad | **P1** |

---

## ORG

| Campo | Contenido |
|-------|-----------|
| Estado V1 | ~99% |
| Conservar | `org_empresa`, sucursal, CC, depto, cargo, parametro_sistema |
| Extender | Ninguna columna obligatoria; `rubro` permanece informativo (no reemplaza vertical CFG) |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | Ya cubre MultiEmpresa; session scope a preservar |
| Impacto código | Nulo/mínimo |
| Prioridad | — |

---

## CAT (`cat_*` / catalogos)

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Básico-sólido (ubigeo, moneda) |
| Conservar | Todas las `cat_*` |
| Extender | — |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | No es gap industrial; catálogos de vertical no entran aquí |
| Impacto código | Nulo |
| Prioridad | — |
