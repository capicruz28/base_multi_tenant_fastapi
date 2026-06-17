# Decisión arquitectónica — Estrategia bootstrap plataforma

**Tipo:** Comparativa y recomendación (sin implementación)  
**Fecha:** 2026-06-05  
**Contexto:** Auditoría aprobada en [`PLATFORM_BOOTSTRAP_AUTOMATION_AUDIT.md`](PLATFORM_BOOTSTRAP_AUTOMATION_AUDIT.md)  
**Pregunta:** ¿Bootstrap plataforma en startup FastAPI o solo vía CLI explícita?

**Estrategia candidata (preferencia inicial):**

```text
bootstrap_v2_sql_apply.ps1
        ↓
Primer arranque FastAPI (permission_sync únicamente)
        ↓
bootstrap_platform.py --apply
        ↓
Login superadmin
```

---

## 1. Resumen ejecutivo

| Estrategia | Veredicto |
|------------|-----------|
| **A — Automático en startup** | Potente para DX; añade responsabilidad de identidad al runtime de la API; riesgos en multi-réplica y prod |
| **B — CLI explícito (`bootstrap_platform.py --apply`)** | **Recomendada** — elimina D010 y `repair_platform_rbac.py`, mantiene startup simple, alinea con separación bootstrap vs runtime |

**Conclusión:** la estrategia candidata **es suficiente** para eliminar pasos manuales D010 y `repair_platform_rbac.py`, siempre que el CLI unifique identidad + RBAC en un solo comando idempotente documentado en el runbook de instalación.

**No se recomienda** implementar bootstrap de identidad plataforma dentro del lifespan FastAPI en la fase inicial (MVP). Opcional como mejora futura solo si hay demanda operativa demostrada.

---

## 2. Definición de las dos estrategias

### Estrategia A — Bootstrap automático post-`permission_sync`

```text
docker compose up
    → permission_sync
    → PlatformBootstrapOrchestrator.ensure_platform_ready()  [dentro del lifespan]
    → API lista + plataforma provisionada
```

- Un solo comando de arranque para el operador.
- Feature flags: `PLATFORM_BOOTSTRAP_ENABLED`, password env, etc.
- La API asume rol de **instalador** además de **servidor**.

### Estrategia B — Bootstrap explícito vía CLI

```text
bootstrap_v2_sql_apply.ps1
docker compose up                    # solo permission_sync
bootstrap_platform.py --apply      # paso explícito, una vez (o recovery)
```

- FastAPI permanece **read-only respecto a identidad plataforma** en startup.
- El CLI es el **único canal oficial** de provisión/reparación plataforma.
- `repair_platform_rbac.py` se **absorbe** en `bootstrap_platform.py` (modo `--rbac-only` opcional para compatibilidad).

---

## 3. Comparación detallada

### 3.1 Instalación inicial

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| Pasos del operador | 2 (SQL + up) | 3 (SQL + up + CLI) |
| Elimina D010 manual | ✅ | ✅ |
| Elimina repair manual | ✅ | ✅ |
| Curva de aprendizaje | Baja (menos pasos) | Media (un paso extra documentado) |
| Orden obligatorio | Implícito (sync antes de bootstrap) | **Explícito** — operador debe arrancar API antes del CLI (catálogo `permiso`) |
| Documentación | Runbook más corto | Runbook con checklist de 3 pasos |

**Análisis:** A gana en conteo de pasos. B gana en **claridad del orden** (SQL → sync → identidad). El paso extra del CLI es equivalente operativamente a ejecutar `repair_platform_rbac.py` hoy, pero unificado y sin extracción D010.

**Empate operativo** si B está bien documentado en `DEPLOYMENT_FIRST_INSTALL_GUIDE.md`.

---

### 3.2 Producción

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| Principio de mínimo privilegio runtime | ❌ API crea usuarios al arrancar | ✅ API no muta identidad en boot |
| Superficie de ataque | Mayor (password env en contenedor API) | Menor (password solo en job CLI puntual) |
| Blast radius de misconfiguración | Alto — cada restart puede re-ejecutar lógica | Bajo — bootstrap es evento controlado |
| Cambio de password superadmin | Riesgo si lógica no es estrictamente idempotente | Sin riesgo en restarts normales |
| Aprobación change management | Bootstrap mezclado con deploy app | Bootstrap = job DBA/ops separado del deploy |
| Opt-in prod | Requiere flags + validación estricta | **Natural** — CLI no se ejecuta salvo install/recovery |

**Análisis:** B es **claramente preferible** en producción. La creación de identidad administrativa es una operación de **provisionamiento**, no de **runtime de aplicación**. Separarla reduce riesgo y facilita auditorías de seguridad.

---

### 3.3 Docker

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| `docker compose up` suficiente | ✅ | ❌ requiere `docker exec … bootstrap_platform.py` |
| Dockerfile / entrypoint | Sin cambios | Sin cambios |
| Init container pattern | No necesario | **Opcional** — contenedor `bootstrap` one-shot en compose |
| CI/CD pipeline | Un stage | Dos stages (deploy + bootstrap job) o init container |
| Imagen única | Sí | Sí |

**Patrón Docker recomendado con B:**

```text
# Opción B1 — Manual post-up (install doc)
docker compose up -d
docker exec … python scripts/bootstrap_platform.py --apply

# Opción B2 — Init service (compose, profile install)
services:
  platform-bootstrap:
    profiles: ["install"]
    depends_on: [backend]
    command: python scripts/bootstrap_platform.py --apply
    restart: "no"
```

**Análisis:** A es más cómodo en Docker dev. B con **profile `install`** en compose cierra la brecha sin meter lógica en el lifespan del backend. Para prod Kubernetes: **Job** one-shot es el equivalente natural de B.

---

### 3.4 Multi-réplica

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| N réplicas arrancando simultáneamente | N ejecuciones concurrentes del bootstrap | 1 ejecución (CLI/Job) |
| Condiciones de carrera | Posibles en INSERT cliente/rol/usuario | Evitadas (single runner) |
| Dependencia de UNIQUE constraints BD | Alta (para corregir races) | Baja |
| Logs duplicados / ruido | N × `[PLATFORM] Bootstrap` | 1 × salida CLI |
| Rolling deploy | Re-ejecuta bootstrap en cada pod nuevo* | No re-ejecuta en deploy normal |

\*Incluso idempotente, cada rolling update dispara la lógica — ruido operativo y carga innecesaria.

**Análisis:** B es **superior** en multi-réplica. El bootstrap de identidad es inherentemente **singleton**; un CLI/Job lo expresa correctamente. A requiere defensas extra (locks, advisory locks SQL, leader election) para ser robusto — complejidad no justificada.

---

### 3.5 Recuperación ante desastres (DR)

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| BD restaurada sin filas plataforma | Auto-repara al primer up de cualquier réplica | Operador ejecuta CLI tras restore |
| BD restaurada desde backup con plataforma OK | Idempotente, no-op | Idempotente, no-op |
| Runbook DR | "Levantar stack" | "Levantar stack + bootstrap_platform --apply si audit falla" |
| Detección de estado | Implícita en logs startup | **`--audit-only`** explícito antes de apply |
| Control del momento de mutación | No controlable | Controlable (ventana de mantenimiento) |

**Análisis:** B favorece **control explícito** en DR — deseable cuando se restaura BD y se quiere auditar antes de mutar. A puede ser conveniente pero opaco (¿reparó o ya estaba OK?).

Comando DR propuesto con B:

```text
bootstrap_platform.py --audit-only   → evaluar
bootstrap_platform.py --apply        → reparar si needs_bootstrap
```

---

### 3.6 Auditoría operativa

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| Trazabilidad "quién creó superadmin" | Logs app mezclados con tráfico | **Job CLI** con timestamp, operador, exit code |
| Evidencia para compliance | Extraer de logs startup multirréplica | Artefacto JSON (`--json-out`) de una ejecución |
| Separación bootstrap vs operación | ❌ Mezclado | ✅ Fase install vs fase run |
| `--audit-only` en CI/CD gate | Difícil (requiere API up + parse logs) | **Natural** — script exit 0/1 |
| Correlación con despliegues | Confuso en rolling updates | Clara — bootstrap no es parte del deploy loop |

**Análisis:** B es **preferible** para auditoría. Las operaciones de provisionamiento deben ser **eventos discretos** con salida estructurada, no efectos secundarios del arranque.

---

### 3.7 Idempotencia

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| Mecanismo idempotente | Mismo código, distinto contexto de invocación | Mismo código |
| Frecuencia de ejecución | Cada restart / cada réplica / cada scale-out | Install + recovery manual |
| Riesgo regresión silenciosa | Mayor (más invocaciones = más superficie de bug) | Menor |
| Verificación post-ejecución | Parse logs | Exit code + JSON audit |

**Análisis:** La idempotencia es **propiedad del servicio**, no de la estrategia de invocación. Pero B **reduce la frecuencia** de ejecución, lo que disminuye probabilidad de bugs latentes y facilita testing.

---

### 3.8 Mantenibilidad

| Criterio | A — Startup automático | B — CLI explícito |
|----------|------------------------|-------------------|
| Responsabilidad `main.py` / lifespan | Crece (RBAC sync + platform identity) | **Estable** (solo RBAC sync) |
| Testing startup | Más pesado (mock BD en lifespan) | Tests del CLI aislados |
| Onboarding mental del dev | "La app se auto-instala" | "SQL + up + bootstrap script" — explícito |
| Acoplamiento install/runtime | Alto | **Bajo** |
| Deprecación repair + D010 | Sí | Sí |
| Evolución futura (K8s Job, Terraform) | Requiere desactivar startup y migrar a CLI | **Ya alineado** |

**Análisis:** B mantiene el startup FastAPI enfocado en su responsabilidad core: **servir API + sincronizar permisos code-first**. La provisión de identidad es otro bounded context.

---

## 4. Matriz de puntuación cualitativa

Escala: ⭐⭐⭐ excelente · ⭐⭐ aceptable · ⭐ débil

| Dimensión | A — Startup | B — CLI |
|-----------|:-----------:|:-------:|
| Instalación inicial (simplicidad) | ⭐⭐⭐ | ⭐⭐ |
| Producción (seguridad/separación) | ⭐ | ⭐⭐⭐ |
| Docker (sin compose extra) | ⭐⭐⭐ | ⭐⭐ |
| Multi-réplica | ⭐ | ⭐⭐⭐ |
| DR / recovery | ⭐⭐ | ⭐⭐⭐ |
| Auditoría operativa | ⭐ | ⭐⭐⭐ |
| Idempotencia (robustez práctica) | ⭐⭐ | ⭐⭐⭐ |
| Mantenibilidad | ⭐⭐ | ⭐⭐⭐ |

**Total cualitativo:** B gana en 6/8 dimensiones. A gana en simplicidad de primer install y conveniencia Docker dev puro.

---

## 5. ¿La estrategia B elimina D010 y repair?

### Sí, si `bootstrap_platform.py` implementa el orquestador completo

| Artefacto legacy | Reemplazo |
|------------------|-----------|
| Extracción bloques A–E D010 | `PlatformIdentityBootstrapService` dentro del CLI |
| `repair_platform_rbac.py --apply` | Misma invocación: fase RBAC del orquestador |
| `repair_platform_rbac.py --audit-only` | `bootstrap_platform.py --audit-only` |

### Precondiciones (sin cambio respecto a auditoría)

1. `bootstrap_v2_sql_apply.ps1` ejecutado (schema + S010/S020).
2. **Al menos un arranque FastAPI** completado (`permission_sync` → `permiso` > 0).
3. `.env` con `SUPERADMIN_*` y password inicial para prod.
4. Ejecutar `bootstrap_platform.py --apply`.

### Lo que NO hace B (correcto según restricciones)

- No crea tenants.
- No crea datos demo.
- No modifica `bootstrap_v2_sql_apply.ps1`.
- No modifica onboarding tenant.

---

## 6. Runbook objetivo con estrategia B

```text
Fase 0 — Infra
  CREATE DATABASE
  Configurar .env (SUPERADMIN_*, PLATFORM_BOOTSTRAP_INITIAL_PASSWORD en prod)

Fase 1 — Schema SQL
  .\scripts\bootstrap_v2_sql_apply.ps1 ...

Fase 2 — Runtime sync
  docker compose up -d
  Verificar: GET /health → 200
  Verificar: permiso activos > 0 (log permission_sync)

Fase 3 — Bootstrap plataforma (NUEVO — reemplaza D010 + repair)
  docker exec … python scripts/bootstrap_platform.py --audit-only
  docker exec … python scripts/bootstrap_platform.py --apply

Fase 4 — Validación
  python scripts/http_smoke_platform_rbac.py
  Login superadmin

Fase 5 — Primer tenant (sin cambios)
  POST /api/v1/clientes/
```

**Pasos eliminados vs hoy:** extracción D010, sqlcmd platform_min, `repair_platform_rbac.py`.

**Paso añadido vs startup automático:** Fase 3 (equivalente operativo al repair actual, pero completo).

---

## 7. Riesgos de la estrategia B y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|:------------:|------------|
| Operador olvida ejecutar CLI | Media | `--audit-only` en checklist install; smoke CI; health endpoint opcional `GET /internal/platform-ready` **solo lectura** (futuro, no bootstrap) |
| Ejecutar CLI antes de permission_sync | Baja | CLI valida catálogo vacío → error claro `PLATFORM_PERMISSO_CATALOG_EMPTY` |
| Ejecutar CLI sin API levantada | Media | Doc: sync requiere arranque previo; CLI no sustituye permission_sync |
| Dos fuentes de verdad (script vs doc) | Baja | Un solo doc canónico; deprecar `PLATFORM_FIRST_BOOT.md` |

### Sobre health check de plataforma (opcional, no bootstrap)

Un endpoint **read-only** `GET /health/platform` que reporte `ready: true/false` **sin mutar BD** es compatible con B y ayuda a detectar "olvidé el CLI" — distinto de ejecutar bootstrap en startup.

---

## 8. ¿Cuándo reconsiderar startup automático (A)?

Solo si en el futuro se cumplen **todas**:

- Entorno single-replica garantizado (dev local).
- Demanda explícita de "zero-touch install" para demos.
- Feature flag default-off en prod permanente.
- Implementación con lock distribuido probado.

**No recomendado como MVP** dado el contexto actual (prod, Docker, posible multi-réplica).

---

## 9. Decisión arquitectónica final

### Aprobado: Estrategia B — CLI explícito

| Decisión | Detalle |
|----------|---------|
| **Startup FastAPI** | Solo `permission_sync` (sin creación identidad plataforma) |
| **Canal oficial bootstrap** | `scripts/bootstrap_platform.py --apply` |
| **Auditoría pre/post** | `--audit-only`, `--dry-run`, `--json-out` |
| **Deprecar** | D010 manual, `repair_platform_rbac.py` (wrapper temporal → eliminar en fase 2) |
| **Orquestador interno** | `PlatformBootstrapOrchestrator` — invocado **solo desde CLI**, no desde lifespan |
| **Docker prod** | Job/init container con profile `install` o step CI/CD post-deploy |
| **Documentación** | Actualizar runbook install a 3 fases (SQL → up → bootstrap) |

### Rechazado para MVP: Estrategia A — bootstrap en startup

Motivos principales:

1. Mezcla provisionamiento con runtime de API.
2. Problemas prácticos en multi-réplica sin locks adicionales.
3. Peor trazabilidad operativa y auditoría.
4. La ganancia (un paso menos) no compensa la complejidad y riesgo en producción.

### Validación de la preferencia inicial

**La estrategia candidata es suficiente y arquitectónicamente superior** para los objetivos del proyecto:

```text
bootstrap_v2_sql_apply.ps1
→ primer arranque FastAPI
→ bootstrap_platform.py --apply
```

Elimina D010 y `repair_platform_rbac.py` manteniendo una arquitectura **más simple, explícita y alineada con producción**.

---

## 10. Alcance de implementación derivado (referencia, sin código)

| Componente | Incluir en MVP |
|------------|:--------------:|
| `PlatformIdentityBootstrapService` | ✅ |
| `PlatformBootstrapOrchestrator` | ✅ |
| `scripts/bootstrap_platform.py` | ✅ |
| Hook en `permission_startup.py` | ❌ |
| Feature flags startup | ❌ (solo flags CLI: password, email) |
| Endpoint read-only platform-ready | Opcional fase 2 |
| Compose profile `install` | Opcional fase 2 |

---

## 11. Referencias

- [`PLATFORM_BOOTSTRAP_AUTOMATION_AUDIT.md`](PLATFORM_BOOTSTRAP_AUTOMATION_AUDIT.md) — diseño del orquestador (aplicable a B)
- [`PLATFORM_FIRST_BOOT.md`](../PLATFORM_FIRST_BOOT.md) — obsoleto tras implementación B
- [`DEPLOYMENT_FIRST_INSTALL_GUIDE.md`](../DEPLOYMENT_FIRST_INSTALL_GUIDE.md) — actualizar Fase plataforma

---

*Documento de decisión arquitectónica. Sin implementación. Sin commits.*
