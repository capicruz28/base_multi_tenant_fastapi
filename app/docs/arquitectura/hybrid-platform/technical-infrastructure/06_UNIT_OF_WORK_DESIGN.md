# 06 — Unit of Work Design

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** AS-IS UoW, G-18, E4 RI-31  
**Restricción:** Diseño transaccional multi-paso. Sin código.

---

## 1. Propósito

Especificar el diseño técnico del **Unit of Work** como mecanismo de agrupación transaccional dentro del Persistence Gateway — preservando semántica AS-IS y extendiéndola a dedicated sin cambios de API.

---

## 2. Definición

**Unit of Work (UoW)** es un scope transaccional que:

- Abre **una** AsyncSession sobre engine resuelto
- Permite múltiples operaciones SQL
- Confirma todas al exit exitoso
- Revierte todas ante cualquier excepción
- Cierra sesión al finalizar scope

**Ubicación AS-IS:** `app/core/application/unit_of_work.py`

---

## 3. Contrato técnico (preservado)

| Elemento | Semántica |
|----------|-----------|
| Entrada | `client_id` opcional (default ContextVar), `connection_type` DEFAULT/ADMIN |
| Método `execute()` | Ejecuta SQLAlchemy construct; SELECT retorna list[dict] |
| Exit success | `commit()` |
| Exit exception | `rollback()` |
| Sesión | Una por scope UoW |

**Invariante G-18:** No crear UoW alternativo por installation mode.

---

## 4. Resolución interna

```
UoW.__aenter__
  → Resolver client_id (param o ContextVar)
  → connection_type DEFAULT:
      → Connection Resolution tenant_data
  → connection_type ADMIN:
      → Connection Resolution control_plane
  → get_db_connection con binding resuelto
  → Retener sesión en scope UoW
```

**Dedicated:** mismo flujo; metadata determina engine; UoW ignora mode.

---

## 5. Consumidores actuales y futuros

| Dominio | Uso UoW | Criticidad |
|---------|---------|------------|
| IAM Session V2 | Creación sesión + tokens atómico | Alta |
| INV procesos transaccionales | Movimientos cabecera-detalle | Alta |
| PUR creación transaccional | Alta | Media |
| MNT | Mantenimiento | Media |
| Onboarding (futuro saga) | **Por paso** — no cross-store | Alta |

---

## 6. UoW vs execute_* — cuándo usar

| Criterio | execute_* | UoW |
|----------|-----------|-----|
| Operaciones SQL | 1 | 2+ atómicas |
| Commit | Por operación | Al final scope |
| Lectura + escritura relacionada | Riesgo inconsistencia | UoW |
| SELECT solo | execute_query | N/A |
| Proceso ERP cabecera-detalle | **UoW obligatorio** | Sí |

---

## 7. Límites del UoW

### 7.1 Un solo almacén por UoW

| Regla | Descripción |
|-------|-------------|
| UoW-01 | Un scope UoW opera **un único** Connection Binding |
| UoW-02 | Cross-plane (CP + DP) requiere **dos scopes** separados |
| UoW-03 | Cross-plane **no** atomicidad SQL distribuida en MVP |
| UoW-04 | Saga onboarding coordina múltiples UoW secuenciales |

**Gap AS-IS onboarding:** single TX mezcla CP+DP — violación UoW-02. Remediación saga (RD-12).

### 7.2 Duración

| Regla | Límite |
|-------|--------|
| UoW-05 | Scope UoW debe ser corto (< segundos) |
| UoW-06 | Prohibido IO externo (HTTP, Redis write crítico) dentro UoW |
| UoW-07 | Redis bridge IAM **post-commit** fuera UoW (AS-IS correcto) |

---

## 8. Post-commit actions

| Patrón | Ejemplo AS-IS | Regla |
|--------|---------------|-------|
| Side effect post-commit | SessionRedisBridge | Ejecutar **después** exit UoW |
| Compensación fallo post-commit | Manual / saga | Documentar en 11 |
| Event emit | Futuro | Post-commit async |

---

## 9. UoW en dedicated

| Aspecto | Comportamiento |
|---------|----------------|
| Resolución | Storage Metadata → dedicated binding |
| Tenant filter | Policy L6 — UoW no altera |
| Rollback | Mismo semantics |
| Performance | Pool dedicado tenant — sin cambio API |

---

## 10. Testing requirements (Etapa 6)

| Test | Objetivo |
|------|----------|
| UoW commit multi-step | Atomicidad preserved |
| UoW rollback on step 2 fail | No partial persist |
| UoW dedicated tenant | Same semantics shared |
| UoW + external session | SR rules from 05 |

---

## 11. Gap AS-IS

| ID | Gap |
|----|-----|
| UoW-G01 | `ENABLE_UNIT_OF_WORK` no enforced |
| UoW-G02 | Onboarding usa session.begin() directo, no UoW wrapper |
| UoW-G03 | Algunos services mezclan execute_* + UoW en mismo flujo sin documentar |

---

## 12. Conclusión

Unit of Work permanece el **mecanismo canónico de atomicidad multi-paso** dentro de un único almacén. Cross-store operations usan saga externa, no UoW extendido.

Documentos relacionados: `07_TRANSACTION_BOUNDARIES`, `05_SESSION_LIFECYCLE`.
