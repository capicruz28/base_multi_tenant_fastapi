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

# FASE 0 — ANÁLISIS FUNCIONAL + CONTRASTE CON BD REAL

⚠ INSTRUCCIÓN CLAVE: Esta fase se ejecuta COMPLETA sin detenerse.
No esperes confirmación entre Fase 0 y Fase 1. Ejecuta ambas en secuencia
y presenta el resultado consolidado en el Paso 0.3.

## Paso 0.1 — Mapa funcional ideal (sin leer BD ni código)

Basándote exclusivamente en conocimiento del dominio ERP SaaS,
define cómo debería funcionar el módulo [MODULO] ([CODIGO]):

1. ¿Cuáles son las entidades principales que maneja este módulo?
2. ¿Qué entidades son maestros (catálogos)?
3. ¿Qué entidades son transaccionales con ciclo de vida (estados)?
4. ¿Qué entidades son cabecera-detalle (nunca se operan por separado)?
5. ¿Qué entidades son derivadas/analíticas (solo lectura, calculadas)?
6. ¿Cuáles son los flujos de negocio principales?
7. ¿Qué integraciones tiene con otros módulos del ERP?

Para cada entidad del mapa ideal, define:
- Tipo: maestro | transaccional-cabecera | detalle-embebido | derivada
- Operaciones esperadas según su tipo
- ¿Tiene endpoints propios o va embebida?

## Paso 0.2 — Leer la BD real del módulo

Ahora lee el archivo SQL adjunto. Filtra ÚNICAMENTE las tablas con prefijo [CODIGO]_.

Para cada tabla encontrada, indica:
- nombre exacto
- campos principales (nombre + tipo de dato)
- claves foráneas (especialmente hacia otras tablas del mismo módulo)
- si tiene: es_activo, cliente_id, empresa_id
- si tiene columnas calculadas (AS ... PERSISTED) → candidata a DERIVADA

## Paso 0.3 — Tabla de contraste: ideal vs BD real

Presenta un único cuadro comparativo con esta estructura:

| Entidad ideal | ¿Existe en BD? | Tabla real | Tipo confirmado | Observación |
|---|---|---|---|---|
| [entidad del mapa ideal] | ✅ Sí / ❌ No | [nombre tabla] | maestro/cabecera/detalle/derivada | [nota] |

Luego responde explícitamente:

A. Entidades del mapa ideal que SÍ existen en tu BD → se implementarán
B. Entidades del mapa ideal que NO existen en tu BD → se documentan como
   "fuera de scope actual" y NO se implementan ni se mencionan más
C. Tablas en tu BD que NO estaban en el mapa ideal → se analizan y clasifican
   según las reglas del tipo (¿son maestros adicionales? ¿detalles no anticipados?)
D. Relaciones cabecera-detalle confirmadas por FK → el detalle NO tendrá
   endpoints de escritura propios

⚠ REGLA CRÍTICA: El alcance de implementación lo define tu BD, no el mapa ideal.
  Si el mapa ideal menciona una entidad que no existe en la BD → se ignora.
  No se crean tablas, no se sugieren migraciones, no se asume su existencia.
  Solo se trabaja con lo que está en la BD real.

⛔ DETENTE AQUÍ. Espera confirmación del contraste antes de continuar con Fase 1.

---

# FASE 1 — ESTRUCTURA TÉCNICA DEL PROYECTO

(La lectura de BD y el contraste ya se realizaron en Fase 0. No releer la BD.)

## Paso 1.1 — Identificar patrón arquitectónico del proyecto

Busca en el proyecto la estructura de carpetas y archivos
de cualquier módulo existente para identificar:
- estructura de carpetas (presentation, application, domain, infrastructure)
- nombres de archivos convencionales usados
- cómo se define un router (APIRouter, prefijos, tags)
- cómo se valida tenant (cliente_id, empresa_id)
- cómo se aplica RBAC (require_permission, patrón del permiso)
- cómo se implementa cabecera+detalle embebido en otros módulos (si existe)

⚠ Solo extrae estructura y patrones técnicos, NO el contenido funcional.

## Paso 1.2 — Checkpoint

Responde únicamente:
1. ¿Qué módulo usarás como referencia de estructura técnica y por qué?
2. ¿Existe algún módulo que ya implemente cabecera+detalle embebido
   que puedas tomar como patrón?

⛔ DETENTE AQUÍ. Espera confirmación antes de continuar con Fase 2.

---

# FASE 2 — AUDITORÍA (NO escribir código aún)

Con base en el contraste confirmado (Fase 0) y el patrón técnico (Fase 1).

## Paso 2.1 — Diagnóstico de salud del módulo

Antes de revisar endpoints o schemas, emite un diagnóstico general
del módulo como si fuera un semáforo:

🟢 SALUDABLE     — El módulo cubre sus flujos principales correctamente.
                   Solo hay ajustes menores (campos, RBAC incompleto).

🟡 AJUSTES       — El módulo funciona pero tiene brechas que afectan
                   la experiencia o la integridad (endpoints mal diseñados,
                   detalle separado de cabecera, campos críticos faltantes).

🔴 PROBLEMAS     — El módulo tiene errores de diseño que impiden que
                   funcione correctamente en producción SaaS.

Justifica el diagnóstico en 3-5 líneas concretas.

### Tablas críticas faltantes (solo si aplica)

⚠ Esta sección solo aparece si detectas una tabla que cumpla
  LAS DOS condiciones siguientes simultáneamente:
  a) No existe en la BD real del módulo
  b) Sin ella, un flujo de negocio PRINCIPAL del módulo no puede funcionar
     (no puede completarse, no puede persistir datos obligatorios)

Si no hay ninguna tabla en esa situación → esta sección NO aparece.
NO menciones tablas "recomendables", "útiles" o "para completar el módulo".
Solo tablas cuya ausencia rompe un flujo principal.

Formato si hay tablas críticas faltantes:
| Tabla sugerida | Flujo que bloquea | Por qué es bloqueante |
Solo informativo. No se crean, no se implementan. La decisión es del desarrollador.

## Paso 2.2 — Inventario y clasificación de endpoints existentes

Busca en el proyecto los archivos del módulo [CODIGO]:
routers, services, repositories, schemas.

Para cada endpoint existente, clasifícalo:

✅ CORRECTO
   Existe en el mapa funcional del módulo, tiene validación de tenant,
   tiene RBAC aplicado y su diseño es arquitectónicamente válido.

⚠ INCOMPLETO
   Existe en el mapa funcional pero tiene uno o más de estos problemas:
   - Falta validación de tenant (cliente_id / empresa_id)
   - Falta permiso RBAC
   - Faltan campos NOT NULL de la BD en el schema
   Se mantiene y se corrige en Fase 3.

🔴 DEPRECATED
   Viola el diseño correcto del módulo. Causas:
   - Endpoint de escritura independiente para tabla detalle-embebido
   - Endpoint de escritura sobre tabla derivada/calculada
   - Endpoint que opera sobre una entidad que no debería tener
     operaciones directas desde el frontend
   → Se marca deprecated=True en el router. No se modifica ni elimina.
   → El frontend NO debe consumirlo.

🔁 REEMPLAZAR
   El endpoint existe pero su diseño es incorrecto Y existe una versión
   correcta que debe implementarse. El original queda DEPRECATED y se
   implementa el reemplazo en Fase 3.

Presenta la tabla:
| Ruta | Método | Entidad | Tenant ✅/❌ | RBAC ✅/❌ | Clasificación | Motivo |

## Paso 2.3 — Brechas funcionales por entidad

Para cada entidad confirmada en el contraste de Fase 0, verifica
qué operaciones del mapa funcional están faltando implementar.

Usa solo las operaciones que corresponden al tipo de entidad:

MAESTRO → listar, detalle, crear, actualizar, desactivar, reactivar
TRANSACCIONAL-CABECERA → listar, detalle,
  crear-con-detalle-embebido, actualizar-con-detalle-embebido (solo borrador),
  aprobar (si BD tiene requiere_autorizacion), procesar, anular

⚠ Para crear Y actualizar con detalle embebido, verificar AMBOS endpoints:
  - ¿El POST recibe List[DetalleCreate] embebido en el body? → si no → ⚠ INCOMPLETO
  - ¿El PUT recibe List[DetalleUpdate] opcional embebido en el body? → si no → ⚠ INCOMPLETO
  No es suficiente que el PUT valide el estado borrador — también debe
  aceptar el detalle embebido. Un PUT que solo actualiza la cabecera
  obliga al frontend a llamadas separadas para el detalle → ⚠ INCOMPLETO
DERIVADA → listar, detalle (solo lectura)

Marca cada operación: ✅ existe y correcto | ⚠ existe incompleto | ❌ falta

## Paso 2.4 — Campos faltantes en schemas

Solo para endpoints ✅ CORRECTO y ⚠ INCOMPLETO.
Compara campos del schema actual contra campos reales de la tabla en BD.

🔴 CRÍTICO   — Campo NOT NULL sin default, ausente en schema de creación.
               El endpoint falla en runtime sin este campo.
⚠ IMPORTANTE — Campo opcional con valor funcional para el frontend.
➕ MENOR     — Campo de auditoría o interno. El frontend no lo necesita enviar.

Solo los campos 🔴 CRÍTICO son obligatorios corregir en Fase 3.
Los ⚠ IMPORTANTE se corrigen si no agregan complejidad.
Los ➕ MENOR se documentan pero no se tocan.

## Paso 2.5 — Reporte de auditoría

Genera el archivo:
app/docs/modulos/AUDITORIA_[CODIGO].md

Con esta estructura exacta:

---
### DIAGNÓSTICO GENERAL
[Semáforo 🟢/🟡/🔴 + justificación en 3-5 líneas]
[Alineación con ERP SaaS: "El módulo cubre X de Y flujos principales"]

### TABLAS CRÍTICAS FALTANTES
[Solo si hay. Si no hay → "Ninguna. La BD cubre todos los flujos principales."]

### ENTIDADES Y CLASIFICACIÓN
[Tabla: entidad | tipo | tabla BD | endpoints propios S/N]

### ENDPOINTS EXISTENTES
[Tabla completa con clasificación ✅/⚠/🔴/🔁]

### ENDPOINTS A DEPRECAR
[Lista con ruta exacta, motivo y qué reemplaza si aplica]

### ENDPOINTS FALTANTES A IMPLEMENTAR
[Lista: ruta sugerida | método | entidad | descripción funcional breve]

### CAMPOS FALTANTES EN SCHEMAS
[Por entidad y prioridad 🔴/⚠/➕]

### PROBLEMAS DE TENANT O RBAC
[Lista concreta de qué falta y dónde]

### SEEDS RBAC FALTANTES
[Lista de permisos faltantes con patrón modulo.recurso.accion]
---

⛔ DETENTE AQUÍ. Espera confirmación antes de continuar con Fase 3.

---

# FASE 3 — IMPLEMENTACIÓN (ejecutar solo tras confirmación)

Orden obligatorio:

1. Marcar DEPRECATED los endpoints identificados en Fase 2
   → Solo agregar deprecated=True en el router. NADA MÁS.
   → No modificar lógica, no tocar services ni repositories existentes.

2. Schemas
   → Agregar campos faltantes en schemas existentes
   → Antes de definir cada campo de texto, clasificarlo según el estándar
     de transformación (UPPER/LOWER/STRIP) y aplicar el @field_validator
     correspondiente desde app/shared/validators.py usando mode="before".
     Las funciones disponibles son: normalize_upper, normalize_lower, normalize_strip.
     Aplicar mediante mixins siguiendo el patrón de app/modules/org/presentation/schemas.py.
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

## Manejo de errores — obligatorio en todos los módulos

### Antes de implementar cualquier validación de error:
Busca en el proyecto el archivo de excepciones personalizadas (exceptions.py
o similar). Identifica las clases existentes y sus códigos HTTP.
USA SIEMPRE las clases del proyecto. NUNCA crear nuevas si ya existe equivalente.

### Para módulos MAESTROS — unicidad:
Para cada tabla, identificar campos con UNIQUE constraint en la BD y agregar:
1. Función de lookup por esos campos en el archivo de queries
   (con parámetro exclude_id opcional para que UPDATE no se invalide a sí mismo)
2. Validación en el service antes del INSERT y antes del UPDATE
3. Lanzar la excepción del proyecto que corresponda (409 para duplicados)
   con detail específico: "Ya existe [entidad] con [campo] '[valor]' en este tenant."
4. Red de seguridad: try/except sobre la operación SQL capturando UNIQUE/duplicate

### Para módulos TRANSACCIONALES — estado:
Antes de aprobar, procesar, anular: verificar estado actual y lanzar 422
con detail: "Solo permitido en estado [requerido]. Estado actual: [actual]."

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

Comienza por la Fase 0 completa (Paso 0.1 → 0.2 → 0.3).
No te detengas entre pasos dentro de la Fase 0.
En el Paso 0.1 defines el mapa ideal sin leer nada.
En el Paso 0.2 lees la BD real (solo tablas con prefijo [CODIGO]_).
En el Paso 0.3 presentas el contraste y te detienes a esperar confirmación.

El alcance de todo el trabajo lo define la BD real, no el mapa ideal.
Entidades del mapa ideal que no existen en la BD → ignorar completamente.