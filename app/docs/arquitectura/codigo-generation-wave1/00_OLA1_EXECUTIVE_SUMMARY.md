# Ola 1 — Motor de Generación Automática de Códigos — Resumen ejecutivo

**Proyecto:** Motor de Generación Automática de Códigos — Ola 1  
**Alcance inicial:** Módulo **ORG**  
**Fecha:** 2026-07-10  
**Estado:** Auditoría funcional — sin implementación  
**Prerequisitos congelados:** `app/core/codigo` (F17D + Ola 0), Bootstrap V2, Empresa Bootstrap V1 (UoW-2)

---

## 1. Objetivo Ola 1

Eliminar progresivamente la **captura manual obligatoria** de códigos de negocio en módulos ERP, sustituyéndola por **`CodigoGeneracionGateway.allocate()`** como único punto de asignación, respetando `SequenceCatalog` y políticas `AUTO_DEFAULT`.

**Primer módulo:** ORG (5 entidades maestras F1 en catálogo).

---

## 2. Hallazgos clave

| # | Hallazgo |
|---|----------|
| H-01 | **Ningún módulo ERP** consume hoy `CodigoGeneracionGateway` en runtime — Ola 1 ORG será la **primera integración productiva**. |
| H-02 | ORG expone **5 entidades** con código de negocio en catálogo; **1 entidad** (`org_parametro_sistema`) tiene campo `codigo_*` pero **fuera del motor**. |
| H-03 | Todas las entidades ORG en catálogo usan **`CodePolicy.AUTO_DEFAULT`** — código manual sigue permitido durante transición. |
| H-04 | Validación actual: **pre-check SELECT** en services + **UNIQUE** en BD; el motor aporta validación de formato + alineación de contador. |
| H-05 | **`org_empresa`** ya opera con **UoW + session** (`create_empresa_servicio`) — candidato ideal para `allocate()` en la misma TX que INSERT y bootstrap cfg. |
| H-06 | Resto de entidades ORG usan **auto-commit por operación** — requerirán UoW local o helper transaccional antes de integrar motor (patrón UoW-1 empresa). |
| H-07 | Onboarding **EMP001** usa `ensure_empresa_inicial` con código **hardcodeado**, no motor — riesgo de divergencia con secuencia TENANT `org_empresa`. |

---

## 3. Entidades en alcance vs fuera de alcance

| Entidad | Motor Ola 1 | Motivo |
|---------|-------------|--------|
| `org_cargo` | **Sí** | `org_cargo` en SequenceCatalog |
| `org_departamento` | **Sí** | idem |
| `org_centro_costo` | **Sí** | idem |
| `org_sucursal` | **Sí** | idem |
| `org_empresa` | **Sí** (fase tardía) | TENANT scope + bootstrap + mayor riesgo |
| `org_parametro_sistema` | **No** | Clave de configuración; sin `sequence_key` |
| Campos `codigo_ciiu`, `codigo_postal`, `ubigeo` | **No** | Códigos externos / referenciales |

---

## 4. Orden de migración recomendado (menor → mayor riesgo)

```
1. org_cargo
2. org_departamento
3. org_centro_costo
4. org_sucursal
5. org_empresa
```

---

## 5. Veredicto

**OLA 1 ORG — LISTA PARA DISEÑO DE IMPLEMENTACIÓN** con condiciones:

1. Introducir helper transaccional ORG reutilizable (patrón UoW empresa) antes de entidades company-scoped.
2. ~~Resolver política EMP001~~ → **Cerrada:** seed cfg `ultimo_numero=1` (BR-BOOT-04); ver `07_BUSINESS_RULES.md` BR-M-02.
3. **No modificar** `app/core/codigo` — toda lógica en capa `modules/org` + seed onboarding.

---

## 6. Documentos de la Ola 1

| Doc | Contenido |
|-----|-----------|
| [`01_ORG_FUNCTIONAL_AUDIT.md`](01_ORG_FUNCTIONAL_AUDIT.md) | Respuestas 1–12 de la auditoría |
| [`02_ORG_MOTOR_ENTITY_MATRIX.md`](02_ORG_MOTOR_ENTITY_MATRIX.md) | Mapeo entidad ↔ motor ↔ BD |
| [`03_ORG_MIGRATION_STRATEGY.md`](03_ORG_MIGRATION_STRATEGY.md) | Estrategia incremental, riesgos, impactos |

**Referencias congeladas (solo lectura):**

- `app/core/codigo/sequence_catalog.py`
- `app/core/codigo/gateway/codigo_generacion_gateway.py`
- `app/docs/arquitectura/code-generation/catalog/21_SEQUENCE_CATALOG_MATRIX.md`
