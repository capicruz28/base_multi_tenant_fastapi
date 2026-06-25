# 04 — Runtime Flows

**Etapa:** 4 — Runtime Architecture  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión

---

## 1. Propósito

Documentar flujos de ejecución específicos: objetivo, participantes, inicio, fin, información propagada y puntos críticos.

---

## 2. Login

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Autenticar usuario; establecer sesión; emitir tokens |
| **Participantes** | Cliente, Edge, Ingress, Tenant Resolution, IAM, Control Plane, Tenant Data, Cache |
| **Inicio** | POST credenciales en Host tenant |
| **Fin** | 200 + tokens (body/cookies) o error auth |

**Propagación:** Host → Tenant Context → validate tenant activo → authenticate identity (Tenant Data) → create session (IAM) → emit JWT with sid, cliente_id, empresa state.

**Puntos críticos:**
- Tenant Context desde Host, no body
- Multi-empresa → selection token sin refresh
- Single empresa → sesión completa
- Dedicated: mismo flujo observable; L6 en auth

---

## 3. Refresh

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Renovar access token; rotar refresh |
| **Participantes** | Cliente, IAM, Cache, Session store |
| **Inicio** | POST refresh (cookie/body) |
| **Fin** | Nuevos tokens o 401 |

**Propagación:** Refresh token → tenant id **desde token** (no Host primario) → session probe → rotation.

**Puntos críticos:**
- Platform host + tenant token mismatch evitado usando token tenant
- Impersonation refresh → 403
- V2 replay detection
- Dedicated: session store location (Q-010)

---

## 4. Logout

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Revocar sesión; idempotente |
| **Participantes** | Cliente, IAM, Cache |
| **Inicio** | POST logout |
| **Fin** | 200 siempre |

**Propagación:** Refresh token tenant → revoke session → optional access jti blacklist.

**Puntos críticos:** Idempotencia; clear cookies web.

---

## 5. ERP Request (operativo)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Operación negocio ERP scoped |
| **Participantes** | Cliente, full pipeline L0–L6, ERP service |
| **Inicio** | Request autenticada Host tenant |
| **Fin** | JSON response / error mapeado |

**Propagación:** Tenant → Identity → Authorization (permiso ERP) → Company → ERP service → L6 tenant data → filter tenant+company.

**Puntos críticos:**
- require_erp_session equivalent
- Cross-scope → 404
- L5 sin mode branch
- Impersonation: tenant operativo = target JWT

---

## 6. Platform Request (superadmin)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Gobernanza cross-tenant |
| **Participantes** | Platform operator, Ingress, Platform services, Control Plane |
| **Inicio** | Host platform (excluded subdomain) |
| **Fin** | Response admin |

**Propagación:** Tenant Context = SYSTEM → Identity platform → Authorization superadmin → L6 control plane only.

**Puntos críticos:** Audit obligatorio; no ERP data reads.

---

## 7. Tenant Admin Request

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Administración tenant (users, roles, org) |
| **Participantes** | Tenant admin, IAM, Tenant Data |
| **Inicio** | Host tenant + admin token |
| **Fin** | CRUD response |

**Propagación:** Full tenant context → tenant admin RBAC → L6 tenant data (users, roles, grants).

**Puntos críticos:** Grants referencian Product Permission read-only.

---

## 8. Onboarding (alta tenant)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Crear tenant operativo inicial |
| **Participantes** | Platform operator, Provisioning orchestrator, Control Plane, Tenant Data |
| **Inicio** | POST /clientes (superadmin) |
| **Fin** | Tenant Activo + credenciales |

**Propagación:** Multi-fase saga (conceptual): Registry → Mode → [Dedicated store prep] → seed DP → IAM admin.

**Puntos críticos:**
- Response shape estable (E2 compatibility)
- Orden dependencias E3
- No TX cross-plane única
- Estado Provisioning intermedio (dedicated async)

---

## 9. Provisioning (Dedicated)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Preparar Tenant Data Store exclusivo |
| **Participantes** | Platform, infra ops, Control Plane metadata |
| **Inicio** | Dedicated tenant approved |
| **Fin** | Storage metadata activa |

**Propagación:** Metadata write → schema apply → health verify → enable routing.

**Puntos críticos:** Metadata antes de ERP seed; rollback si falla.

---

## 10. Impersonation

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Superadmin opera como tenant |
| **Participantes** | Platform operator, IAM, Cache, Tenant Data target |
| **Inicio** | POST impersonate/{tenant} |
| **Fin** | Access token impersonation |

**Propagación:** Overlay impersonation → target tenant in JWT → Host may stay platform → ERP uses target tenant context.

**Puntos críticos:**
- No refresh
- Parent session in cache
- End impersonation restore
- L6 resolves target tenant store

---

## 11. Migration (Shared → Dedicated)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Mover data plane sin cambiar ownership |
| **Participantes** | Platform ops, Control Plane, source/target stores |
| **Inicio** | Tenant → Migrando |
| **Fin** | Tenant Activo dedicated |

**Propagación:** Invalidate all sessions → copy DP → switch metadata → verify → Activo.

**Puntos críticos:**
- No ERP traffic during Migrando
- Sequence counter validation
- Engine cache invalidation (Q-063)

---

## 12. Background Job

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Mantenimiento (session cleanup, etc.) |
| **Participantes** | Scheduler, IAM, Control Plane |
| **Inicio** | Cron / interval |
| **Fin** | Job complete log |

**Propagación:** Synthetic context (system or per-tenant batch) → L6 explicit route.

**Puntos críticos:**
- No inherit HTTP context
- Tenant iteration explicit
- No user Identity Context unless scoped

---

## 13. Health Check

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Liveness/readiness probe |
| **Participantes** | Probe, FastAPI, L6 optional |
| **Inicio** | GET /health |
| **Fin** | 200/503 |

**Propagación:** Optional Tenant Context default → optional DB ping.

**Puntos críticos:** No auth; no leak infra details.

---

## 14. Company Selection (post-login)

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Completar sesión multi-empresa |
| **Participantes** | Cliente, IAM, Tenant Data |
| **Inicio** | POST seleccionar empresa + selection token |
| **Fin** | Full session tokens |

**Propagación:** Selection token → validate Host tenant match → set Company → issue refresh.

---

## 15. Company Switch

| Aspecto | Detalle |
|---------|---------|
| **Objetivo** | Cambiar empresa en sesión activa |
| **Participantes** | Cliente, IAM |
| **Inicio** | POST cambiar empresa |
| **Fin** | New tokens same tenant |

**Puntos críticos:** Blocked in impersonation; atomic rotation.

---

## 16. Tabla comparativa flujos

| Flujo | Tenant Context | Company Context | L6 Store |
|-------|----------------|-----------------|----------|
| Login | Host | Optional pending | Both |
| Refresh | Token | From token | IAM store |
| ERP | Host | Required | Tenant DP |
| Platform | SYSTEM | N/A | Control |
| Tenant Admin | Host | Optional | Tenant DP |
| Onboarding | N/A new | Seed | Both phases |
| Impersonation | Host platform | Target | Target DP |
| Health | Default | N/A | Optional |
| Background | Synthetic | N/A | Explicit |

---

## 17. Conclusión

Cada flujo es variante del pipeline canónico con **gates distintos** y **rutas L6 distintas**. Ningún flujo expone Installation Mode al cliente.

Detalle secuencial: `07_RUNTIME_SEQUENCE_DIAGRAMS.md`.
