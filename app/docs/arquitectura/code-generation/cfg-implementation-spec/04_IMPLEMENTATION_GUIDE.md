# Guía de implementación — orden oficial v1.0

**Paquete:** `cfg-implementation-spec`  
**Versión:** 1.0  
**Precondición:** autorización explícita del usuario para escribir código

---

## 1. Principios de ejecución

1. Seguir **solo** este paquete `cfg-implementation-spec/` v1.0.  
2. No reabrir G-01…G-06 ni paquetes históricos.  
3. No modificar Motor, ORG, INV.  
4. No extender `CfgCodigoSecuenciaRepository` (**G-06**).  
5. OpenAPI snapshot solo al final, cuando endpoints estén estables.

---

## 2. Orden exacto de pasos

| Paso | Trabajo | Criterio de hecho |
|------|---------|-------------------|
| **1** | Seed RBAC `cfg.secuencias.consultar` + `cfg.secuencias.actualizar` + grant ADMIN_TENANT | Permisos existen en entorno |
| **2** | Esqueleto `app/modules/cfg/` + `queries/cfg/` | Imports OK |
| **3** | `presentation/schemas.py` | Read, Update, Preview, Paginated |
| **4** | `cfg_deps.py` | session client id + tenant ERP session |
| **5** | `codigo_secuencia_queries.py` | list (sin page SQL), get, update config, set activo |
| **6** | Enrich + validaciones (funcs en service/support) | BR de `03` |
| **7** | Services GET list + detail | Pipeline G-04 |
| **8** | `router.py` + endpoints GET + mount `api.py` | 200 list/detail |
| **9** | Tests unitarios lectura + aislamiento | Ver `05` |
| **10** | Services PATCH + DELETE soft + reactivar | org_empresa lock |
| **11** | Endpoints mutación | |
| **12** | Tests mutación | |
| **13** | Service + endpoint preview | Gateway; inactiva 200 |
| **14** | Tests preview sin side-effect | |
| **15** | Actualizar OpenAPI snapshot | Contratos `02` |
| **16** | Checklist `06` completo | Certificación MVP |

---

## 3. Archivos permitidos a tocar

| Path | Acción |
|------|--------|
| `app/modules/cfg/**` | Crear |
| `app/infrastructure/database/queries/cfg/**` | Crear |
| `app/api/v1/api.py` | include_router |
| Seeds/permisos RBAC (ruta canónica del repo) | Insert/grant |
| `tests/unit/test_cfg_*.py` (y api si aplica) | Crear |
| OpenAPI snapshot | Actualizar en paso 15 |

---

## 4. Archivos prohibidos

| Path |
|------|
| `app/core/codigo/**` |
| `app/modules/org/**` |
| `app/modules/inv/**` |
| `CfgCodigoSecuenciaRepository` (no extender en MVP) |
| Frontend |

---

## 5. Mapeo service ↔ endpoint

| Service | Endpoint |
|---------|----------|
| `list_codigo_secuencias_servicio` | GET `/` |
| `get_codigo_secuencia_servicio` | GET `/{id}` |
| `update_codigo_secuencia_servicio` | PATCH `/{id}` |
| `desactivar_codigo_secuencia_servicio` | DELETE `/{id}` |
| `reactivar_codigo_secuencia_servicio` | POST `/{id}/reactivar` |
| `preview_codigo_secuencia_servicio` | POST `/{id}/preview` |

---

## 6. Notas de implementación concretas

- Preferir propagar `CustomException`; no `except Exception → 500`.  
- PATCH: merge parcial (solo campos enviados).  
- Preview: assert en test que `ultimo_numero` no cambia.  
- Listado: no usar `apply_erp_pagination` en SQL (G-04).  
- Helpers: un solo archivo support opcional; evitar proliferar módulos.

---

## 7. Fuera de esta guía

Align, diagnóstico, Frontend, fiscal, colisión formato, historial audit dedicado.
