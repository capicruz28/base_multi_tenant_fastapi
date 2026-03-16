# Validación alineación RBAC — Módulo QMS (Control de Calidad)

**Fecha:** 2026-02-18  
**Estado:** Completado

---

## 1. Endpoints encontrados

| Archivo | Recurso RBAC | Endpoints |
|---------|--------------|-----------|
| endpoints_parametros.py | parametro_calidad | GET "", GET /{id}, POST, PUT |
| endpoints_no_conformidades.py | no_conformidad | GET "", GET /{id}, POST, PUT |
| endpoints_inspecciones.py | inspeccion | GET "", GET /{id}, POST, PUT + detalles (GET list, POST, GET by id, PUT) |
| endpoints_planes.py | plan_inspeccion | GET "", GET /{id}, POST, PUT + detalles (GET list, POST, GET by id, PUT) |

**Total endpoints QMS:** 24

---

## 2. Endpoints decorados

Todos con Patrón A (MODULE_CODE = "qms"). **24/24 (100 %).**

---

## 3. Permisos generados

qms.parametro_calidad.leer, .crear, .actualizar; qms.no_conformidad.*; qms.inspeccion.*; qms.plan_inspeccion.* → **12 permisos únicos**.

---

## 4–5. Inconsistencias / Introspección

Ninguna. Detectables por auto-registro.
