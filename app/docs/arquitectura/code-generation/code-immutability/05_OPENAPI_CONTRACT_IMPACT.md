# Impacto OpenAPI / contrato Frontend — Inmutabilidad del código

**Fecha:** 2026-07-13  
**Alcance:** Contrato HTTP ORG (y plantilla INV)  
**Sin regenerar OpenAPI en esta auditoría**

---

## 1. Qué cambia para Frontend

### 1.1 Update (PUT) — breaking de contrato de campos

| Entidad | Campo que **desaparece** del body Update | Ruta | Permiso |
|---------|------------------------------------------|------|---------|
| Empresa | `codigo_empresa` | PUT `/org/empresa/{empresa_id}` | `org.empresa.actualizar` |
| Sucursal | `codigo` | PUT `/org/sucursales/{id}` | `org.sucursal.actualizar` |
| Departamento | `codigo` | PUT `/org/departamentos/{id}` | `org.departamento.actualizar` |
| Centro de costo | `codigo` | PUT `/org/centros-costo/{id}` | `org.centro_costo.actualizar` |
| Cargo | `codigo` | PUT `/org/cargos/{id}` | `org.cargo.actualizar` |

**Implicación React:**

| Acción UI | Obligatorio |
|-----------|-------------|
| Campo código en form **edición** → `readOnly` / disabled | Sí |
| No incluir código en payload PUT | Sí |
| Mostrar código desde GET detalle | Sí |
| Validación Yup/Zod: no exigir código en Update | Sí |
| Mensaje: “El código no se puede modificar” | Recomendado |

### 1.2 Create — **sin cambio**

| Aspecto | Contrato |
|---------|----------|
| Campo código optional | Igual (Ola 1) |
| Omisión → auto | Igual |
| Manual → aceptado AUTO_DEFAULT | Igual |
| Response 201 incluye código | Igual |

### 1.3 Read / List — **sin cambio**

| Aspecto | Contrato |
|---------|----------|
| Campo código siempre presente | Igual |
| Columnas grilla | Igual |
| `buscar` por código | Igual |

### 1.4 Soft delete / reactivar — **sin cambio**

No involucran código.

---

## 2. Qué no cambia

| Superficie | Estado |
|------------|--------|
| Paths y métodos HTTP | Estables |
| Códigos de permiso RBAC | Estables |
| Envelope errores CustomException | Estable |
| Session scope TENANT / COMPANY | Estable |
| Motor Gateway endpoints (no existen públicos ERP) | N/A |
| Módulo admin cfg (futuro) | Fuera de esta ADR |

---

## 3. OpenAPI — efecto mecánico

Al quitar campos de modelos Update Pydantic:

| Artefacto generado | Efecto |
|--------------------|--------|
| `components.schemas.EmpresaUpdate` | Sin `codigo_empresa` |
| `…SucursalUpdate` etc. | Sin `codigo` |
| `required` arrays Update | Sin el campo (ya era optional) |
| Create schemas | Sin cambio |
| Read schemas | Sin cambio |

**Codegen TypeScript:** tipos Update pierden la propiedad → compilación FE fallará donde se asigne `codigo` en Update DTO — **deseable** como red de seguridad.

---

## 4. Errores nuevos (fase strict)

| Status | Código interno | Cuándo |
|--------|----------------|--------|
| 422 | `CODE_IMMUTABLE` | Cliente intenta mutar código (si se implementa reject explícito) |

Si fase strip (campo ausente + extras ignored): **no hay error** — el código simplemente no cambia.

---

## 5. Actualización del contrato FE Ola 1 (documental)

Tras aprobación, estos archivos **deben** enmendarse (fase implementación/docs):

| Archivo wave1 | Cambio |
|---------------|--------|
| `frontend-contract/00_EXECUTIVE_SUMMARY.md` | Quitar “UPDATE código editable” |
| `02_ENTITY_CONTRACTS.md` | § Impacto edición → solo lectura / omitido PUT |
| `03_HTTP_ERRORS_AND_RUNTIME_FLOW.md` | UPDATE motor: N/A; add CODE_IMMUTABLE |
| `04_FRONTEND_MIGRATION_STRATEGY.md` | Eleva “Fase madurez solo lectura” a **obligatorio** |

Hasta entonces, el contrato FE Ola 1 refleja el **AS-IS** (editable) — **conflictivo** con BR-IMM propuesto.

---

## 6. Checklist Frontend post-deploy BE

- [ ] Regenerar cliente OpenAPI / tipos
- [ ] Forms Update: código read-only
- [ ] PUT payload sin código (5 entidades)
- [ ] Caso e2e: editar nombre no altera código
- [ ] Caso e2e: intento cambiar código no persiste / 422
- [ ] Copy UX alineado a BR-IMM

---

## 7. Resumen ejecutivo FE

| Pregunta | Respuesta |
|----------|-----------|
| ¿Rompe altas (CREATE)? | **No** |
| ¿Rompe listados? | **No** |
| ¿Rompe edición de nombre/otros? | **No** si se omite código |
| ¿Rompe edición que envía código? | **Sí** (comportamiento o contrato) |
| ¿Esfuerzo FE? | Bajo–medio (mismo patrón ×5) |

---

*Testing: [`06_TESTING_STRATEGY.md`](06_TESTING_STRATEGY.md)*
