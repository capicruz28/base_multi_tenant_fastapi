# Validación FASE 3 — Módulos restantes (INV, FIN, SVC, TKT)

**Fecha:** 2026-02-18  
**Alcance:** Endpoints de riesgo BAJO en INV, FIN, SVC y TKT (tras HCM y LOG).  
**Objetivo:** Verificación estructural y confirmación de alineación con `rbac_patterns_and_conventions.md`.

---

## 1. Resumen global

| Módulo | Endpoints analizados | Endpoints decorados | No decorados (por diseño) | Inconsistencias |
|--------|----------------------|---------------------|----------------------------|-----------------|
| **INV** | 45 | 44 | 1 (stock_por_producto_almacen — MEDIO) | 0 |
| **FIN** | 16 | 12 | 4 (asiento_detalle — MEDIO) | 0 |
| **SVC** | 4 | 4 | 0 | 0 |
| **TKT** | 4 | 4 | 0 | 0 |
| **Total** | 69 | 64 | 5 | 0 |

---

## 2. INV (Inventarios)

### 2.1 Archivos modificados

| Archivo | Handlers total | Decorados | No decorados |
|---------|----------------|-----------|--------------|
| endpoints_categorias.py | 4 | 4 | 0 |
| endpoints_unidades_medida.py | 4 | 4 | 0 |
| endpoints_productos.py | 4 | 4 | 0 |
| endpoints_almacenes.py | 4 | 4 | 0 |
| endpoints_stock.py | 5 | 4 | 1 (stock_por_producto_almacen — MEDIO) |
| endpoints_tipos_movimiento.py | 4 | 4 | 0 |
| endpoints_movimientos.py | 4 | 4 | 0 |
| endpoints_inventario_fisico.py | 4 | 4 | 0 |

### 2.2 Permisos aplicados

- `inv.categoria.*`, `inv.unidad_medida.*`, `inv.producto.*`, `inv.almacen.*`, `inv.stock.*` (solo CRUD estándar), `inv.tipo_movimiento.*`, `inv.movimiento.*`, `inv.inventario_fisico.*` (leer, crear, actualizar).
- Endpoint **stock_por_producto_almacen** (GET `/producto/{id}/almacen/{id}`) no decorado — riesgo MEDIO.

### 2.3 Candidatos [C] nuevos

Véase `rbac_new_permissions_candidates.md` — sección INV (categoria, unidad_medida, almacen, stock, tipo_movimiento, movimiento, inventario_fisico). `inv.producto.*` [S] en seed.

---

## 3. FIN (Finanzas)

### 3.1 Archivos modificados

| Archivo | Handlers total | Decorados | No decorados |
|---------|----------------|-----------|--------------|
| endpoints_plan_cuentas.py | 4 | 4 | 0 |
| endpoints_periodos.py | 4 | 4 | 0 |
| endpoints_asientos.py | 8 | 4 | 4 (detalles asiento — MEDIO) |

### 3.2 Permisos aplicados

- **Plan de cuentas:** `fin.plan_cuenta.leer|crear|actualizar`.
- **Periodos:** `fin.periodo.leer|crear|actualizar`.
- **Asientos (solo CRUD cabecera):** `fin.asiento.leer|crear|actualizar`.
- **No decorados:** get_asiento_detalles, post_asiento_detalle, get_asiento_detalle, put_asiento_detalle — riesgo MEDIO.

### 3.3 Candidatos [C] nuevos

Véase `rbac_new_permissions_candidates.md` — sección FIN (plan_cuenta, periodo). `fin.asiento.*` [S] en seed.

---

## 4. SVC (Órdenes de servicio)

### 4.1 Cambio realizado

- **post_orden_servicio:** se añadió `_: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.crear"))`. Los demás handlers (GET list, GET by id, PUT) ya tenían permiso.

### 4.2 Permisos

- `svc.orden_servicio.leer`, `svc.orden_servicio.crear`, `svc.orden_servicio.actualizar` [S] en seed.

---

## 5. TKT (Tickets)

### 5.1 Cambio realizado

- **post_ticket:** se añadió `_: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.crear"))`. Los demás handlers ya tenían permiso.

### 5.2 Permisos

- `tkt.ticket.leer`, `tkt.ticket.crear`, `tkt.ticket.actualizar` [S] en seed.

---

## 6. Verificación estructural

| Criterio | INV | FIN | SVC | TKT |
|----------|-----|-----|-----|-----|
| current_user + require_permission en handlers BAJO | Sí | Sí | Sí | Sí |
| Orden dependencias (current_user luego permiso) | Sí | Sí | Sí | Sí |
| Convención `<modulo>.<recurso>.<accion>` | Sí | Sí | Sí | Sí |
| MODULE_CODE / RESOURCE_CODE donde aplica | Sí | Sí | (implícito) | (implícito) |
| Sin cambios de paths, nombres ni lógica | Sí | Sí | Sí | Sí |

---

## 7. Compatibilidad con auto-registro

Todos los endpoints decorados usan `Depends(require_permission(...))` con string concreto; el código de permiso es recuperable por AST o inspección y compatible con la tabla `permiso`.

---

## 8. Alineación con el estándar

**Confirmación:** INV, FIN, SVC y TKT mantienen alineación completa con `docs/rbac_patterns_and_conventions.md`: Patrón A, convención `<modulo>.<recurso>.<accion>`, solo riesgo BAJO modificado, MEDIO no tocado.

---

## 9. Resumen FASE 3 completa (todos los módulos BAJO)

| Módulo | Endpoints decorados (BAJO) |
|--------|----------------------------|
| HCM | 36 |
| LOG | 20 |
| INV | 44 |
| FIN | 12 |
| SVC | 4 (1 añadido: POST) |
| TKT | 4 (1 añadido: POST) |
| **Total FASE 3** | **120** |

**FASE 3 (solo riesgo BAJO) finalizada.** No se han detectado inconsistencias. Los módulos MEDIO/ALTO (Users, RBAC permisos, Menús/Áreas, detalles guía, detalles asiento, stock_por_producto_almacen) quedan sin modificar para revisión manual posterior.
