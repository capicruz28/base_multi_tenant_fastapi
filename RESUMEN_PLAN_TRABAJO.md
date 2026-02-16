# 📋 RESUMEN EJECUTIVO - PLAN DE CORRECCIONES CRÍTICAS

**Objetivo:** Preparar el sistema para módulos ERP corrigiendo riesgos críticos  
**Tiempo Total:** 2-3 días  
**Enfoque:** Incremental, seguro, con verificaciones

---

## 🎯 FASES PRINCIPALES

### 🔴 FASE 1: Corregir SSO - Tokens con `cliente_id`
- **Tiempo:** 2-4 horas
- **Riesgo:** BAJO
- **Cambios:** 2 archivos
- **Impacto:** Seguridad crítica para SSO

### 🔴 FASE 2: Auditoría y Corrección de Queries TextClause/String
- **Tiempo:** 1-2 días
- **Riesgo:** MEDIO
- **Cambios:** ~10-15 archivos
- **Impacto:** Previene fuga de datos entre tenants

### 🟡 FASE 3: Validar `menu_id` en BD Dedicada
- **Tiempo:** 4-8 horas
- **Riesgo:** BAJO
- **Cambios:** 3 archivos + 1 nuevo servicio
- **Impacto:** Previene datos huérfanos

### 🟡 FASE 4: Corregir Flujo de `cleanup_expired_tokens`
- **Tiempo:** 2-4 horas
- **Riesgo:** BAJO
- **Cambios:** 1 archivo + 1 nuevo job
- **Impacto:** Limpieza correcta en Multi-DB

---

## ✅ ANTES DE COMENZAR

1. **Backup de código**
   ```bash
   git checkout -b correcciones-criticas-readiness-erp
   ```

2. **Backup de BD**
   - BD Central
   - BD Dedicadas (si aplica)

3. **Verificar ambiente**
   - Servidor funcionando
   - Tests pasando
   - BD accesible

---

## 📊 CRONOGRAMA SUGERIDO

### Día 1
- ✅ Preparación (30 min)
- ✅ Fase 1: SSO (2-4 horas)
- ✅ Fase 3: Validar menu_id (4-8 horas)
- ✅ Verificaciones y tests

### Día 2
- ✅ Fase 2: Auditoría queries (1-2 días)
- ✅ Verificaciones continuas

### Día 3
- ✅ Fase 4: Cleanup tokens (2-4 horas)
- ✅ Tests finales
- ✅ Documentación

---

## 🚨 RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|--------|------------|
| Romper funcionalidad existente | Tests después de cada fase |
| Queries sin filtro de tenant | Auditoría exhaustiva + tests de aislamiento |
| Regresiones | Rollback por fase si algo falla |
| Tiempo insuficiente | Priorizar fases críticas (1, 2, 3) |

---

## ✅ CRITERIOS DE ÉXITO

- ✅ SSO funciona con validación de tenant
- ✅ Todas las queries tienen filtro de tenant
- ✅ `menu_id` se valida en BD dedicadas
- ✅ Cleanup funciona en Single y Multi-DB
- ✅ Tests pasan
- ✅ Sin regresiones

---

## 📝 PRÓXIMOS PASOS

1. **Revisar plan completo** (`PLAN_TRABAJO_CORRECCIONES_CRITICAS.md`)
2. **Confirmar cronograma**
3. **Preparar ambiente** (backups, tests)
4. **Comenzar Fase 1**

---

**¿Listo para proceder?** Confirma y comenzamos con la Fase 1.
