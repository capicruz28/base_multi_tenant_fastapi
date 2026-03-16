# Candidatos a permisos nuevos (alta en tabla `permiso`)

**Fecha:** 2026-02-18  
**Contexto:** Permisos con convención `<modulo>.<recurso>.<accion>` usados en FASE 3 que **no** están en el seed actual (`SEED_PERMISOS_RBAC.sql`). Deben validarse para seed o auto-registro en la tabla `permiso`.

---

## Criterio

- **[S]** = permiso ya existente en seed (no listado aquí).
- **[C]** = candidato para alta (listado en este documento).

---

## Candidatos detectados en HCM (FASE 3 piloto)

Los siguientes códigos se aplicaron en endpoints HCM y **no** figuran en el seed actual. El seed HCM solo incluye `hcm.empleado.*` y `hcm.planilla.leer` / `hcm.planilla.crear`.

| Código | Recurso | Acción | Nota |
|--------|---------|--------|------|
| hcm.contrato.leer | contrato | leer | CRUD contratos |
| hcm.contrato.crear | contrato | crear | |
| hcm.contrato.actualizar | contrato | actualizar | |
| hcm.concepto_planilla.leer | concepto_planilla | leer | CRUD conceptos planilla |
| hcm.concepto_planilla.crear | concepto_planilla | crear | |
| hcm.concepto_planilla.actualizar | concepto_planilla | actualizar | |
| hcm.planilla.actualizar | planilla | actualizar | Seed solo tiene leer/crear |
| hcm.planilla_empleado.leer | planilla_empleado | leer | CRUD planilla empleados |
| hcm.planilla_empleado.crear | planilla_empleado | crear | |
| hcm.planilla_empleado.actualizar | planilla_empleado | actualizar | |
| hcm.planilla_detalle.leer | planilla_detalle | leer | CRUD planilla detalle |
| hcm.planilla_detalle.crear | planilla_detalle | crear | |
| hcm.planilla_detalle.actualizar | planilla_detalle | actualizar | |
| hcm.asistencia.leer | asistencia | leer | CRUD asistencia |
| hcm.asistencia.crear | asistencia | crear | |
| hcm.asistencia.actualizar | asistencia | actualizar | |
| hcm.vacaciones.leer | vacaciones | leer | CRUD vacaciones |
| hcm.vacaciones.crear | vacaciones | crear | |
| hcm.vacaciones.actualizar | vacaciones | actualizar | |
| hcm.prestamo.leer | prestamo | leer | CRUD préstamos |
| hcm.prestamo.crear | prestamo | crear | |
| hcm.prestamo.actualizar | prestamo | actualizar | |

---

## Uso recomendado

- Incluir estos códigos en un **script de ampliación del seed** (MERGE/INSERT en `permiso`) con el `modulo_id` correspondiente al módulo HCM en `SEED_MODULO_MENU_COMPLETO.sql`, o
- Usarlos como entrada al **auto-registro** de permisos cuando esté implementado.

No se ha añadido lógica adicional en el proyecto; los endpoints quedan preparados para que el permiso exista en BD (403 hasta que se dé de alta el permiso y se asigne al rol correspondiente).

---

## Candidatos detectados en LOG (FASE 3)

Los siguientes códigos se aplicaron en endpoints LOG (riesgo BAJO) y **no** figuran en el seed actual. El seed LOG incluye `log.ruta.*`; el resto son [C].

| Código | Recurso | Acción | Nota |
|--------|---------|--------|------|
| log.transportista.leer | transportista | leer | CRUD transportistas |
| log.transportista.crear | transportista | crear | |
| log.transportista.actualizar | transportista | actualizar | |
| log.vehiculo.leer | vehiculo | leer | CRUD vehículos |
| log.vehiculo.crear | vehiculo | crear | |
| log.vehiculo.actualizar | vehiculo | actualizar | |
| log.guia_remision.leer | guia_remision | leer | CRUD guías de remisión (cabecera) |
| log.guia_remision.crear | guia_remision | crear | |
| log.guia_remision.actualizar | guia_remision | actualizar | |
| log.despacho.leer | despacho | leer | CRUD despachos (cabecera) |
| log.despacho.crear | despacho | crear | |
| log.despacho.actualizar | despacho | actualizar | |

---

## Candidatos detectados en INV (FASE 3)

Los siguientes códigos se aplicaron en endpoints INV (riesgo BAJO) y **no** figuran en el seed actual. El seed INV incluye `inv.producto.*`; el resto son [C].

| Código | Recurso | Acción | Nota |
|--------|---------|--------|------|
| inv.categoria.leer | categoria | leer | CRUD categorías |
| inv.categoria.crear | categoria | crear | |
| inv.categoria.actualizar | categoria | actualizar | |
| inv.unidad_medida.leer | unidad_medida | leer | CRUD unidades de medida |
| inv.unidad_medida.crear | unidad_medida | crear | |
| inv.unidad_medida.actualizar | unidad_medida | actualizar | |
| inv.almacen.leer | almacen | leer | CRUD almacenes |
| inv.almacen.crear | almacen | crear | |
| inv.almacen.actualizar | almacen | actualizar | |
| inv.stock.leer | stock | leer | CRUD stock |
| inv.stock.crear | stock | crear | |
| inv.stock.actualizar | stock | actualizar | |
| inv.tipo_movimiento.leer | tipo_movimiento | leer | CRUD tipos de movimiento |
| inv.tipo_movimiento.crear | tipo_movimiento | crear | |
| inv.tipo_movimiento.actualizar | tipo_movimiento | actualizar | |
| inv.movimiento.leer | movimiento | leer | CRUD movimientos |
| inv.movimiento.crear | movimiento | crear | |
| inv.movimiento.actualizar | movimiento | actualizar | |
| inv.inventario_fisico.leer | inventario_fisico | leer | CRUD inventario físico |
| inv.inventario_fisico.crear | inventario_fisico | crear | |
| inv.inventario_fisico.actualizar | inventario_fisico | actualizar | |

---

## Candidatos detectados en FIN (FASE 3)

Los siguientes códigos se aplicaron en endpoints FIN (riesgo BAJO) y **no** figuran en el seed actual. El seed FIN incluye `fin.asiento.*`; el resto son [C].

| Código | Recurso | Acción | Nota |
|--------|---------|--------|------|
| fin.plan_cuenta.leer | plan_cuenta | leer | CRUD plan de cuentas |
| fin.plan_cuenta.crear | plan_cuenta | crear | |
| fin.plan_cuenta.actualizar | plan_cuenta | actualizar | |
| fin.periodo.leer | periodo | leer | CRUD periodos contables |
| fin.periodo.crear | periodo | crear | |
| fin.periodo.actualizar | periodo | actualizar | |
