CAXIS ERP — PROMPT MAESTRO v2
==============================

# CONTEXTO

Sistema SaaS ERP multi-tenant.
Stack: FastAPI + SQL Server.
El sistema ya tiene: autenticación JWT, RBAC, arquitectura modular.

Módulo objetivo: [MODULO] — [CODIGO]

---

# REGLAS ABSOLUTAS (leer primero, respetar siempre)

❌ NO modificar tablas ni estructura de BD
❌ NO eliminar código existente
❌ NO romper endpoints actuales ni cambiar sus contratos
❌ NO asumir campos que no existan en la BD
✅ Reutilizar patrones de otros módulos ya implementados
✅ Respetar multi-tenant: validar cliente_id y empresa_id siempre
✅ Respetar RBAC con patrón: [modulo].[recurso].[accion]

---

# FASE 1 — LECTURA Y COMPRENSIÓN (NO escribir código aún)

## Paso 1.1 — Leer la BD del módulo

Busca en el archivo SQL adjunto ÚNICAMENTE las tablas
que contengan el prefijo [CODIGO]_.

Para cada tabla encontrada, indica:
- nombre exacto de la tabla
- tipo: maestro / transaccional / derivada
- campos principales (nombre + tipo de dato)
- claves foráneas hacia otras tablas
- si tiene campo es_activo, cliente_id, empresa_id

⚠ NO leas el archivo completo. Filtra solo las tablas del módulo.

## Paso 1.2 — Identificar patrón arquitectónico del proyecto

Busca en el proyecto la estructura de carpetas y archivos
de cualquier módulo existente para identificar:
- estructura de carpetas (presentation, application, domain, infrastructure)
- nombres de archivos convencionales usados
- cómo se define un router (APIRouter, prefijos, tags)
- cómo se valida tenant (cliente_id, empresa_id)
- cómo se aplica RBAC (require_permission, patrón del permiso)

⚠ NO uses la lógica ni los endpoints existentes como referencia.
⚠ Solo extrae la estructura y los patrones técnicos, NO el contenido funcional.
El contenido funcional lo define el prompt maestro y la BD, no el código actual.

## Paso 1.3 — Checkpoint obligatorio

Antes de continuar, responde estas preguntas:
1. ¿Cuántas tablas encontraste para el módulo [CODIGO]?
2. ¿Qué tipo de módulo es? (maestro/transaccional/analítico)
3. ¿Qué módulo usarás como referencia de estructura técnica 
   (carpetas, archivos, patrones de router/service/tenant/RBAC)?
   Nota: se usa solo para estructura, no como referencia funcional.
4. ¿Hay tablas derivadas que NO deben tener CRUD?

⛔ DETENTE AQUÍ. Espera confirmación antes de continuar.

---

# FASE 2 — AUDITORÍA (NO escribir código aún)

Con base en lo detectado en Fase 1:

## Paso 2.1 — Implementación actual

Busca en el proyecto los archivos del módulo [CODIGO]:
- routers
- services
- repositories
- schemas

Para cada endpoint existente indica:
| Ruta | Método | Entidad | Tiene tenant? | Tiene RBAC? |

## Paso 2.2 — Brechas funcionales

Para cada tabla del módulo, verifica si existe el patrón correcto.

Si es MAESTRO, debe tener: crear, listar, detalle, actualizar,
activar/desactivar. Marca lo que falta.

Si es TRANSACCIONAL, debe tener: crear (borrador), actualizar
(solo en borrador), aprobar, procesar, anular, listar, detalle.
Marca lo que falta.

Si es DERIVADA/ANALÍTICA: solo debe tener lectura.
Si tiene escritura, marca como ⚠ incorrecto.

## Paso 2.3 — Campos faltantes en schemas

Para cada endpoint existente, compara los campos del schema
contra los campos reales de la tabla en la BD.
Lista los campos que existen en la BD pero no están en el schema.

## Paso 2.4 — Reporte de auditoría

Genera el archivo:
app/docs/modulos/AUDITORIA_[CODIGO].md

Con esta estructura:
- Tablas detectadas y su tipo
- Endpoints existentes
- Endpoints faltantes (con ruta sugerida y método)
- Campos faltantes en schemas
- Problemas de tenant o RBAC
- Código marcado como obsoleto o incorrecto (NO eliminarlo)

⛔ DETENTE AQUÍ. Espera confirmación antes de continuar.

---

# FASE 3 — IMPLEMENTACIÓN (ejecutar solo tras confirmación)

Implementar únicamente lo listado en el reporte de auditoría.
Orden obligatorio:

1. Schemas (agregar campos faltantes)
2. Models/ORM (si faltan)
3. Repositories (métodos faltantes)
4. Services (lógica de negocio faltante)
5. Routers (endpoints faltantes)
6. Seeds RBAC si faltan permisos

## Reglas de implementación

Para módulos TRANSACCIONALES:
- Usar BEGIN TRANSACTION / COMMIT / ROLLBACK en operaciones
  que modifiquen cabecera + detalle juntos
- El detalle siempre se maneja embebido en la cabecera
- Solo permitir actualización cuando estado = borrador

Para módulos MAESTROS:
- Nunca eliminar físicamente (usar es_activo = 0)
- Validar unicidad de código/nombre dentro del tenant

Para TODOS los endpoints:
- Incluir cliente_id en todos los filtros y creaciones
- Incluir empresa_id cuando la tabla lo tenga
- Aplicar permiso RBAC correspondiente

## Comportamiento durante implementación

- Implementar un bloque a la vez (schemas → repositories → etc.)
- Al completar cada bloque, indicar brevemente qué se hizo
- Si encuentras una ambigüedad, usa el patrón del módulo
  de referencia elegido en Fase 1, no inventes uno nuevo
- Si un campo de la BD no está claro funcionalmente,
  inclúyelo en el schema como opcional y documéntalo

---

# FASE 4 — VERIFICACIÓN FINAL

Al terminar toda la implementación:

1. Lista todos los archivos modificados o creados
2. Para cada endpoint nuevo, confirma que tiene:
   - validación de cliente_id
   - validación de empresa_id (si aplica)
   - permiso RBAC
3. Verifica que ningún endpoint existente haya cambiado
   su ruta, método o estructura de response
4. Genera el archivo final:
   app/docs/modulos/[CODIGO]_IMPLEMENTACION.md

---

# INICIO

Comienza por la Fase 1.
Lee únicamente las tablas del módulo [CODIGO] en la BD.
No leas archivos completos. Filtra por prefijo.