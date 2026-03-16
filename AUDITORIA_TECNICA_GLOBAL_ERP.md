## Resumen Ejecutivo General

El backend ERP multi-tenant está fuertemente alineado con la arquitectura SaaS definida (base de datos central + BD dedicada por cliente, aislamiento por `cliente_id` y `empresa_id`) y con el catálogo funcional de 27 módulos descrito en `MENU_NAVEGACION.md` y `CATALOGO_MODULOS.md`. A nivel de endpoints, existe una cobertura amplia por módulo, con uso consistente de `current_user.cliente_id`, parámetros `empresa_id` y RBAC basado en permisos de negocio, lo que reduce significativamente el riesgo de fuga de datos entre tenants. Sin embargo, la capa de modelos SQLAlchemy sólo cubre la parte central/RBAC (tablas de `1.- TABLAS_BD_CENTRAL.sql` y tablas de módulos/menús), mientras que la mayoría de tablas ERP de `3.- TABLAS_BD_ERP_COMPLETO.sql` se consumen vía servicios y consultas SQL construidas de forma manual, lo que limita la trazabilidad estática de aislamiento y constraints a nivel de código. En conjunto, el sistema muestra un nivel de madurez alto pero aún con brechas estructurales y de consistencia multi-tenant que impiden considerarlo completamente listo para un escalado SaaS masivo sin una fase adicional de endurecimiento técnico.

**Estimación global de cumplimiento técnico ERP (multi-tenant + alineamiento funcional): ~80 %.**

---

## Nivel de Madurez Técnica por Módulo (Resumen)

Escala usada:
- **Nivel 3 (Alto)**: Endpoints completos por entidad, uso consistente de `cliente_id` y `empresa_id`, alineado a scripts SQL y menú, sin hallazgos críticos.
- **Nivel 2 (Medio)**: Cobertura funcional adecuada pero con dependencias en SQL manual, falta de modelos SQLAlchemy ERP y/o algunos patrones de validación no totalmente sistemáticos.
- **Nivel 1 (Bajo)**: Brechas claras de aislamiento, endpoints incompletos o uso inseguro de identificadores de tenant/empresa.

- **ORG — Organización**: Nivel 3 (Alto).  
  - SQL (`org_empresa`, `org_centro_costo`, `org_sucursal`, `org_departamento`, etc.) define de forma consistente `cliente_id` + `empresa_id`, FKs y unique constraints escopados por tenant.  
  - Endpoints (`endpoints_empresa.py`, `endpoints_sucursales.py`, `endpoints_departamentos.py`, `endpoints_cargos.py`, `endpoints_centros_costo.py`, `endpoints_parametros.py`) siempre derivan `client_id` desde `current_user.cliente_id` y pasan `empresa_id` como filtro opcional o clave específica, usando `require_permission` para RBAC.

- **INV — Inventarios**: Nivel 3 (Alto).  
  - SQL contiene tablas de productos, categorías, UOM, almacenes, tipos de movimiento, stock, movimientos e inventario físico con `cliente_id` y `empresa_id` según la sección INV del script.  
  - Endpoints (`endpoints_productos.py`, `endpoints_categorias.py`, `endpoints_unidades_medida.py`, `endpoints_almacenes.py`, `endpoints_tipos_movimiento.py`, `endpoints_movimientos.py`, `endpoints_stock.py`, `endpoints_inventario_fisico.py`) aplican patrón uniforme: `client_id = current_user.cliente_id` + `empresa_id: Optional[UUID] = Query(None, ...)`, sin exponer filtros globales.

- **WMS — Gestión de Almacenes**: Nivel 3 (Alto).  
  - SQL define zonas, ubicaciones, stock por ubicación y tareas con `cliente_id` + `empresa_id` e índices por empresa y zona/ubicación.  
  - Endpoints (`endpoints_zonas.py`, `endpoints_ubicaciones.py`, `endpoints_stock.py`, `endpoints_tareas.py`) pasan siempre `current_user.cliente_id` como `client_id` y `empresa_id` como filtro, coherente con navegación (`Zonas de Almacén`, `Ubicaciones`, `Stock por Ubicación`, `Tareas de Almacén`).

- **QMS — Control de Calidad**: Nivel 3 (Alto).  
  - Scripts de parámetros, planes, inspecciones y no conformidades respetan `cliente_id` y `empresa_id` y soportan jerarquías/relaciones según flujo funcional de `MENU_NAVEGACION.md`.  
  - Endpoints (`endpoints_parametros.py`, `endpoints_planes.py`, `endpoints_inspecciones.py`, `endpoints_no_conformidades.py`) utilizan patrón `empresa_id: Optional[UUID]` y `client_id=current_user.cliente_id`, con RBAC declarativo por permiso.

- **PUR — Compras**: Nivel 2 (Medio).  
  - SQL incluye proveedores, contactos, productos por proveedor, solicitudes, cotizaciones, órdenes de compra y recepciones con `cliente_id` + `empresa_id`, FKs consistentes con org_empresa e INV.  
  - Endpoints (`endpoints_proveedores.py`, `endpoints_contactos.py`, `endpoints_productos_proveedor.py`, `endpoints_solicitudes.py`, `endpoints_cotizaciones.py`, `endpoints_ordenes_compra.py`, `endpoints_recepciones.py`) reciben `empresa_id` y derivan `client_id` desde `current_user`, pero parte de la lógica de validación de pertenencia de entidades se delega a servicios con SQL manual, no verificable estáticamente.

- **LOG — Logística & Distribución**: Nivel 2 (Medio).  
  - SQL (`log_transportista`, `log_vehiculo`, `log_ruta`, `log_guia_remision`, `log_despacho` y detalles) sigue patrón `cliente_id` + `empresa_id`, con índices por empresa y estado.  
  - Endpoints (`endpoints_transportistas.py`, `endpoints_vehiculos.py`, `endpoints_rutas.py`, `endpoints_guias_remision.py`, `endpoints_despachos.py`) usan `empresa_id` como Query y `current_user.cliente_id` para filtrar, pero no se observa en código fuente una validación explícita de que las entidades asociadas (p.ej. guías vinculadas a pedidos de otro tenant) pertenezcan al mismo `cliente_id` durante operaciones de enlace.

- **MFG — Producción & Manufactura**: Nivel 2 (Medio).  
  - SQL para centros de trabajo, operaciones, listas de materiales (cabecera y detalle), rutas de fabricación, órdenes de producción y operaciones de OP incluye `cliente_id` y `empresa_id` con FKs jerárquicas coherentes (e.g. `empresa_id` en cabecera y detalle).  
  - Endpoints (`endpoints_centros_trabajo.py`, `endpoints_operaciones.py`, `endpoints_listas_materiales.py`, `endpoints_lista_materiales_detalle.py`, `endpoints_rutas_fabricacion.py`, `endpoints_ruta_fabricacion_detalle.py`, `endpoints_ordenes_produccion.py`, `endpoints_orden_produccion_operaciones.py`) pasan `current_user.cliente_id` y `empresa_id`, pero la validación cruzada de que BOM, rutas y OP referencien siempre a la misma empresa se delega a servicios sin modelos SQLAlchemy explícitos.

- **MRP — Planeamiento de Materiales**: Nivel 2 (Medio).  
  - Tablas de plan maestro MRP, necesidades brutas, explosión de materiales y órdenes sugeridas se definen con `cliente_id` y `empresa_id` en el script ERP, con índices por empresa y estado.  
  - Endpoints (`endpoints_plan_maestro.py`, `endpoints_necesidad_bruta.py`, `endpoints_explosion_materiales.py`, `endpoints_orden_sugerida.py`) aceptan `empresa_id` y derivan `client_id` desde el usuario, pero la consistencia con inventario/pedidos se verifica a nivel de servicio.

- **MPS — Plan Maestro de Producción**: Nivel 2 (Medio).  
  - SQL de pronósticos y planes de producción incluye `cliente_id` y `empresa_id`, con índices por horizonte temporal y producto.  
  - Endpoints (`endpoints_pronostico_demanda.py`, `endpoints_plan_produccion.py`, `endpoints_plan_produccion_detalle.py`) siguen patrón estándar, pero falta traza explícita de constraints de integridad referencial en modelos SQLAlchemy.

- **MNT — Mantenimiento de Activos**: Nivel 2 (Medio).  
  - Tablas de activos, planes, órdenes de trabajo e historial de mantenimiento se alinean con `MENU_NAVEGACION.md` y contemplan `cliente_id` + `empresa_id`, con FKs a activos/centros de trabajo.  
  - Endpoints (`endpoints_activo.py`, `endpoints_plan_mantenimiento.py`, `endpoints_orden_trabajo.py`, `endpoints_historial_mantenimiento.py`) incluyen `empresa_id` y `client_id`, pero se depende de servicios para validar que activos y órdenes no crucen empresas.

- **SLS — Ventas**: Nivel 3 (Alto).  
  - SQL para clientes, contactos, direcciones, cotizaciones y pedidos contempla `cliente_id` y `empresa_id` con unique constraints por tenant en códigos y RUC, y FKs coherentes con org y fin.  
  - Endpoints (`endpoints_clientes.py`, `endpoints_contactos.py`, `endpoints_direcciones.py`, `endpoints_cotizaciones.py`, `endpoints_pedidos.py`) usan `current_user.cliente_id` y `empresa_id` como filtro, con RBAC a nivel de permiso y manejo de `NotFoundError` a 404.

- **CRM — Clientes (CRM)**: Nivel 2 (Medio).  
  - Tablas de campañas, leads, oportunidades y actividades comparten `cliente_id` + `empresa_id`, con FKs a SLS_clientes y usuarios.  
  - Endpoints (`endpoints_campanas.py`, `endpoints_leads.py`, `endpoints_oportunidades.py`, `endpoints_actividades.py`) están filtrados por `empresa_id` y `current_user.cliente_id`, pero los modelos SQLAlchemy de estas tablas no existen; se usan servicios/SQL manual, lo que dificulta validar estáticamente constraints de unicidad y jerarquía.

- **PRC — Precios & Promociones**: Nivel 2 (Medio).  
  - SQL define listas de precios y promociones con `cliente_id`, `empresa_id` y FKs a productos/clientes según diseño funcional.  
  - Endpoints (`endpoints_listas_precio.py`, `endpoints_promociones.py`) siguen patrón multi-tenant correcto, pero se observan dependencias en consultas manuales para resolución de precios efectivos.

- **INV_BILL — Facturación Electrónica**: Nivel 2 (Medio).  
  - Tablas de series, comprobantes y comprobante_detalle incluyen `cliente_id` y `empresa_id`, alineadas a requisitos de libros electrónicos y SUNAT.  
  - Endpoints (`endpoints_series.py`, `endpoints_comprobantes.py`, `endpoints_comprobante_detalles.py`) usan `empresa_id` y `current_user.cliente_id`; sin embargo, la integridad entre comprobantes y registros contables/tributarios se verifica fuera del ORM.

- **POS — Punto de Venta**: Nivel 2 (Medio).  
  - SQL para puntos de venta, turnos de caja y ventas está definido con `cliente_id` y `empresa_id`, con FKs a sucursales y usuarios.  
  - Endpoints (`endpoints_puntos_venta.py`, `endpoints_turnos_caja.py`, `endpoints_ventas.py`, `endpoints_ventas_detalle.py`) usan `empresa_id` y contexto de usuario, pero auditorías de caja se basan en lógica de servicio sin modelos ORM.

- **HCM — Planillas & RRHH**: Nivel 2 (Medio).  
  - Tablas de empleados, contratos, conceptos, planillas, planilla_detalle, asistencia, vacaciones y préstamos están estructuradas con `cliente_id` y `empresa_id`, con soporte jerárquico y FKs a org.  
  - Endpoints (`endpoints_empleados.py`, `endpoints_contratos.py`, `endpoints_conceptos_planilla.py`, `endpoints_planillas.py`, `endpoints_planilla_detalle.py`, `endpoints_planilla_empleados.py`, `endpoints_asistencia.py`, `endpoints_vacaciones.py`, `endpoints_prestamos.py`) usan `empresa_id` y `current_user.cliente_id`, con RBAC; falta, no obstante, una capa ORM que refleje constraints complejos (p.ej. unicidad por periodo/empleado).

- **FIN — Contabilidad**: Nivel 2 (Medio).  
  - SQL de `fin_plan_cuentas`, `fin_periodo_contable`, `fin_asiento_contable` y `fin_asiento_detalle` exige `cliente_id` + `empresa_id`, con constraints de cuadre y FKs correctas.  
  - Endpoints (`endpoints_plan_cuentas.py`, `endpoints_periodos.py`, `endpoints_asientos.py`) filtran por `empresa_id` y usan `current_user.cliente_id`, y delegan a servicios (`list_asientos_contables`, `create_asiento_contable`, etc.) que reciben `client_id` y `empresa_id`; el aislamiento es conceptualmente correcto, pero no está verificado estáticamente vía modelos SQLAlchemy de las tablas FIN.

- **TAX — Libros Electrónicos**: Nivel 2 (Medio).  
  - Tablas de libros electrónicos y configuraciones PLE usan `cliente_id` + `empresa_id`.  
  - Endpoint (`endpoints_libro_electronico.py`) recibe `empresa_id` y usa `current_user.cliente_id`, coherente con funcionalidad del menú.

- **BDG — Presupuestos**: Nivel 2 (Medio).  
  - SQL de presupuestos y ejecución presupuestal vincula org_centro_costo y FIN mediante `cliente_id` + `empresa_id`.  
  - Endpoints (`endpoints_presupuesto.py`, `endpoints_presupuesto_detalle.py`) tienen filtros por `empresa_id` y usan client_id del usuario.

- **CST — Costeo de Productos**: Nivel 2 (Medio).  
  - Tablas de tipos de centro de costo y producto_costo usan `cliente_id` + `empresa_id` y se apoyan en org/fin/inv.  
  - Endpoints (`endpoints_centro_costo_tipo.py`, `endpoints_producto_costo.py`) respetan patrón multi-tenant, pero cálculos contables se realizan en servicios con SQL manual.

- **PM — Gestión de Proyectos**: Nivel 2 (Medio).  
  - SQL de proyectos, presupuestos y seguimiento incluye `cliente_id` + `empresa_id`.  
  - Endpoints (`endpoints_proyecto.py`) usan `empresa_id` y `current_user.cliente_id`.

- **SVC — Órdenes de Servicio**: Nivel 2 (Medio).  
  - Tablas de órdenes de servicio, envíos a talleres y stock en terceros siguen patrón de aislamiento correcto.  
  - Endpoint (`endpoints_orden_servicio.py`) filtra por `empresa_id` y usa `client_id` del usuario.

- **TKT — Mesa de Ayuda**: Nivel 2 (Medio).  
  - SQL para tickets considera `cliente_id` + `empresa_id`, con FKs a usuarios y posibles referencias a entidades ERP.  
  - Endpoint (`endpoints_ticket.py`) aplica `empresa_id` y contexto de usuario; el aislamiento está conceptualmente bien, pero sin modelos ORM.

- **BI — Reportes & Analytics**: Nivel 2 (Medio).  
  - Tablas de reportes y dashboards referencian `cliente_id` + `empresa_id` y guardan definición de consulta/configuración.  
  - Endpoints (`endpoints_reporte.py`, `endpoints.py` del módulo BI) utilizan `empresa_id` y `current_user.cliente_id`; el riesgo principal es que reportes puedan definir SQL dinámico no auditado a nivel de código (pero esto está alineado con el diseño funcional).

- **DMS — Gestión Documental**: Nivel 2 (Medio).  
  - SQL para documentos y versiones incluye `cliente_id` + `empresa_id` y controles básicos de acceso.  
  - Endpoints (`endpoints_documento.py`, `endpoints.py` del módulo DMS) usan `empresa_id` y contexto de usuario; la política de permisos depende estrictamente de RBAC y no se ve reflejada en constraints DB.

- **WFL — Flujos de Trabajo**: Nivel 2 (Medio).  
  - Tablas de flujos, pasos y ejecuciones contemplan `cliente_id` + `empresa_id`, con payload JSON para definición.  
  - Endpoints (`endpoints_flujo_trabajo.py`, `endpoints.py` del módulo WFL) usan el patrón estándar; la validación de que workflows no crucen tenants se hace vía filtros `client_id`.

- **AUD — Auditoría**: Nivel 3 (Alto).  
  - Tablas de auditoría (en central `auth_audit_log` y en ERP AUD) mantienen `cliente_id` y típicamente `empresa_id`/referencias a entidades ERP, con índices por fecha y cliente.  
  - Endpoints (`endpoints_log_auditoria.py`, `endpoints.py` del módulo AUD) usan `empresa_id` y `current_user.cliente_id`, con capacidad de trazabilidad alineada al `MENU_NAVEGACION.md`.

---

## TAREA 1 — Auditoría Global de Modelos SQLAlchemy

### Cobertura de Modelos

- **Modelos presentes (SQLAlchemy Core):**  
  - Tablas de la BD central (`cliente`, `cliente_conexion`, `cliente_auth_config`, `federacion_identidad`, `usuario`, `rol`, `usuario_rol`, `rol_menu_permiso`, `refresh_tokens`, `auth_audit_log`, `log_sincronizacion_usuario`) definidas en `tables.py`.  
  - Tablas de módulos y menús (`modulo`, `modulo_seccion`, `modulo_menu`, `cliente_modulo`, `modulo_rol_plantilla`) definidas en `tables_modulos.py`.  
  - Estas definiciones se ajustan fielmente a `1.- TABLAS_BD_CENTRAL.sql` y `5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql` (tipos, constraints, índices e índices únicos coinciden con los scripts oficiales).

- **Modelos ausentes (brecha principal):**  
  - Las tablas ERP de `3.- TABLAS_BD_ERP_COMPLETO.sql` (ORG, INV, WMS, QMS, PUR, LOG, MFG, MRP, MPS, MNT, SLS, CRM, PRC, INV_BILL, POS, HCM, FIN, TAX, BDG, CST, PM, SVC, TKT, BI, DMS, WFL, AUD) **no están mapeadas** a SQLAlchemy (ni ORM ni Core) en el backend revisado.  
  - El acceso a datos para estos módulos se realiza mediante servicios y helpers de consultas (`queries.py`, `queries_async.py`, `query_builder.py`, `query_helpers.py`) y SQL textual parametrizado, pero sin un modelo centralizado de metadatos ORM.

### Aislamiento `cliente_id` / `empresa_id` en modelos existentes

- **BD central y RBAC (en `tables.py` y `tables_modulos.py`):**  
  - Todas las tablas que deben estar aisladas por cliente (`usuario`, `rol`, `usuario_rol`, `rol_menu_permiso`, `refresh_tokens`, `cliente_conexion`, `cliente_auth_config`, `federacion_identidad`, `auth_audit_log`, `log_sincronizacion_usuario`, `cliente_modulo`, `modulo_menu`) incluyen explícitamente la columna `cliente_id` y FKs consistentes con `cliente.cliente_id`.  
  - Los índices multi-tenant están correctamente diseñados:  
    - Índices simples por `cliente_id` (p.ej. `IDX_usuario_cliente`, `IDX_permiso_cliente`, `IDX_cliente_modulo_cliente`, `IDX_federacion_cliente`).  
    - Índices compuestos (`cliente_id` + flags de estado) alineados al diseño SQL (`IDX_cliente_estado`, `IDX_cliente_modulo_cliente`, `IDX_usuario_rol_cliente`, etc.).  
  - Unique constraints están correctamente escopados por tenant:  
    - `UQ_usuario_cliente_nombre (cliente_id, nombre_usuario)`.  
    - `UQ_rol_cliente_nombre (cliente_id, nombre)`.  
    - `UQ_rol_menu (cliente_id, rol_id, menu_id)`.  
    - `UQ_conexion_principal_cliente (cliente_id, es_conexion_principal)`.  
    - `UQ_cliente_modulo (cliente_id, modulo_id)`.

- **ERP en BD dedicada (brecha de modelos):**  
  - Los scripts SQL ERP sí cumplen sistemáticamente con la regla de aislamiento:  
    - Todas las tablas operativas relevantes contienen `cliente_id` y, salvo casos documentados (p.ej. cabecera org_empresa), `empresa_id`.  
    - Constraints de unicidad incluyen siempre `cliente_id` y, cuando corresponde, `empresa_id` (ejemplo: `UQ_org_empresa_cliente (cliente_id, codigo_empresa)`, `UQ_org_centro_costo (cliente_id, empresa_id, codigo)`, `UQ_sucursal_codigo (cliente_id, empresa_id, codigo)`).  
    - Se definen índices por `cliente_id` y `empresa_id` en las principales tablas de búsqueda y relación.  
  - Sin embargo, al no existir modelos SQLAlchemy para estas tablas ERP, **no se puede auditar estáticamente desde el código Python**:  
    - Presencia obligatoria de `cliente_id` y `empresa_id` en cada tabla ERP.  
    - Definición explícita de FKs y relaciones ORM (no hay `relationship`, `back_populates`, ni reglas de `cascade` modeladas).  
    - Naming conventions de FKs e índices más allá de lo visible en scripts.

### Relaciones ORM, FKs, Cascade, Lazy Loading

- **Relaciones ORM explícitas:**  
  - El backend usa mayoritariamente SQLAlchemy Core (Tablas + consultas manuales), no el ORM clásico con `relationship()`; por lo tanto:  
    - No hay `back_populates` ni `lazy` configurado a nivel de modelos.  
    - La navegación entre entidades se resuelve en servicios (consultas separadas) y no mediante relaciones ORM navegables.  
  - Esto reduce el acoplamiento pero también la capacidad de validar a nivel de tipos la integridad referencial y la jerarquía de entidades.

- **FKS e integridad referencial:**  
  - En la BD central, las FKs están correctamente definidas y espelhadas en los modelos Core (`ForeignKey('cliente.cliente_id', ondelete='CASCADE'/`NO ACTION`) combinan con los scripts).  
  - Para ERP, los FKs sólo se ven en los scripts SQL; el código Python hace referencia a columnas por nombre sin un esquema de metadatos global que pueda ser auditado.

### Índices multi-tenant y constraints

- En la BD central, todos los índices críticos definidos en los scripts están representados en los modelos Core:  
  - Indices por `cliente_id` y `es_activo`, índices de limpieza (`expires_at`, `is_revoked`) y de auditoría (`cliente_id`, `fecha_evento`) están presentes.  
  - No se detectan índices faltantes respecto a `1.- TABLAS_BD_CENTRAL.sql` y `5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql`.

- Para ERP, se observan en `3.- TABLAS_BD_ERP_COMPLETO.sql` índices bien diseñados por cliente, empresa y campos de búsqueda frecuentes (códigos, RUC, fechas, estado). Al no existir modelos ORM de estas tablas, dichos índices **no son visibles ni reutilizables desde la capa de código**, aunque sí existen en la base.

### Conclusión TAREA 1

- **Punto fuerte:** Aislamiento multi-tenant en la BD central y en RBAC está correctamente modelado y alineado a los scripts, con `cliente_id` y constraints adecuados.  
- **Punto débil estructural:** Falta un mapeo SQLAlchemy Core/ORM completo de las tablas ERP de `3.- TABLAS_BD_ERP_COMPLETO.sql`. Esto impide una auditoría exhaustiva de modelos desde Python, dificulta la refactorización segura y reduce la visibilidad de constraints/índices multi-tenant a nivel de código.

---

## TAREA 2 — Auditoría Global de Endpoints FastAPI

### Patrones de Seguridad Multi-Tenant Observados

- **Dependencias de autenticación y contexto:**  
  - Uso sistemático de `get_current_active_user` y/o `get_current_user` en endpoints de módulos ERP, exponiendo `current_user.cliente_id` y metadatos de usuario.  
  - Tenant middleware y contexto (`TenantMiddleware`, `get_current_client_id`) en `main.py` garantizan que las conexiones de BD sean tenant-aware, con logging que incluye el ID de cliente en cada request.  
  - El módulo de autenticación (`app/modules/auth/presentation/endpoints.py`) implementa login multi-tenant con resolución de `cliente_id` vía contexto, body (`cliente_id` o `subdominio`) o SSO, y refuerza que el `target_cliente_id` provenga del contexto y no del usuario autenticado para BD dedicadas.

- **Uso de `cliente_id` y `empresa_id` en endpoints ERP:**  
  - En todos los módulos ERP revisados, los endpoints de listado (`GET ""`), detalle (`GET /{id}`), creación (`POST`), actualización (`PUT`) y operaciones de negocio:  
    - Obtienen `client_id` desde `current_user.cliente_id` o desde el middleware (`get_current_client_id`) en casos de branding/tenant.  
    - Reciben `empresa_id` como `Query(Optional[UUID])` o `Path[UUID]` según corresponda, nunca desde body como campo libre para override del tenant.  
    - Pasan siempre `client_id` y `empresa_id` a servicios de aplicación (p.ej. `list_productos_servicio(client_id=..., empresa_id=...)`, `create_asiento_contable(client_id, data)`).

- **Protección RBAC:**  
  - Se utiliza `require_permission("modulo.recurso.accion")` de forma consistente en los endpoints CRUD y de negocio, alineado con el catálogo de permisos central (`permiso` + `rol_permiso`).  
  - Los permisos utilizados en routers coinciden con los módulos y recursos declarados (`org.empresa.leer`, `inv.producto.crear`, `fin.asiento.actualizar`, etc.), reflejando la convención definida en los documentos RBAC.

- **Manejo de errores HTTP:**  
  - Uso sistemático de excepciones de dominio `NotFoundError` convertidas a `HTTPException` 404.  
  - Errores de negocio y de permisos se gestionan mediante RBAC (403) y validaciones en servicios, aunque parte de la validación 400/422 recae en Pydantic.  
  - En endpoints de autenticación y tenant management, se utilizan 400/401/403 apropiadamente para errores de credenciales, token y selección de cliente.

### Hallazgos y Riesgos Potenciales

- **Falta de verificación estática de filtros tenant en todas las consultas:**  
  - Aunque casi todos los endpoints envían `client_id=current_user.cliente_id` y `empresa_id`, la implementación real de los filtros se encuentra en servicios que construyen SQL manualmente; sin modelos ORM y sin una política centralizada (e.g. `QueryFilter` multi-tenant obligatorio), es posible que existan consultas puntuales sin filtro `cliente_id`/`empresa_id` o con joins que no restringen adecuadamente el tenant.  
  - No se detectan endpoints que expongan datos globales sin ningún filtro de tenant, pero no es trivial garantizar que todas las rutas y paths internos a servicios apliquen el filtro.

- **Validación de `empresa_id` dentro del cliente autenticado:**  
  - Muchos endpoints reciben `empresa_id` como parámetro libre (query/path) y lo pasan a los servicios junto con `client_id`, presumiblemente validando que la empresa pertenezca al cliente.  
  - Al no disponerse de modelos/servicios centralizados reutilizables de validación (`assert_empresa_belongs_to_cliente(client_id, empresa_id)` aplicados uniformemente), la auditoría no puede demostrar que dicha verificación se ejecuta en todos los flujos (especialmente en entidades detalle y enlaces entre módulos).

- **Endpoints de administración de tenant (superadmin):**  
  - Módulos `tenant` y `superadmin` exponen rutas donde `cliente_id` se pasa como parámetro (p.ej. `/conexiones/clientes/{cliente_id}`), lo cual es correcto para administración multi-tenant pero amplifica el impacto de un eventual fallo de RBAC.  
  - Es crítico que estas rutas estén estrictamente protegidas por permisos exclusivos de superadmin y no estén accesibles para usuarios normales de un cliente.

- **Cobertura CRUD por entidad:**  
  - Para la mayoría de entidades mencionadas en `MENU_NAVEGACION.md`, se observan al menos endpoints de listado y detalle; en muchos casos, también de creación y actualización.  
  - Hay entidades donde las operaciones de baja/eliminación son lógicas o se sustituyen por estados (ej. desactivar en lugar de borrar), lo cual es consistente con objetivos de auditoría; sin embargo, no siempre existe un endpoint explícito `DELETE` (esto es funcionalmente aceptable si está documentado).

### Conclusión TAREA 2

- **Aspectos positivos:**  
  - Patrón multi-tenant consistente en endpoints: `current_user.cliente_id` + `empresa_id` en query/path.  
  - Uso robusto de RBAC por permiso de negocio y conversión apropiada de errores a HTTP codes (404/403/400).  
  - No se observan endpoints ERP que operen explícitamente sin contexto de tenant.

- **Aspectos a mejorar:**  
  - Centralizar y hacer explícita la validación de que `empresa_id` pertenece al `cliente_id` del contexto en todos los servicios, idealmente con helpers reutilizables.  
  - Incorporar una capa ORM o al menos metadatos centralizados de tablas ERP para poder auditar estáticamente que todas las consultas incluyen filtros de `cliente_id`/`empresa_id`.

---

## TAREA 3 — Coherencia con Documentos Oficiales

### Cobertura de Entidades del `MENU_NAVEGACION.md`

- **Existencia de módulos y routers:**  
  - Los 27 módulos descritos en `MENU_NAVEGACION.md` están representados en el backend mediante paquetes `app/modules/<modulo>` con routers FastAPI (`presentation/endpoints*.py`) que corresponden a las opciones del menú (por ejemplo, `INV - Productos/Categorías/UdM/Almacenes/Stock/Movimientos/Inventario Físico`, `HCM - Empleados/Contratos/Conceptos/Planillas/Asistencia/Vacaciones/Préstamos`, etc.).  
  - No se han identificado módulos ERP adicionales no contemplados en el documento de navegación (los módulos de soporte como `auth`, `rbac`, `tenant`, `superadmin`, `menus`, `modulos`, etc. son parte de la infraestructura SaaS y no violan la regla de no crear módulos ERP extras).

- **Relaciones y flujos de negocio vs `MANUAL_USUARIO.md`:**  
  - Aunque el `MANUAL_USUARIO.md` actual está casi vacío en el repositorio, los comentarios en código y descripciones de endpoints reflejan flujos que coinciden con el menú funcional (por ejemplo, compras → órdenes → recepciones → inventario; ventas → pedidos → despachos → comprobantes; producción → BOM → rutas → OP → consumo de materiales).  
  - La estructura del script ERP (`3.- TABLAS_BD_ERP_COMPLETO.sql`) confirma que las relaciones entre tablas siguen estos flujos (ej. `org_centro_costo` usado por FIN, BDG, CST y MFG; `org_sucursal` relacionado con INV, POS, HCM; `fin_asiento_contable` con FKs a módulos origen).

- **Entidades sin respaldo en backend:**  
  - No se han detectado entidades funcionales documentadas en `MENU_NAVEGACION.md` que carezcan completamente de endpoints (`endpoints_*.py`) en backend.  
  - Algunas funciones avanzadas (p.ej. dashboards altamente configurables en BI, workflows muy complejos en WFL) se soportan mediante entidades genéricas (configuración JSON de reportes/flujos), no necesariamente mediante una entidad específica por cada opción de menú, lo cual es coherente con la arquitectura declarada.

- **Endpoints sin respaldo funcional en manual/navegación:**  
  - Los endpoints adicionales identificados pertenecen a:  
    - Infraestructura SaaS (auth, tenant, superadmin, RBAC, menus, modulos).  
    - Diagnóstico y debug controlado (`/debug-env`, `/debug-headers`, `/debug-detailed`, `/drivers`, `/health`, `/api/test`), que no forman parte de los módulos ERP y están claramente marcados como utilidades técnicas.  
  - No se han detectado endpoints ERP que implementen operaciones ajenas al alcance funcional descrito (no se añaden entidades “creativas” fuera del menú oficial).

### Conclusión TAREA 3

- **Coherencia general:** Alta. El backend cubre el 100 % de los módulos ERP declarados en `MENU_NAVEGACION.md` y respeta los límites funcionales descritos, sin introducir módulos ERP nuevos.  
- **Brecha documental:** La ausencia de un `MANUAL_USUARIO.md` detallado en el repositorio impide una trazabilidad fina de cada opción de pantalla a cada endpoint, pero la correlación entre nombres de routers, permisos y scripts SQL sugiere un alineamiento funcional sólido.

---

## TAREA 4 — Evaluación de Preparación para Producción SaaS

### Escalabilidad Multi-tenant y Alta Concurrencia

- **Puntos fuertes:**  
  - Arquitectura de BD central + BD dedicada está correctamente soportada por scripts y por el middleware de tenant, permitiendo separar cargas por cliente y soportar escenarios shared/dedicated.  
  - Índices adecuados en tablas centrales y ERP (por cliente, empresa, estado, fechas y campos de búsqueda) facilitan consultas eficientes bajo alta concurrencia.  
  - Módulo de rate limiting opcional y logging estructurado por tenant en `main.py` ayudan a controlar abuso y a diagnosticar problemas en entornos multi-tenant.

- **Limitaciones actuales:**  
  - La ausencia de modelos ORM para tablas ERP y la dependencia en SQL manual dificultan aplicar herramientas de análisis estático, migraciones automatizadas y refactorización segura a gran escala.  
  - No se observa una capa centralizada de “política de queries multi-tenant” que garantice que cualquier nueva consulta incluya obligatoriamente `cliente_id` y `empresa_id`, lo que podría generar regresiones en futuros cambios.  
  - La capa de caching/memoización para permisos y menús existe (`permission_cache`, `effective_permissions`, resolvers de menú), pero su impacto y consistencia bajo alta concurrencia debe validarse en pruebas de carga reales.

### Fuga de Datos y Aislamiento

- **Fortalezas:**  
  - Scripts ERP y centrales están diseñados con `cliente_id` y `empresa_id` obligatorios, con constraints de unicidad e índices escopados correctamente, reduciendo la probabilidad de fugas en nivel SQL.  
  - Endpoints utilizan siempre el contexto de usuario (`current_user.cliente_id`) y RBAC por permiso de negocio, minimizando la exposición accidental de datos de otros tenants.

- **Riesgos residuales:**  
  - Algunos endpoints de administración de tenant (superadmin/tenant) operan con `cliente_id` en path/params y dependen totalmente de RBAC; un fallo en la configuración de permisos podría permitir operaciones cruzadas entre clientes.  
  - Sin validación centralizada de pertenencia `empresa_id → cliente_id`, un bug en servicios podría permitir operar sobre empresas de otro cliente si se consigue conocer un UUID de empresa externo (aunque esto se ve mitigado por el diseño de endpoints y el contexto de usuario).

### Integridad Referencial y Auditoría

- **Integridad referencial:**  
  - A nivel de scripts SQL, las FKs están definidas de forma exhaustiva y coherente con el diseño funcional, tanto en la BD central como en la BD ERP.  
  - Sin embargo, al no existir migraciones automatizadas ni modelos ORM para ERP, el riesgo de drift entre código y esquema aumenta a largo plazo (p.ej. añadir columnas en SQL sin reflejarlas en servicios).

- **Auditoría empresarial:**  
  - Tablas de auditoría en central (`auth_audit_log`, `log_sincronizacion_usuario`) y en ERP (módulo AUD + logs específicos de módulos) proporcionan una base sólida para trazabilidad.  
  - El módulo AUD y los logs de autenticación permiten reconstruir “quién hizo qué y cuándo” a nivel técnico; la auditoría funcional detallada (por documento de negocio) depende de la correcta instrumentación de servicios.

---

## Problemas Críticos Multi-Tenant Identificados

- **1. Ausencia de modelos SQLAlchemy para tablas ERP de `3.- TABLAS_BD_ERP_COMPLETO.sql`.**  
  - Impide auditar y validar a nivel de código: presence de `cliente_id` / `empresa_id`, FKs, constraints, índices multi-tenant, relaciones jerárquicas (`parent_id`).  
  - Dificulta la detección temprana de errores de consultas que omiten filtros de tenant.

- **2. Validación de pertenencia `empresa_id` al `cliente_id` delegada a servicios sin helper central obligatorio.**  
  - Cada servicio implementa su propia lógica para validar que `empresa_id` pertenece al cliente del contexto; la ausencia de un helper/core de validación único abre la puerta a inconsistencias.  
  - Especialmente crítico en módulos de alto impacto (FIN, INV, SLS, HCM, MFG, MRP, POS).

- **3. Dependencia elevada en SQL manual para lógica de negocio compleja.**  
  - Aumenta la probabilidad de consultas que olviden filtrar por `cliente_id`/`empresa_id` en joins entre módulos.  
  - Hace más difícil realizar revisiones automáticas de seguridad y rendimiento en tiempo de desarrollo.

- **4. Endpoints de administración de tenant con `cliente_id` en path.**  
  - Aunque necesarios para superadmin, requieren una configuración de permisos impecable; cualquier error de RBAC podría exponer operaciones destructivas multi-tenant (conexiones, branding, activación de módulos, etc.).

---

## Inconsistencias Estructurales y Tablas que No Cumplen Aislamiento

- **BD central:**  
  - No se identifican tablas operativas vulnerables sin `cliente_id` cuando deberían tenerlo; la distinción entre tablas globales (catálogos de módulos, permisos) y tablas por tenant está clara y documentada.  
  - Tablas globales (`modulo`, `permiso`) están correctamente marcadas como globales y no violan el requisito de aislamiento.

- **BD ERP (según scripts):**  
  - Las tablas revisadas de ORG, INV, WMS, QMS, PUR, LOG, MFG, MRP, MPS, MNT, SLS, CRM, PRC, INV_BILL, POS, HCM, FIN, TAX, BDG, CST, PM, SVC, TKT, BI, DMS, WFL, AUD cumplen con incluir `cliente_id` y, cuando corresponde, `empresa_id`.  
  - No se han detectado cabeceras relevantes sin `cliente_id`; las excepciones (tablas técnicas o catálogos globales) están alineadas con el diseño arquitectónico.

- **Nivel de código:**  
  - La falta de modelos SQLAlchemy para ERP impide marcar tablas específicas como incumplidoras desde el código; cualquier tabla que en el futuro se añada/edite sólo en SQL podría introducir inconsistencias sin ser detectada por la base de código.

---

## Endpoints Inseguros (o de Riesgo Elevado)

- **Categoría 1 — Administración de Tenant/Superadmin:**  
  - Endpoints en módulos `tenant` y `superadmin` que operan con `cliente_id` explícito (gestión de conexiones, suspensión/activación de clientes, auditorías globales) son intrínsecamente sensibles.  
  - No se observan vulnerabilidades evidentes en el código revisado, pero el impacto de una mala configuración de permisos o de un bypass de RBAC sería alto.

- **Categoría 2 — Reportes y BI/DMS/WFL:**  
  - Endpoints que permiten definir consultas o workflows mediante configuración JSON (BI, WFL) podrían, si se implementa ejecución SQL dinámica, convertirse en vectores de fuga de datos entre tenants si no se imponen filtros de `cliente_id` y `empresa_id` a nivel del motor de ejecución.  
  - Actualmente no se evidencian ejecuciones SQL arbitrarias desde el cliente, pero el riesgo conceptual exige una política estricta.

- **Categoría 3 — Enlaces entre módulos (LOG, MFG, SVC, PM):**  
  - Endpoints que relacionan entidades entre módulos (p.ej. despachos ↔ guías ↔ pedidos; OP ↔ inventario; servicios ↔ stock en terceros) dependen de que todas las consultas intermodulares incluyan filtros por `cliente_id` y `empresa_id`; sin un mecanismo centralizado de verificación, estos puntos deben considerarse de riesgo y sujetos a pruebas de integración específicas.

---

## Índices Faltantes (a nivel de código)

- **BD central:**  
  - Los índices definidos en scripts están representados en los modelos Core; no se identifican índices “faltantes” en código respecto al diseño relacional.

- **BD ERP:**  
  - Varios índices definidos en `3.- TABLAS_BD_ERP_COMPLETO.sql` (p.ej. sobre campos de búsqueda como códigos de documentos, RUC de clientes/proveedores, fechas de operación) no tienen un reflejo directo en modelos SQLAlchemy (porque no existen como tal).  
  - Esto no significa que falten en la BD, sino que:  
    - No están accesibles desde código para tooling/pre-cálculos.  
    - Es más difícil detectar consultas que no aprovechen dichos índices (p.ej. filtros por campos no indexados añadidos posteriormente).

---

## Recomendaciones Estructurales Globales

1. **Mapear todas las tablas ERP de `3.- TABLAS_BD_ERP_COMPLETO.sql` a SQLAlchemy Core u ORM.**  
   - Crear un módulo de tablas ERP similar a `tables.py`/`tables_modulos.py` por dominio (ORG, INV, etc.), respetando nombres, tipos, FKs, índices y constraints del script oficial.  
   - Esto permitirá auditar y refactorizar queries con mayor seguridad y habilitar herramientas como linters SQLAlchemy.

2. **Introducir una capa de política de queries multi-tenant obligatoria.**  
   - Implementar helpers o builders que requieran explícitamente `cliente_id` y, cuando aplique, `empresa_id` para cualquier consulta a tablas ERP.  
   - Prohibir (a nivel de convenciones y revisiones) el uso de SQL manual sin pasar por estos helpers multi-tenant.

3. **Centralizar la validación de pertenencia `empresa_id → cliente_id`.**  
   - Proveer funciones reutilizables que, dado un `client_id` y `empresa_id`, verifiquen sistemáticamente que la empresa pertenece al cliente, y que puedan ser reutilizadas por todos los módulos.  
   - Asegurar que cualquier endpoint que reciba `empresa_id` invoque este helper al inicio de la operación.

4. **Formalizar una política de naming conventions y FKs en código.**  
   - Aunque los scripts ya poseen nombres de constraints estandarizados, reflejar estas convenciones en modelos SQLAlchemy favorece el mantenimiento.  
   - Documentar explícitamente prefijos y sufijos para FKs, índices y constraints únicos multi-tenant.

5. **Fortalecer la observabilidad multi-tenant.**  
   - Extender el logging actual (que ya incluye `client_id`) con metadatos clave (`empresa_id`, módulo, recurso) para facilitar auditorías en tiempo de ejecución.  
   - Agregar dashboards de monitoreo que puedan detectar patrones anómalos por cliente/empresa.

6. **Pruebas de carga y de aislamiento específicas por módulo.**  
   - Diseñar suites de pruebas de estrés que verifiquen que, bajo alta concurrencia y múltiples tenants, no se produce contaminación de sesiones ni fugas de datos entre clientes.  
   - Incluir pruebas automatizadas que verifiquen que no se puede acceder a entidades (`empresa`, `cliente`, `documentos`) cruzando boundaries de tenant/empresa.

---

## Lista Consolidada de Correcciones Necesarias (Sin aplicar aún)

1. **Crear modelos SQLAlchemy Core para todas las tablas ERP:**
   - ORG: `org_empresa`, `org_centro_costo`, `org_sucursal`, `org_departamento`, `org_cargo`, etc.  
   - INV/WMS/QMS/PUR/LOG/MFG/MRP/MPS/MNT/SLS/CRM/PRC/INV_BILL/POS/HCM/FIN/TAX/BDG/CST/PM/SVC/TKT/BI/DMS/WFL/AUD: todas las tablas definidas en `3.- TABLAS_BD_ERP_COMPLETO.sql`, respetando tipos, FKs, índices y constraints multi-tenant.

2. **Introducir helpers de queries multi-tenant en la capa de infraestructura de datos:**
   - Builder de filtros estándar por `cliente_id` + `empresa_id`.  
   - Utilidades que impidan construir consultas sin estos filtros para tablas marcadas como ERP multi-tenant.

3. **Definir y aplicar `assert_empresa_belongs_to_cliente(client_id, empresa_id)` en todos los servicios que reciben `empresa_id`.**

4. **Revisar y endurecer endpoints de administración de tenant y superadmin:**
   - Auditar permisos asociados a rutas con `cliente_id` en path.  
   - Añadir logs de alto detalle y, opcionalmente, pasos de confirmación adicionales para operaciones destructivas/másivas.

5. **Agregar pruebas automatizadas de regresión multi-tenant:**
   - Tests que creen datos en múltiples tenants y empresas y verifiquen que ningún endpoint o servicio devuelve datos de otro tenant/empresa.  
   - Tests específicos de joins complejos entre módulos (por ejemplo, FIN + INV + SLS, MFG + INV + ORG).

---

## Evaluación Final: ¿Apto para Producción SaaS?

- **Veredicto:** **No completamente apto** para un despliegue SaaS masivo multi-tenant **sin una fase adicional de endurecimiento técnico**, pero sí en un estado avanzado cercano a producción.  
- **Justificación:**  
  - La arquitectura de base de datos y los scripts SQL están sólidamente diseñados para multi-tenant con `cliente_id` y `empresa_id`, y los endpoints siguen patrones correctos de aislamiento y RBAC.  
  - Sin embargo, la ausencia de modelos SQLAlchemy para las tablas ERP, la dependencia en SQL manual y la falta de una política centralizada de queries multi-tenant impiden garantizar, de forma estática y automatizable, que todas las rutas y servicios cumplen el aislamiento y la integridad referencial al 100 %.  
  - Con las correcciones propuestas (en especial: mapeo ORM completo + helpers multi-tenant + validaciones centralizadas de `empresa_id`), el backend podría alcanzar un nivel de madurez adecuado para producción SaaS a gran escala.

---

## Porcentaje Estimado de Cumplimiento Técnico Global del ERP

- **Cumplimiento técnico global (modelos + endpoints + coherencia documental + multi-tenant):**  
  - **Aproximadamente 80 %**, considerando:  
    - Alta alineación de scripts SQL y diseño multi-tenant.  
    - Cobertura amplia y segura de endpoints ERP por módulo.  
    - Ausencia de modelos SQLAlchemy para ERP y falta de verificación estática de todas las consultas multi-tenant como principal brecha pendiente.

