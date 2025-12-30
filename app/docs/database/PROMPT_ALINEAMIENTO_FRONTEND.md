# Prompt para Alineamiento del Frontend con Refactorización de Módulos y Menús

## 📋 CONTEXTO DE LA REFACTORIZACIÓN

Se ha completado una refactorización completa del sistema de módulos, secciones, menús y plantillas de roles en el backend. El frontend debe ser actualizado para alinearse con estos cambios.

### Cambios Principales en el Backend:

1. **Nuevas Tablas y Estructura**:
   - `modulo` (catálogo de módulos ERP)
   - `cliente_modulo` (activación de módulos por cliente)
   - `modulo_seccion` (secciones dentro de módulos)
   - `modulo_menu` (menús jerárquicos)
   - `modulo_rol_plantilla` (plantillas de roles)

2. **Nuevos Endpoints**:
   - `/modulos-v2/` - Catálogo de módulos
   - `/cliente-modulo/` - Activación de módulos por cliente
   - `/secciones/` - Gestión de secciones
   - `/modulos-menus/` - Gestión de menús + menú del usuario
   - `/plantillas-roles/` - Gestión de plantillas de roles

3. **Cambio Crítico en Stored Procedure**:
   - **ANTES**: `sp_GetMenuForUser` (estructura antigua con `menu` y `area_menu`)
   - **AHORA**: `sp_obtener_menu_usuario` (nueva estructura con `modulo_menu`, `modulo_seccion`, `modulo`)

4. **Nueva Estructura de Respuesta del Menú**:
   ```json
   {
     "modulos": [
       {
         "modulo_id": "uuid",
         "codigo": "LOGISTICA",
         "nombre": "Logística y Distribución",
         "icono": "local_shipping",
         "color": "#FF9800",
         "categoria": "operaciones",
         "orden": 2,
         "secciones": [
           {
             "seccion_id": "uuid",
             "codigo": "RUTAS",
             "nombre": "Gestión de Rutas",
             "icono": "route",
             "orden": 1,
             "menus": [
               {
                 "menu_id": "uuid",
                 "codigo": "LOGISTICA_RUTAS_LISTA",
                 "nombre": "Lista de Rutas",
                 "icono": "route",
                 "ruta": "/logistica/rutas",
                 "nivel": 1,
                 "tipo_menu": "pantalla",
                 "orden": 1,
                 "permisos": {
                   "ver": true,
                   "crear": true,
                   "editar": false,
                   "eliminar": false,
                   "exportar": false,
                   "imprimir": false,
                   "aprobar": false
                 },
                 "submenus": [...]
               }
             ]
           }
         ]
       }
     ]
   }
   ```

---

## 🎯 PROMPT PARA EL FRONTEND

```
Necesito que analices y refactorices el frontend para alinearlo con la refactorización completa del backend de módulos, secciones, menús y permisos.

## CONTEXTO DE LA REFACTORIZACIÓN

El backend ha sido completamente refactorizado con las siguientes características:

### 1. NUEVA ESTRUCTURA DE DATOS
- Módulos ERP organizados en catálogo (`modulo`)
- Secciones dentro de módulos (`modulo_seccion`)
- Menús jerárquicos dentro de secciones (`modulo_menu`)
- Plantillas de roles que se aplican automáticamente al activar módulos
- Activación de módulos por cliente con configuración personalizada

### 2. NUEVOS ENDPOINTS (ver backend_spec.json)
- `/modulos-v2/` - Catálogo de módulos (GET, POST, PUT, DELETE, PATCH)
- `/cliente-modulo/` - Activación de módulos por cliente
- `/secciones/` - Gestión de secciones de módulos
- `/modulos-menus/` - Gestión de menús + endpoint crítico: GET `/modulos-menus/usuario/{usuario_id}/`
- `/plantillas-roles/` - Gestión de plantillas de roles

### 3. CAMBIO CRÍTICO EN STORED PROCEDURE
**ANTES**: `sp_GetMenuForUser` retornaba estructura plana con `menu` y `area_menu`
**AHORA**: `sp_obtener_menu_usuario` retorna estructura jerárquica con:
- Módulos → Secciones → Menús → Submenús
- Permisos agregados por rol
- Información de módulos activos del cliente

### 4. NUEVA ESTRUCTURA DE RESPUESTA DEL MENÚ
El endpoint `GET /modulos-menus/usuario/{usuario_id}/` retorna:
```json
{
  "modulos": [
    {
      "modulo_id": "uuid",
      "codigo": "LOGISTICA",
      "nombre": "Logística",
      "icono": "local_shipping",
      "color": "#FF9800",
      "categoria": "operaciones",
      "orden": 2,
      "secciones": [
        {
          "seccion_id": "uuid",
          "codigo": "RUTAS",
          "nombre": "Gestión de Rutas",
          "icono": "route",
          "orden": 1,
          "menus": [
            {
              "menu_id": "uuid",
              "codigo": "LOGISTICA_RUTAS_LISTA",
              "nombre": "Lista de Rutas",
              "icono": "route",
              "ruta": "/logistica/rutas",
              "nivel": 1,
              "tipo_menu": "pantalla",
              "orden": 1,
              "permisos": {
                "ver": true,
                "crear": true,
                "editar": false,
                "eliminar": false,
                "exportar": false,
                "imprimir": false,
                "aprobar": false
              },
              "submenus": [...]
            }
          ]
        }
      ]
    }
  ]
}
```

## TAREAS REQUERIDAS

### FASE 1: ANÁLISIS COMPLETO DEL PROYECTO
1. **Analizar estructura actual del frontend**:
   - Identificar todos los archivos relacionados con módulos, menús, áreas y permisos
   - Revisar cómo se construye actualmente el sidebar/menú dinámico
   - Identificar servicios/API calls relacionados con módulos y menús
   - Revisar componentes que usan la estructura antigua de menús

2. **Mapear cambios necesarios**:
   - Endpoints antiguos → Endpoints nuevos
   - Estructura antigua de menú → Nueva estructura jerárquica
   - Componentes que necesitan actualización
   - Servicios/helpers que necesitan refactorización

3. **Identificar dependencias**:
   - Componentes que dependen de la estructura antigua
   - Hooks/custom hooks relacionados
   - Contextos/estados globales relacionados
   - Rutas y navegación que usan menús

### FASE 2: PLAN DE REFACTORIZACIÓN
Generar un plan detallado que incluya:

1. **Archivos a modificar** (solo relacionados con módulos, menús, permisos):
   - Lista completa de archivos
   - Tipo de cambio requerido (refactor, reemplazo, nuevo)
   - Dependencias entre cambios

2. **Nuevos componentes/servicios necesarios**:
   - Servicios para nuevos endpoints
   - Componentes para nueva estructura jerárquica
   - Hooks para gestión de módulos y menús
   - Tipos/interfaces TypeScript actualizados

3. **Mejoras de UX/UI propuestas**:
   - Mejoras en el sidebar con nueva estructura jerárquica
   - Visualización de módulos con secciones
   - Indicadores visuales de módulos activos
   - Mejoras en la navegación jerárquica
   - Mejoras en la gestión de permisos en UI

4. **Orden de ejecución**:
   - Secuencia lógica de cambios
   - Puntos de validación
   - Riesgos y mitigaciones

### FASE 3: IMPLEMENTACIÓN
Solo después de aprobar el plan, proceder con:

1. **Actualizar servicios/API**:
   - Crear servicios para nuevos endpoints
   - Actualizar llamadas al endpoint del menú del usuario
   - Migrar de estructura antigua a nueva

2. **Refactorizar construcción del menú**:
   - Actualizar componente del sidebar para nueva estructura
   - Implementar renderizado jerárquico: Módulos → Secciones → Menús → Submenús
   - Integrar permisos en la visualización
   - Manejar estados de módulos activos/inactivos

3. **Actualizar componentes relacionados**:
   - Componentes que usan información de módulos
   - Componentes de gestión de permisos
   - Componentes de administración de módulos (si existen)

4. **Mejorar UX/UI**:
   - Implementar mejoras propuestas en el plan
   - Asegurar navegación fluida con nueva estructura
   - Mejorar feedback visual de permisos y estados

## RESTRICCIONES CRÍTICAS

⚠️ **NO MODIFICAR**:
- Autenticación y login
- Gestión de usuarios (excepto referencias a módulos/menús)
- Roles base (solo actualizar referencias a menús)
- Configuración de cliente/tenant (excepto módulos)
- Cualquier funcionalidad no relacionada con módulos, menús, secciones o permisos

✅ **SÍ MODIFICAR**:
- Construcción del menú dinámico/sidebar
- Llamadas a endpoints de módulos y menús
- Componentes que renderizan menús
- Servicios relacionados con módulos/menús
- Tipos/interfaces de módulos, menús, secciones
- Gestión de permisos en UI (solo referencias a menús)

## ENTREGABLES

1. **Análisis completo**:
   - Mapa de archivos actuales relacionados
   - Identificación de cambios necesarios
   - Dependencias identificadas

2. **Plan de refactorización detallado**:
   - Lista de archivos a modificar
   - Nuevos componentes/servicios necesarios
   - Mejoras de UX/UI propuestas
   - Orden de ejecución
   - Estimación de complejidad

3. **Implementación** (solo después de aprobación):
   - Código refactorizado
   - Nuevos componentes
   - Servicios actualizados
   - Mejoras de UX/UI implementadas

## INFORMACIÓN ADICIONAL

- **backend_spec.json**: Contiene la especificación completa de los nuevos endpoints
- **Estructura antigua**: Usaba `menu` y `area_menu` con SP `sp_GetMenuForUser`
- **Estructura nueva**: Usa `modulo_menu`, `modulo_seccion`, `modulo` con SP `sp_obtener_menu_usuario`
- **Endpoint crítico**: `GET /modulos-menus/usuario/{usuario_id}/` - Retorna menú completo con nueva estructura

## FORMATO DE RESPUESTA

Por favor, proporciona:
1. Análisis completo del proyecto frontend
2. Plan detallado de refactorización con mejoras UX/UI
3. Esperar aprobación antes de implementar
4. Implementación paso a paso con validaciones

¿Puedes comenzar con el análisis completo del proyecto frontend y generar el plan de refactorización?
```

---

## 📝 NOTAS ADICIONALES PARA EL PROMPT

Este prompt está diseñado para:

1. ✅ **Ser específico**: Solo módulos, menús, secciones y permisos
2. ✅ **Incluir contexto completo**: Estructura antigua vs nueva
3. ✅ **Mencionar el cambio crítico**: SP antiguo → SP nuevo
4. ✅ **Pedir análisis primero**: Antes de cualquier cambio
5. ✅ **Incluir mejoras UX/UI**: Como parte del plan
6. ✅ **Ser restrictivo**: No tocar nada no relacionado
7. ✅ **Ser estructurado**: Fases claras con entregables

El prompt debe ser usado con el archivo `backend_spec.json` que el usuario proporcionará, y debe analizar todo el proyecto frontend antes de proponer cambios.

