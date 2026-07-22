# Checklist pre-código, Definition of Ready y certificación INV

---

## 1. Checklist obligatorio antes de iniciar código

Marcar **todos** antes del primer PR de implementación.

### 1.1 Gobernanza

- [ ] Baseline V1 leído y aceptado como obligatorio
- [ ] `inv-wave1-audit/` aprobado (alcance 7 entidades)
- [ ] Este Blueprint aprobado como guía mecánica
- [ ] Acuerdo explícito: **cero** cambios en Motor / Gateway / Catalog / BR-IMM / ORG

### 1.2 Golden Reference a mano

- [ ] Plantilla service: `cargo_service.py` (CREATE UoW + UPDATE IMM)
- [ ] Plantilla adapter: `org_codigo_generation_service.py`
- [ ] Plantilla queries dual-path: `cargo_queries.py`
- [ ] Plantilla tests: `test_org_cargo_motor_integration.py` + `test_org_br_imm_update_immutability.py`

### 1.3 Piloto Categoría — gaps AS-IS conocidos

- [ ] Confirmado: no existe `get_categoria_by_codigo` → crear en implementación
- [ ] Confirmado: `create_categoria` sin `session` → dual-path
- [ ] Confirmado: `CategoriaCreate.codigo` required → Optional
- [ ] Confirmado: `CategoriaUpdate.codigo` presente → eliminar
- [ ] Confirmado: create sin UoW → adoptar `get_connection_for_tenant`

### 1.4 Entorno

- [ ] Tenant de prueba con cfg EMPRESA sembrada (keys INV en `cfg_codigo_secuencia`)
- [ ] Suite ORG motor + IMM sigue verde (regresión Golden Reference)

### 1.5 Alcance del primer PR (recomendado)

- [ ] PR-0: solo `InvCodigoGenerationService` + test adapter **o**
- [ ] PR-1: Adapter + Categoría completa (schemas + queries + service + tests)

**No** mezclar Producto/Movimiento en el PR del piloto.

---

## 2. Definition of Ready (DoR) — por entidad

Una entidad está **Ready** para implementar cuando:

| # | Criterio |
|---|----------|
| R1 | `sequence_key` + campo + policy + scope documentados (matriz audit) |
| R2 | Plantilla ORG identificada (cargo F1 / movimiento F2) |
| R3 | Lista de archivos a tocar (schema, service, queries, tests) |
| R4 | Gaps AS-IS listados (`get_by_codigo`, dual-path, required Create, Update field) |
| R5 | Casos de test ID definidos (INV-C* / INV-U* / INV-D*) |
| R6 | Dependencias previas certificadas (p.ej. Producto: Cat+UM preferible) |
| R7 | Fuera de alcance explícito (barra, stock, workflow no-número) |
| R8 | Entidad anterior del orden §03 en verde (salvo #1 Categoría) |

### 2.1 DoR Categoría (piloto) — estado Blueprint

| Criterio | Estado |
|----------|--------|
| R1–R5 | ✅ Cubierto por este paquete |
| R6 | N/A (primera) |
| R7 | Stock/kardex/producto fuera |
| R8 | N/A |

→ **Categoría está Ready para código** tras checklist §1.

### 2.2 DoR Producto — extras

- [ ] No eliminar `codigo_barra` / `codigo_interno` / `codigo_fabricante` / `codigo_sunat` del Update
- [ ] `get_producto_by_sku` dual-path
- [ ] Test IMM solo sobre `codigo_sku`

### 2.3 DoR Movimiento — extras

- [ ] Inventario de callers que setean `numero_movimiento` (create, estorno, aprobación IF)
- [ ] Plan UoW cabecera+detalle
- [ ] Decisión documentada: body con número → ignore vs 422 (Blueprint recomienda ignore + allocate)

---

## 3. Definition of Done — entidad certificada

| # | Criterio |
|---|----------|
| D1 | CREATE auto (o AUTO_REQUIRED) verde |
| D2 | CREATE manual (solo F1) + 409 dup verde |
| D3 | UPDATE sin campo Motor en schema + payload |
| D4 | Motor no invocado en UPDATE |
| D5 | Diff `app/core/codigo/**` vacío |
| D6 | Diff ORG vacío |
| D7 | Tests entidad verdes |
| D8 | List/get/paginación sin regresión |

---

## 4. Criterios para declarar INV certificado bajo Baseline V1

INV como módulo queda **certificado** solo si:

| # | Criterio |
|---|----------|
| C1 | Las **7** entidades de la matriz Ola 1 cumplen DoD entidad |
| C2 | `InvCodigoGenerationService` es el único adapter INV → Gateway |
| C3 | Ningún gen timestamp de correlativo MOV permanece en create/estorno/ajuste |
| C4 | BR-IMM aplicado a todos los campos Motor (`codigo`, `codigo_sku`, `numero_*`) |
| C5 | OpenAPI vivo alineado; snapshot regenerado |
| C6 | Checklist Baseline V1 § INV (`baseline-v1/04_CHECKLISTS.md`) completo |
| C7 | DoD Baseline (`baseline-v1/06_DEFINITION_OF_DONE.md`) D1–D7, T1–T7, C1–C4 |
| C8 | Documento de cierre INV Wave 1 (futuro) referencia este Blueprint + Baseline |
| C9 | ORG sigue Golden Reference normativa (INV no la reemplaza) |

```text
[ ] C1 … C9
[ ] Arquitectura: “sin desviación Baseline V1 / Blueprint”
→ INV Ola 1 CERTIFICADO
```

---

## 5. Confirmación final del Blueprint

| Afirmación | Valor |
|------------|-------|
| Guía definitiva de implementación INV | **Este paquete** |
| Primera línea de código permitida solo tras | Checklist §1 completo |
| Primera entidad | Categoría |
| Motor / Gateway / Catalog / BR-IMM / Baseline | **Intocables** |
| ORG | Golden Reference permanente |

---

*Índice: [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md)*
