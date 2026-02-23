# Estado de implementación — Módulos ERP

**Referencia:** TABLAS_BD_ERP_COMPLETO.sql, CATALOGO_MODULOS.md, MENU_NAVEGACION.md  
**Fecha:** 2026-02-18

---

## Confirmación: módulos ya implementados (14)

Según `app/api/v1/api.py` y los módulos existentes en `app/modules/`, están implementados **14 módulos ERP** (no 13; se cuenta MFG que se acaba de completar):

| # | Módulo   | Prefijo API | Descripción breve                    |
|---|----------|-------------|--------------------------------------|
| 1 | ORG      | /org        | Organización (empresa, sucursales, cargos, centros de costo) |
| 2 | INV      | /inv        | Inventarios (productos, almacenes, stock, movimientos)      |
| 3 | PUR      | /pur        | Compras (proveedores, OC, recepciones)                      |
| 4 | SLS      | /sls        | Ventas (clientes, cotizaciones, pedidos)                    |
| 5 | INV_BILL | /inv-bill   | Facturación electrónica (comprobantes, series)              |
| 6 | PRC      | /prc        | Precios y promociones (listas, promociones)                  |
| 7 | LOG      | /log        | Logística (transportistas, vehículos, guías, despachos)        |
| 8 | FIN      | /fin        | Finanzas y contabilidad (plan de cuentas, periodos, asientos) |
| 9 | WMS      | /wms        | Gestión de almacenes (zonas, ubicaciones, tareas)          |
|10 | QMS      | /qms        | Control de calidad (parámetros, planes, inspecciones, NC)    |
|11 | CRM      | /crm        | Gestión de clientes (campañas, leads, oportunidades, actividades) |
|12 | POS      | /pos        | Punto de venta (puntos de venta, turnos, ventas rápidas)    |
|13 | HCM      | /hcm        | Planillas y RRHH (empleados, contratos, planillas, asistencia, vacaciones, préstamos) |
|14 | MFG      | /mfg        | Manufactura y producción (centros, operaciones, BOM, rutas, OP, consumo) |

---

## Módulos pendientes de implementar (13)

Total de módulos en MENU_NAVEGACION / CATALOGO: **27**.  
Pendientes: **27 − 14 = 13**.

---

## Orden recomendado para implementar (por dependencias)

El orden respeta dependencias entre módulos (ORG e INV como base; MFG, FIN, SLS ya implementados). Implementar en este orden para no bloquear dependencias.

| Orden | Módulo | Dependencias principales | Tablas en TABLAS_BD_ERP_COMPLETO.sql |
|-------|--------|--------------------------|--------------------------------------|
| **1** | **MRP** | ORG, INV, MFG | mrp_plan_maestro, mrp_necesidad_bruta, mrp_explosion_materiales, mrp_orden_sugerida |
| **2** | **MPS** | ORG, INV, MFG | mps_pronostico_demanda, mps_plan_produccion, mps_plan_produccion_detalle |
| **3** | **MNT** | ORG, MFG | mnt_activo, mnt_plan_mantenimiento, mnt_orden_trabajo, mnt_historial_mantenimiento |
| **4** | **CST** | ORG, INV, MFG | cst_centro_costo_tipo, cst_producto_costo |
| **5** | **TAX** | FIN, INV_BILL | tax_libro_electronico |
| **6** | **BDG** | FIN, ORG | bdg_presupuesto, bdg_presupuesto_detalle |
| **7** | **PM** | ORG, FIN | pm_proyecto |
| **8** | **SVC** | ORG, INV | svc_orden_servicio |
| **9** | **TKT** | ORG (usuarios) | tkt_ticket |
| **10** | **DMS** | ORG | dms_documento |
| **11** | **WFL** | ORG, RBAC | wfl_flujo_trabajo |
| **12** | **BI** | Todos (lectura) | bi_reporte |
| **13** | **AUD** | Todos (log) | aud_log_auditoria |

---

## Resumen de dependencias (pendientes)

- **MRP, MPS, MNT, CST** requieren MFG (y ORG/INV) ya implementados → pueden seguir en ese orden.
- **TAX** requiere FIN e INV_BILL.
- **BDG, PM** requieren FIN y ORG.
- **SVC** requiere INV (y ORG).
- **TKT, DMS, WFL** requieren principalmente ORG (y RBAC para WFL).
- **BI** y **AUD** son transversales (lectura/log sobre el resto); pueden ir al final.

---

## Cómo proceder

Para cada módulo pendiente, en este orden:

1. Revisar en **TABLAS_BD_ERP_COMPLETO.sql** las tablas del módulo.
2. Revisar en **MENU_NAVEGACION.md** las pantallas/opciones del módulo.
3. Seguir el mismo patrón: `tables_erp/tables_<mod>.py` → `queries/<mod>/*` → `modules/<mod>/presentation/schemas.py` → `application/services/*` → `presentation/endpoints_*.py` → registrar en `api.py` → actualizar **PLAN_IMPLEMENTACION_MODULOS_ERP.md** → crear **DOC_FRONTEND_MODULO_<MOD>.md**.

Indica con cuál módulo pendiente quieres continuar (recomendado: **MRP** como siguiente).
