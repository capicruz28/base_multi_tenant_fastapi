# Documentación Frontend — Módulo BI (Reportes & Analytics)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** BI - Reportes y Analytics

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
/api/v1/bi
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Orden recomendado:** Configurar ORG; luego crear reportes (SQL, dashboards) y categorizarlos por módulo/categoría.

### Alcance (CATALOGO_MODULOS / MENU_NAVEGACION)

- **Reportes configurables:** Crear reportes personalizados con SQL; guardar configuración (filtros, gráficos).
- **Dashboards:** KPIs en tiempo real; gráficos interactivos (configuración en `configuracion_json`).

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Reportes

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/bi/reportes | Listar (empresa_id, tipo_reporte, modulo_origen, categoria, es_activo, es_publico, buscar) |
| GET | /api/v1/bi/reportes/{reporte_id} | Detalle |
| POST | /api/v1/bi/reportes | Crear reporte |
| PUT | /api/v1/bi/reportes/{reporte_id} | Actualizar |

**Campos principales en creación:** empresa_id, codigo_reporte, nombre, descripcion, modulo_origen (código módulo: INV, SLS, FIN, etc.), categoria (ventas, inventarios, finanzas, etc.), tipo_reporte ('sql' | 'olap' | 'dashboard'), query_sql (texto SQL opcional), configuracion_json (JSON: gráficos, filtros, ejes), es_publico, creado_por_usuario_id, es_activo.

**Ejemplo configuracion_json:** estructura libre; típicamente gráficos (tipo, ejes, colores) y filtros (parámetros, valores por defecto). Ej. `{"graficos":[{"tipo":"line","ejeX":"fecha","ejeY":"total"}],"filtros":[{"param":"fecha_desde","tipo":"date"}]}`. El frontend puede ofrecer editor visual o JSON crudo.

---

## Schemas TypeScript

### Reporte

```typescript
interface ReporteCreate {
  empresa_id: string;
  codigo_reporte: string;
  nombre: string;
  descripcion?: string;
  modulo_origen?: string;   // ej. 'INV', 'SLS', 'FIN'
  categoria?: string;       // ej. 'ventas', 'inventarios', 'finanzas'
  tipo_reporte?: 'sql' | 'olap' | 'dashboard';
  query_sql?: string;
  configuracion_json?: string;  // JSON: gráficos, filtros
  es_publico?: boolean;
  creado_por_usuario_id?: string;
  es_activo?: boolean;
}

interface ReporteUpdate {
  codigo_reporte?: string;
  nombre?: string;
  descripcion?: string;
  modulo_origen?: string;
  categoria?: string;
  tipo_reporte?: string;
  query_sql?: string;
  configuracion_json?: string;
  es_publico?: boolean;
  es_activo?: boolean;
}

interface ReporteRead extends ReporteCreate {
  reporte_id: string;
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
| 404 | Reporte no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/bi
  /reportes
    /list
    /create
    /:reporte_id/edit
    /:reporte_id
    /:reporte_id/ejecutar   # Ejecutar reporte (si el backend expone endpoint de ejecución)
  /dashboards
    # Listar reportes tipo 'dashboard' o vista unificada de KPIs
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) configurado.

### 2. Reportes

- Crear reporte: POST /bi/reportes (empresa_id, codigo_reporte, nombre, tipo_reporte, query_sql opcional, configuracion_json como string, es_activo: true).
- Listar por empresa_id, tipo_reporte, categoria o modulo_origen para pantallas de reportes y dashboards.
- Editar query_sql y configuracion_json (PUT) para ajustar consultas y visualización sin cambiar código.

### 3. Dashboards

- Consumir GET /bi/reportes (tipo_reporte: 'dashboard' o categoria según convención) y renderizar widgets según configuracion_json.
- KPIs en tiempo real: ejecutar reportes tipo 'sql' con parámetros (cuando exista endpoint de ejecución) o consumir endpoints específicos de cada módulo.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **configuracion_json:** Es un string (JSON). El backend no valida la estructura; el frontend puede definir el esquema (gráficos, filtros, ejes) y enviar/recibir como string. Parsear con JSON.parse / JSON.stringify al editar.

3. **tipo_reporte:** 'sql' (reporte con query personalizado), 'olap', 'dashboard'. Permite clasificar y mostrar en distintas vistas (lista de reportes vs. vista dashboard).

4. **query_sql:** Solo almacenamiento; la **ejecución** de SQL no está expuesta en esta API por seguridad. El frontend puede consumir un endpoint dedicado de ejecución de reportes (si se implementa) con parámetros validados y solo lectura.

5. **IDs en URLs:** reporte_id es UUID.

6. **codigo_reporte:** Debe ser único por (cliente_id, empresa_id). El backend no genera código; el frontend puede proponer secuencia o valor libre.

7. **es_publico:** Si está disponible para todos los usuarios del tenant; útil para reportes compartidos vs. personales.

8. **modulo_origen / categoria:** Facilitan filtrar y agrupar reportes en el menú (por módulo o por categoría de negocio).

---

**Fin de la documentación del módulo BI**
