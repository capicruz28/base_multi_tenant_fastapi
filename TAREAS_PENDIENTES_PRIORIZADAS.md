# 📋 Tareas Pendientes Priorizadas

**Fecha:** Diciembre 2024  
**Estado:** Revisión y priorización completada

---

## 🔴 PRIORIDAD CRÍTICA (Hacer Ahora)

### 1. Ejecutar Script de Índices en BD
**Tiempo estimado:** 15 minutos  
**Riesgo:** Bajo  
**Impacto:** Alto (30-60% mejora en queries)

```sql
USE [tu_base_datos];
GO
:r app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql
```

**Acción:** Ejecutar en horario de bajo tráfico

---

### 2. Activar Validación Estricta en Producción
**Tiempo estimado:** 5 minutos  
**Riesgo:** Bajo (si tests pasan)  
**Impacto:** Alto (seguridad)

```env
ENABLE_QUERY_TENANT_VALIDATION=true
ALLOW_TENANT_FILTER_BYPASS=false
```

**Acción:** Activar después de probar en desarrollo

---

## 🟡 PRIORIDAD ALTA (Esta Semana)

### 3. Migrar Archivos Críticos de Auth
**Tiempo estimado:** 2-3 horas  
**Riesgo:** Medio  
**Impacto:** Alto (seguridad y performance)

**Archivos:**
- `app/core/auth/user_builder.py` - Tiene ejecuciones síncronas
- `app/core/auth/user_context.py` - Tiene ejecuciones síncronas

**Acción:** Seguir guía en `docs/MIGRACION_LEGACY_CODE.md`

---

### 4. Ejecutar Tests de Seguridad
**Tiempo estimado:** 30 minutos  
**Riesgo:** Ninguno  
**Impacto:** Medio (validación)

```bash
pytest tests/security/ -v
pytest tests/unit/ -v
```

**Acción:** Ejecutar antes de activar validación estricta

---

## 🟢 PRIORIDAD MEDIA (Este Mes)

### 5. Migrar Resto de Código Legacy
**Tiempo estimado:** 1-2 semanas  
**Riesgo:** Medio  
**Impacto:** Medio (mantenibilidad)

**Archivos identificados:** 23 archivos  
**Herramienta:** `python scripts/analyze_legacy_code.py`

**Acción:** Migrar gradualmente, empezar con servicios más usados

---

### 6. Integrar Métricas en Endpoints
**Tiempo estimado:** 2-3 horas  
**Riesgo:** Bajo  
**Impacto:** Medio (monitoreo)

**Archivos creados:**
- `app/core/metrics/basic_metrics.py` ✅
- `app/api/metrics_endpoint.py` ✅

**Acción:** Agregar router a `main.py` y probar

---

### 7. Expandir Tests
**Tiempo estimado:** 1 semana  
**Riesgo:** Bajo  
**Impacto:** Medio (calidad)

**Tests a crear:**
- Tests de integración para servicios críticos
- Tests de performance básicos
- Tests de carga (opcional)

---

## 🔵 PRIORIDAD BAJA (Futuro)

### 8. Eliminar queries.py Completamente
**Tiempo estimado:** 1 día  
**Riesgo:** Bajo (después de migración completa)  
**Impacto:** Bajo (limpieza)

**Acción:** Solo después de migrar todos los archivos

---

### 9. Monitoreo Avanzado
**Tiempo estimado:** 1-2 semanas  
**Riesgo:** Bajo  
**Impacto:** Medio (observabilidad)

**Opciones:**
- Integrar Prometheus
- Dashboard de métricas
- Alertas automáticas

---

## 📊 Resumen de Prioridades

| Prioridad | Tareas | Tiempo Total | Impacto |
|-----------|--------|--------------|---------|
| 🔴 Crítica | 2 | ~20 min | Alto |
| 🟡 Alta | 2 | ~3 horas | Alto |
| 🟢 Media | 3 | ~3 semanas | Medio |
| 🔵 Baja | 2 | ~3 semanas | Bajo |

---

## ✅ Checklist Rápido

### Esta Semana
- [ ] Ejecutar script de índices en BD
- [ ] Ejecutar tests de seguridad
- [ ] Activar validación estricta (si tests pasan)
- [ ] Migrar user_builder.py y user_context.py

### Este Mes
- [ ] Integrar métricas en main.py
- [ ] Migrar 5-10 archivos legacy más
- [ ] Expandir tests básicos

### Futuro
- [ ] Completar migración de código legacy
- [ ] Eliminar queries.py
- [ ] Monitoreo avanzado

---

**Última actualización:** Diciembre 2024


