# Documentación Frontend — Módulo WFL (Flujos de Trabajo)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** WFL - Flujos de Trabajo

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)
8. [Notas Importantes](#notas-importantes)

---

## Información General

### Base URL

```
/api/v1/wfl
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Orden recomendado:** Configurar ORG; luego definir flujos de trabajo (aprobación, revisión, notificación) y asociarlos a módulos.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Flujos de Trabajo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/wfl/flujos-trabajo | Listar (empresa_id, tipo_flujo, modulo_aplicable, es_activo, buscar) |
| GET | /api/v1/wfl/flujos-trabajo/{flujo_id} | Detalle |
| POST | /api/v1/wfl/flujos-trabajo | Crear flujo |
| PUT | /api/v1/wfl/flujos-trabajo/{flujo_id} | Actualizar |

**Campos principales en creación:** empresa_id, codigo_flujo, nombre, descripcion, tipo_flujo (aprobacion, revision, notificacion), modulo_aplicable (código del módulo donde aplica, ej. PUR, SLS, MFG), definicion_pasos (JSON con pasos del workflow: roles, orden, condiciones), es_activo.

**Ejemplo definicion_pasos (JSON):** estructura libre; típicamente array de pasos, ej. `[{"orden":1,"rol":"gerente","nombre":"Aprobación Gerente"},{"orden":2,"rol":"finanzas","nombre":"Aprobación Finanzas"}]`. El frontend puede ofrecer editor visual o JSON crudo.

### 2. Seguimiento (UI)

El menú incluye "Seguimiento" para ver estado de aprobaciones pendientes. Por ahora no hay tabla de instancias de aprobación en este módulo; la pantalla puede listar flujos activos y, cuando exista integración con módulos (ej. OC, pedidos), mostrar pendientes según reglas de negocio o endpoints específicos de cada módulo.

---

## Schemas TypeScript

### Flujo de Trabajo

```typescript
interface FlujoTrabajoCreate {
  empresa_id: string;
  codigo_flujo: string;
  nombre: string;
  descripcion?: string;
  tipo_flujo: 'aprobacion' | 'revision' | 'notificacion';
  modulo_aplicable?: string;   // ej. 'PUR', 'SLS', 'MFG'
  definicion_pasos?: string;   // JSON: pasos del workflow
  es_activo?: boolean;
}

interface FlujoTrabajoUpdate {
  codigo_flujo?: string;
  nombre?: string;
  descripcion?: string;
  tipo_flujo?: string;
  modulo_aplicable?: string;
  definicion_pasos?: string;
  es_activo?: boolean;
}

interface FlujoTrabajoRead extends FlujoTrabajoCreate {
  flujo_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Flujo de trabajo no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/wfl
  /flujos-trabajo
    /list
    /create
    /:flujo_id/edit
    /:flujo_id
  /seguimiento
    # Estado de aprobaciones (según integración con otros módulos)
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) configurado.

### 2. Flujos de Trabajo

- Crear flujo: POST /wfl/flujos-trabajo (empresa_id, codigo_flujo, nombre, tipo_flujo, modulo_aplicable, definicion_pasos como JSON string, es_activo: true).
- Listar por empresa_id, tipo_flujo o modulo_aplicable para asignar flujos a módulos o pantallas.
- Editar definicion_pasos (PUT) para ajustar pasos, roles u orden sin cambiar código.

### 3. Seguimiento

- Consumir GET /wfl/flujos-trabajo (es_activo: true) y, cuando existan instancias de aprobación en otros módulos o tablas, integrar con esos endpoints para mostrar pendientes por usuario/rol.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **definicion_pasos:** Es un string (JSON). El backend no valida la estructura; el frontend puede definir el esquema (ej. array de pasos con orden, rol, nombre) y enviar/recibir como string. Parsear con JSON.parse / JSON.stringify al editar.

3. **modulo_aplicable:** Código corto del módulo donde aplica el flujo (PUR, SLS, MFG, FIN, etc.). Útil para filtrar flujos por módulo en pantallas de aprobación.

4. **tipo_flujo:** aprobacion, revision, notificacion. Permite clasificar flujos; la lógica de uso (quién aprueba, notificaciones) se implementa en frontend o en servicios que consuman estos flujos.

5. **IDs en URLs:** flujo_id es UUID.

6. **codigo_flujo:** Debe ser único por (cliente_id, empresa_id). El backend no genera código; el frontend puede proponer secuencia o valor libre.

7. **Instancias de aprobación:** Este módulo solo almacena la **definición** del flujo. Las instancias (ej. “OC 001 pendiente de aprobación por Gerente”) pueden estar en el módulo correspondiente (PUR, etc.) o en una tabla futura de instancias de workflow; la documentación se actualizará si se añaden endpoints de instancias.

---

**Fin de la documentación del módulo WFL**
