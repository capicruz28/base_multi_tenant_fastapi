# Session Store — Referencias lógicas cross-plane (CP → DP)

**Versión:** 1.0  
**Fecha:** 2026-06-27  
**Estado:** **Normativo** — extiende ADR-001-A, ADR-002-A y F9 Baseline  
**Migraciones:** `V033__remove_cross_plane_session_fks.sql`, `V034__remove_cross_plane_session_empresa_fks.sql`

---

## 1. Decisión

El agregado IAM Session Store (`user_session`, `token_family`, `refresh_tokens`) persiste en **Control Plane** (ADR-002-A). Las columnas de contexto tenant desnormalizadas hacia identidad y empresa operativa son **referencias lógicas UUID**, sin FK física cross-plane hacia tablas del **Data Plane**.

| Columna | Entidad DP | Validación write |
|---------|------------|------------------|
| `usuario_id` | Identity (`usuario`) | Identity Gateway en login |
| `empresa_id` | Company (`org_empresa`) | Selección/cambio empresa vía lectura DP |
| `cliente_id` | Tenant Registry (`cliente`) | **FK CP válida** — metadata platform |

Precedente simétrico: DTSP elimina FK `cliente_id → cliente` en almacén DP Dedicated.

---

## 2. FK eliminadas (brownfield)

| Migración | FK | Motivo |
|-----------|-----|--------|
| V033 | `FK_session_usuario`, `FK_family_usuario`, `FK_token_usuario` | Identity autoritativa en DP |
| V034 | `FK_session_empresa`, `FK_token_empresa` | Company autoritativa en DP |

---

## 3. FK conservadas (intra-CP)

Integridad del agregado session y tenant registry:

- `FK_session_cliente`, `FK_family_cliente`, `FK_token_cliente` → `cliente`
- `FK_family_session`, `FK_token_session`, `FK_token_family`, `FK_token_parent`

---

## 4. Greenfield bootstrap

`V020`, `V031` y `tables_session_management_new.sql` **no crean** FK cross-plane hacia `usuario` ni `org_empresa` en tablas session.

---

## 5. ORM

`UserSessionTable`, `TokenFamilyTable`, `RefreshTokensTable` en `tables.py`: `usuario_id` y `empresa_id` sin `ForeignKey`.

---

## 6. Invariantes runtime

1. Toda fila session con `usuario_id` proviene de un flujo que validó identidad vía IG.
2. Toda fila con `empresa_id` NOT NULL proviene de flujo que validó empresa activa en DP (mismo tenant).
3. Revocación por lifecycle usuario/empresa es responsabilidad application-layer (`SessionRevocationService`), no CASCADE BD cross-plane.

---

## 7. Fuera de alcance

- `auth_audit_log` mantiene FK legacy hacia `usuario`/`org_empresa` — no bloquea hot path session.
- Ticket futuro si aplica el mismo patrón a auditoría IAM.
