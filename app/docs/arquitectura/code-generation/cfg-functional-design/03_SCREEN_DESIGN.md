# Diseño de pantallas e información

**Paquete:** `cfg-functional-design`  
**Fecha:** 2026-07-17  
**Nota:** Diseño funcional de UI — no mockups gráficos ni componentes React.

---

## 1. P1 — Listado de secuencias (hub)

### Propósito

Descubrir secuencias del tenant y entrar al detalle.

### Elementos

| Zona | Contenido |
|------|-----------|
| Título | Secuencias de código |
| Subtítulo | “Configuración del Motor de códigos de su organización” |
| Filtros | Módulo, scope_type, empresa, activo/inactivo, buscar (key o prefijo) |
| Tabla | Filas de secuencias |
| Paginación | Contrato ERP v1 (`page` / `limit`) |
| Acciones fila | Ver detalle; Preview rápido (opcional MVP+) |

### Columnas de tabla (MVP)

| Columna | Fuente | Notas |
|---------|--------|-------|
| Módulo | Catalog enrich `modulo_codigo` | ORG / INV / … |
| Secuencia | `sequence_key` | Código técnico legible |
| Entidad | Catalog `entity_table` / label | Nombre amigable si existe |
| Scope | `scope_type` | Badge |
| Empresa / Almacén / PV | ids o nombres si enrich futuro | MVP: UUID o “—” si TENANT |
| Prefijo | `prefijo` | |
| Padding | `longitud_numero` | |
| Último Nº | `ultimo_numero` | Read-only |
| Política | `generation_policy` | Badge |
| Estado | `es_activo` | Activa / Inactiva |
| Acciones | Ver | |

### Orden por defecto sugerido

`modulo_codigo` ASC, `sequence_key` ASC (o tie-breaker `secuencia_id`).

---

## 2. P2 — Detalle de secuencia

### Secciones

#### A) Identidad (solo lectura)

| Campo mostrado | Label UX |
|----------------|----------|
| `sequence_key` | Clave de secuencia |
| `modulo_codigo` | Módulo |
| Entidad / tabla destino | Entidad |
| Columna de código | Campo de código |
| `scope_type` | Tipo de ámbito |
| `empresa_id` / almacén / PV | Ámbito (si aplica) |
| `secuencia_id` | ID (secundario, colapsable) |

#### B) Política y catálogo (solo lectura)

| Campo | Label UX |
|-------|----------|
| `generation_policy` | Política de generación |
| `catalog_policy` (si drift) | Política en catálogo |
| Familia / allow_manual (enrich) | Comportamiento |

Banner si `generation_policy ≠ catalog_policy` (MVP: mostrar ambos; alerta fuerte en v1.2).

#### C) Formato y contador

| Campo | Editable MVP | Label UX |
|-------|--------------|----------|
| `prefijo` | Sí* | Prefijo |
| `separador` | Sí* | Separador |
| `longitud_numero` | Sí* | Dígitos del número |
| `numero_inicial` | Sí* | Número inicial |
| `ultimo_numero` | **No** | Último número usado |
| Ejemplo formato | Derivado | “Ejemplo: PRE-0001” (estático con valores actuales) |

\*Excepto `org_empresa` (bloqueado).

#### D) Estado y auditoría

| Campo | Editable | Label |
|-------|----------|-------|
| `es_activo` | Vía acciones | Estado |
| `fecha_creacion` | No | Creada |
| `fecha_actualizacion` | No | Última actualización |
| `usuario_actualizacion_id` | No | Actualizado por (nombre si enrich) |

#### E) Acciones

| Acción | Permiso | MVP |
|--------|---------|-----|
| Editar configuración | actualizar | Sí |
| Previsualizar | consultar | Sí |
| Activar | actualizar | Sí (si inactiva) |
| Desactivar | actualizar | Sí (si activa; no org_empresa) |
| Alinear contador | mantener | No |
| Ver diagnóstico | diagnosticar | No |

---

## 3. Información mostrada por cada secuencia (contrato funcional Read)

### Visible y útil

- Identidad de negocio (módulo, key, entidad, scope)
- Formato (prefijo, separador, padding, piso)
- Contador (`ultimo_numero`)
- Política de generación
- Estado activo
- Timestamps de auditoría
- Metadatos de catálogo (defaults, supports_preview)

### Visible pero secundario / avanzado

- `secuencia_id`
- `scope_fingerprint` (solo panel “técnico” colapsado)
- UUIDs de empresa/almacén/PV si no hay nombre

### Campos nunca visibles en UI (MVP)

| Campo / dato | Motivo |
|--------------|--------|
| Internals del Motor (locks, SQL) | No aportan al Admin |
| Definición completa SequenceCatalog dump | Exceso; solo enrich necesario |
| Store FISCAL / series comprobante | Fuera de producto cfg v1 |
| Secretos / connection strings | N/A |
| `cliente_id` como campo editable | Implícito en sesión; no mostrar como input (opcional display técnico colapsado) |

---

## 4. Campos editables vs solo lectura vs nunca expuestos

### Editables (clase B) — MVP

| Campo | Reglas UX |
|-------|-----------|
| `prefijo` | Mayúsculas normalizadas; max 10 |
| `separador` | Vacío o `-` (u otros permitidos por validación) |
| `longitud_numero` | Entero ≥ 1; validar anti-agotamiento |
| `numero_inicial` | Entero ≥ 1; no superar lógica de colisión con contador |
| `es_activo` | Solo vía Activar/Desactivar (no checkbox silencioso sin confirmación en desactivar) |

### Solo lectura (clases A/C/D + enrich)

| Campo |
|-------|
| `secuencia_id`, `cliente_id`, `sequence_key`, `scope_type`, `scope_fingerprint` |
| `empresa_id`, `almacen_id`, `punto_venta_id` |
| `generation_policy` |
| `ultimo_numero` |
| `fecha_creacion`, `fecha_actualizacion`, `usuario_actualizacion_id` |
| Metadatos catálogo |

### Nunca editables vía producto (aunque existan en BD)

| Campo | Nota |
|-------|------|
| `ultimo_numero` | Solo Motor / align post-MVP |
| Identidad / scope | Solo bootstrap/lazy |
| `generation_policy` | Solo gobernanza Catalog |

---

## 5. Organización visual recomendada (sin mockup)

1. **Una composición por pantalla:** listado = hub; detalle = ficha única.  
2. **Sin cards decorativas** innecesarias: secciones con tipografía y jerarquía.  
3. Badges solo para policy y estado (información, no adorno).  
4. Preview y desactivar en **modal de confirmación/resultado**, no páginas nuevas.  
5. Evitar dashboard de métricas en el hub MVP (reservar a Diagnóstico v1.2).

---

## 6. Empty / locked states

| Estado | UI |
|--------|----|
| Secuencia locked (`org_empresa`) | Badge “Protegida”; formulario no editable |
| Inactiva | Banner ámbar en detalle |
| Drift policy (si detectable) | Badge discreto MVP; panel v1.2 |
| Lazy no materializada | No aparece en listado hasta existir fila (MVP); v1.2 puede listar “pendientes” |
