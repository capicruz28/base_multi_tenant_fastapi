# Ola 1 ORG — Contrato Frontend ↔ Backend (Motor de Códigos)

**Etapa:** Cierre oficial Ola 1 ORG — **referencia única para Frontend**  
**Fecha:** 2026-07-12  
**Estado:** **OLA 1 ORG CERRADA** — Backend listo; Frontend puede iniciar alineación  
**Alcance:** 5 entidades ORG integradas al Motor de Códigos  
**Autoridad:** Este directorio prevalece sobre borradores en `codigo-generation-wave1/04_FUNCTIONAL_CONTRACT.md` para integración React

---

## 1. Veredicto de cierre

| Aspecto | Estado |
|---------|--------|
| Integración motor ORG (5 entidades) | ✅ Implementada y testeada |
| Campo código opcional en CREATE | ✅ Schemas publicados |
| Generación automática AUTO_DEFAULT | ✅ Via `OrgCodigoGenerationService` → Gateway |
| Bootstrap `org_empresa` (EMP001 → EMP002) | ✅ Normativa BR-BOOT-04 |
| Contrato API estable para Frontend | ✅ Este paquete documental |
| Módulo admin cfg | ⏸ Fuera de Ola 1 — etapa posterior |

**Conclusión:** El Backend ORG está **listo** para que el equipo Frontend inicie la alineación del proyecto React **sin cambios adicionales en Backend** para Ola 1.

---

## 2. Qué cambió para Frontend (resumen)

| Antes | Ahora (Ola 1) |
|-------|---------------|
| Campo código **obligatorio** en formularios CREATE | Campo código **opcional** — omitir = auto-generación |
| Frontend generaba o forzaba correlativo | Backend asigna código vía motor |
| Mismo contrato Read (código siempre presente) | **Sin cambio** en respuestas GET/POST 201 |
| UPDATE con código | **Normativa BR-IMM:** inmutable post-CREATE. Runtime Update aún permite mutación → **fase implementación** (schemas/services). Contrato FE objetivo: solo lectura |

---

## 3. Documentos de este paquete

| # | Documento | Contenido |
|---|-----------|-----------|
| 00 | Este archivo | Resumen ejecutivo, cierre Ola 1, índice |
| 01 | [`01_COMPARATIVE_MATRIX.md`](01_COMPARATIVE_MATRIX.md) | Matriz comparativa 5 entidades |
| 02 | [`02_ENTITY_CONTRACTS.md`](02_ENTITY_CONTRACTS.md) | Contrato detallado por entidad (13 puntos × 5) |
| 03 | [`03_HTTP_ERRORS_AND_RUNTIME_FLOW.md`](03_HTTP_ERRORS_AND_RUNTIME_FLOW.md) | Errores HTTP, flujo FE→BD, casos transversales |
| 04 | [`04_FRONTEND_MIGRATION_STRATEGY.md`](04_FRONTEND_MIGRATION_STRATEGY.md) | Cambios obligatorios/opcionales, estrategia migración |

---

## 4. Endpoints CREATE (referencia rápida)

**Prefijo módulo:** `/org`  
**Autenticación:** JWT ERP + sesión scope según entidad

| Entidad | Método | Ruta | Permiso RBAC | Sesión ERP |
|---------|--------|------|--------------|------------|
| Empresa | POST | `/org/empresa` | `org.empresa.crear` | TENANT |
| Sucursal | POST | `/org/sucursales` | `org.sucursal.crear` | COMPANY |
| Departamento | POST | `/org/departamentos` | `org.departamento.crear` | COMPANY |
| Centro de costo | POST | `/org/centros-costo` | `org.centro_costo.crear` | COMPANY |
| Cargo | POST | `/org/cargos` | `org.cargo.crear` | COMPANY |

**Status éxito:** `201 Created` + body Read con código asignado.

---

## 5. Matriz comparativa (resumen)

Ver detalle en [`01_COMPARATIVE_MATRIX.md`](01_COMPARATIVE_MATRIX.md).

| Entidad | sequence_key | Scope | Policy | Prefijo | Padding | Campo | Manual CREATE |
|---------|--------------|-------|--------|---------|---------|-------|---------------|
| Empresa | `org_empresa` | TENANT | AUTO_DEFAULT | EMP | 3 | `codigo_empresa` | Sí (opcional) |
| Sucursal | `org_sucursal` | EMPRESA | AUTO_DEFAULT | SUC | 3 | `codigo` | Sí (opcional) |
| Departamento | `org_departamento` | EMPRESA | AUTO_DEFAULT | DEP | 3 | `codigo` | Sí (opcional) |
| Centro costo | `org_centro_costo` | EMPRESA | AUTO_DEFAULT | CC | 3 | `codigo` | Sí (opcional) |
| Cargo | `org_cargo` | EMPRESA | AUTO_DEFAULT | CAR | 3 | `codigo` | Sí (opcional) |

**Formato auto típico:** `{PREFIJO}{NNN}` sin separador (ej. `SUC001`, `CAR042`).

---

## 6. Plan recomendado para Frontend

| Fase | Alcance | Riesgo |
|------|---------|--------|
| **FE-1** | Quitar `required` del código en CREATE (5 formularios) | Bajo |
| **FE-2** | Omitir campo del payload o enviar `null` | Bajo |
| **FE-3** | Mostrar código asignado post-201 en detalle/toast | Bajo |
| **FE-4** | Mensajes 409 duplicado (codigo / RUC empresa) | Medio |
| **FE-5** | Override manual colapsado (implantación) | Opcional |
| **FE-6** | Preview próximo código (cuando exista API cfg) | Futuro |

---

## 7. Relación con otras olas

| Ola | Relación |
|-----|----------|
| Ola 1 ORG motor | **Cerrada** — este contrato |
| Admin cfg (`codigo-generation-admin/`) | Preview/diagnóstico — no bloquea FE-1..FE-4 |
| Ola 2+ (INV, …) | Contratos futuros en el mismo patrón |

---

## 8. Referencias Backend (solo lectura)

| Recurso | Ubicación |
|---------|-----------|
| Schemas Create/Read | `app/modules/org/presentation/schemas.py` |
| Services CREATE | `app/modules/org/application/services/*_service.py` |
| Catálogo secuencias | `app/core/codigo/sequence_catalog.py` |
| Tests integración | `tests/unit/test_org_*_motor_integration.py` |
| Contrato normativo previo | `codigo-generation-wave1/04_FUNCTIONAL_CONTRACT.md` |

---

*Siguiente paso Frontend: implementar FE-1 tras revisión de [`04_FRONTEND_MIGRATION_STRATEGY.md`](04_FRONTEND_MIGRATION_STRATEGY.md).*
