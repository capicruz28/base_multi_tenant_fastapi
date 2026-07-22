# Ola 1A — Contrato funcional ERP ↔ Motor de Generación de Códigos

**Proyecto:** Motor de Generación Automática de Códigos — Ola 1A  
**Alcance normativo inicial:** Módulo **ORG** (Ola 1)  
**Fecha:** 2026-07-10  
**Estado:** Contrato funcional aprobado para diseño — **sin implementación**  
**Prerequisitos:** Auditoría ORG [`01_ORG_FUNCTIONAL_AUDIT.md`](01_ORG_FUNCTIONAL_AUDIT.md), motor congelado (`app/core/codigo`)

---

## 0. Propósito y autoridad

Este documento define **cómo debe comportarse el ERP** — desde la perspectiva del usuario, integrador y contrato API — al usar el Motor de Generación Automática de Códigos.

| Aspecto | Autoridad |
|---------|-----------|
| Políticas de negocio por entidad | **Este contrato** (Ola 1A) |
| Implementación técnica del motor | `app/core/codigo` — **congelado** |
| Mapeo técnico ORG | [`02_ORG_MOTOR_ENTITY_MATRIX.md`](02_ORG_MOTOR_ENTITY_MATRIX.md) |
| Políticas canónicas globales | `app/docs/arquitectura/code-generation/08_CODE_POLICIES.md` (F15A) |

**Nota terminológica:** en el catálogo técnico la política equivalente a «manual obligatorio» es **`MANUAL_ONLY`** (no existe `MANUAL_REQUIRED` en el motor).

---

## 1. ¿Qué entidades dejarán de solicitar código manual?

### 1.1 Estado objetivo Ola 1 ORG (captura manual eliminada en UX)

Las siguientes entidades **dejarán de exigir** que el usuario ingrese código en el formulario de **alta (CREATE)**. El sistema asignará el código de forma automática salvo override explícito de implantación (ver §2).

| Entidad ERP | Campo | Formulario afectado | Estado objetivo UX |
|-------------|-------|---------------------|-------------------|
| Empresa | `codigo_empresa` | Alta empresa | **Sin input obligatorio** |
| Sucursal | `codigo` | Alta sucursal | **Sin input obligatorio** |
| Centro de costo | `codigo` | Alta centro de costo | **Sin input obligatorio** |
| Departamento | `codigo` | Alta departamento | **Sin input obligatorio** |
| Cargo | `codigo` | Alta cargo | **Sin input obligatorio** |

### 1.2 Entidades que nunca pasarán a generación automática (Ola 1)

| Entidad / campo | Motivo funcional |
|-----------------|------------------|
| `org_parametro_sistema.codigo_parametro` | Clave de configuración definida por implementador; no es correlativo de negocio |
| `org_empresa.ruc` | Identidad legal externa (SUNAT) |
| `org_empresa.codigo_ciiu` | Catálogo externo |
| `codigo_postal`, `ubigeo` | Referencias geográficas |
| `org_parametro_sistema.modulo_codigo` | Identificador de módulo, no secuencia |

### 1.3 Alcance fuera de Ola 1

El contrato de **eliminación de captura manual en UI** se extiende en olas posteriores al resto del ERP (INV, PUR, SLS, …) según la misma lógica F15A. **Ola 1A solo exige cumplimiento normativo en ORG.**

---

## 2. ¿Qué entidades continuarán permitiendo código manual y por qué?

### 2.1 Maestros ORG con AUTO_DEFAULT (convivencia transitoria y permanente)

Las **5 entidades ORG del motor** mantienen **`AUTO_DEFAULT`** como política real:

| Entidad | Política motor | ¿Manual permitido? | Por qué |
|---------|----------------|-------------------|---------|
| Empresa | AUTO_DEFAULT | **Sí** (API + override implantación) | Maestro F1; datos legados; migraciones; convivencia con `EMP001` bootstrap |
| Sucursal | AUTO_DEFAULT | **Sí** | Códigos semánticos legacy (`SUC-LIMA-01`) |
| Centro de costo | AUTO_DEFAULT | **Sí** | Jerarquías contables predefinidas por implantador |
| Departamento | AUTO_DEFAULT | **Sí** | Estructuras organizacionales importadas |
| Cargo | AUTO_DEFAULT | **Sí** | Catálogos RRHH preexistentes |

**Regla funcional AUTO_DEFAULT:**

- Si el cliente **omite** el código → el sistema **genera** (comportamiento objetivo Ola 1).
- Si el cliente **envía** un código válido y único → el sistema **acepta** y alinea contador cuando corresponda.

### 2.2 Entidades MANUAL_ONLY (permanente)

| Entidad | Campo | Política funcional | Por qué |
|---------|-------|-------------------|---------|
| Parámetro sistema | `codigo_parametro` | **MANUAL_ONLY** | Clave estable de configuración; el implementador debe nombrarla |
| Parámetro sistema | `modulo_codigo` | **MANUAL_ONLY** | Selector de módulo, no secuencia |

### 2.3 Entidades EXTERNAL (permanente)

| Campo | Política | Por qué |
|-------|----------|---------|
| `ruc` | **EXTERNAL** | Norma tributaria; no secuencia interna |
| `codigo_ciiu` | **EXTERNAL** | Catálogo SUNAT |
| `codigo_postal`, `ubigeo` | **EXTERNAL** | Estándares geo/postales |

### 2.4 Edición (UPDATE) — regla transversal ORG

| Operación | Código en UPDATE |
|-----------|------------------|
| Maestros gobernados por Motor (AUTO_DEFAULT) | **Inmutable** desde CREATE — **BR-IMM-01…05** (enforcement runtime pendiente Fase 2) |
| MANUAL_ONLY / EXTERNAL | Código Motor: **BR-IMM**; campos EXTERNAL (RUC, etc.) según regla propia |

> **Normativa:** `code-generation/07_BUSINESS_RULES.md` §3.4 · ADR `code-generation/code-immutability/`.  
> BR-M-30/31 ya no aplican.

---

## 3. Política del motor que utilizará realmente cada entidad

### 3.1 ORG — Ola 1 (normativa vinculante)

| Entidad | Campo | Política **real** | sequence_key | Comportamiento CREATE esperado |
|---------|-------|-------------------|--------------|--------------------------------|
| Empresa | `codigo_empresa` | **AUTO_DEFAULT** | `org_empresa` | Auto si omitido; manual aceptado |
| Sucursal | `codigo` | **AUTO_DEFAULT** | `org_sucursal` | Auto si omitido; manual aceptado |
| Centro de costo | `codigo` | **AUTO_DEFAULT** | `org_centro_costo` | Auto si omitido; manual aceptado |
| Departamento | `codigo` | **AUTO_DEFAULT** | `org_departamento` | Auto si omitido; manual aceptado |
| Cargo | `codigo` | **AUTO_DEFAULT** | `org_cargo` | Auto si omitido; manual aceptado |
| Parámetro sistema | `codigo_parametro` | **MANUAL_ONLY** | — (sin motor) | Usuario siempre debe aportar |
| Parámetro sistema | `modulo_codigo` | **MANUAL_ONLY** | — | Usuario siempre debe aportar |
| Empresa | `ruc` | **EXTERNAL** | — | Usuario siempre debe aportar |
| Empresa | `codigo_ciiu` | **EXTERNAL** | — | Opcional; catálogo externo |

**Ninguna entidad ORG de Ola 1 usa AUTO_REQUIRED.** Los documentos de proceso (AUTO_REQUIRED) pertenecen a olas posteriores (INV, FIN, …).

### 3.2 Formato de código auto-generado (expectativa usuario)

Prefijos oficiales del catálogo congelado:

| Entidad | Ejemplo auto-generado | Patrón |
|---------|----------------------|--------|
| Empresa | `EMP001`, `EMP002` | EMP + 3 dígitos |
| Sucursal | `SUC001` | SUC + 3 dígitos |
| Centro de costo | `CC001` | CC + 3 dígitos |
| Departamento | `DEP001` | DEP + 3 dígitos |
| Cargo | `CAR001` | CAR + 3 dígitos |

El usuario **no elige** el prefijo en operación normal; proviene de configuración tenant/empresa (`cfg_codigo_secuencia`).

### 3.3 ERP completo (referencia — fuera implementación Ola 1)

Las demás entidades ERP siguen las políticas F15A / `SequenceCatalog` sin cambio en Ola 1A. Ejemplos:

| Familia | Política dominante |
|---------|-------------------|
| Maestros F1 (INV, PUR, SLS, …) | AUTO_DEFAULT |
| Documentos F2 (movimientos, OC, …) | AUTO_REQUIRED (olas futuras) |
| Series fiscales | MANUAL_ONLY en alta de serie |
| Identidad legal | EXTERNAL |

---

## 4. ¿Cómo cambiarán los formularios del Frontend?

> Diseño funcional — **sin implementación** en esta etapa.

### 4.1 Formularios de alta (CREATE) — estado objetivo

| Entidad | Antes (AS-IS) | Después (TO-BE Ola 1) |
|---------|---------------|------------------------|
| Empresa | Input obligatorio `Código empresa` | **Eliminado** del formulario principal |
| Sucursal | Input obligatorio `Código` | **Eliminado** |
| Centro de costo | Input obligatorio `Código` | **Eliminado** |
| Departamento | Input obligatorio `Código` | **Eliminado** |
| Cargo | Input obligatorio `Código` | **Eliminado** |
| Parámetro | Input obligatorio `Código parámetro` | **Sin cambio** (MANUAL_ONLY) |
| Empresa RUC | Input obligatorio | **Sin cambio** (EXTERNAL) |

### 4.2 Elementos UX nuevos (recomendados)

| Elemento | Cuándo | Mensaje / comportamiento |
|----------|--------|--------------------------|
| Badge informativo | Alta maestro ORG | «El código se asignará automáticamente al guardar» |
| Código en detalle post-guardado | Tras CREATE exitoso | Mostrar código asignado en **solo lectura** |
| Listados / grillas | Sin cambio | Columna código sigue visible |
| Búsqueda | Sin cambio | `buscar` sigue filtrando por código |
| Override implantación (opcional Fase transitoria) | Rol implementador | Sección colapsada «Código manual (avanzado)» — ver §6 |

### 4.3 Formularios de edición (UPDATE)

| Entidad AUTO_DEFAULT | Comportamiento |
|---------------------|----------------|
| Campo código | **Solo lectura** — **BR-IMM-01** (normativa oficial). Enforcement Backend = fase runtime pendiente. |
| Objetivo FE | Omitir código del PUT; input disabled / readOnly |

### 4.4 Formularios sin cambio

- Parámetros de sistema (manual obligatorio).
- Campos EXTERNAL (RUC, CIIU, geo).
- Pantallas de listado, filtros y exportación.

### 4.5 Preview (fase opcional posterior)

El contrato **no exige** preview en Ola 1A. Si se implementa endpoint preview:

- Mostrar estimación **no vinculante** («próximo código estimado: CAR003»).
- Disclaimer oficial del motor: el valor definitivo se fija al guardar.

---

## 5. ¿Cómo cambiarán los contratos OpenAPI?

> Definición funcional del contrato futuro — **OpenAPI actual no se modifica en Ola 1A**.

### 5.1 Schemas Create — evolución normativa

| Schema | Campo | AS-IS | TO-BE Ola 1 |
|--------|-------|-------|-------------|
| `EmpresaCreate` | `codigo_empresa` | `required` | **`optional`** |
| `SucursalCreate` | `codigo` | `required` | **`optional`** |
| `CentroCostoCreate` | `codigo` | `required` | **`optional`** |
| `DepartamentoCreate` | `codigo` | `required` | **`optional`** |
| `CargoCreate` | `codigo` | `required` | **`optional`** |
| `ParametroCreate` | `codigo_parametro` | `required` | **sin cambio** |

### 5.2 Schemas Read — sin cambio

| Regla | Detalle |
|-------|---------|
| Código siempre presente | Tras CREATE exitoso, `*Read` incluye el código asignado (auto o manual) |
| Tipos y longitudes | Sin cambio (`max_length=20`, etc.) |

### 5.3 Schemas Update — sin cambio estructural Ola 1

| Campo | Comportamiento |
|-------|----------------|
| `codigo` / `codigo_empresa` | Permanece **optional**; si se envía, validación motor + unicidad |

### 5.4 Respuestas HTTP — reglas funcionales

| Escenario | Status | Detalle funcional |
|-----------|--------|-------------------|
| CREATE sin código, auto OK | **201** | Body Read con código generado |
| CREATE con código manual válido | **201** | Body Read con código aceptado |
| CREATE con código duplicado | **409** | «Ya existe … con el código …» |
| CREATE con código formato inválido | **422** | Validación motor (`VAL_MASTER`) |
| CREATE manual cuando política lo rechace | **422** | `MANUAL_NOT_ALLOWED` (no aplica ORG Ola 1) |

### 5.5 Endpoints — sin cambio de rutas

Rutas, permisos RBAC y `operationId` **permanecen**. Solo evoluciona semántica del body Create.

---

## 6. Compatibilidad durante la transición

### 6.1 Fases del contrato funcional

```
Fase T0 — AS-IS (hoy)
  └─ Código required en Create; usuario siempre captura

Fase T1 — Convivencia (Ola 1 implementada)
  └─ Código optional en Create
  └─ Frontend nuevo: no envía código
  └─ Clientes legacy: pueden seguir enviando código manual

Fase T2 — Madurez ORG (objetivo Ola 1)
  └─ UI sin captura manual en alta
  └─ API acepta manual solo rol implantación / integraciones

Fase T3 — Endurecimiento (opcional futuro, fuera Ola 1)
  └─ Evaluar AUTO_REQUIRED solo si negocio lo exige (no previsto maestros ORG)
```

### 6.2 Reglas de compatibilidad API

| Cliente | Envía código en CREATE | Resultado |
|---------|------------------------|-----------|
| Frontend nuevo | No | Auto-generado |
| Frontend legacy | Sí (válido, único) | Aceptado (AUTO_DEFAULT) |
| Integración batch | Sí (import) | Aceptado; alineación contador |
| Cualquiera | Sí (duplicado) | 409 |
| Cualquiera | Sí (formato inválido) | 422 |

### 6.3 Compatibilidad de datos existentes

| Situación | Tratamiento |
|-----------|-------------|
| Registros legacy con códigos no estándar | Permanecen válidos; no se renumera |
| EMP001 onboarding | Permanece en bootstrap; cfg TENANT `org_empresa` con `ultimo_numero=1` (BR-BOOT-04); primer auto runtime = `EMP002` |
| Nuevas altas sin código | Formato motor estándar |

### 6.4 Versionado y release

| Recomendación | Detalle |
|---------------|---------|
| Release coordinado | Backend (optional Create) + Frontend (sin input) en **misma ventana** por entidad |
| Orden por entidad | cargo → departamento → CC → sucursal → empresa |
| Rollback | Si Frontend viejo envía código required, sigue funcionando en T1 |

---

## 7. Estrategia de migración Backend + Frontend recomendada

### 7.1 Principio: **una entidad, un incremento, un release**

| Paso | Backend | Frontend | Gate |
|------|---------|----------|------|
| 1 | Infra UoW + helper gateway ORG | — | Tests unit |
| 2 | `org_cargo` optional + allocate | Quitar input código alta cargo | E2E cargo |
| 3 | `org_departamento` | idem | E2E dpto |
| 4 | `org_centro_costo` | idem | E2E CC |
| 5 | `org_sucursal` | idem | E2E sucursal |
| 6 | `org_empresa` | idem + mantener RUC | E2E empresa + bootstrap |

### 7.2 Responsabilidades

| Capa | Responsabilidad |
|------|-----------------|
| **Backend** | `CodigoGeneracionGateway.allocate` antes INSERT; Create optional; Read unchanged; mensajes 409/422 |
| **Frontend** | Eliminar input obligatorio; mostrar código post-save; ocultar override salvo rol implantación |
| **QA** | Matriz: create sin código, create manual, duplicado, rollback TX, listado/buscar |
| **Docs** | Release notes por entidad |

### 7.3 Coordinación mínima por entidad

1. Backend despliega con campo **optional** (compatible con FE legacy).
2. Frontend despliega sin enviar código (activa auto).
3. Validar en staging tenant limpio + tenant con datos legacy.
4. Marcar entidad como **«captura manual eliminada en UX»** (§8).

### 7.4 Fuera de alcance coordinado Ola 1

- Modificaciones motor (`app/core/codigo/**`).
- Endurecimiento a AUTO_REQUIRED en maestros ORG.

**Incluido en Ola 1 (bootstrap):** seed cfg TENANT `org_empresa` con `ultimo_numero=1` (BR-BOOT-04). Sin cambio a `ensure_empresa_inicial` (EMP001).

---

## 8. Criterios para considerar eliminada la captura manual en ORG

La captura manual se considera **eliminada** para una entidad ORG cuando se cumplen **todos** los criterios:

### 8.1 Criterios de producto (UX)

| ID | Criterio | Verificación |
|----|----------|--------------|
| C-UX-01 | Formulario de alta **no muestra** input de código en flujo estándar | Revisión UX / demo |
| C-UX-02 | Usuario operativo estándar **no puede** ingresar código en alta | RBAC + UI |
| C-UX-03 | Código asignado **visible** en detalle/listado tras guardar | E2E |
| C-UX-04 | Mensaje informativo de auto-asignación presente | Copy review |

### 8.2 Criterios de contrato API

| ID | Criterio | Verificación |
|----|----------|--------------|
| C-API-01 | Campo código **optional** en schema Create publicado | OpenAPI diff |
| C-API-02 | CREATE sin código retorna **201** con código en Read | Test integración |
| C-API-03 | CREATE sin código usa **gateway** (no lógica ad-hoc) | Test unit + code review |
| C-API-04 | Unicidad garantizada (409 duplicado) | Test |

### 8.3 Criterios operativos

| ID | Criterio | Verificación |
|----|----------|--------------|
| C-OP-01 | **≥ 30 días** en producción/staging sin incidencia P1/P2 de códigos | Operaciones |
| C-OP-02 | **≥ 95%** de altas nuevas sin campo código en payload (métrica API/log) | Telemetría |
| C-OP-03 | Cero tickets «código duplicado por captura manual» en ventana | Soporte |
| C-OP-04 | Tenant Dedicated y Shared validados | Smoke F4 |

### 8.4 Criterios por entidad (checklist cierre Ola 1 ORG)

| Entidad | C-UX | C-API | C-OP | Estado |
|---------|------|-------|------|--------|
| Cargo | ☐ | ☐ | ☐ | Pendiente |
| Departamento | ☐ | ☐ | ☐ | Pendiente |
| Centro de costo | ☐ | ☐ | ☐ | Pendiente |
| Sucursal | ☐ | ☐ | ☐ | Pendiente |
| Empresa | ☐ | ☐ | ☐ | Pendiente |

**Cierre Ola 1 ORG:** las **5 filas** marcadas + regresión suite ORG verde.

### 8.5 Qué NO implica «eliminada la captura manual»

| No implica | Por qué |
|------------|---------|
| Política AUTO_REQUIRED | Maestros ORG permanecen AUTO_DEFAULT |
| API rechaza manual | Integraciones pueden enviar código en T2 |
| Renumeración legacy | Datos históricos no se migran |
| Parámetros manuales | MANUAL_ONLY permanente |

---

## 9. Resumen ejecutivo del contrato

| Pregunta | Respuesta contrato Ola 1A |
|----------|---------------------------|
| ¿Quién deja de pedir código? | 5 maestros ORG en alta UX |
| ¿Quién sigue manual? | Parámetros; campos EXTERNAL; override API AUTO_DEFAULT |
| ¿Política real ORG? | **AUTO_DEFAULT** (5 entidades motor) |
| ¿Frontend? | Sin input código en alta; código visible post-save |
| ¿OpenAPI? | Create optional; Read unchanged |
| ¿Transición? | T1 convivencia → T2 madurez UX |
| ¿Migración? | Entidad por entidad; release coordinado BE+FE |
| ¿Cierre? | Checklist §8.4 + métricas §8.3 |

---

## 10. Veredicto

**CONTRATO FUNCIONAL OLA 1A — APROBADO** como base normativa para implementación Backend y Frontend de Ola 1 ORG.

**Siguiente paso:** implementación Fase 1 infra ORG + piloto `org_cargo` conforme a [`03_ORG_MIGRATION_STRATEGY.md`](03_ORG_MIGRATION_STRATEGY.md), respetando este contrato.

---

## 11. Referencias

| Documento | Relación |
|-----------|----------|
| [`00_OLA1_EXECUTIVE_SUMMARY.md`](00_OLA1_EXECUTIVE_SUMMARY.md) | Contexto Ola 1 |
| [`01_ORG_FUNCTIONAL_AUDIT.md`](01_ORG_FUNCTIONAL_AUDIT.md) | Auditoría técnica |
| [`03_ORG_MIGRATION_STRATEGY.md`](03_ORG_MIGRATION_STRATEGY.md) | Strangler técnico |
| `08_CODE_POLICIES.md` | Políticas globales F15A |
| `21_SEQUENCE_CATALOG_MATRIX.md` | Catálogo congelado |
