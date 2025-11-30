# 🚀 FASE 1: INSTRUCCIONES DE ACTIVACIÓN

## ✅ IMPLEMENTACIÓN COMPLETA

La Fase 1 (Seguridad Crítica) está **completamente implementada** y lista para usar.

---

## 📦 PASO 1: INSTALAR DEPENDENCIAS

```bash
pip install slowapi==0.1.9
```

O si usas `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🔧 PASO 2: CONFIGURAR VARIABLES DE ENTORNO

### Opción A: Sistema Funciona Igual (Recomendado para empezar)

**No hacer nada.** Los flags están en `False` por defecto, el sistema funciona exactamente igual que antes.

### Opción B: Activar en Desarrollo

Agregar al archivo `.env`:

```env
# Feature Flags - FASE 1: SEGURIDAD
ENABLE_TENANT_TOKEN_VALIDATION=false
ENABLE_QUERY_TENANT_VALIDATION=false
ENABLE_RATE_LIMITING=false

# Configuración de Rate Limiting (solo se usa si ENABLE_RATE_LIMITING=true)
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
```

**Por ahora, dejar todo en `false`** para testing inicial.

---

## 🧪 PASO 3: VERIFICAR QUE TODO FUNCIONA

### 3.1 Iniciar la aplicación

```bash
python -m uvicorn app.main:app --reload
```

### 3.2 Verificar logs

Deberías ver:

```
ℹ️ Módulo de rate limiting cargado pero desactivado (comportamiento por defecto)
ℹ️ Rate limiting desactivado (comportamiento por defecto)
```

**✅ Si ves estos mensajes, todo está bien.**

### 3.3 Probar endpoints

1. **Login:** Debe funcionar normalmente
2. **Obtener usuario:** Debe funcionar normalmente
3. **Cualquier endpoint:** Debe funcionar normalmente

**✅ Si todo funciona igual que antes, la implementación es correcta.**

---

## 🎯 PASO 4: ACTIVAR GRADUALMENTE (CUANDO ESTÉS LISTO)

### 4.1 Activar en Desarrollo (Primero)

```env
# .env (desarrollo)
ENABLE_TENANT_TOKEN_VALIDATION=true
ENABLE_QUERY_TENANT_VALIDATION=true
ENABLE_RATE_LIMITING=true
```

**Reiniciar la aplicación** y monitorear logs:

```bash
# Buscar estos mensajes:
✅ Módulo de rate limiting cargado y activo
✅ Rate limiting configurado y activo
[RATE_LIMITING] Activado. Límites: Login=5/minute, API=100/minute
```

### 4.2 Testing en Desarrollo

1. **Probar login:**
   - Hacer 5 intentos de login → Debe funcionar
   - Hacer 6 intentos rápidos → Debe bloquear (rate limit)

2. **Probar validación de tenant:**
   - Login en tenant A
   - Intentar usar token en tenant B → Debe rechazar (si validación activa)

3. **Monitorear logs:**
   - Buscar advertencias de queries sin filtro de tenant
   - Verificar que no hay errores

### 4.3 Activar en Staging

```env
# .env (staging)
ENABLE_TENANT_TOKEN_VALIDATION=true
ENABLE_QUERY_TENANT_VALIDATION=true
ENABLE_RATE_LIMITING=true
```

**Testing exhaustivo:**
- Probar todos los endpoints
- Verificar que usuarios legítimos no se bloquean
- Verificar que rate limiting no es muy restrictivo

### 4.4 Activar en Producción (Gradual)

**Semana 1:** Monitoreo intensivo
```env
# Activar todos los flags
ENABLE_TENANT_TOKEN_VALIDATION=true
ENABLE_QUERY_TENANT_VALIDATION=true
ENABLE_RATE_LIMITING=true
```

**Monitorear:**
- Número de tokens rechazados
- Número de requests bloqueados por rate limit
- Advertencias de queries sin filtro

---

## 🚨 ROLLBACK INMEDIATO

Si algo falla, simplemente cambiar flags a `false`:

```env
ENABLE_TENANT_TOKEN_VALIDATION=false
ENABLE_QUERY_TENANT_VALIDATION=false
ENABLE_RATE_LIMITING=false
```

**Reiniciar aplicación** → Sistema vuelve al comportamiento anterior en 30 segundos.

---

## 📊 MONITOREO

### Logs a Revisar

1. **Rate Limiting:**
   ```
   Rate limit excedido para IP: X.X.X.X
   ```

2. **Validación de Tenant:**
   ```
   [SECURITY] Token de tenant X usado en tenant Y
   ```

3. **Queries sin Filtro:**
   ```
   [SECURITY] Query sin filtro explícito de cliente_id detectada
   ```

### Métricas

- Requests bloqueados por rate limit (debe ser bajo)
- Tokens rechazados por validación (debe ser 0 para usuarios legítimos)
- Advertencias de queries (revisar y corregir gradualmente)

---

## ✅ CHECKLIST

Antes de activar en producción:

- [ ] ✅ Dependencias instaladas (`slowapi`)
- [ ] ✅ Sistema funciona con flags OFF
- [ ] ✅ Testing en desarrollo exitoso
- [ ] ✅ Testing en staging exitoso
- [ ] ✅ Monitoreo configurado
- [ ] ✅ Plan de rollback listo
- [ ] ✅ Equipo notificado

---

## 🎯 RESUMEN

**Estado Actual:**
- ✅ Código implementado
- ✅ Flags desactivados (comportamiento actual preservado)
- ✅ Listo para testing

**Próximos Pasos:**
1. Instalar `slowapi`
2. Verificar que todo funciona (flags OFF)
3. Activar gradualmente (dev → staging → producción)

**Garantía:**
- ✅ Sistema NO se rompe (flags OFF por defecto)
- ✅ Rollback inmediato (cambiar flags)
- ✅ Funciona igual que antes (comportamiento preservado)

---

**¡Fase 1 lista para usar! 🎉**

