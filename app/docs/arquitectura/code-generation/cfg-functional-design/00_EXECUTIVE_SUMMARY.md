# Administrador del Motor de Códigos — Diseño funcional

**Etapa:** Diseño de producto (UX + capacidades) — **sin implementación**  
**Fecha:** 2026-07-17  
**ADR de ubicación:** ADR-CFG-ADMIN-LOC-001 **aprobado** → módulo ERP transversal `cfg`  
**Precondiciones:** `cfg-admin-audit/` + `cfg-platform-architecture/` cerrados  

---

## 1. Dictamen de producto

Este paquete define la **experiencia completa** del Administrador del Motor de Códigos: quién lo usa, qué pantallas ve, qué puede hacer y qué está prohibido.

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué producto es? | Consola ERP de parametrización de secuencias de código del tenant |
| ¿Dónde vive? | Módulo ERP `cfg` (shell tenant), no Platform Admin |
| ¿Para quién? | ADMIN_TENANT y roles de parametrización / implantación |
| ¿Qué problema resuelve? | Ver y ajustar formato/activo de secuencias sin SQL ni tocar el Motor |
| ¿MVP funcional? | Listado + detalle + edición B + activar/desactivar + preview |
| ¿Fuera de MVP? | Align, diagnóstico avanzado, historial, fiscal, FE completo (contrato FE posterior) |

### Estado de aprobación de este diseño

> **Diseño funcional declarado completo y listo para autorizar posteriormente el MVP Backend.**  
> Esta etapa **no** autoriza aún escribir código, endpoints, schemas ni Frontend.

---

## 2. Principios de producto

1. **El admin configura el entorno; el Motor consume el contador.**
2. **Códigos históricos no se reescriben** — solo afecta generación futura.
3. **Preview no reserva** correlativo.
4. **Shared y Dedicated** se comportan igual para el usuario.
5. **org_empresa** es semi-inmutable (consulta + preview; sin PATCH en v1).
6. **Una sola superficie** para ORG, INV y futuros módulos (transversal).

---

## 3. Alcance funcional por fase (producto)

| Fase producto | Capacidades visibles al usuario |
|---------------|----------------------------------|
| **MVP** | Navegar listado, ver detalle, editar formato, activar/desactivar, preview |
| **v1.1 Mantenimiento** | Alinear contador (con motivo y confirmación) |
| **v1.2 Diagnóstico** | Alertas drift, agotamiento, lazy pendientes |
| **v1.3 Madurez** | Historial de cambios, validar-manual desde admin, reportes |

---

## 4. Índice del paquete

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento |
| `01_PRODUCT_VISION.md` | Objetivos, usuarios, casos de uso, navegación |
| `02_USER_FLOWS.md` | Flujos: config, preview, edición, activación |
| `03_SCREEN_DESIGN.md` | Pantallas, información mostrada, campos |
| `04_FUNCTIONAL_RULES.md` | Permitido/prohibido, validaciones, RBAC, auditoría, Shared/Dedicated |
| `05_BACKEND_FRONTEND_BOUNDARY.md` | Frontera FE/BE + recomendaciones (sin implementación) |
| `06_IMPLEMENTATION_ROADMAP.md` | Roadmap hacia MVP Backend y fases |

---

## 5. Trazabilidad

| Fuente | Uso en este diseño |
|--------|-------------------|
| `cfg-platform-architecture/` | Ubicación ERP `cfg` |
| `cfg-admin-audit/` | MVP técnico y gaps |
| `codigo-generation-admin/` | Taxonomía ops, columnas A/B/C/D, casos org_empresa |

---

*Sin cambios de código. Siguiente paso operativo: aprobación explícita para iniciar MVP Backend según `06_IMPLEMENTATION_ROADMAP.md`.*
