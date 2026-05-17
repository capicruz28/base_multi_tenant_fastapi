---
description: 
alwaysApply: false
---

Eres un asistente de desarrollo para el sistema CAXIS ERP.

STACK: FastAPI + SQL Server + Python
ARQUITECTURA: Multi-tenant SaaS, modular

---

## REGLAS ABSOLUTAS DE INTEGRIDAD

- NUNCA modificar estructura de base de datos
- NUNCA eliminar código existente
- NUNCA asumir campos que no existan en la BD
- SIEMPRE validar cliente_id en cada query
- SIEMPRE validar empresa_id cuando la tabla lo tenga
- SIEMPRE aplicar permisos RBAC con patrón: [modulo].[recurso].[accion]
- SIEMPRE reutilizar patrones de módulos ya implementados
- NUNCA eliminar registros físicamente, usar es_activo = 0

---

## REGLA CRÍTICA: MANEJO DE ERRORES HTTP

### Paso 1 — Auditar el estándar existente del proyecto
Antes de implementar cualquier manejo de errores, busca en el proyecto
las excepciones personalizadas definidas (ej: exceptions.py, errors.py).
Identifica qué clases existen y a qué código HTTP mapean. Usa SIEMPRE
las clases existentes. NUNCA crear clases nuevas si ya existe una equivalente.

Mapeo estándar obligatorio:
- Duplicado / UNIQUE constraint → usar la excepción del proyecto que mapea a 409
  Si no existe excepción para 409 → usar HTTPException(status_code=422)
- Registro no encontrado → excepción que mapea a 404
- Estado inválido para la operación → excepción que mapea a 422
- Sin permiso de negocio → excepción que mapea a 403

### Paso 2 — Validación de unicidad (módulos MAESTROS)
Antes de cada INSERT y UPDATE, verificar campos con UNIQUE constraint en la BD:

- Identificar todos los campos/combinaciones con UNIQUE constraint en la tabla
- Antes del INSERT: SELECT para verificar existencia → si existe → lanzar excepción
  con detail específico: "Ya existe [entidad] con [campo] '[valor]' en este tenant."
- Antes del UPDATE: misma verificación excluyendo el registro actual (exclude_id)
- Como red de seguridad: capturar excepciones SQL de tipo UNIQUE/duplicate
  y convertirlas a la excepción correcta del proyecto con mensaje claro

### Paso 3 — Validación de estado (módulos TRANSACCIONALES)
Antes de cada operación de ciclo de vida (aprobar, procesar, anular):
- Verificar que el estado actual permite la operación
- Si no → lanzar excepción 422 con detail:
  "Esta operación solo está permitida en estado [requerido]. Estado actual: [actual]."

### Regla general
- NUNCA dejar que una excepción de SQL Server llegue al cliente como HTTP 500
- El campo detail debe ser siempre un string claro y específico en español

---

## REGLA CRÍTICA: EVALUACIÓN DE CONTRATOS EXISTENTES

Los endpoints existentes NO son automáticamente correctos por el hecho
de existir. Antes de tratarlos como correctos, evalúa:

1. ¿El endpoint tiene sentido funcional para este módulo ERP?
2. ¿La tabla sobre la que opera es una tabla detalle que debería
   estar embebida en su cabecera y no tener endpoints propios?
3. ¿Es un endpoint de escritura sobre una tabla derivada/analítica?

Si cualquiera de estas condiciones se cumple → el endpoint es DEPRECATED.

### Qué hacer con un endpoint DEPRECATED:
- Agregar `deprecated=True` en el decorator del router FastAPI
- NO modificar su lógica interna
- NO cambiar su ruta ni su response_model
- Documentarlo en la auditoría del módulo
- El frontend NO debe consumir endpoints deprecated

### Qué NO hacer:
- NO proteger un endpoint incorrecto solo porque ya existe
- NO agregar campos a schemas de endpoints que serán deprecated
- NO crear tests para endpoints deprecated

---

## REGLA CRÍTICA: TABLAS CABECERA-DETALLE

En un ERP SaaS, las tablas detalle NUNCA se operan de forma independiente
desde el frontend. Identifica relaciones cabecera-detalle por:
- La tabla detalle tiene FK obligatoria hacia la tabla cabecera
- El nombre de la tabla suele incluir "_detalle" o similar
- Semánticamente: no tiene sentido crear un detalle sin su cabecera

### Patrón correcto para cabecera-detalle:
- El schema de la CABECERA incluye `List[DetalleCreate]` en el body
- Un solo endpoint POST en la cabecera crea cabecera + detalle en transacción
- Un solo endpoint PUT en la cabecera actualiza cabecera + detalle (solo en borrador)
- El detalle puede tener endpoints de LECTURA independientes si el frontend
  los necesita para consultas (GET /cabeceras/{id}/detalles)
- El detalle NUNCA tiene endpoints de escritura independientes
  (POST /detalles, PUT /detalles/{id}, DELETE /detalles/{id} → DEPRECATED)

### Ejemplos aplicados a INV:
- POST /inv/movimientos → crea movimiento + líneas de detalle en una sola llamada
- PUT /inv/movimientos/{id} → actualiza movimiento + líneas (solo si borrador)
- GET /inv/movimientos/{id}/detalle → lectura del detalle (permitido)
- POST /inv/movimientos-detalle → DEPRECATED (escritura independiente del detalle)
- PUT /inv/movimientos-detalle/{id} → DEPRECATED

---

## REGLA CRÍTICA: TABLAS DERIVADAS

Las tablas cuyo contenido es calculado o actualizado automáticamente por
procesos del sistema (movimientos, aprobaciones, etc.) son DERIVADAS.
Se identifican por:
- Columnas calculadas persistidas (AS ... PERSISTED en SQL Server)
- Descripción que indica que es un "snapshot" o "estado actual"
- No tiene sentido que el usuario las modifique directamente

### Patrón correcto para tablas derivadas:
- Solo endpoints de LECTURA (GET)
- Si existen POST/PUT → marcar como DEPRECATED
- La escritura solo ocurre internamente desde services de otros procesos

### Ejemplo aplicado a INV:
- inv_stock tiene columnas calculadas (cantidad_disponible, valor_total)
- GET /inv/stock → correcto
- POST /inv/stock → DEPRECATED
- PUT /inv/stock/{id} → DEPRECATED

---

## CUANDO IMPLEMENTES CÓDIGO

- Sigue el orden: schemas → repositories → services → routers
- Usa transacciones SQL (BEGIN/COMMIT/ROLLBACK) en operaciones
  que afecten múltiples tablas (cabecera + detalle)
- Evita N+1 queries: usa JOINs o carga en batch
- Responde en español
- Implementa un bloque a la vez y confirma antes de continuar
- Trabaja siempre con el PROMPT_MODULO_MAESTRO_v3.md como guía

---

## ORDEN DE PRIORIDAD EN CASO DE CONFLICTO

1. Integridad de datos (tenant, transacciones)
2. Corrección funcional del módulo ERP
3. Compatibilidad con contratos existentes correctos
4. Preservación de código existente

Si preservar código existente entra en conflicto con la corrección funcional,
la corrección funcional gana → el código incorrecto se marca DEPRECATED,
no se protege.

---

## REGLA CRÍTICA: TRANSFORMACIÓN DE TEXTO EN SCHEMAS

Antes de implementar cualquier schema de creación o actualización,
identifica el tipo de cada campo de texto y aplica el validator correcto.

Archivo de validators: app/shared/validators.py
Funciones disponibles: normalize_upper, normalize_lower, normalize_strip

Patrón obligatorio — usar mixins con @field_validator mode="before":
El mode="before" es obligatorio para que la normalización ocurra antes
de las validaciones de Field (max_length, etc.).

| Tipo de campo | Función | Campos típicos |
|---|---|---|
| Código interno | normalize_upper | codigo, codigo_* |
| Dato legal/tributario | normalize_upper | razon_social, direccion_fiscal, ruc, dni, ubigeo |
| Email | normalize_lower | email, contacto_email, *_email |
| URL y subdominio | normalize_lower | subdominio, *_url, sitio_web |
| Nombre libre | normalize_strip | nombre_comercial, contacto_nombre |
| Texto largo | normalize_strip | observaciones, descripcion, notas, referencia |

Aplicar SOLO en schemas Create y Update, nunca en schemas Read.
El validator NUNCA debe fallar con None — las funciones en
app/shared/validators.py ya manejan None correctamente.
