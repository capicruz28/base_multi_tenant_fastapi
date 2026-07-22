# Roadmap de implementación (post diseño funcional)

**Paquete:** `cfg-functional-design`  
**Fecha:** 2026-07-17  
**Estado del diseño funcional:** **COMPLETO — apto para autorizar MVP Backend**  
**Estado de implementación:** **NO iniciada** (requiere autorización explícita)

---

## 1. Cierre de esta etapa

Quedan definidos:

- Objetivos y usuarios  
- Casos de uso MVP y post-MVP  
- Navegación y pantallas  
- Flujos de configuración, preview, edición, activación  
- Campos visibles / editables / ocultos  
- Operaciones permitidas y prohibidas  
- Paridad Shared/Dedicated  
- Auditoría, RBAC, validaciones  
- Riesgos UX y recomendaciones FE/BE  

**No** se ha creado código, endpoints, OpenAPI, schemas ni Frontend.

---

## 2. Roadmap por fases

### Fase 0 — Gobernanza (actual)

| Entregable | Estado |
|------------|--------|
| Auditoría AS-IS | ✅ `cfg-admin-audit/` |
| ADR ubicación ERP `cfg` | ✅ Aprobado |
| Diseño funcional producto | ✅ **Este paquete** |
| Autorización MVP Backend | ⏳ Pendiente usuario |

### Fase 1 — MVP Backend (siguiente, cuando se autorice)

| Entregable | Criterio de hecho |
|------------|-------------------|
| Módulo `app/modules/cfg/` | Estructura V4 |
| RBAC `consultar` + `actualizar` | Seed + enforcement |
| GET list + GET detail | Tenant-scoped + enrich |
| PATCH B + activar/desactivar | Validaciones + org_empresa lock |
| POST preview | Gateway; sin consumo |
| Tests + OpenAPI | Gate certificación Backend MVP |

**Gate producto Backend MVP:** cumple CU-01..CU-08 a nivel API.

### Fase 2 — Contrato Frontend (docs)

Paquete tipo `cfg-frontend-contract/` (análogo ORG/INV FE): pantallas, estados, copy, checklist — **sin** implementar FE aún si se mantiene la disciplina de olas.

### Fase 3 — MVP Frontend

Menú + P1 + P2 + modales preview/desactivar según este diseño.

### Fase 4 — v1.1 Mantenimiento

Align + permiso `mantener` + CU-09.

### Fase 5 — v1.2 Diagnóstico

Panel DGN + permiso `diagnosticar`.

### Fase 6 — v1.3 Madurez

Historial, validar-manual admin, hardening anti-colisión avanzada.

---

## 3. Dependencias y no-dependencias

| Dependencia | Nota |
|-------------|------|
| Motor certificado Ola 1 | ✅ Ya cerrado |
| ORG/INV Backend/FE | ✅ No se reabren |
| ADR-CFG-ADMIN-LOC-001 | ✅ Aprobado |
| Extensión menor Repo (`numero_inicial`, audit) | Permitida en Fase 1 si MVP lo exige |
| Cambios Gateway/Catalog | **No** en Fase 1 |

---

## 4. Criterios para declarar “MVP Backend listo para FE”

- [ ] List/detail/patch/preview/activar-desactivar operativos  
- [ ] org_empresa locked en servidor  
- [ ] Preview sin side-effect verificado en tests  
- [ ] Aislamiento tenant + impersonación verificados  
- [ ] Shared y Dedicated paths de escritura cubiertos  
- [ ] OpenAPI publicado del recurso `/cfg/secuencias`  
- [ ] Mensajes de error estables documentados  

---

## 5. Conclusión oficial

> El **diseño funcional** del Administrador del Motor de Códigos (módulo ERP `cfg`) se declara **completo y aprobado como base de producto** para iniciar, **cuando el usuario lo autorice**, el **MVP Backend**.  
> Hasta esa autorización explícita: **no implementar**.

---

## 6. Índice de lectura para el equipo

1. `00_EXECUTIVE_SUMMARY.md` — dictamen  
2. `01_PRODUCT_VISION.md` — qué y para quién  
3. `02_USER_FLOWS.md` — cómo se usa  
4. `03_SCREEN_DESIGN.md` — qué se ve  
5. `04_FUNCTIONAL_RULES.md` — reglas duras  
6. `05_BACKEND_FRONTEND_BOUNDARY.md` — quién hace qué  
7. `06_IMPLEMENTATION_ROADMAP.md` — este documento  

Referencias de arquitectura: `cfg-platform-architecture/`, `cfg-admin-audit/`, `codigo-generation-admin/`.
