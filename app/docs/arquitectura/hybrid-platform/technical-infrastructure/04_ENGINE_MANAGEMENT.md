# 04 — Engine Management

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** AS-IS SQLAlchemy audit, G-17  
**Restricción:** Diseño de ciclo de vida AsyncEngine. Sin código.

---

## 1. Propósito

Definir cómo se **crean, cachean, reutilizan, invalidan y destruyen** los AsyncEngine SQLAlchemy que respaldan el Persistence Gateway.

---

## 2. Estado AS-IS (baseline)

| Aspecto | Comportamiento actual |
|---------|----------------------|
| Driver | `mssql+aioodbc` |
| Cache | Dict proceso `_async_engines` |
| Keys | `"admin"`, `"tenant_{client_id}"` |
| Pool | `pool_size`, `max_overflow`, `pool_recycle`, `pool_pre_ping` desde settings |
| Creación | Lazy on first access per key |
| Shutdown | `close_all_async_engines()` **existe pero no se invoca** |
| Legacy | Pool sync `connection_pool.py` separado |

---

## 3. Principios de diseño

| # | Principio |
|---|-----------|
| EM-01 | Un engine por Connection Binding key único en el proceso worker |
| EM-02 | Engines son **recursos de proceso**, no de request |
| EM-03 | No introducir engine global único para todos los tenants dedicated |
| EM-04 | No introducir engine por request |
| EM-05 | Preservar `pool_pre_ping` para detectar conexiones stale |
| EM-06 | Dispose engine implica drenar pool y recrear en próximo acceso |

---

## 4. Ciclo de vida

### 4.1 Estados de un engine

```
[No existe] → create on first access → [Active]
[Active] → dispose (invalidación) → [Disposed]
[Active] → process shutdown → [Closed]
[Disposed] → next access → create → [Active]
```

### 4.2 Creación

| Trigger | Acción |
|---------|--------|
| Primer acceso a engine key | Construir connection string desde binding → `create_async_engine` |
| Post-dispose access | Recrear con metadata actualizada |

**Parámetros pool:** heredados de settings globales. **Decisión TD-04:** pool sizing uniforme MVP; per-tenant tuning futuro vía metadata opcional.

### 4.3 Reutilización

| Escenario | Comportamiento |
|-----------|----------------|
| Múltiples requests mismo tenant dedicated | Mismo engine; checkout conexiones del pool |
| Múltiples requests shared | Engine compartido (key consolidada TD-03) |
| Múltiples execute_* mismo request | Mismo engine; **sesiones distintas** (ver 05) |

### 4.4 Invalidación (dispose)

| Evento | Acción |
|--------|--------|
| Migración cutover dedicated | Dispose `tenant_{id}` |
| Cambio credenciales | Dispose key afectada |
| Metadata invalidation manual | Dispose keys tenant afectados |
| Error pool exhaustion persistente | Dispose + alert (ops) |

### 4.5 Shutdown proceso

| Acción | Obligatorio Etapa 6 |
|--------|---------------------|
| Invocar cierre todos async engines | **Sí** — cerrar gap AS-IS |
| Invocar cierre pools sync legacy | Preservar AS-IS |
| Orden | Async engines → sync pools |

---

## 5. Engine key strategy (decisión TD-03)

| Modo | Key MVP | Key optimizado (post-MVP) |
|------|---------|---------------------------|
| Control Plane | `admin` | `admin` |
| Shared tenant data | `tenant_{id}` (AS-IS) | `shared_default` (consolidado) |
| Dedicated tenant data | `tenant_{id}` | `tenant_{id}` |

**Trade-off consolidación shared:**

| Pros | Contras |
|------|---------|
| Menos engines en memoria | Cambio comportamiento cache keys |
| Pool compartido más eficiente | Requiere validación no cross-tenant leak |

**Recomendación MVP:** mantener AS-IS keys; consolidación como optimización fase 2 con tests dedicados.

---

## 6. Límites operativos

| Límite | Valor sugerido | Acción al exceder |
|--------|----------------|-------------------|
| Max dedicated engines por worker | Configurable (ej. 50) | LRU dispose o reject + 503 |
| Engine idle timeout | No MVP | Futuro: dispose engines unused |

---

## 7. Multi-worker considerations

| Aspecto | Comportamiento |
|---------|----------------|
| Cache engines | **Local por worker** — no compartido |
| Metadata cache | Local por worker (ver 02 O-E5-01) |
| Dedicated tenant sticky sessions | **No requerido** — cualquier worker resuelve |
| Connection storm al deploy | Gradual warmup; pool_pre_ping |

---

## 8. Observabilidad

| Métrica | Uso |
|---------|-----|
| `engines_active_count` | Por worker |
| `engine_create_total` | Detectar churn |
| `pool_checked_out` | Por engine key |
| `pool_overflow` | Saturation |
| `engine_dispose_total` | Invalidaciones |

Logs: incluir engine key e installation mode; **nunca** connection string completo.

---

## 9. Extensiones futuras

| Extensión | Impacto engine |
|-----------|----------------|
| Read replica | Segundo engine key `{id}_readonly` |
| Multi-Region | Key incluye region suffix |
| On-Premise tunnel | Connection string con params tunnel; engine key unchanged |
| DR secondary | Failover metadata → dispose + recreate |

---

## 10. Gap AS-IS

| ID | Gap |
|----|-----|
| EM-G01 | Async engines no cerrados en shutdown |
| EM-G02 | Keys redundantes shared |
| EM-G03 | Dos sistemas pool (async + sync) coexisten |
| EM-G04 | `DatabaseConnection` enum duplicado en deprecated files |

---

## 11. Conclusión

Engine Management proporciona **AsyncEngine cacheados por proceso** como capa intermedia entre Connection Binding y Session Lifecycle. La estrategia preserva AS-IS con mejoras obligatorias en shutdown e invalidación post-lifecycle events.

Documentos relacionados: `10_ENGINE_CACHE_POLICY`, `03_CONNECTION_RESOLUTION`, `11_FAILURE_RECOVERY`.
