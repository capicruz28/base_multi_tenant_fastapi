# Estructura de Módulos ERP — Diseño Completo

**Objetivo:** Definir la estructura ordenada de carpetas, módulos y dependencias para implementar los 27 módulos ERP siguiendo la arquitectura actual del proyecto y el orden de dependencias.

**Referencias:** 
- Estructura actual: `app/modules/` (auth, rbac, modulos, menus, users, tenant, superadmin)
- Catálogo: `CATALOGO_MODULOS.md`
- Menú: `MENU_NAVEGACION.md`
- Tablas: `TABLAS_BD_ERP_COMPLETO.sql`

---

## 1. Orden de dependencias entre módulos (orden de creación)

Los módulos deben crearse e integrarse en este orden para respetar dependencias:

```
Nivel 0 (Base)
└── ORG  — Organización (empresa, sucursal, centro_costo, departamento, cargo, parametros)

Nivel 1 (Dependen solo de ORG)
├── INV  — Inventarios (productos, almacenes, stock, movimientos)
├── HCM  — Planillas & RRHH (empleados, contratos, planilla)
├── FIN  — Contabilidad (plan_cuentas, periodos, asientos)
└── DMS  — Gestión Documental

Nivel 2 (Dependen de ORG + INV y/o otros Nivel 1)
├── PUR  — Compras (proveedores, OC, recepción) ...................... ORG, INV
├── SLS  — Ventas (clientes, cotizaciones, pedidos) ................. ORG, INV
├── WMS  — Almacenes avanzados (zonas, ubicaciones, tareas) ......... ORG, INV
├── QMS  — Calidad (inspecciones, no conformidades) .................. ORG, INV
├── MFG  — Producción (BOM, órdenes producción, rutas) .............. ORG, INV
└── MNT  — Mantenimiento (activos, planes, OT) ...................... ORG [, MFG opcional]

Nivel 3 (Dependen de Nivel 2)
├── INV_BILL — Facturación electrónica (comprobantes, series) ........ SLS
├── LOG  — Logística (transportistas, guías, despachos) ............. ORG, SLS
├── SVC  — Órdenes de servicio (talleres, stock en terceros) ........ ORG, INV
├── MRP  — Planeamiento de materiales (explosión BOM, sugerencias)  MFG, INV
├── CRM  — Gestión de clientes (leads, oportunidades) ............... ORG, SLS
├── PRC  — Precios y promociones ..................................... ORG, INV, SLS
├── TAX  — Libros electrónicos (PLE) ................................ FIN
└── BDG  — Presupuestos .............................................. FIN, ORG

Nivel 4 (Dependen de Nivel 3 u otros)
├── MPS  — Plan maestro de producción ............................... MFG, MRP
├── CST  — Costeo de productos ....................................... INV, MFG, FIN
├── POS  — Punto de venta ............................................ ORG, INV, SLS
├── PM   — Gestión de proyectos ...................................... ORG
├── TKT  — Mesa de ayuda ............................................. ORG
├── BI   — Reportes y analytics ..................................... (todos)
├── WFL  — Flujos de trabajo ......................................... ORG
└── AUD  — Auditoría ................................................. (todos)
```

**Orden recomendado de implementación (primeros 5 módulos básicos):**

1. **ORG**  
2. **INV**  
3. **PUR**  
4. **SLS**  
5. **INV_BILL**

Luego, según necesidad: LOG, WMS, QMS, MFG, MNT, SVC, etc.

---

## 2. Estructura de carpetas por módulo (patrón actual)

Cada módulo ERP sigue el mismo patrón que `auth`, `rbac`, `modulos`, `menus`:

```
app/
├── api/
│   └── v1/
│       └── api.py                    # Incluye routers de todos los módulos ERP
│
├── core/                             # Sin cambios (auth, config, tenant, exceptions, etc.)
│
├── infrastructure/
│   └── database/
│       ├── queries/
│       │   ├── org/                  # Queries ORG
│       │   │   ├── __init__.py
│       │   │   ├── empresa_queries.py
│       │   │   ├── sucursal_queries.py
│       │   │   ├── centro_costo_queries.py
│       │   │   ├── departamento_queries.py
│       │   │   ├── cargo_queries.py
│       │   │   └── parametro_queries.py
│       │   ├── inv/                  # Queries INV
│       │   │   ├── __init__.py
│       │   │   ├── categoria_queries.py
│       │   │   ├── unidad_medida_queries.py
│       │   │   ├── producto_queries.py
│       │   │   ├── almacen_queries.py
│       │   │   ├── stock_queries.py
│       │   │   ├── tipo_movimiento_queries.py
│       │   │   ├── movimiento_queries.py
│       │   │   └── inventario_fisico_queries.py
│       │   ├── pur/                  # Queries PUR
│       │   ├── sls/                  # Queries SLS
│       │   ├── inv_bill/             # Queries Facturación
│       │   ├── log/
│       │   ├── wms/
│       │   ├── qms/
│       │   ├── mfg/
│       │   ├── mnt/
│       │   ├── svc/
│       │   └── ...                   # Resto de módulos
│       ├── tables_erp/               # Tablas SQLAlchemy Core por dominio
│       │   ├── __init__.py           # Re-exporta todas las tablas ERP
│       │   ├── tables_org.py         # org_empresa, org_centro_costo, org_sucursal, ...
│       │   ├── tables_inv.py         # inv_producto, inv_almacen, inv_stock, ...
│       │   ├── tables_pur.py
│       │   ├── tables_sls.py
│       │   ├── tables_inv_bill.py
│       │   └── ...
│       ├── tables.py                 # Tablas central/auth (existente)
│       ├── tables_modulos.py         # Tablas módulos/menú (existente)
│       └── queries_async.py         # Sin cambios estructurales; usa queries por módulo
│
└── modules/
    ├── auth/                         # Existente
    ├── rbac/                         # Existente
    ├── users/                        # Existente
    ├── menus/                        # Existente
    ├── modulos/                      # Existente
    ├── tenant/                      # Existente
    ├── superadmin/                  # Existente
    │
    │   ═══════════════════════════════════════════════════════════
    │   MÓDULOS ERP (nuevos) — Mismo patrón por módulo
    │   ═══════════════════════════════════════════════════════════
    │
    ├── org/                          # Módulo ORG — Organización
    │   ├── __init__.py
    │   ├── application/
    │   │   ├── __init__.py
    │   │   ├── services/
    │   │   │   ├── __init__.py
    │   │   │   ├── empresa_service.py
    │   │   │   ├── sucursal_service.py
    │   │   │   ├── centro_costo_service.py
    │   │   │   ├── departamento_service.py
    │   │   │   ├── cargo_service.py
    │   │   │   └── parametro_sistema_service.py
    │   │   └── use_cases/            # Opcional
    │   ├── domain/
    │   │   ├── __init__.py
    │   │   └── entities/             # Opcional: Empresa, Sucursal, ...
    │   ├── infrastructure/
    │   │   ├── __init__.py
    │   │   └── repositories/         # Opcional; si no, se usan queries en infrastructure/database/queries/org
    │   └── presentation/
    │       ├── __init__.py
    │       ├── schemas.py            # Pydantic: EmpresaRead, EmpresaCreate, ...
    │       ├── endpoints_empresa.py
    │       ├── endpoints_sucursales.py
    │       ├── endpoints_centros_costo.py
    │       ├── endpoints_departamentos.py
    │       ├── endpoints_cargos.py
    │       └── endpoints_parametros.py
    │
    ├── inv/                          # Módulo INV — Inventarios
    │   ├── __init__.py
    │   ├── application/
    │   │   ├── __init__.py
    │   │   └── services/
    │   │       ├── __init__.py
    │   │       ├── categoria_producto_service.py
    │   │       ├── unidad_medida_service.py
    │   │       ├── producto_service.py
    │   │       ├── almacen_service.py
    │   │       ├── stock_service.py
    │   │       ├── tipo_movimiento_service.py
    │   │       ├── movimiento_service.py
    │   │       └── inventario_fisico_service.py
    │   ├── domain/
    │   │   └── __init__.py
    │   ├── infrastructure/
    │   │   └── __init__.py
    │   └── presentation/
    │       ├── __init__.py
    │       ├── schemas.py
    │       ├── endpoints_categorias.py
    │       ├── endpoints_unidades_medida.py
    │       ├── endpoints_productos.py
    │       ├── endpoints_almacenes.py
    │       ├── endpoints_stock.py
    │       ├── endpoints_tipos_movimiento.py
    │       ├── endpoints_movimientos.py
    │       └── endpoints_inventario_fisico.py
    │
    ├── pur/                          # Módulo PUR — Compras
    │   ├── __init__.py
    │   ├── application/
    │   │   └── services/
    │   │       ├── proveedor_service.py
    │   │       ├── solicitud_compra_service.py
    │   │       ├── cotizacion_compra_service.py
    │   │       ├── orden_compra_service.py
    │   │       └── recepcion_service.py
    │   ├── domain/
    │   ├── infrastructure/
    │   └── presentation/
    │       ├── schemas.py
    │       ├── endpoints_proveedores.py
    │       ├── endpoints_solicitudes_compra.py
    │       ├── endpoints_cotizaciones.py
    │       ├── endpoints_ordenes_compra.py
    │       └── endpoints_recepciones.py
    │
    ├── sls/                          # Módulo SLS — Ventas
    │   ├── __init__.py
    │   ├── application/
    │   │   └── services/
    │   │       ├── cliente_venta_service.py
    │   │       ├── cotizacion_venta_service.py
    │   │       └── pedido_service.py
    │   ├── domain/
    │   ├── infrastructure/
    │   └── presentation/
    │       ├── schemas.py
    │       ├── endpoints_clientes.py
    │       ├── endpoints_cotizaciones.py
    │       └── endpoints_pedidos.py
    │
    ├── inv_bill/                     # Módulo INV_BILL — Facturación electrónica
    │   ├── __init__.py
    │   ├── application/
    │   │   └── services/
    │   │       ├── serie_comprobante_service.py
    │   │       └── comprobante_service.py
    │   ├── domain/
    │   ├── infrastructure/
    │   └── presentation/
    │       ├── schemas.py
    │       ├── endpoints_series.py
    │       ├── endpoints_comprobantes.py
    │       └── endpoints_registro_ventas.py
    │
    ├── log/                          # LOG — Logística
    ├── wms/                          # WMS — Almacenes
    ├── qms/                          # QMS — Calidad
    ├── mfg/                          # MFG — Producción
    ├── mnt/                          # MNT — Mantenimiento
    ├── svc/                          # SVC — Servicios
    ├── crm/                          # CRM
    ├── prc/                          # PRC — Precios
    ├── pos/                          # POS
    ├── hcm/                          # HCM — Planillas
    ├── fin/                          # FIN — Contabilidad
    ├── tax/                          # TAX
    ├── bdg/                          # BDG — Presupuestos
    ├── cst/                          # CST — Costeo
    ├── pm/                           # PM — Proyectos
    ├── tkt/                          # TKT — Mesa de ayuda
    ├── bi/                           # BI — Reportes
    ├── dms/                          # DMS — Documental
    ├── wfl/                          # WFL — Workflows
    └── aud/                          # AUD — Auditoría
```

Cada módulo `log`, `wms`, … `aud` tiene la misma forma: `application/services/`, `domain/`, `infrastructure/`, `presentation/` (schemas + endpoints por subdominio).

---

## 3. Integración en API v1 (`app/api/v1/api.py`)

Los routers se incluyen por grupo y en orden de dependencia lógica (no técnica). Prefijos y tags sugeridos:

```python
# ========================================
# MÓDULOS ERP (por orden de dependencia)
# ========================================

# Nivel 0 - Organización
from app.modules.org.presentation import endpoints_empresa, endpoints_sucursales, ...
api_router.include_router(endpoints_empresa.router, prefix="/org/empresa", tags=["ORG - Empresa"])
api_router.include_router(endpoints_sucursales.router, prefix="/org/sucursales", tags=["ORG - Sucursales"])
# ... resto ORG

# Nivel 1 - Inventarios
from app.modules.inv.presentation import endpoints_productos, endpoints_almacenes, ...
api_router.include_router(endpoints_productos.router, prefix="/inv/productos", tags=["INV - Productos"])
# ... resto INV

# Compras
from app.modules.pur.presentation import ...
api_router.include_router(..., prefix="/pur/...", tags=["PUR - Compras"])

# Ventas
from app.modules.sls.presentation import ...
api_router.include_router(..., prefix="/sls/...", tags=["SLS - Ventas"])

# Facturación
from app.modules.inv_bill.presentation import ...
api_router.include_router(..., prefix="/facturacion/...", tags=["INV_BILL - Facturación"])

# ... LOG, WMS, QMS, MFG, MNT, SVC, etc.
```

Prefijos sugeridos por módulo:

- `/org/` — Organización  
- `/inv/` — Inventarios  
- `/pur/` — Compras  
- `/sls/` — Ventas  
- `/facturacion/` o `/inv-bill/` — Facturación  
- `/log/` — Logística  
- `/wms/` — Almacenes  
- `/qms/` — Calidad  
- `/mfg/` — Producción  
- `/mnt/` — Mantenimiento  
- `/svc/` — Servicios  
- Resto análogo (crm, prc, pos, hcm, fin, tax, bdg, cst, pm, tkt, bi, dms, wfl, aud).

---

## 4. Tablas ERP (SQLAlchemy Core)

- **Ubicación:** `app/infrastructure/database/tables_erp/`
- **Archivos:** uno por dominio, alineado con `TABLAS_BD_ERP_COMPLETO.sql`:
  - `tables_org.py` → org_empresa, org_centro_costo, org_sucursal, org_departamento, org_cargo, org_parametro_sistema
  - `tables_inv.py` → inv_categoria_producto, inv_unidad_medida, inv_producto, inv_almacen, inv_stock, inv_tipo_movimiento, inv_movimiento, inv_movimiento_detalle, inv_inventario_fisico, inv_inventario_fisico_detalle
  - `tables_pur.py`, `tables_sls.py`, `tables_inv_bill.py`, …
- **Metadata:** Reutilizar `metadata` de `app.infrastructure.database.tables` para FKs entre tablas central y ERP donde aplique, o un `metadata_erp` propio si se mantienen BDs separadas.
- **Uso:** En servicios y en `queries_async` (o helpers) se importan desde `app.infrastructure.database.tables_erp`.

---

## 5. Menús (MENU_NAVEGACION.md)

- Cada ítem del menú en `MENU_NAVEGACION.md` se refleja en:
  - **BD:** `modulo` (por módulo ERP), `modulo_seccion` (si aplica), `modulo_menu` (una entrada por opción de menú con ruta y nombre).
- **Rutas front:** Deben coincidir con las rutas definidas en `modulo_menu.ruta` (ej. `/org/empresa`, `/inv/productos`, `/inv/almacenes`, …).
- **Seeding:** Script o migración que inserte módulos ERP y sus ítems de menú a partir de `MENU_NAVEGACION.md` (y de `CATALOGO_MODULOS.md` para códigos/nombres de módulo).

---

## 6. Reglas de diseño (senior SaaS)

1. **Multi-tenant:** Todas las queries y servicios reciben o resuelven `client_id` (y `empresa_id` si aplica) desde el contexto; no confiar en parámetros de cliente sin validar.
2. **Aislamiento:** Usar SQLAlchemy Core + `apply_tenant_filter` o TextClause con filtro automático; stored procedures validando `client_id` contra contexto.
3. **Capas:**  
   - Presentation: solo DTOs (schemas) y llamadas a application.  
   - Application: servicios y use cases; sin acceso directo a SQL.  
   - Infrastructure: queries, tablas, repositorios (si se usan).
4. **Errores:** Usar `BaseService.handle_service_errors` y excepciones de `app.core.exceptions`.
5. **Permisos:** Cada endpoint protegido; menús y acciones alineados con `rol_menu_permiso` (RBAC/LBAC existente).
6. **Orden de implementación:** Respetar el orden de dependencias de la sección 1 para no tener referencias rotas entre módulos.

---

## 7. Resumen de estructura con módulos creados (vista reducida)

```
app/
├── api/v1/api.py                     # Incluye routers: /org/*, /inv/*, /pur/*, /sls/*, /facturacion/*, ...
├── core/                             # Sin cambios
├── infrastructure/database/
│   ├── queries/
│   │   ├── org/
│   │   ├── inv/
│   │   ├── pur/
│   │   ├── sls/
│   │   ├── inv_bill/
│   │   ├── log/
│   │   ├── wms/
│   │   ├── qms/
│   │   ├── mfg/
│   │   └── ... (resto por módulo)
│   ├── tables_erp/
│   │   ├── tables_org.py
│   │   ├── tables_inv.py
│   │   ├── tables_pur.py
│   │   ├── tables_sls.py
│   │   ├── tables_inv_bill.py
│   │   └── ...
│   ├── tables.py
│   ├── tables_modulos.py
│   └── queries_async.py
└── modules/
    ├── auth/ ... users/ menus/ modulos/ tenant/ superadmin/  # Existentes
    ├── org/      # application/services, presentation/endpoints_*, schemas
    ├── inv/
    ├── pur/
    ├── sls/
    ├── inv_bill/
    ├── log/
    ├── wms/
    ├── qms/
    ├── mfg/
    ├── mnt/
    ├── svc/
    ├── crm/
    ├── prc/
    ├── pos/
    ├── hcm/
    ├── fin/
    ├── tax/
    ├── bdg/
    ├── cst/
    ├── pm/
    ├── tkt/
    ├── bi/
    ├── dms/
    ├── wfl/
    └── aud/
```

Con esta estructura, todos los módulos quedan creados de forma ordenada, siguiendo la estructura actual del proyecto y las dependencias entre módulos. Cuando indiques cómo quieres proceder (por ejemplo: solo ORG+INV primero, o solo BD + menús), se puede bajar a tareas concretas de implementación paso a paso.
