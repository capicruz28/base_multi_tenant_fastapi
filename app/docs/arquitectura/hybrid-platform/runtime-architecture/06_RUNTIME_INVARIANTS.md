# 06 — Runtime Invariants

**Etapa:** 4 — Runtime Architecture  
**Fecha:** 2026-06-25  
**Estado:** Normativo para runtime

---

## 1. Propósito

Definir **reglas obligatorias** del comportamiento en ejecución. Violación = bug de arquitectura o deuda explícita.

---

## 2. Invariantes — Contexto

| ID | Invariante |
|----|------------|
| RI-01 | Toda request HTTP productiva tiene Tenant Context establecido antes del handler. |
| RI-02 | Tenant Context se destruye al finalizar request (teardown). |
| RI-03 | Tenant Context proviene de Host en producción como fuente primaria. |
| RI-04 | Una request tiene exactamente un Tenant Context activo. |
| RI-05 | Identity Context requiere Tenant Context previo en endpoints protegidos. |
| RI-06 | Company Context requiere Identity Context previo. |
| RI-07 | Authorization Context es derivado; no es SSOT de permisos. |
| RI-08 | Persistence Context no es visible para Application Layer. |
| RI-09 | Contextos no persisten entre requests del mismo cliente. |
| RI-10 | Async child tasks no heredan contexto automáticamente. |

---

## 3. Invariantes — Tenant & aislamiento

| ID | Invariante |
|----|------------|
| RI-11 | Ninguna operación tenant-data accede datos de otro tenant. |
| RI-12 | Cross-tenant superadmin requiere gate y audit explícitos. |
| RI-13 | Tenant suspendido no ejecuta operaciones mutativas ERP. |
| RI-14 | Tenant en estado Migrando no acepta tráfico ERP operativo. |
| RI-15 | Tenant Retirado rechaza autenticación nueva. |
| RI-16 | Subdominio excluido (api, admin) mapea a tenant SYSTEM, no tenant cliente. |
| RI-17 | Identificador tenant en JWT debe coherir con Host salvo impersonation. |
| RI-18 | Impersonation establece tenant operativo desde JWT target, no fila SYSTEM. |
| RI-19 | Company Context no cambia Tenant Data Store route. |
| RI-20 | Multi-empresa: datos filtrados por company identifier en scope COMPANY. |

---

## 4. Invariantes — Seguridad & IAM

| ID | Invariante |
|----|------------|
| RI-21 | Endpoints protegidos rechazan request sin credencial válida. |
| RI-22 | Access token revocado (blacklist) rechazado aunque no expirado. |
| RI-23 | Refresh usa tenant identifier del refresh token, no del Host. |
| RI-24 | Logout es idempotente (siempre 200). |
| RI-25 | Impersonation no emite refresh token. |
| RI-26 | Impersonation refresh attempt → 403. |
| RI-27 | Company switch bloqueado durante impersonation. |
| RI-28 | Session probe en /me rechaza sesión revocada V2. |
| RI-29 | RBAC gate precede ejecución handler mutativo. |
| RI-30 | ERP operativo requiere company identifier salvo platform operator pattern. |

---

## 5. Invariantes — Persistencia & modos

| ID | Invariante |
|----|------------|
| RI-31 | Application Layer nunca resuelve conexión o almacén. |
| RI-32 | Application Layer nunca conoce Installation Mode. |
| RI-33 | Frontend nunca recibe Installation Mode en response. |
| RI-34 | OpenAPI responses no incluyen metadata de almacén. |
| RI-35 | Control Plane operations route exclusivamente a Control Plane Store. |
| RI-36 | Tenant data operations route a Tenant Data Store del tenant. |
| RI-37 | Shared y Dedicated producen mismo contrato observable L5. |
| RI-38 | Metadata ausente implica fallback Shared (compat legacy). |
| RI-39 | Dedicated explícito nunca fallback a Shared silencioso. |
| RI-40 | Tenant filter aplicado en tenant-data shared; policy encapsulada L6. |

---

## 6. Invariantes — ERP & negocio

| ID | Invariante |
|----|------------|
| RI-41 | ERP services no contienen branch Shared/Dedicated. |
| RI-42 | Workflow states no editables directamente por cliente HTTP. |
| RI-43 | Cross-scope access retorna 404, no 403. |
| RI-44 | Derived data (stock) no writable directamente por API cliente. |
| RI-45 | Soft delete usa desactivación lógica, no DELETE físico ERP. |
| RI-46 | Audit user identifiers provienen de Identity Context, no payload. |

---

## 7. Invariantes — Platform & provisioning

| ID | Invariante |
|----|------------|
| RI-47 | Product Permission definitions solo lectura desde tenant runtime. |
| RI-48 | Platform admin opera sobre Control Plane; no ERP day-to-day data. |
| RI-49 | Onboarding response contract estable independiente modo. |
| RI-50 | Provisioning dedicated precede seed ERP en tenant store. |
| RI-51 | Storage Metadata owner es Platform; lectura L6 only. |

---

## 8. Invariantes — Cache & performance

| ID | Invariante |
|----|------------|
| RI-52 | Permission cache invalidation tras cambio grants; stale max bounded. |
| RI-53 | Redis blacklist checked before Identity Context accepted. |
| RI-54 | Engine/store cache invalidation tras cambio Installation Mode. |
| RI-55 | Health endpoint no expone credenciales ni connection strings. |

---

## 9. Invariantes — Observabilidad

| ID | Invariante |
|----|------------|
| RI-56 | Request correlation id propagado logs cross-layer. |
| RI-57 | Errores SQL nunca retornados raw al cliente. |
| RI-58 | Impersonation actions auditadas en Platform/IAM audit. |
| RI-59 | Installation Mode puede aparecer en logs infra, nunca en response body. |

---

## 10. Invariantes — Background & lifecycle

| ID | Invariante |
|----|------------|
| RI-60 | Background jobs declaran tenant scope explícitamente. |
| RI-61 | Migration invalida todas las sesiones activas del tenant. |
| RI-62 | Teardown ejecuta aunque handler lance excepción. |

---

## 11. Resumen por categoría

| Categoría | Count |
|-----------|-------|
| Contexto | 10 |
| Tenant/aislamiento | 10 |
| Seguridad/IAM | 10 |
| Persistencia/modos | 10 |
| ERP | 6 |
| Platform | 5 |
| Cache | 4 |
| Observabilidad | 4 |
| Background | 3 |
| **Total** | **62** |

---

## 12. Invariantes con excepción AS-IS conocida

| ID | Invariante | AS-IS gap |
|----|------------|-----------|
| RI-32 | L5 no conoce mode | user_context, rol_service branches |
| RI-40 | Filter encapsulado | filter también en query layer visible |
| RI-54 | Cache invalidation | engine cache no invalidado shutdown |

Documentado en `08_RUNTIME_RISKS.md`.

---

## 13. Verificación conceptual (pre-producción dedicated)

Checklist:

- [ ] RI-31, RI-32, RI-41 verificados en review L5
- [ ] RI-11, RI-17 tested cross-tenant
- [ ] RI-23, RI-25 refresh/logout impersonation
- [ ] RI-36 dedicated routes to exclusive store
- [ ] RI-39 no silent fallback dedicated
- [ ] RI-62 teardown under exception

---

## 14. Conclusión

62 invariantes definen el **contrato de comportamiento runtime**. Son verificables por review, test de integración y observabilidad sin referirse a implementación concreta.
