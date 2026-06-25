# 05 — Session Lifecycle

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** AS-IS SQLAlchemy audit, G-17, RD-01  
**Restricción:** Ciclo de vida AsyncSession SQLAlchemy. Sin código.

**Nota terminológica:** Este documento trata **sesiones de base de datos** (SQLAlchemy AsyncSession). Las **sesiones IAM** (tokens, user sessions) se referencian solo donde intersectan con persistencia (RD-11 abierta).

---

## 1. Propósito

Definir cómo se **abren, utilizan, confirman, revierten y cierran** las sesiones SQLAlchemy dentro del Persistence Gateway.

---

## 2. Principios

| # | Principio |
|---|-----------|
| SL-01 | **No existe sesión global por request HTTP** — preservar AS-IS |
| SL-02 | **No introducir** SessionLocal, scoped_session, Depends(get_db) |
| SL-03 | Cada operación atómica abre y cierra su propia sesión salvo UoW |
| SL-04 | Sesión nunca sobrevive al scope que la creó |
| SL-05 | `expire_on_commit=False` — preservar AS-IS para Core dict results |
| SL-06 | Sessionmaker se instancia por apertura (AS-IS) — optimizable post-MVP |

---

## 3. Patrones de lifecycle

### 3.1 Operación atómica (execute_*)

```
Abrir sesión sobre engine resuelto
  → Ejecutar SQL
  → SELECT: sin commit
  → INSERT/UPDATE/DELETE: commit automático
  → Excepción: rollback
  → Finally: close sesión
```

| Aspecto | Valor |
|---------|-------|
| Scope | Una llamada execute_* |
| Transacciones | Auto-commit mutaciones |
| Conexiones simultáneas mismo request | **Múltiples** (una por execute_*) |

### 3.2 Unit of Work

```
Abrir sesión al entrar scope UoW
  → Múltiples execute internos sin commit intermedio
  → Éxito: commit al salir
  → Excepción: rollback al salir
  → Finally: close sesión
```

| Aspecto | Valor |
|---------|-------|
| Scope | Bloque async with UoW |
| Transacciones | Commit único al final |
| Reutilización engine | Mismo engine; una sesión |

### 3.3 Conexión explícita (control_plane / onboarding)

```
Abrir sesión vía get_db_connection
  → Caller ejecuta SQL directo o begin()
  → Caller decide commit (session.begin() o manual)
  → Excepción: rollback
  → Finally: close sesión
```

| Aspecto | Valor |
|---------|-------|
| Scope | async with get_db_connection |
| Uso | Onboarding, bootstrap, scripts |
| Commit | **Responsabilidad caller** |

---

## 4. Relación engine ↔ sesión

| Recurso | Scope | Cantidad típica por request ERP |
|---------|-------|--------------------------------|
| AsyncEngine | Proceso worker | 1 (shared) o 1 (dedicated) |
| AsyncSession | Operación / UoW | N (una por execute_*) |

**Implicación performance:** Endpoint ERP con 5 queries sin UoW = 5 checkouts pool. **No cambiar en MVP** — UoW disponible donde se requiera atomicidad.

---

## 5. Propagación de sesión externa (caso especial)

AS-IS: algunos repositories aceptan sesión externa (ej. secuencias config). Reglas:

| Regla | Descripción |
|-------|-------------|
| SR-01 | Sesión externa solo dentro mismo scope UoW o transacción explícita |
| SR-02 | Gateway no abre segunda sesión si sesión externa provista |
| SR-03 | Caller externo responsable de commit/rollback |
| SR-04 | Prohibido pasar sesión entre requests |

---

## 6. Interacción con tenant filter y auditor

| Fase | Acción |
|------|--------|
| Pre-open | Resolver connection binding |
| Pre-execute | apply_tenant_filter (tenant_data shared) |
| Pre-execute | QueryAuditor validación (producción) |
| Post-execute | Result mapping |
| Close | Liberar conexión al pool |

Orden **invariable** — filter antes de execute.

---

## 7. Sesiones IAM vs sesiones SQL

| Concepto | Persistencia | Decisión |
|----------|--------------|----------|
| User Session V2 (IAM) | Transversal — **RD-11 abierta** | Ruta L6 TBD |
| Refresh token family | Idem | Idem |
| AsyncSession SQL | Siempre efímera operación | Este documento |

**Comportamiento independiente de RD-11:** AsyncSession lifecycle **no cambia** según ubicación store sesiones IAM. Solo cambia Connection Binding previo.

---

## 8. Background jobs

| Aspecto | Regla |
|---------|-------|
| ContextVar tenant | **No disponible** — inyectar tenant_id explícito |
| Sesión | Mismo patrón execute_* o UoW |
| Scope | Una sesión por iteración job |
| Cleanup | Close garantizado en finally |

---

## 9. Errores y recovery

| Error | Acción sesión |
|-------|---------------|
| SQL timeout | Rollback si transacción abierta; close |
| Connection lost | Rollback; close; no retry automático mismo execute |
| Pool timeout | Propagar error mapeado; métrica |
| Commit failure | Rollback; close; propagar |

Detalle recovery: `11_FAILURE_RECOVERY.md`.

---

## 10. Gap AS-IS

| ID | Gap |
|----|-----|
| SL-G01 | sessionmaker recreado cada apertura — overhead menor |
| SL-G02 | Múltiples sesiones por endpoint — N+1 conexiones |
| SL-G03 | ENABLE_UNIT_OF_WORK setting sin enforcement |
| SL-G04 | auth/endpoints Azure AD path potencialmente roto (sync deprecated) |

---

## 11. Decisiones técnicas

| ID | Decisión |
|----|----------|
| TD-05 | No introducir request-scoped session en MVP |
| TD-06 | Preservar auto-commit execute_* mutaciones |
| TD-07 | UoW semantics unchanged (G-18) |

---

## 12. Conclusión

Session Lifecycle mantiene el modelo **sesión por operación** AS-IS, con UoW para atomicidad multi-paso. Es agnóstico a Shared/Dedicated — la variación ocurre upstream en Connection Resolution.

Documentos relacionados: `06_UNIT_OF_WORK_DESIGN`, `07_TRANSACTION_BOUNDARIES`, `08_QUERY_EXECUTION_MODEL`.
