# Corrección de Auditoría: IDOR (Insecure Direct Object Reference)

## ✅ Cambios Implementados

### 📋 Resumen

Se implementaron correcciones críticas de seguridad para hacer el filtro `cliente_id` **OBLIGATORIO** en la capa de persistencia, previniendo vulnerabilidades IDOR (exposición de datos entre inquilinos).

---

## 🔒 Cambios Realizados

### 1. **Configuración de Seguridad** (`app/core/config.py`)

**Nuevo Flag de Configuración:**
```python
# ✅ CORRECCIÓN AUDITORÍA: Filtro obligatorio de cliente_id
# Por defecto, el filtro de tenant es OBLIGATORIO en BaseRepository
# Para permitir bypass (solo en casos especiales), establecer a "true"
# ⚠️ ADVERTENCIA: Permitir bypass reduce la seguridad multi-tenant
ALLOW_TENANT_FILTER_BYPASS: bool = os.getenv("ALLOW_TENANT_FILTER_BYPASS", "false").lower() == "true"
```

**Comportamiento:**
- Por defecto: `false` (filtro OBLIGATORIO)
- Solo cambiar a `true` en casos especiales (scripts de migración, mantenimiento)
- ⚠️ **ADVERTENCIA:** Activar este flag reduce la seguridad multi-tenant

---

### 2. **BaseRepository - Filtro Obligatorio** (`app/infrastructure/database/repositories/base_repository.py`)

**Cambios en `_build_tenant_filter()`:**

**ANTES:**
- `allow_no_context=True` permitía bypass sin restricciones
- Solo loggeaba advertencia

**AHORA:**
- `allow_no_context=True` **SOLO funciona** si `ALLOW_TENANT_FILTER_BYPASS=True` está configurado
- Si se intenta bypass sin el flag, se **RECHAZA** con `ValidationError`
- Logging de **ERROR** cuando se permite bypass (para auditoría)

**Código Clave:**
```python
if target_client_id is None:
    if allow_no_context and settings.ALLOW_TENANT_FILTER_BYPASS:
        # ⚠️ BYPASS PERMITIDO: Solo si está habilitado globalmente
        logger.error("[SECURITY CRITICAL] Query sin filtro de tenant permitida...")
        return ("", ())
    elif allow_no_context and not settings.ALLOW_TENANT_FILTER_BYPASS:
        # ⚠️ BYPASS SOLICITADO PERO NO PERMITIDO: Rechazar
        raise ValidationError(...)
    else:
        # ✅ SEGURIDAD: Requerir contexto de tenant o client_id explícito
        raise ValidationError(...)
```

---

### 3. **execute_query - Validación Estricta** (`app/infrastructure/database/queries.py`)

**Cambios en Validación de Tenant:**

**ANTES:**
- `skip_tenant_validation=True` omitía validación sin restricciones
- Si había error en validación, solo loggeaba (no bloqueaba)

**AHORA:**
- `skip_tenant_validation=True` **SOLO funciona** si `ALLOW_TENANT_FILTER_BYPASS=True`
- Si se intenta omitir validación sin el flag, se **VALIDA DE TODAS FORMAS**
- Si hay error en validación, se **BLOQUEA** la query (mejor bloquear que permitir inseguro)

**Código Clave:**
```python
should_validate = (
    not skip_tenant_validation or 
    (skip_tenant_validation and not settings.ALLOW_TENANT_FILTER_BYPASS)
)

if should_validate and client_id is None and connection_type == DatabaseConnection.DEFAULT:
    # Validación obligatoria...
    if not has_cliente_id_filter:
        logger.error("[SECURITY CRITICAL] Query sin filtro de cliente_id...")
        raise ValidationError(...)  # BLOQUEA la query
```

---

## 🎯 Impacto en el Sistema

### ✅ **Mejoras de Seguridad:**

1. **Filtro Obligatorio por Defecto:**
   - Todas las queries en `BaseRepository` **DEBEN** incluir filtro `cliente_id`
   - No se puede omitir sin configuración explícita

2. **Bypass Controlado:**
   - Bypass solo funciona si `ALLOW_TENANT_FILTER_BYPASS=true` está configurado
   - Requiere decisión consciente del administrador

3. **Validación Estricta:**
   - Queries sin filtro son **BLOQUEADAS** automáticamente
   - Mejor bloquear que permitir queries inseguras

4. **Logging de Seguridad:**
   - Todos los bypass se registran como **ERROR** (para auditoría)
   - Fácil identificar intentos de bypass

### ⚠️ **Código Existente que Requiere Atención:**

**Archivo:** `app/modules/superadmin/application/services/superadmin_auditoria_service.py`
- **Línea 379:** Usa `skip_tenant_validation=True`
- **Razón:** Busca en BD central sin contexto de tenant específico
- **Acción Requerida:** 
  - Si este código es necesario, configurar `ALLOW_TENANT_FILTER_BYPASS=true` en `.env`
  - O mejor: Refactorizar para usar `client_id` explícito o conexión ADMIN

---

## 📝 Configuración Requerida

### **Para Uso Normal (Recomendado):**
```env
# .env
ALLOW_TENANT_FILTER_BYPASS=false  # Por defecto, más seguro
```

### **Para Scripts de Migración/Mantenimiento:**
```env
# .env (temporalmente)
ALLOW_TENANT_FILTER_BYPASS=true  # Solo durante migraciones
```

**⚠️ IMPORTANTE:** Desactivar el flag después de completar la migración.

---

## 🧪 Testing Recomendado

1. **Verificar que queries normales funcionan:**
   ```python
   # Debe funcionar normalmente
   repo = UsuarioRepository()
   usuarios = repo.find_all()  # ✅ Aplica filtro automáticamente
   ```

2. **Verificar que queries sin filtro son bloqueadas:**
   ```python
   # Debe fallar con ValidationError
   query = "SELECT * FROM usuario WHERE usuario_id = ?"
   results = execute_query(query, (user_id,))  # ❌ BLOQUEADO
   ```

3. **Verificar bypass (solo si está configurado):**
   ```python
   # Solo funciona si ALLOW_TENANT_FILTER_BYPASS=true
   results = execute_query(query, (user_id,), skip_tenant_validation=True)
   ```

---

## 🔍 Verificación Post-Implementación

### ✅ Checklist:

- [x] Flag de configuración agregado
- [x] BaseRepository valida filtro obligatorio
- [x] execute_query valida filtro obligatorio
- [x] Bypass requiere configuración explícita
- [x] Logging de seguridad implementado
- [ ] Verificar que código existente funciona
- [ ] Documentar casos especiales que requieren bypass
- [ ] Actualizar documentación de desarrollo

---

## 📚 Referencias

- **Auditoría Original:** `ANALISIS_AUDITORIA_TERCERO_COMPLETA.md`
- **Problema:** IDOR (Insecure Direct Object Reference)
- **Solución:** Filtro `cliente_id` obligatorio en capa de persistencia

---

**Fecha de Implementación:** 2024-12-19  
**Estado:** ✅ Implementado - Requiere Testing y Verificación

