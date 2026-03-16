# Validación HCM — Checkpoint arquitectónico RBAC

**Fecha:** 2026-02-18  
**Módulo:** HCM (Planillas y RRHH) — piloto FASE 3  
**Objetivo:** Verificación estructural y de naming antes de continuar con el resto de módulos.

---

## 1. Verificación estructural global

### 1.1 Criterios comprobados

| Criterio | Resultado |
|----------|-----------|
| Todos los endpoints HCM de riesgo BAJO incluyen `current_user` | **Sí** — En los 9 archivos, cada handler declara `current_user: UsuarioReadWithRoles = Depends(get_current_active_user)`. |
| Todos incluyen `require_permission` | **Sí** — Cada handler declara `_: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))`. |
| Ningún handler quedó sin decorar | **Sí** — 36 handlers (9 archivos × 4 endpoints CRUD). Recuento: 36 apariciones de `Depends(get_current_active_user)` y 36 de `require_permission(`. |
| No hay permisos duplicados o inconsistentes | **Sí** — Un solo permiso por handler; formato único `hcm.<recurso>.<accion>`. |
| Convención `<modulo>.<recurso>.<accion>` | **Sí** — Todos los permisos son de la forma `hcm.<RESOURCE_CODE>.<leer|crear|actualizar>`. |

### 1.2 Resumen numérico

| Métrica | Valor |
|--------|--------|
| **Total archivos de endpoints HCM** | 9 |
| **Total endpoints (handlers) analizados** | 36 |
| **Total endpoints decorados con Patrón A** | 36 |
| **Endpoints sin decorar** | 0 |
| **Inconsistencias detectadas** | 0 |

### 1.3 Desglose por archivo

| Archivo | Handlers | current_user | require_permission | MODULE_CODE | RESOURCE_CODE |
|---------|----------|--------------|--------------------|-------------|---------------|
| endpoints_empleados.py | 4 | 4 | 4 | hcm | empleado |
| endpoints_contratos.py | 4 | 4 | 4 | hcm | contrato |
| endpoints_conceptos_planilla.py | 4 | 4 | 4 | hcm | concepto_planilla |
| endpoints_planillas.py | 4 | 4 | 4 | hcm | planilla |
| endpoints_planilla_empleados.py | 4 | 4 | 4 | hcm | planilla_empleado |
| endpoints_planilla_detalle.py | 4 | 4 | 4 | hcm | planilla_detalle |
| endpoints_asistencia.py | 4 | 4 | 4 | hcm | asistencia |
| endpoints_vacaciones.py | 4 | 4 | 4 | hcm | vacaciones |
| endpoints_prestamos.py | 4 | 4 | 4 | hcm | prestamo |

### 1.4 Inconsistencias encontradas

**Ninguna.** No se detectaron handlers sin permiso, permisos duplicados con distinto naming ni desvíos de la convención.

### 1.5 Confirmación final de alineación

**HCM cumple en su totalidad el Patrón A y la convención de permisos.** Los 36 endpoints de riesgo BAJO están decorados con `current_user` + `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>")`, con orden de parámetros correcto y sin alterar paths, firmas lógicas ni comportamiento.

---

## 2. Validación de naming de permisos candidatos [C]

### 2.1 Revisión sobre `rbac_new_permissions_candidates.md`

| Verificación | Resultado |
|--------------|-----------|
| **Variaciones semánticas duplicadas** | No existen. No hay pares como `hcm.planilla.actualizar` vs `hcm.planillas.actualizar`; en todo el módulo se usa **singular** en el código de permiso (planilla, contrato, empleado, etc.). |
| **Singular/plural vs RESOURCE_CODE** | Consistente. Todos los archivos definen `RESOURCE_CODE` en singular (empleado, contrato, concepto_planilla, planilla, planilla_empleado, planilla_detalle, asistencia, prestamo). El único recurso con nombre en plural es **vacaciones** (router `/vacaciones`), que se mantiene por coherencia con el path y el dominio; no existe `hcm.vacacion.*`. |
| **Recursos vs router real** | Coinciden. Cada `RESOURCE_CODE` corresponde al router que lo contiene: empleados→empleado, contratos→contrato, conceptos-planilla→concepto_planilla, planillas→planilla, planilla-empleados→planilla_empleado, planilla-detalle→planilla_detalle, asistencia→asistencia, vacaciones→vacaciones, prestamos→prestamo. |

### 2.2 Inconsistencias detectadas en candidatos [C]

**Ninguna.** La lista de candidatos en `rbac_new_permissions_candidates.md` es coherente con los `RESOURCE_CODE` usados en código y con la convención singular (salvo el caso explícito de `vacaciones`).

### 2.3 Recomendación

No se requieren cambios en el naming. Los códigos [C] listados están listos para alta en la tabla `permiso` o para auto-registro sin ajustes de convención.

---

## 3. Compatibilidad con auto-registro

### 3.1 Introspección del permiso

- **Forma del decorator:** Cada endpoint declara `Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))`.
- **A runtime:** El argumento de `require_permission` es un string concreto (p. ej. `"hcm.empleado.leer"`), ya que `MODULE_CODE` y `RESOURCE_CODE` son constantes del módulo y `<accion>` es literal (`"leer"`, `"crear"`, `"actualizar"`).
- **Extracción del código RBAC:** Una herramienta puede:
  1. **Por AST:** Resolver `MODULE_CODE`, `RESOURCE_CODE` y el literal de acción en cada handler y construir `codigo = f"{MODULE_CODE}.{RESOURCE_CODE}.{accion}"`.
  2. **Por inspección en tiempo de carga:** Recorrer las dependencias de cada ruta y, si existe una dependencia que invoque `require_permission`, obtener el valor del string pasado (p. ej. desde el grafo de dependencias de FastAPI o desde el callable).

En ambos casos el **código de permiso** (ej. `hcm.empleado.leer`) es recuperable sin modificar de nuevo los endpoints.

### 3.2 Sincronización con la tabla `permiso`

- El código de permiso generado (`<modulo>.<recurso>.<accion>`) coincide con el formato esperado por la tabla `permiso` (campo `codigo` y, si aplica, `recurso` y `accion` derivables del mismo string).
- Un proceso de **auto-registro** puede:
  - Recorrer los endpoints decorados,
  - Extraer el `codigo` de permiso (como arriba),
  - Insertar o actualizar filas en `permiso` (y opcionalmente en `rol_permiso`) **sin tocar el código** de los endpoints.

### 3.3 Confirmación explícita

**Sí:** Los decorators añadidos en HCM permiten la introspección automática del permiso, la extracción del código RBAC desde `require_permission` y la futura sincronización automática con la tabla `permiso` sin modificar de nuevo los endpoints.

---

## 4. Conclusión del checkpoint

| Aspecto | Estado |
|---------|--------|
| Estructural (current_user + require_permission en todos los handlers) | **OK** |
| Sin handlers sin decorar | **OK** |
| Sin permisos duplicados o inconsistentes | **OK** |
| Convención `<modulo>.<recurso>.<accion>` | **OK** |
| Naming de candidatos [C] (singular/plural, recurso vs router) | **OK** |
| Compatibilidad con auto-registro | **OK** |

**No se han detectado inconsistencias críticas.** El módulo HCM queda validado como piloto RBAC y se autoriza la continuidad de FASE 3 con el siguiente módulo (LOG, solo riesgo BAJO), aplicando a partir de ahora un mini reporte de validación por módulo antes de avanzar al siguiente.
