# IAM Session Management V2 — Ticket Cutover F14

**Ticket:** IAM-BE-F14-CUTOVER-01  
**Tipo:** Epic / Release  
**Fase objetivo:** F14 — Cutover producción  
**Estado:** Abierto (plantilla F0 — ejecutar tras F13)  
**Fecha creación:** 2026-06-22  

> Plantilla operativa derivada de `IAM-SESSION-MANAGEMENT-V2-F0-EXECUTION-PLAN.md` §8.  
> Registrar en Jira/Linear/Azure DevOps con este contenido.

---

## Objetivo

Activar IAM Session Management V2 en producción: DDL en entornos pendientes, deploy backend, `IAM_SESSION_MANAGEMENT_V2_ENABLED=true`, smoke tests y monitoreo 24h.

---

## Pre-requisitos

- [ ] F13 merged en `feature/iam-session-v2`
- [ ] Suite `tests/unit/test_iam_sessions_v2_*` verde
- [ ] Suite regresión V1 con flag OFF verde
- [ ] Staging con esquema v3 + flag ON ≥ 48h sin incidentes P0
- [ ] FE desplegado tolerante a JSON superset (contrato V2)
- [ ] Comunicación usuarios enviada (T-72h)

---

## Alcance DDL

| Entorno | Acción |
|---------|--------|
| **Dev** | **OMITIR** — esquema v3 ya aplicado |
| **Staging** | Aplicar solo si esquema v3 ausente |
| **Producción** | Aplicar `tables_session_management_new.sql` (o V031 bootstrap) donde no exista v3 |
| **Multi-DB** | Inventario tenants dedicados; ejecutar en cada BD |

- [ ] Inventario tenants Multi-DB completado
- [ ] Script DDL probado en clone staging
- [ ] Backup validado restaurable

---

## Pasos ventana de mantenimiento

1. Comunicación inicio ventana
2. Backup BD central + tenants dedicados
3. DDL en entornos pendientes
4. Deploy backend release `X.Y.Z`
5. `IAM_SESSION_MANAGEMENT_V2_ENABLED=true` (y allowlist si aplica)
6. Smoke tests M1–M10 (ver IMPLEMENTATION-PLAN §13.2)
7. Monitor errores auth 401/500 — 24h
8. Cierre ventana o rollback según criterios

---

## Rollback

| Escenario | Acción |
|-----------|--------|
| Código defectuoso post-deploy | `IAM_SESSION_MANAGEMENT_V2_ENABLED=false` inmediato |
| DDL ya aplicado | Flag OFF **no restaura sesiones** — usuarios deben re-login |
| Rollback completo datos | Restaurar snapshot BD pre-ventana (≤1h) |

Referencia: `IAM-SESSION-MANAGEMENT-V2-IMPLEMENTATION-PLAN-01.md` §9.1

---

## Comunicación usuarios

**Asunto:** Actualización de seguridad de sesiones — re-inicio de sesión requerido

**Cuerpo (plantilla):**

> Hemos actualizado el sistema de gestión de sesiones para mejorar la seguridad de su cuenta.  
> Deberá **iniciar sesión nuevamente** en todos sus dispositivos después del mantenimiento.  
> Si experimenta problemas, contacte soporte.

---

## Criterios de éxito F14

- [ ] 0 errores P0 auth en 24h post-cutover
- [ ] Login / refresh / logout operativos en staging y prod
- [ ] FE sin regresiones en listado sesiones
- [ ] Métricas replay/compromise monitoreadas (si aplica)

---

## Referencias

- `IAM-SESSION-MANAGEMENT-V2-IMPLEMENTATION-PLAN-01.md` — Fase F14
- `ERP-IAM-SESSIONS-API-CONTRACT-V2.md`
- `tables_session_management_new.sql`

---

**Fin — IAM-BE-F14-CUTOVER-01**
