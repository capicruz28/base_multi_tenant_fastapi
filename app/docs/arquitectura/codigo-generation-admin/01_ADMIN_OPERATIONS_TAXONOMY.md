# Taxonomía de operaciones administrativas

**Referencia:** Auditoría módulo admin Motor de Códigos  
**Tabla:** `cfg_codigo_secuencia` (61 secuencias CFG; fiscal excluido)

---

## 1. Operaciones de configuración

Personalizan el **formato futuro** de códigos sin reescribir históricos (BR-P-01).

| ID | Operación | Descripción | Evidencia normativa |
|----|-----------|-------------|---------------------|
| CFG-01 | **Listar secuencias** | Por tenant; filtros scope, empresa, activo, sequence_key | `CfgCodigoSecuenciaRepository.get_by_cliente`; IDX `cliente_id+es_activo` |
| CFG-02 | **Obtener detalle** | Fila cfg + metadatos catálogo (entidad, módulo, policy nominal) | SC-GOV-01 |
| CFG-03 | **Actualizar prefijo** | `prefijo` NVARCHAR(10) | BR-CUST, `02_PREFIX_STANDARD` PFX-* |
| CFG-04 | **Actualizar separador** | `separador` (∅ o `-` típico) | BS-CFG-01 |
| CFG-05 | **Actualizar padding** | `longitud_numero` | BR-CUST-01 anti-colisión |
| CFG-06 | **Actualizar numero_inicial** | Solo si no viola códigos existentes | BR-S-01, BR-CUST-01 |
| CFG-07 | **Activar secuencia** | `es_activo = 1` | BR-CUST-02 inverso |
| CFG-08 | **Desactivar secuencia** | `es_activo = 0` — bloquea nuevos allocate | BR-CUST-02, TD-M-04 |

**Restricciones transversales:**

- Validar unicidad visual futura (prefijo+pad no agota espacio columna destino).
- Cambios auditados (`usuario_actualizacion_id`, `fecha_actualizacion`).
- **No** afectan códigos ya persistidos en tablas de negocio.

---

## 2. Operaciones operativas

Consultas que **informan** sin alterar estado del contador (salvo allocate runtime en otros módulos).

| ID | Operación | Descripción | Consumo contador |
|----|-----------|-------------|------------------|
| OPS-01 | **Preview próximo código** | Estimación del siguiente auto | **No** — `PreviewReader` / Gateway.preview |
| OPS-02 | **Validar código manual** | Pre-check formato antes de alta ERP | **No** — Gateway.validate_manual |
| OPS-03 | **Consultar estado contador** | Lectura `ultimo_numero`, `numero_inicial` | Solo lectura |

**Cuándo es útil preview (OPS-01):**

- Pantallas de alta maestro AUTO_DEFAULT (UX: «próximo código estimado»).
- Validación implantación post-cambio de prefijo.
- **Desaconsejado** como reserva de número (BR-S-01 espíritu; no hay lock).

---

## 3. Operaciones de mantenimiento

Intervenciones **excepcionales**, rol elevado, típicamente post-importación o corrección de drift.

| ID | Operación | Descripción | Mecanismo autorizado |
|----|-----------|-------------|---------------------|
| MNT-01 | **Alinear contador (align)** | Elevar `ultimo_numero` al high-water de códigos existentes | `CodigoGeneracionGateway.align_counter` |
| MNT-02 | **Validar configuración pre-cambio** | Simular impacto de PATCH antes de aplicar | Servicio admin (sin persistir) |
| MNT-03 | **Reparación post-importación lote** | Align masivo al cierre de lote migración | BR-M-41, TX-05 |
| MNT-04 | **Sincronizar lazy row** | Forzar creación fila cfg para scope existente sin fila | Delegar `ensure_row` vía preview/allocate dry-run — **no** INSERT admin directo sin catálogo |

**Prohibido en mantenimiento:**

| ID | Operación prohibida | Motivo |
|----|---------------------|--------|
| MNT-X1 | Editar `ultimo_numero` vía PATCH | Bypass parser/validación; riesgo colisión |
| MNT-X2 | «Reiniciar a 0» arbitrario | BR-S-02; solo excepcional con validación MAX negocio |
| MNT-X3 | DELETE físico de fila cfg | Soft-disable únicamente; historial contador |

---

## 4. Operaciones de diagnóstico

Solo lectura; pueden cruzar cfg con catálogo y datos de negocio (aggregates).

| ID | Operación | Descripción |
|----|-----------|-------------|
| DGN-01 | **Drift cfg vs catálogo** | `generation_policy`, prefijo default, scope_type incoherentes |
| DGN-02 | **Secuencias lazy pendientes** | Entidades scope ALMACEN/PV sin fila cfg |
| DGN-03 | **Agotamiento correlativo** | `ultimo_numero` cerca de `10^padding - 1` |
| DGN-04 | **Contador vs MAX negocio** | MAX parte numérica parseable en tabla destino > `ultimo_numero` |
| DGN-05 | **Secuencia inactiva con allocate reciente** | Detección anomalía operativa |
| DGN-06 | **Salud org_empresa TENANT** | Verificar coherencia post-bootstrap EMP001 (BR-BOOT-04) |

**Historial futuro (Fase F):**

| ID | Operación | Notas |
|----|-----------|-------|
| DGN-07 | **Historial cambios admin** | Requiere tabla audit o eventos; **no existe hoy** en cfg |

---

## 5. Matriz operación → rol RBAC (resumen)

| Clase | Permiso base |
|-------|--------------|
| Configuración lectura | `cfg.secuencias.consultar` |
| Configuración escritura | `cfg.secuencias.actualizar` |
| Operativas | `cfg.secuencias.consultar` (preview incluido) |
| Mantenimiento | `cfg.secuencias.mantener` |
| Diagnóstico | `cfg.secuencias.diagnosticar` |

Detalle en [`06_SECURITY_RBAC_AND_FRONTEND.md`](06_SECURITY_RBAC_AND_FRONTEND.md).

---

## 6. Operaciones fuera del módulo admin

Permanecen en **runtime ERP** (módulos ORG, INV, …):

| Operación | Dueño |
|-----------|-------|
| `allocate` en create documento/maestro | Servicios ERP vía `OrgCodigoGenerationService` / equivalentes |
| Seed onboarding | Bootstrap V2 / TBO |
| Lazy `ensure_row` en primer allocate | Motor (`AllocationCoordinator`) |
| Fiscal serie/número | `FiscalSeriesStore` — **módulo admin fiscal separado** (futuro) |

---

*Columnas y clasificación: [`02_CFG_COLUMN_REFERENCE.md`](02_CFG_COLUMN_REFERENCE.md)*
