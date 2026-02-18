# ✅ FASE 2 COMPLETADA - Corrección de Queries TextClause/String Críticas

**Fecha:** Febrero 2025  
**Estado:** ✅ COMPLETADA (Queries Críticas Corregidas)  
**Tiempo:** ~1 hora

---

## 📋 Resumen de Correcciones

### Objetivo
Corregir queries críticas que usan `text()` o string SQL contra tablas con `cliente_id` sin filtro de tenant, previniendo fuga de datos entre tenants.

### Queries Críticas Corregidas

#### 1. ✅ DELETE_EXPIRED_TOKENS (CRÍTICA)

**Archivo:** `app/infrastructure/database/queries/auth/auth_queries.py` (línea 111-115)

**Problema:** Query eliminaba tokens expirados de TODOS los tenants sin filtro.

**ANTES:**
```sql
DELETE FROM refresh_tokens
WHERE expires_at < GETDATE()
  AND is_revoked = 1;
```

**DESPUÉS:**
```sql
DELETE FROM refresh_tokens
WHERE expires_at < GETDATE()
  AND is_revoked = 1
  AND cliente_id = :cliente_id;
```

**Función modificada:** `cleanup_expired_tokens()` en `refresh_token_service.py`
- Ahora requiere contexto de tenant (`get_current_client_id()`)
- Pasa `cliente_id` como parámetro nombrado
- Lanza `ValidationError` si no hay contexto
- **Impacto:** Previene eliminación de tokens de otros tenants

#### 2. ✅ REVOKE_REFRESH_TOKEN_BY_ID (CRÍTICA)

**Archivo:** `app/infrastructure/database/queries/auth/auth_queries.py` (línea 140-145)

**Problema:** Query podía revocar tokens de cualquier tenant usando solo `token_id`.

**ANTES:**
```sql
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.usuario_id, INSERTED.cliente_id
WHERE token_id = :token_id;
```

**DESPUÉS:**
```sql
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.usuario_id, INSERTED.cliente_id
WHERE token_id = :token_id
  AND cliente_id = :cliente_id;
```

**Función modificada:** `revoke_refresh_token_by_id()` en `refresh_token_service.py`
- Ahora requiere contexto de tenant
- Pasa `cliente_id` como parámetro nombrado
- **Impacto:** Previene revocación de tokens de otros tenants

---

## ✅ Queries Verificadas (Ya Correctas)

### refresh_token_service.py
Todas las demás queries de refresh tokens ya incluyen `cliente_id`:
- ✅ `GET_REFRESH_TOKEN_BY_HASH` - Tiene `cliente_id` en WHERE
- ✅ `INSERT_REFRESH_TOKEN` - Tiene `cliente_id` en VALUES
- ✅ `REVOKE_REFRESH_TOKEN` - Tiene `cliente_id` en WHERE
- ✅ `REVOKE_REFRESH_TOKEN_BY_USER` - Tiene `cliente_id` en WHERE
- ✅ `REVOKE_ALL_USER_TOKENS` - Tiene `cliente_id` en WHERE
- ✅ `GET_ACTIVE_SESSIONS_BY_USER` - Tiene `cliente_id` en WHERE
- ✅ `GET_ALL_ACTIVE_SESSIONS` - Tiene `cliente_id` en WHERE

### permiso_service.py
- ✅ Queries de `rol_menu_permiso` - Todas incluyen `cliente_id` en WHERE o VALUES
- ✅ Usa parámetros posicionales (`?`) pero siempre pasa `cliente_id`

### rol_service.py
- ✅ Queries de `rol_menu_permiso` - Incluyen `cliente_id` en VALUES
- ✅ Usa parámetros nombrados (`:cliente_id`)

### user_service.py
- ✅ `SELECT_USUARIOS_PAGINATED` - Tiene `cliente_id` en WHERE
- ✅ `SELECT_USUARIOS_PAGINATED_MULTI_DB` - Para BD dedicadas (no necesita filtro)

---

## 📊 Resultados de Auditoría

**Script de auditoría ejecutado:** `scripts/audit_text_queries.py`

**Total de issues detectados:** 591
- Alta severidad: 448 (muchos falsos positivos - comentarios, imports, etc.)
- Media severidad: 143

**Queries Realmente Críticas Encontradas y Corregidas:** 2
1. ✅ `DELETE_EXPIRED_TOKENS` - CORREGIDA
2. ✅ `REVOKE_REFRESH_TOKEN_BY_ID` - CORREGIDA

**Nota:** El script detectó muchos falsos positivos (comentarios, imports, código que menciona tablas pero no son queries reales). Las queries realmente críticas fueron identificadas y corregidas.

---

## 🔧 Cambios Técnicos Detallados

### Archivos Modificados

1. **`app/infrastructure/database/queries/auth/auth_queries.py`**
   - `DELETE_EXPIRED_TOKENS`: Añadido `AND cliente_id = :cliente_id`
   - `REVOKE_REFRESH_TOKEN_BY_ID`: Añadido `AND cliente_id = :cliente_id`

2. **`app/modules/auth/application/services/refresh_token_service.py`**
   - `cleanup_expired_tokens()`: 
     - Añadido `get_current_client_id()` para obtener contexto
     - Pasa `cliente_id` a query con `.bindparams(cliente_id=cliente_id)`
     - Maneja `RuntimeError` si no hay contexto
   - `revoke_refresh_token_by_id()`:
     - Añadido `get_current_client_id()` para obtener contexto
     - Pasa `cliente_id` a query con `.bindparams(cliente_id=cliente_id)`
   - Añadido import: `ValidationError`

---

## ✅ Verificaciones Realizadas

- [x] Queries críticas corregidas
- [x] Funciones modificadas requieren contexto de tenant
- [x] Sin errores de sintaxis (linter limpio)
- [x] Imports añadidos correctamente
- [x] Código documentado

---

## 🧪 Próximos Pasos para Testing

### Tests Requeridos

1. **Test de `cleanup_expired_tokens`:**
   - Crear tokens expirados en tenant A
   - Ejecutar cleanup con contexto de tenant A
   - Verificar que solo tokens de tenant A se eliminan
   - Verificar que tokens de tenant B NO se eliminan

2. **Test de `revoke_refresh_token_by_id`:**
   - Crear token en tenant A
   - Intentar revocar con contexto de tenant B
   - Debe fallar o no encontrar el token

3. **Test sin contexto:**
   - Intentar `cleanup_expired_tokens()` sin contexto
   - Debe lanzar `ValidationError`

---

## 📝 Notas Importantes

1. **`cleanup_expired_tokens` ahora requiere contexto:**
   - Para limpiar todos los tenants, usar `RefreshTokenCleanupJob.cleanup_all_tenants()` (Fase 4)
   - Esta función será implementada en Fase 4

2. **`revoke_refresh_token_by_id` ahora requiere contexto:**
   - Solo puede revocar tokens del tenant actual
   - Previene revocación accidental de tokens de otros tenants

3. **Otras queries verificadas:**
   - La mayoría de queries ya tenían filtro de tenant correcto
   - Solo estas 2 queries críticas necesitaban corrección inmediata

---

## 🚨 Rollback (Si es Necesario)

Si algo falla, revertir cambios:

```bash
git checkout app/infrastructure/database/queries/auth/auth_queries.py
git checkout app/modules/auth/application/services/refresh_token_service.py
```

---

## ✅ Criterio de Éxito Fase 2

- ✅ Queries críticas corregidas
- ✅ Funciones requieren contexto de tenant
- ✅ Sin errores de sintaxis
- ✅ Código documentado
- ⏳ Tests de aislamiento (pendiente)

---

**Fase 2 completada exitosamente.** ✅

*Próximo paso: Fase 3 - Validar `menu_id` en BD Dedicada*
