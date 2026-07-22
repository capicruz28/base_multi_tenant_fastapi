# Checklist de regresión — integración plataforma CFG

---

## 1. Matriz riesgo / impacto / dependencia (por punto)

| Punto | Riesgo | Impacto | Dependencia |
|-------|--------|---------|-------------|
| S010 sin UUID/código únicos | Colisión / onboarding no encuentra módulo | Alto | Antes de trial |
| S010 sin menú visible | OwnerSync 0 RMP; menú vacío CFG | Alto | Ruta + es_visible |
| S021 sin `/cfg/%` y ruta corta | BD queda `/cfg/...`; FE puede vivir del normalizer, pero BD desalineada | Medio | Decisión ruta seed |
| `TRIAL_MODULES` sin S010 | `ONBOARDING_MODULOS_BASE_NOT_FOUND` | Bloqueante | Fase 1 antes Fase 3 |
| Health floor 18 sin bump | False negative repair/health | Medio | Contar menús CFG |
| Añadir CFG a Manager/User | Viola “solo ADMIN_TENANT” | Alto | **No hacer** |
| Dedicated sin S068 en profile | 403 API cfg en tenants Dedicated nuevos | Alto | Fase 2 |
| Checksum S010 viejo | Fallo provision Dedicated | Alto | Tras editar S010 |
| `modulo` count 27 | Fallo row_expectations | Medio | 28 |
| Solo `cliente_modulo` sin OwnerSync (activate manual) | Menú no aparece | Medio | Sync al activar o repair |
| Tocar S068 / OpenAPI | Fuera de alcance / regresión contrato | Alto | **No hacer** |
| Meter CFG en S020 | Mezcla con IAM; rompe patrón aprobado | Alto | **No hacer** |
| R020 modificado para CFG | Pipeline incorrecto vs ORG/INV | Medio | Usar trial Python |

---

## 2. Checklist funcional post-implementación

### Catálogo

- [ ] `modulo.codigo = 'CFG'` existe y activo  
- [ ] Sección CFG activa  
- [ ] `modulo_menu` con ruta efectiva `/app/cfg/secuencias`  
- [ ] S020 **sin** entradas CFG nuevas  

### Bootstrap / Dedicated

- [ ] S021 cubre `/cfg/%` (si aplica)  
- [ ] `catalog_profiles` incluye S068  
- [ ] Checksum S010 actualizado  
- [ ] Expectation `modulo` = 28  

### Onboarding / trial

- [ ] `TRIAL_MODULES` contiene `CFG`  
- [ ] Tenant nuevo: fila `cliente_modulo` CFG  
- [ ] ADMIN_TENANT: RMP menú CFG `puede_ver=1`  
- [ ] ADMIN_TENANT: RP `cfg.secuencias.consultar` (+ actualizar)  
- [ ] Manager/User: **sin** RMP CFG  
- [ ] Health floor actualizado  

### Menú / API

- [ ] `GET /auth/menu` → módulo CFG presente  
- [ ] Ruta ítem = `/app/cfg/secuencias`  
- [ ] `GET /auth/permissions/me` incluye códigos cfg  
- [ ] `GET /api/v1/cfg/secuencias` OK para admin  
- [ ] Manager sin permiso cfg → 403 API y sin menú  

### Regresión ORG / INV / IAM

- [ ] Menús ORG (`/app/org/...`) intactos  
- [ ] Menús INV intactos  
- [ ] `SYS_ADMIN.TENANT.*` (`/admin/...`) intactos  
- [ ] Conteo trial owner ≥ floor nuevo; ORG+INV+TENANT no reducidos  
- [ ] Login Manager sigue viendo solo su bundle ORG/INV  

### Shared + Dedicated

- [ ] Smoke Shared PASS  
- [ ] Smoke Dedicated PASS  
- [ ] Impersonación menú CFG PASS  

---

## 3. Checklist negativo (no regresiones de alcance)

- [ ] Ningún cambio OpenAPI CFG  
- [ ] Ningún permiso nuevo  
- [ ] Ninguna ruta FE `/admin` para CFG  
- [ ] Ningún cambio de contratos `frontend-contracts/cfg`  
- [ ] Seed datos `cfg_codigo_secuencia` sigue funcionando (orquestador)  

---

## 4. Criterio de cierre del plan

El plan de integración plataforma se considera **ejecutado con éxito** cuando las secciones 2 y 3 están PASS en Shared y Dedicated, sin haber alterado las decisiones aprobadas listadas en `00_EXECUTIVE_SUMMARY.md`.
