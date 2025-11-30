# ✅ FASE 1: ACTIVADA Y LISTA PARA USAR

## 🎯 ESTADO ACTUAL

**La Fase 1 está ACTIVADA por defecto** y lista para usar tanto en desarrollo como en producción.

---

## 🔐 QUÉ SE ACTIVÓ

### 1. ✅ Validación de Tenant en Tokens JWT

**¿Qué hace?**
- Verifica que el `cliente_id` del token JWT coincida con el tenant actual (subdominio)
- Previene que un usuario del tenant A use su token en el tenant B

**¿Cómo funciona?**
```python
# Cuando un usuario hace login en tenant "acme"
# El token incluye: cliente_id = 2

# Si intenta usar ese token en tenant "innova" (cliente_id = 3)
# → RECHAZADO con error 403
```

**Excepciones:**
- ✅ Superadmin puede cambiar de tenant (comportamiento esperado)
- ✅ Si no hay contexto (scripts de fondo), permite (comportamiento esperado)

**Impacto:**
- ✅ **Usuarios normales:** No pueden usar tokens en otros tenants (SEGURIDAD)
- ✅ **Superadmin:** Puede cambiar de tenant normalmente
- ⚠️ **Si un usuario cambia de subdominio:** Debe hacer login nuevamente

---

### 2. ✅ Validación de Queries (Advertencias)

**¿Qué hace?**
- Detecta queries que NO incluyen filtro de `cliente_id`
- **Solo loggea advertencias** (NO bloquea queries)

**¿Cómo funciona?**
```python
# Query SIN filtro de tenant (riesgosa)
SELECT * FROM usuario WHERE nombre_usuario = ?

# Query CON filtro de tenant (segura)
SELECT * FROM usuario WHERE nombre_usuario = ? AND cliente_id = ?
```

**Impacto:**
- ✅ **No rompe nada:** Las queries se ejecutan normalmente
- ✅ **Solo advertencias:** Se loggean queries potencialmente riesgosas
- ✅ **Útil para auditoría:** Identifica queries que necesitan corrección

**Para usar validación estricta:**
```python
# Usar execute_query_safe() con require_tenant_validation=True
result = execute_query_safe(query, params, require_tenant_validation=True)
```

---

### 3. ✅ Rate Limiting

**¿Qué hace?**
- Limita el número de requests por minuto desde la misma IP
- Protege contra ataques de fuerza bruta

**Límites configurados:**
- **Login:** 10 intentos por minuto por IP
- **API general:** 200 requests por minuto por IP

**¿Cómo funciona?**
```python
# Usuario intenta hacer login 11 veces en 1 minuto
# → Las primeras 10 funcionan
# → La 11ª es bloqueada con error 429 (Too Many Requests)
```

**Impacto:**
- ✅ **Uso normal:** No se ve afectado (límites generosos)
- ✅ **Ataques:** Bloqueados automáticamente
- ⚠️ **Si se bloquea legítimamente:** Esperar 1 minuto o usar otra IP

**Headers de respuesta:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 5
X-RateLimit-Reset: 1634567890
```

---

## ⚙️ CONFIGURACIÓN ACTUAL

### Valores por Defecto (Activados)

```python
ENABLE_TENANT_TOKEN_VALIDATION = True  # ✅ Activado
ENABLE_QUERY_TENANT_VALIDATION = True  # ✅ Activado (solo advertencias)
ENABLE_RATE_LIMITING = True            # ✅ Activado

RATE_LIMIT_LOGIN = "10/minute"         # 10 intentos por minuto
RATE_LIMIT_API = "200/minute"          # 200 requests por minuto
```

### Cómo Desactivar (Si es Necesario)

**Opción 1: Variable de entorno**
```bash
# .env
ENABLE_TENANT_TOKEN_VALIDATION=false
ENABLE_QUERY_TENANT_VALIDATION=false
ENABLE_RATE_LIMITING=false
```

**Opción 2: Código (no recomendado)**
```python
# app/core/config.py
ENABLE_TENANT_TOKEN_VALIDATION: bool = False
```

---

## 🧪 CÓMO VERIFICAR QUE FUNCIONA

### 1. Verificar Rate Limiting

**Test 1: Login normal**
```bash
# Hacer login normalmente
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"
```

**Test 2: Rate limit (bloqueo)**
```bash
# Hacer 11 intentos de login rápidos
for i in {1..11}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test&password=wrong"
done

# El 11º intento debe retornar 429 (Too Many Requests)
```

**Respuesta esperada:**
```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

### 2. Verificar Validación de Tenant

**Test: Token cross-tenant**
```bash
# 1. Login en tenant "acme" (cliente_id=2)
curl -X POST http://acme.localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=pass1"

# Obtener access_token del response

# 2. Intentar usar ese token en tenant "innova" (cliente_id=3)
curl -X GET http://innova.localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer <access_token_de_acme>"

# Debe retornar 403 (Forbidden)
```

**Respuesta esperada:**
```json
{
  "detail": "Token no válido para este tenant. Por favor, inicie sesión nuevamente."
}
```

### 3. Verificar Advertencias de Queries

**Revisar logs:**
```bash
# Buscar en logs advertencias como:
[SECURITY] Query sin filtro explícito de cliente_id detectada. Query: SELECT * FROM usuario WHERE...
```

---

## 📊 MONITOREO

### Logs a Revisar

1. **Rate Limiting activado:**
   ```
   ✅ Módulo de rate limiting cargado y activo
   ✅ Rate limiting configurado y activo
   [RATE_LIMITING] Activado. Límites: Login=10/minute, API=200/minute
   ```

2. **Validación de tenant:**
   ```
   [SECURITY] Token de tenant 2 usado en tenant 3. Usuario: user1
   ```

3. **Queries sin filtro:**
   ```
   [SECURITY] Query sin filtro explícito de cliente_id detectada. Query: SELECT...
   ```

### Métricas Importantes

- **Requests bloqueados por rate limit:** Debe ser bajo (< 1%)
- **Tokens rechazados por validación:** Debe ser 0 para usuarios legítimos
- **Advertencias de queries:** Revisar y corregir gradualmente

---

## ⚠️ CASOS ESPECIALES

### 1. Superadmin Cambiando de Tenant

**Comportamiento esperado:**
- ✅ Superadmin puede usar su token en cualquier tenant
- ✅ No se bloquea (comportamiento correcto)

### 2. Usuario Legítimo Bloqueado por Rate Limit

**Solución:**
- Esperar 1 minuto
- O aumentar límite en `.env`:
  ```env
  RATE_LIMIT_LOGIN=20/minute  # Aumentar a 20 intentos
  ```

### 3. Query Sin Filtro de Tenant

**Solución:**
- Revisar logs para identificar queries problemáticas
- Agregar `WHERE cliente_id = ?` a la query
- O usar `execute_query_safe()` con validación

---

## 🔧 AJUSTES RECOMENDADOS

### Para Desarrollo

```env
# .env (desarrollo)
# Límites más generosos para testing
RATE_LIMIT_LOGIN=20/minute
RATE_LIMIT_API=500/minute
```

### Para Producción

```env
# .env (producción)
# Límites más estrictos para seguridad
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

Después de activar, verificar:

- [ ] ✅ Aplicación inicia sin errores
- [ ] ✅ Logs muestran "Rate limiting activado"
- [ ] ✅ Login funciona normalmente
- [ ] ✅ Rate limit bloquea después de 10 intentos
- [ ] ✅ Token de tenant A no funciona en tenant B
- [ ] ✅ Superadmin puede cambiar de tenant
- [ ] ✅ No hay errores en logs

---

## 🎯 RESUMEN

**Estado:** ✅ **ACTIVADO Y FUNCIONANDO**

**Funcionalidades activas:**
1. ✅ Validación de tenant en tokens JWT
2. ✅ Advertencias de queries sin filtro
3. ✅ Rate limiting (10 login/min, 200 API/min)

**Seguridad mejorada:**
- ✅ Tokens no pueden usarse cross-tenant
- ✅ Protección contra fuerza bruta
- ✅ Detección de queries riesgosas

**Comportamiento:**
- ✅ Usuarios normales: Más seguro (deben hacer login por tenant)
- ✅ Superadmin: Sin cambios (puede cambiar de tenant)
- ✅ Rate limiting: Protege sin afectar uso normal

---

## 🚨 SI ALGO FALLA

### Desactivar Temporalmente

```env
# .env
ENABLE_TENANT_TOKEN_VALIDATION=false
ENABLE_QUERY_TENANT_VALIDATION=false
ENABLE_RATE_LIMITING=false
```

**Reiniciar aplicación** → Vuelve al comportamiento anterior.

---

**¡Fase 1 activada y lista! 🎉**

