# FASE 3 RBAC — Cambios aplicados

**Fecha:** 2026-02-18  
**Alcance en este reporte:** Módulo HCM (piloto).  
**Patrón aplicado:** Patrón A (dominio de negocio).

---

## Resumen

| Métrica | Valor |
|--------|--------|
| Módulo | HCM (Planillas y RRHH) |
| Archivos modificados | 9 |
| Endpoints modificados | 36 |
| Patrón usado | A (require_permission como dependencia del handler) |

---

## Listado de endpoints modificados

| Módulo | Archivo | Función | Ruta | Permiso aplicado | Patrón |
|--------|---------|---------|------|------------------|--------|
| HCM | endpoints_empleados.py | get_empleados | GET /api/v1/hcm/empleados | hcm.empleado.leer | A |
| HCM | endpoints_empleados.py | get_empleado | GET /api/v1/hcm/empleados/{id} | hcm.empleado.leer | A |
| HCM | endpoints_empleados.py | post_empleado | POST /api/v1/hcm/empleados | hcm.empleado.crear | A |
| HCM | endpoints_empleados.py | put_empleado | PUT /api/v1/hcm/empleados/{id} | hcm.empleado.actualizar | A |
| HCM | endpoints_contratos.py | get_contratos | GET /api/v1/hcm/contratos | hcm.contrato.leer | A |
| HCM | endpoints_contratos.py | get_contrato | GET /api/v1/hcm/contratos/{id} | hcm.contrato.leer | A |
| HCM | endpoints_contratos.py | post_contrato | POST /api/v1/hcm/contratos | hcm.contrato.crear | A |
| HCM | endpoints_contratos.py | put_contrato | PUT /api/v1/hcm/contratos/{id} | hcm.contrato.actualizar | A |
| HCM | endpoints_conceptos_planilla.py | get_conceptos_planilla | GET /api/v1/hcm/conceptos-planilla | hcm.concepto_planilla.leer | A |
| HCM | endpoints_conceptos_planilla.py | get_concepto_planilla | GET /api/v1/hcm/conceptos-planilla/{id} | hcm.concepto_planilla.leer | A |
| HCM | endpoints_conceptos_planilla.py | post_concepto_planilla | POST /api/v1/hcm/conceptos-planilla | hcm.concepto_planilla.crear | A |
| HCM | endpoints_conceptos_planilla.py | put_concepto_planilla | PUT /api/v1/hcm/conceptos-planilla/{id} | hcm.concepto_planilla.actualizar | A |
| HCM | endpoints_planillas.py | get_planillas | GET /api/v1/hcm/planillas | hcm.planilla.leer | A |
| HCM | endpoints_planillas.py | get_planilla | GET /api/v1/hcm/planillas/{id} | hcm.planilla.leer | A |
| HCM | endpoints_planillas.py | post_planilla | POST /api/v1/hcm/planillas | hcm.planilla.crear | A |
| HCM | endpoints_planillas.py | put_planilla | PUT /api/v1/hcm/planillas/{id} | hcm.planilla.actualizar | A |
| HCM | endpoints_planilla_empleados.py | get_planilla_empleados | GET /api/v1/hcm/planilla-empleados | hcm.planilla_empleado.leer | A |
| HCM | endpoints_planilla_empleados.py | get_planilla_empleado | GET /api/v1/hcm/planilla-empleados/{id} | hcm.planilla_empleado.leer | A |
| HCM | endpoints_planilla_empleados.py | post_planilla_empleado | POST /api/v1/hcm/planilla-empleados | hcm.planilla_empleado.crear | A |
| HCM | endpoints_planilla_empleados.py | put_planilla_empleado | PUT /api/v1/hcm/planilla-empleados/{id} | hcm.planilla_empleado.actualizar | A |
| HCM | endpoints_planilla_detalle.py | get_planilla_detalles | GET /api/v1/hcm/planilla-detalle | hcm.planilla_detalle.leer | A |
| HCM | endpoints_planilla_detalle.py | get_planilla_detalle | GET /api/v1/hcm/planilla-detalle/{id} | hcm.planilla_detalle.leer | A |
| HCM | endpoints_planilla_detalle.py | post_planilla_detalle | POST /api/v1/hcm/planilla-detalle | hcm.planilla_detalle.crear | A |
| HCM | endpoints_planilla_detalle.py | put_planilla_detalle | PUT /api/v1/hcm/planilla-detalle/{id} | hcm.planilla_detalle.actualizar | A |
| HCM | endpoints_asistencia.py | get_asistencias | GET /api/v1/hcm/asistencia | hcm.asistencia.leer | A |
| HCM | endpoints_asistencia.py | get_asistencia | GET /api/v1/hcm/asistencia/{id} | hcm.asistencia.leer | A |
| HCM | endpoints_asistencia.py | post_asistencia | POST /api/v1/hcm/asistencia | hcm.asistencia.crear | A |
| HCM | endpoints_asistencia.py | put_asistencia | PUT /api/v1/hcm/asistencia/{id} | hcm.asistencia.actualizar | A |
| HCM | endpoints_vacaciones.py | get_vacaciones | GET /api/v1/hcm/vacaciones | hcm.vacaciones.leer | A |
| HCM | endpoints_vacaciones.py | get_vacaciones_by_id_endpoint | GET /api/v1/hcm/vacaciones/{id} | hcm.vacaciones.leer | A |
| HCM | endpoints_vacaciones.py | post_vacaciones | POST /api/v1/hcm/vacaciones | hcm.vacaciones.crear | A |
| HCM | endpoints_vacaciones.py | put_vacaciones | PUT /api/v1/hcm/vacaciones/{id} | hcm.vacaciones.actualizar | A |
| HCM | endpoints_prestamos.py | get_prestamos | GET /api/v1/hcm/prestamos | hcm.prestamo.leer | A |
| HCM | endpoints_prestamos.py | get_prestamo | GET /api/v1/hcm/prestamos/{id} | hcm.prestamo.leer | A |
| HCM | endpoints_prestamos.py | post_prestamo | POST /api/v1/hcm/prestamos | hcm.prestamo.crear | A |
| HCM | endpoints_prestamos.py | put_prestamo | PUT /api/v1/hcm/prestamos/{id} | hcm.prestamo.actualizar | A |

---

## Cambios estructurales realizados (por archivo)

En cada archivo del módulo HCM se realizó **únicamente**:

1. **Import añadido:** `from app.core.authorization.rbac import require_permission`
2. **Metadata añadida:** `MODULE_CODE = "hcm"` y `RESOURCE_CODE = "<recurso>"` (empleado, contrato, concepto_planilla, planilla, planilla_empleado, planilla_detalle, asistencia, vacaciones, prestamo).
3. **Dependencia añadida** en cada handler: `_: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))`, colocada **inmediatamente después** de `current_user`, con acción `leer` (GET), `crear` (POST) o `actualizar` (PUT).

No se modificaron paths, nombres de funciones, `response_model`, schemas, ni lógica interna.

---

## Próximos pasos (FASE 3 continuada)

Tras validar HCM, aplicar el mismo criterio a:

- LOG (solo riesgo BAJO; excluir subrecursos detalle de guía)
- INV
- FIN (excluir detalles de asiento)
- SVC (POST orden-servicio)
- TKT (POST ticket)
- Resto de módulos BAJO según `docs/rbac_alignment_plan_endpoints.md`
