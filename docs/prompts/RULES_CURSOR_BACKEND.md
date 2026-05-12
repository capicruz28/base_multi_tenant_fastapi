---
description:
alwaysApply: true
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