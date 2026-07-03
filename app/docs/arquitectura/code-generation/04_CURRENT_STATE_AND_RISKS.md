# F15 — Estado actual, restricciones y riesgos

**Fase:** F15 — Auditoría arquitectónica  
**Fecha:** 2026-07-02  
**Método:** Análisis de V010 + ORM (`tables.py`) + servicios implementados (ORG, INV, PUR, SLS, tenant onboarding).

---

## 1. Estado actual de generación de códigos

### 1.1 Resumen por modo

| Modo | Descripción | Entidades afectadas (runtime) |
|------|-------------|-------------------------------|
| **Manual (API obliga al cliente)** | El usuario/envía el código en el payload Create | ORG (todos los maestros), INV movimiento (`numero_movimiento` required), INV producto (`codigo_sku`), almacén, categoría, UM, inventario físico |
| **Manual con validación pre-insert** | Service verifica duplicado antes de INSERT | `org_empresa`, `org_sucursal`, `org_centro_costo`, `org_departamento`, `org_cargo`, `inv_producto` |
| **Manual sin pre-check** | Confía en UNIQUE SQL (409 si duplicado) | `inv_almacen`, `inv_categoria_producto`, `inv_unidad_medida`, resto de módulos sin servicio |
| **Bootstrap fijo** | Constante hardcodeada en provisioning | `org_empresa` → `EMP001` (`minimal_erp_tenant_bootstrap_service`, onboarding) |
| **Automático ad hoc (timestamp)** | `strftime` + microsegundos, sin secuencia | `inv_estorno_proceso.gen_numero_movimiento_estorno()`, `inventario_fisico_aprobacion_service._gen_numero_movimiento()` |
| **Derivado de otro documento** | Concatenación de strings | PUR recepción → `PUR-{numero_recepcion}`; SLS cotización → pedido `PED-{numero_cotizacion}` |
| **Seed sin consumo** | Inserta filas en `cfg_codigo_secuencia` | Onboarding (`SECUENCIAS_CODIGO` × 9) y dedicated seed |
| **Inexistente** | Sin servicio ni lógica | ~90% de tablas V010 con códigos |

### 1.2 Infraestructura existente pero no integrada

| Componente | Ubicación | Estado |
|------------|-----------|--------|
| Tabla `cfg_codigo_secuencia` | V010 DDL | ✅ Existe |
| `CfgCodigoSecuenciaTable` | `app/infrastructure/database/tables.py` | ✅ ORM |
| `CfgCodigoSecuenciaRepository` | `app/infrastructure/database/repositories/` | ✅ CRUD + `insert_secuencia`, `update_ultimo_numero` |
| Consumo en servicios ERP | — | ❌ **Ningún servicio llama `update_ultimo_numero` ni `get_by_entidad` para generar** |
| API de administración de secuencias | — | ❌ No existe |

**Entidades en `SECUENCIAS_CODIGO` (onboarding):**

| entidad | prefijo | longitud | separador | ultimo_inicial |
|---------|---------|----------|-----------|----------------|
| org_empresa | EMP | 3 | — | 0 |
| org_sucursal | SUC | 3 | — | 0 |
| org_departamento | DEP | 3 | — | 0 |
| org_cargo | CAR | 3 | — | 0 |
| org_centro_costo | CC | 3 | — | 0 |
| inv_almacen | ALM | 3 | — | 0 |
| inv_producto | P | 5 | — | 0 |
| inv_categoria | CAT | 3 | — | 0 |
| inv_movimiento | MOV | 6 | — | 0 |

> Nota: `inv_categoria` en seed no coincide con nombre de tabla `inv_categoria_producto` — inconsistencia de clave `entidad`.

---

## 2. Inconsistencias entre módulos

### 2.1 Validación de unicidad

| Módulo | Pre-check SELECT | Catch SQL UNIQUE | Normalización (`normalize_upper`) |
|--------|------------------|------------------|-----------------------------------|
| ORG maestros | ✅ | Implícito | ✅ schemas |
| INV producto | ✅ SKU | Implícito | ✅ schemas |
| INV almacén/categoría/UM | ❌ | Solo SQL | Parcial en schemas |
| INV movimiento | ❌ | Solo SQL | Campo required en API |

### 2.2 Estrategias de numeración documental

| Flujo | Estrategia | Riesgo |
|-------|------------|--------|
| Movimiento INV create | Cliente provee `numero_movimiento` | Colisiones, formatos libres |
| Estorno INV | `INV-EST-{yymmdd}-{micro}` | Colisión baja pero no secuencial; no auditable como correlativo |
| Ajuste inv. físico | `INV-AJUS-{yymmdd}-{micro}` | Idem |
| Recepción PUR → movimiento | `PUR-{numero_recepcion}` | Depende de número manual de recepción; trunca a 20 chars |
| Cotización → pedido SLS | `PED-{numero_cotizacion}` | Acoplamiento; longitud compuesta puede exceder límites |

### 2.3 Desalineación seed vs. UNIQUE

Ver `03_SEQUENCE_SCOPE.md` §4: 8 de 9 secuencias seed usan `empresa_id=NULL` pero las tablas exigen unicidad por empresa.

### 2.4 Convención de nombres `entidad` en cfg

- Seed usa `inv_categoria`; tabla real `inv_categoria_producto`.
- Sin catálogo oficial de claves `entidad` en DDL.

---

## 3. Restricciones actuales (BD + API)

### 3.1 Base de datos

| Restricción | Cobertura | Observación |
|-------------|-----------|-------------|
| UNIQUE compuesto | Alta en maestros y documentos | Garantiza integridad **si** se inserta |
| Índices de búsqueda | Parcial (`codigo_barra`, `numero_completo`, documentos terceros) | No todos los códigos tienen índice dedicado |
| FK scope | `cliente_id` + `empresa_id` en mayoría | Coherente con multi-tenant |
| Longitud fija NVARCHAR | 20 chars estándar | Truncamiento silencioso posible en derivados (`[:20]`) |
| `cfg_codigo_secuencia.prefijo` | Máx 5 chars | Limita prefijos como `INV-AJUS` (8 chars) |

### 3.2 Capa de presentación (schemas)

- ORG e INV aplican `normalize_upper` / `normalize_strip` en Create/Update (conforme estándar V4).
- `numero_movimiento` es **obligatorio** en `MovimientoCreate` — API no permite omisión para autogenerar.
- Longitudes validadas con `max_length` alineado a BD en módulos implementados.

### 3.3 Repositorio de secuencias

- `insert_secuencia` es idempotente (no duplica por entidad).
- `update_ultimo_numero` existe pero **sin caller** en application layer.
- Conexión: `DatabaseConnection.ADMIN` con `client_id` — compatible con routing híbrido si el tenant store contiene la tabla.

---

## 4. Riesgos funcionales

### 4.1 Riesgos P0 (críticos)

| ID | Riesgo | Impacto |
|----|--------|---------|
| R-P0-01 | **Códigos libres en documentos** (`numero_movimiento`, futuros OC/pedidos) | Duplicados, saltos, fraude, imposibilidad de auditoría correlativa |
| R-P0-02 | **Motor configurado pero no usado** | Falsa sensación de control; `cfg_codigo_secuencia` desincronizada de la realidad |
| R-P0-03 | **Scope incorrecto en seed** (secuencia tenant vs. empresa) | Si se activara el motor sin corrección, colisiones multiempresa o números “saltados” |
| R-P0-04 | **Numeración fiscal sin integración** (`invbill_serie_comprobante.numero_actual`) | Riesgo legal SUNAT: huecos, duplicados, series agotadas |

### 4.2 Riesgos P1 (altos)

| ID | Riesgo | Impacto |
|----|--------|---------|
| R-P1-01 | **Formatos heterogéneos** (timestamp vs. prefijo vs. manual) | Búsqueda, reporting e integraciones EDI/API frágiles |
| R-P1-02 | **Derivación por concatenación** (`PUR-`, `PED-`) | Dependencia de numeración upstream; overflow NVARCHAR(20) |
| R-P1-03 | **Homónimos semánticos** (`codigo_proveedor` maestro vs. línea) | Errores de integración con proveedores |
| R-P1-04 | **Sin política para `codigo_sku` vs. `codigo_interno`** | Duplicidad de identificadores de producto |
| R-P1-05 | **WMS scope por almacén no modelado en cfg** | Imposible secuencia correcta para tareas/ubicaciones sin extensión |

### 4.3 Riesgos P2 (medios)

| ID | Riesgo | Impacto |
|----|--------|---------|
| R-P2-01 | Catálogos geo sin UNIQUE en V010 | Duplicados en departamento/provincia/distrito si se cargan mal |
| R-P2-02 | `codigo_parametro` libre | Inconsistencia en configuración entre empresas |
| R-P2-03 | Campos opcionales (`dms_documento.codigo_documento`) | Documentos sin identificador humano |
| R-P2-04 | Multi-tenant `cliente.codigo_cliente` manual | Colisiones solo a nivel plataforma (mitigado por UNIQUE global) |

---

## 5. Problemas de búsqueda e integración

1. **Listados `buscar`:** módulos ORG/INV buscan por código en SQL ILIKE — formatos libres degradan relevancia.
2. **Integración PUR→INV:** `documento_referencia_numero` recibe truncamiento; pérdida de trazabilidad si el origen cambia de formato.
3. **Facturación electrónica:** `numero_completo` computed depende de `serie`/`numero` con longitudes fijas distintas al resto del ERP (10 vs. 20).
4. **Dedicated DB:** secuencias deben vivir en el mismo store que ERP; el repositorio ya acepta sesión de onboarding transaccional, pero servicios ERP no participan.

---

## 6. Verificación de uso real (muestra representativa)

| Servicio | Archivo | Comportamiento código |
|----------|---------|----------------------|
| `create_empresa_servicio` | `org/.../empresa_service.py` | Manual + duplicate check |
| `create_sucursal_servicio` | `org/.../sucursal_service.py` | Manual + duplicate check |
| `create_producto_servicio` | `inv/.../producto_service.py` | Manual SKU + duplicate check |
| `create_movimiento_servicio` | `inv/.../movimiento_service.py` | Manual `numero_movimiento` del payload |
| `gen_numero_movimiento_estorno` | `inv/.../inv_estorno_proceso.py` | Auto timestamp |
| `_insertar_secuencias_codigo` | `tenant/.../cliente_onboarding_service.py` | Solo seed |
| `ClienteService._validar_codigo_cliente` | `tenant/.../cliente_service.py` | Manual plataforma |

---

## 7. Conclusiones de la auditoría de estado

1. El ERP **no tiene motor de generación operativo**; solo infraestructura dormida y seeds.
2. La política de facto es **código manual** con validación desigual entre módulos.
3. Los únicos automáticos son **workarounds locales** (timestamp), incompatibles con un estándar corporativo.
4. Las restricciones BD son sólidas para integridad **reactiva** (UNIQUE), pero no **proactivas** (formato, secuencia, scope).
5. La activación del motor requiere Fase 2: servicio transversal, ajuste de contratos API (código opcional en create), y corrección de scope en cfg.

---

*Arquitectura objetivo: `05_PROPOSED_ARCHITECTURE.md`.*
