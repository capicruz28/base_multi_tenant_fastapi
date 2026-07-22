# Dependencias e impacto — ORG, CFG, OpenAPI, Frontend

---

## 1. Dependencias con ORG

| Dependencia | Detalle | Impacto Ola 1 INV |
|-------------|---------|-------------------|
| Sesión `empresa_id` | INV company-scoped como ORG maestros EMPRESA | Reutilizar patrón `require_session_empresa_id` / deps INV |
| `empresa_id` body | Debe coincidir con sesión | Igual ORG |
| `sucursal_id` en almacén | FK opcional → `org_sucursal` | No requiere Motor ORG en runtime ALLOCATE |
| `centro_costo_id` | FK opcional → ORG | Solo validación existencia |
| Golden Reference | Adapter + UoW + BR-IMM | **Copiar patrón**, no llamar services ORG para códigos |
| EMP001 / bootstrap empresa | Crea empresa + seed cfg EMPRESA | INV sequences ya en catálogo EMPRESA seed |

**No** hay dependencia de código: INV **no** consume `OrgCodigoGenerationService`; replica un `InvCodigoGenerationService` análogo.

---

## 2. Dependencias con CFG

| Tema | Estado | Acción Ola 1 |
|------|--------|--------------|
| Filas `cfg_codigo_secuencia` scope EMPRESA | Seed al crear empresa (`insertar_secuencias_codigo` / onboarding) | Verificar keys INV presentes post-bootstrap; **no** módulo admin CFG |
| Prefijos / padding | cfg override | Solo lectura runtime vía Motor |
| Admin `/cfg/secuencias` | Diseño futuro | **Fuera** Ola 1 INV |
| Lazy ensure | Motor | Si falta fila, comportamiento documentado Motor (steady-state) |

**Conclusión:** Ola 1 INV **no** implementa CFG admin; solo consume cfg ya sembrada.

---

## 3. Impacto OpenAPI

| Schema AS-IS | Cambio requerido al implementar |
|--------------|----------------------------------|
| `CategoriaCreate.codigo` required | → Optional (AUTO_DEFAULT) |
| `UnidadMedidaCreate.codigo` required | → Optional |
| `ProductoCreate.codigo_sku` required | → Optional |
| `AlmacenCreate.codigo` required | → Optional |
| `TipoMovimientoCreate.codigo` required | → Optional |
| `MovimientoCreate.numero_movimiento` required | → **Omitir del Create** o Optional ignorado (AUTO_REQUIRED) |
| `InventarioFisicoCreate.numero_inventario` required | → Idem AUTO_REQUIRED |
| Todos `*Update` con código/número | → **Quitar** campos Motor (BR-IMM) |
| Todos `*Read` | Sin cambio funcional (código/número required) |

PUT paths estables; solo cambia shape del body Update/Create.

Regenerar `openapi_snapshot.json` al cierre de cada fase certificada (como ORG).

---

## 4. Impacto Frontend

| Área | Cambio FE (posterior a BE) |
|------|----------------------------|
| Formularios Create maestros | Quitar required; badge “código automático” |
| Create producto | `codigo_sku` optional; conservar inputs barra/fabricante |
| Create movimiento / IF | **Eliminar** input número; mostrar post-201 |
| Formularios Update | Código/número **solo lectura** |
| Listados | Sin cambio de columnas |
| Estorno / ajuste | Tras fase F2: esperar número Motor, no string timestamp |
| Contrato | Nuevo paquete `inv-wave1/frontend-contract` (futuro) — no en esta auditoría |

**Compatibilidad:** FE que hoy envía código manual en maestros AUTO_DEFAULT **sigue válido** hasta que oculten el campo.

---

## 5. Impacto procesos INV (no OpenAPI)

| Proceso | Hallazgo | Acción fase documentos |
|---------|----------|------------------------|
| `gen_numero_movimiento_estorno` | Timestamp ad hoc | Sustituir por `allocate("inv_movimiento")` en misma UoW de estorno |
| `_gen_numero_movimiento` en aprobación IF | Prefijo `INV-AJUS` timestamp | ALLOCATE Motor (mismo key movimiento o documentar excepción — **preferir** `inv_movimiento`) |

Esto es **mayor riesgo funcional** que los maestros; por eso fase B debe ser explícita.

---

## 6. Riesgos arquitectónicos

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| A-01 | Tentar modificar Catalog “porque padding SKU es 5” | Alta | Prohibido Baseline; cfg override |
| A-02 | Migrar documentos antes que maestros | Media | OK si deps listas; recomendar maestros primero |
| A-03 | Dejar Update SKU mutable “por stock” | Alta | BR-IMM desde CREATE; no detector de stock |
| A-04 | Doble numeración estorno vs create manual | Alta | Un solo allocate path |
| A-05 | Mezclar FISCAL con MOV | Baja | MOV es CFG F2, no serie SUNAT |
| A-06 | UoW incompleta en movimiento+detalle | Alta | Allocate + cabecera + detalle misma TX (como patrón INV ya parcial) |
| A-07 | Scope ALMACEN confundido con EMPRESA | Media | Catálogo dice EMPRESA para estas keys — no inventar ALMACEN en Ola 1 |

---

*Plan de implementación: [`04_IMPLEMENTATION_PLAN.md`](04_IMPLEMENTATION_PLAN.md)*
