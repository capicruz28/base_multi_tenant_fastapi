# 02 — Storage Metadata Resolution

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** E3 Canonical Data Model, E4 RD-08, G-13  
**Restricción:** Diseño técnico. Sin SQL, código ni pseudocódigo.

---

## 1. Propósito

Definir cómo la infraestructura **obtiene, interpreta, cachea e invalida** la metadata que determina dónde persiste cada tenant (Shared vs Dedicated).

---

## 2. Fuentes de verdad

| Dato | Plano | Almacén autoritativo | Consumidor |
|------|-------|---------------------|------------|
| Tenant Registry (existencia, subdominio, estado) | Control Plane | Control Plane Store | Tenant Middleware, gateway |
| Installation Mode | Control Plane | Control Plane Store | Gateway L6 exclusivamente |
| Storage Endpoint Metadata | Control Plane | Control Plane Store (`cliente_conexion` AS-IS) | Connection Resolution |
| Provisioning State | Control Plane | Control Plane Store | Saga onboarding, migration |

**Principio E3:** Installation Mode y Storage Endpoint Metadata son **Control Plane**. Nunca residen en Tenant Data Store del tenant.

---

## 3. Modelo conceptual de metadata

### 3.1 Registro de tenant (Tenant Registry entry)

| Campo conceptual | Uso en resolución |
|------------------|-------------------|
| Identificador tenant | Clave primaria de resolución |
| Subdominio | Lookup Host → tenant |
| Estado lifecycle | Activo / Provisioning / Migrando / Suspendido / Retirado |
| Installation Mode | `shared` \| `dedicated` \| futuro `on_premise` |

### 3.2 Registro de almacén (Storage Endpoint entry)

Presente cuando Installation Mode ≠ shared puro:

| Campo conceptual | Uso |
|------------------|-----|
| Identificador tenant (FK) | Vincula metadata a tenant |
| Servidor / host | Endpoint físico dedicated |
| Nombre base de datos | Catálogo SQL Server destino |
| Credenciales | Autenticación (cifradas en CP) |
| Versión schema aplicada | Validación post-provisioning |
| Estado conexión | Activa / Pendiente / Error |
| Región (futuro) | Multi-region routing |

### 3.3 Metadata derivada (no persistida)

| Derivado | Cálculo |
|----------|---------|
| Route binding | `(tenant_id, operation_class) → {store_type, engine_key, connection_params}` |
| Tenant filter policy | `shared → enforce cliente_id`; `dedicated → policy encapsulada L6` |
| Fallback eligibility | Metadata ausente + mode ≠ dedicated → shared |

---

## 4. Mapeo AS-IS → canónico

| Concepto canónico | Representación AS-IS |
|-------------------|---------------------|
| Installation Mode `shared` | `database_type = "single"` |
| Installation Mode `dedicated` | `database_type = "multi"` + fila `cliente_conexion` |
| Storage Endpoint Metadata | Campos `cliente_conexion` (servidor, nombre_bd, credenciales) |
| Metadata cache | `core/tenant/cache.py` |

**Nota:** La nomenclatura AS-IS (`single`/`multi`) es **implementación legacy**. El diseño canónico usa `shared`/`dedicated`. La traducción ocurre exclusivamente en L6.

---

## 5. Flujo de resolución

### 5.1 Trigger

Metadata se consulta cuando el Persistence Gateway necesita resolver ruta para operación `tenant_data` y no existe binding válido en cache intra-request.

### 5.2 Secuencia

```
1. Verificar cache proceso (tenant metadata cache)
   → HIT: retornar metadata
   → MISS: continuar

2. Consultar Control Plane Store
   → Leer Installation Mode + Storage Endpoint (si aplica)
   → Usar operación control_plane (ADMIN route)

3. Validar estado tenant
   → Provisioning: política según operación (ver 11)
   → Migrando: bloqueo ERP (RD-13)
   → Retirado: rechazo

4. Construir route binding
   → shared: DEFAULT → credenciales globales settings
   → dedicated: DEFAULT → credenciales Storage Endpoint

5. Almacenar en cache proceso con TTL
6. Retornar binding al Connection Resolution
```

### 5.3 Chicken-and-egg

La lectura inicial de metadata **requiere** acceso a Control Plane Store. AS-IS resuelve esto consultando ADMIN sin metadata previa. Este patrón se **preserva**: metadata lookup nunca depende de tenant-data store del tenant objetivo.

---

## 6. Políticas de fallback (RD-08, G-13)

| Condición | Acción |
|-----------|--------|
| Metadata ausente + mode implícito shared / legacy | Fallback a Shared (settings globales) |
| Metadata ausente + mode explícito dedicated | **Error** — no fallback silencioso (RI-39) |
| Metadata corrupta / credenciales inválidas | Error mapeado; retry no automático en request |
| Storage Endpoint estado Error | Error; alerta ops; tenant puede quedar Suspendido |

---

## 7. Cache strategy

### 7.1 Niveles de cache

| Nivel | Scope | Contenido | Invalidación |
|-------|-------|-----------|--------------|
| **L-A: Intra-request** | Request HTTP | Route binding resuelto | Teardown request |
| **L-B: Proceso worker** | Worker uvicorn/gunicorn | Storage Metadata por tenant_id | TTL + eventos explícitos |
| **L-C: No cache** | — | Credenciales desencriptadas | Nunca cachear plaintext |

### 7.2 TTL recomendado (decisión técnica TD-02)

| Cache | TTL default | Justificación |
|-------|-------------|---------------|
| Metadata proceso | 5–15 minutos | Balance freshness vs carga CP |
| Route binding intra-request | Vida del request | RD-01 |

**Configurable vía settings** sin hardcode en L5.

### 7.3 Eventos de invalidación obligatorios

| Evento | Acción |
|--------|--------|
| Provisioning dedicated completado | Invalidar tenant_id |
| Migración Shared→Dedicated cutover | Invalidar + dispose engine tenant |
| Cambio credenciales Storage Endpoint | Invalidar + dispose engine |
| Rollback migración | Invalidar + restaurar mode shared |
| Actualización manual ops | API/hook invalidación explícita |

---

## 8. Interacción con Tenant Middleware

| Aspecto | Decisión |
|---------|----------|
| Middleware carga metadata en startup request | **Permitido** para optimización |
| Middleware expone Installation Mode a L5 | **Prohibido** (RD-03) |
| Middleware usa metadata solo para validación tenant activo | Sí |
| Duplicación lookup middleware + gateway | Aceptable si L-A cache evita doble consulta CP |

**Gap AS-IS (RR-81):** Middleware popula `TenantContext.database_type`. Remediación: middleware puede cargar metadata internamente pero **no publicar mode** en contexto consumible por L5.

---

## 9. Estados lifecycle y resolución

| Estado tenant | Metadata resolution | ERP tenant_data |
|---------------|--------------------|--------------------|
| Activo | Normal | Permitido |
| Provisioning | Parcial; dedicated pendiente | Limitado a ops saga |
| Migrando | Frozen; mode transition | **Bloqueado** (RD-13) |
| Suspendido | Readable; mutaciones bloqueadas L5 | Lectura según policy |
| Retirado | Rechazo autenticación | N/A |

---

## 10. Preguntas abiertas

| ID | Pregunta | Impacto |
|----|----------|---------|
| O-E5-01 | ¿Metadata cache distribuido (Redis) vs solo proceso? | Multi-worker consistency |
| O-E5-02 | ¿Versionado schema en metadata obligatorio day-1? | Provisioning validation |
| O-E5-03 | ¿On-Premise metadata incluye VPN/tunnel config? | Extensión futura |

---

## 11. Riesgos

| ID | Riesgo | Mitigación diseño |
|----|--------|-------------------|
| TR-01 | Cache stale post-migración | Invalidación event-driven obligatoria |
| TR-02 | Fallback shared en tenant dedicated mal configurado | RI-39: fail explicit |
| TR-03 | Metadata lookup amplifica carga CP | TTL + L-A cache |
| TR-04 | Credenciales en logs | Nunca loggear Storage Endpoint secrets |

---

## 12. Conclusión

Storage Metadata Resolution es el **primer paso del pipeline L6**: traduce identidad tenant en decisión de almacén. Vive en Control Plane, se cachea agresivamente, e invalida en eventos de lifecycle.

Documentos relacionados: `03_CONNECTION_RESOLUTION`, `10_ENGINE_CACHE_POLICY`.
