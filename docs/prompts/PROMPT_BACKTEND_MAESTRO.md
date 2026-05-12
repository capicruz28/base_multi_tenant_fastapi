CAXIS ERP — PROMPT MAESTRO v3
==============================

# CONTEXTO

Sistema SaaS ERP multi-tenant.
Stack: FastAPI + SQL Server.
El sistema ya tiene: autenticación JWT, RBAC, arquitectura modular.

Módulo objetivo: [MODULO] — [CODIGO]

---

# REGLAS ABSOLUTAS (leer primero, respetar siempre)

❌ NO modificar tablas ni estructura de BD
❌ NO eliminar código existente (marcarlo como deprecated si es incorrecto)
❌ NO asumir campos que no existan en la BD
✅ Reutilizar patrones de otros módulos ya implementados
✅ Respetar multi-tenant: validar cliente_id y empresa_id siempre
✅ Respetar RBAC con patrón: [modulo].[recurso].[accion]

⚠ REGLA CRÍTICA SOBRE CONTRATOS EXISTENTES:
  Los endpoints existentes NO son automáticamente correctos.
  Antes de protegerlos, debes evaluar si su diseño es arquitectónicamente
  válido para un sistema ERP SaaS. Si no lo es, se marcan como DEPRECATED
  (no se eliminan, no se modifican, solo se documentan y ocultan del contrato
  público usando deprecated=True en OpenAPI). El frontend NO debe consumir
  endpoints marcados como deprecated.

---

# FASE 0 — ANÁLISIS FUNCIONAL DEL MÓDULO (NUEVO — ejecutar primero)

Antes de leer código o BD, analiza el módulo desde la perspectiva funcional
de un ERP SaaS para el módulo [MODULO] ([CODIGO]).

## Paso 0.1 — ¿Cómo debería funcionar este módulo en un ERP real?

Responde estas preguntas basándote en el conocimiento general del dominio:

1. ¿Cuáles son las entidades principales que maneja este módulo?
2. ¿Qué entidades son maestros (catálogos)?
3. ¿Qué entidades son transaccionales y tienen ciclo de vida (estados)?
4. ¿Qué entidades son cabecera-detalle (nunca se operan por separado)?
5. ¿Qué entidades son derivadas/analíticas (solo lectura, calculadas por el sistema)?
6. ¿Cuáles son los flujos de negocio principales?
   Ej: "En inventarios: un movimiento siempre incluye su detalle embebido,
   nunca se crean líneas de detalle por separado desde el frontend."
7. ¿Qué integraciones tiene con otros módulos?

## Paso 0.2 — Definir el mapa de entidades y sus contratos esperados

Con base en el análisis anterior, define ANTES de ver la BD:

Para cada entidad identificada, define:
- Tipo: maestro | transaccional-cabecera | transaccional-detalle-embebido | derivada
- Si es detalle-embebido: ¿en qué cabecera va embebida?
- Operaciones esperadas (desde perspectiva ERP, no desde la BD):
  - MAESTRO: listar, detalle, crear, actualizar, desactivar, reactivar
  - TRANSACCIONAL (cabecera+detalle embebido): listar, detalle, crear-con-detalle,
    actualizar-con-detalle (solo en borrador), aprobar, procesar, anular
  - DERIVADA: solo listar y detalle (readonly)
- ¿Debe tener endpoints propios o ir embebida en otra entidad?

⛔ DETENTE AQUÍ. Espera confirmación del mapa funcional antes de continuar.

---

# FASE 1 — LECTURA Y COMPRENSIÓN (NO escribir código aún)

## Paso 1.1 — Leer la BD del módulo

Busca en el archivo SQL adjunto ÚNICAMENTE las tablas
que contengan el prefijo [CODIGO]_.

Para cada tabla encontrada, indica:
- nombre exacto de la tabla
- tipo según Fase 0 (maestro / cabecera / detalle-embebido / derivada)
- campos principales (nombre + tipo de dato)
- claves foráneas hacia otras tablas
- si tiene campo es_activo, cliente_id, empresa_id
- ¿tiene FK hacia otra tabla del mismo módulo? → posible relación cabecera-detalle

## Paso 1.2 — Confirmar o corregir el mapa funcional (Fase 0 vs BD real)

Compara el mapa funcional definido en Fase 0 contra lo encontrado en la BD.

Para cada tabla:
- ¿Confirma la clasificación de Fase 0? ✅ / ❌
- Si hay divergencia, explica cuál prevalece y por qué
- ¿La tabla tiene FK a otra tabla del mismo módulo (relación cabecera-detalle)?
  Si sí → confirmar que el detalle NO tendrá endpoints propios de escritura

## Paso 1.3 — Identificar patrón arquitectónico del proyecto

Busca en el proyecto la estructura de carpetas y archivos
de cualquier módulo existente para identificar:
- estructura de carpetas (presentation, application, domain, infrastructure)
- nombres de archivos convencionales usados
- cómo se define un router (APIRouter, prefijos, tags)
- cómo se valida tenant (cliente_id, empresa_id)
- cómo se aplica RBAC (require_permission, patrón del permiso)
- cómo se implementa cabecera+detalle embebido en otros módulos (si existe)

⚠ Solo extrae estructura y patrones técnicos, NO el contenido funcional.

## Paso 1.4 — Checkpoint obligatorio

Antes de continuar, responde:
1. ¿Cuántas tablas encontraste para el módulo [CODIGO]?
2. ¿Cuáles son cabecera y cuáles son detalle-embebido?
3. ¿El mapa de Fase 0 fue confirmado o corregido por la BD?
4. ¿Qué módulo usarás como referencia de estructura técnica?
5. ¿Hay tablas derivadas que NO deben tener escritura?

⛔ DETENTE AQUÍ. Espera confirmación antes de continuar.

---

# FASE 2 — AUDITORÍA (NO escribir código aún)

Con base en el mapa funcional confirmado (Fase 0 + Fase 1):

## Paso 2.1 — Inventario de endpoints existentes

Busca en el proyecto los archivos del módulo [CODIGO]:
routers, services, repositories, schemas.

Para cada endpoint existente indica:
| Ruta | Método | Entidad | Tiene tenant? | Tiene RBAC? | ¿Es correcto? |

La columna "¿Es correcto?" evalúa si el endpoint existe en el mapa funcional
definido en Fase 0. Si no existe → candidato a DEPRECATED.

## Paso 2.2 — Clasificación de endpoints existentes

Para cada endpoint encontrado, clasifícalo en una de estas categorías:

✅ CORRECTO: existe en el mapa funcional, tiene tenant y RBAC, está bien diseñado.

⚠ INCOMPLETO: existe en el mapa funcional pero le faltan campos, tenant o RBAC.

🔴 DEPRECATED: NO existe en el mapa funcional o viola el diseño correcto del módulo.
   Ejemplos de causas para DEPRECATED:
   - Endpoint de escritura para tabla derivada
   - Endpoint de escritura independiente para tabla detalle-embebido
     (ej: POST /movimientos-detalle cuando el detalle debe ir embebido en la cabecera)
   - Endpoint que expone operaciones que el módulo ERP no debería permitir

🔁 REEMPLAZAR: existe pero debe ser reemplazado por un diseño correcto.
   (el original queda deprecated, se implementa uno nuevo correcto)

## Paso 2.3 — Brechas funcionales

Para cada entidad del mapa funcional, verifica qué falta implementar.

MAESTRO → necesita: listar, detalle, crear, actualizar, desactivar, reactivar.
TRANSACCIONAL-CABECERA → necesita:
  - listar, detalle
  - crear (con detalle embebido en el body)
  - actualizar (solo si estado=borrador, con detalle embebido)
  - aprobar (si la BD tiene campo requiere_autorizacion)
  - procesar (cambia estado y afecta tablas derivadas)
  - anular (cambia estado, no elimina)
DERIVADA → solo listar y detalle. Si tiene escritura → marcar como DEPRECATED.

## Paso 2.4 — Campos faltantes en schemas

Para cada endpoint CORRECTO o INCOMPLETO, compara los campos del schema
contra los campos reales de la tabla en la BD.
Lista campos que existen en la BD pero no están en el schema.

Prioridad ALTA: campos NOT NULL sin default que no están en el schema de creación.
Prioridad MEDIA: campos opcionales que aportan información relevante al frontend.
Prioridad BAJA: campos de auditoría o internos que el frontend no necesita enviar.

## Paso 2.5 — Reporte de auditoría

Genera el archivo:
app/docs/modulos/AUDITORIA_[CODIGO].md

Con esta estructura:

### A. Mapa funcional del módulo
- Descripción funcional del módulo en contexto ERP
- Entidades y su clasificación (maestro/cabecera/detalle-embebido/derivada)
- Flujos de negocio principales

### B. Endpoints existentes clasificados
- Tabla con: ruta, método, clasificación (✅/⚠/🔴/🔁), motivo

### C. Endpoints a marcar como DEPRECATED
- Lista con ruta exacta y razón funcional del deprecado
- Instrucción: marcar con deprecated=True en el router (no eliminar)
- Nota para el frontend: NO consumir estos endpoints

### D. Endpoints faltantes a implementar
- Lista con ruta sugerida, método, entidad y descripción funcional

### E. Campos faltantes en schemas (por prioridad)

### F. Problemas de tenant o RBAC

### G. Seeds RBAC faltantes

⛔ DETENTE AQUÍ. Espera confirmación antes de continuar.

---

# FASE 3 — IMPLEMENTACIÓN (ejecutar solo tras confirmación)

Orden obligatorio:

1. Marcar DEPRECATED los endpoints identificados en Fase 2
   → Solo agregar deprecated=True en el router. NADA MÁS.
   → No modificar lógica, no tocar services ni repositories existentes.

2. Schemas
   → Agregar campos faltantes en schemas existentes
   → Crear schemas nuevos para endpoints cabecera+detalle embebido

3. Repositories (métodos faltantes)

4. Services (lógica de negocio faltante)

5. Routers (endpoints nuevos)
   → Los endpoints de detalle-embebido van en el router de la cabecera
   → NO crear routers independientes para tablas detalle

6. Seeds RBAC si faltan permisos

## Reglas de implementación

Para TABLAS DETALLE-EMBEBIDO:
- El detalle SIEMPRE va embebido en el body de la cabecera
- Schema de creación: CabeceraCreate incluye List[DetalleCreate] como campo obligatorio
- Schema de actualización: CabeceraUpdate incluye List[DetalleUpdate] opcional
- Schema de respuesta: CabeceraResponse incluye List[DetalleResponse]
- NO crear endpoints POST/PUT/DELETE independientes para el detalle
- El detalle puede tener endpoints de LECTURA independientes solo si el
  frontend los necesita para consultas específicas (ej: listar líneas de un movimiento)

Para módulos TRANSACCIONALES:
- Usar BEGIN TRANSACTION / COMMIT / ROLLBACK en operaciones
  que modifiquen cabecera + detalle juntos
- Solo permitir actualización cuando estado = borrador
- Validar estado antes de cada operación de ciclo de vida

Para módulos MAESTROS:
- Nunca eliminar físicamente (usar es_activo = 0)
- Validar unicidad de código/nombre dentro del tenant (cliente_id + empresa_id)

Para TODOS los endpoints:
- Incluir cliente_id en todos los filtros y creaciones
- Incluir empresa_id cuando la tabla lo tenga
- Aplicar permiso RBAC correspondiente

## Comportamiento durante implementación

- Implementar un bloque a la vez
- Al completar cada bloque, indicar brevemente qué se hizo
- Si hay ambigüedad, usar el patrón del módulo de referencia de Fase 1
- Nunca inventar campos que no estén en la BD

---

# FASE 4 — VERIFICACIÓN FINAL

Al terminar:

1. Lista todos los archivos modificados o creados
2. Lista todos los endpoints marcados como DEPRECATED con su ruta exacta
3. Para cada endpoint NUEVO confirma:
   - validación de cliente_id ✅/❌
   - validación de empresa_id (si aplica) ✅/❌
   - permiso RBAC ✅/❌
4. Para endpoints de cabecera+detalle confirma:
   - el detalle va embebido en el body ✅/❌
   - la transacción cubre cabecera y detalle juntos ✅/❌
5. Verifica que ningún endpoint CORRECTO haya cambiado
   su ruta, método o estructura de response
6. Genera el archivo final:
   app/docs/modulos/[CODIGO]_IMPLEMENTACION.md

---

# INICIO

Comienza por la Fase 0.
No leas código ni BD aún.
Define primero cómo debería funcionar este módulo en un ERP real.
Detente al finalizar Fase 0 y espera confirmación.