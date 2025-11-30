# 📋 CÓMO VER LOS LOGS

## 📍 UBICACIÓN DE LOS LOGS

Los logs se generan en **dos lugares**:

### 1. ✅ Consola (Terminal/PowerShell)

**Cuando inicias la aplicación**, los logs aparecen directamente en la consola:

```bash
python -m uvicorn app.main:app --reload
```

**Verás algo como:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
✅ Módulo de connection pooling cargado y activo
✅ Módulo de Redis cache cargado y activo
[CONNECTION_POOL] Pool ADMIN inicializado. Size=10, MaxOverflow=5
[REDIS_CACHE] Conectado exitosamente. Host=localhost:6379, DB=0
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### 2. ✅ Archivo de Logs

**Ubicación:** `logs/app.log`

**Ruta completa:**
```
d:\base_multi_tenant_fastapi\logs\app.log
```

**Cómo verlos:**

**Opción A: PowerShell (Windows)**
```powershell
# Ver últimas 50 líneas
Get-Content logs\app.log -Tail 50

# Ver en tiempo real (como tail -f)
Get-Content logs\app.log -Wait -Tail 20
```

**Opción B: Notepad/Editor**
- Abrir `logs/app.log` con cualquier editor de texto
- Buscar las líneas que mencionan "pooling" o "Redis"

**Opción C: Comando type (Windows)**
```cmd
type logs\app.log
```

---

## 🔍 QUÉ BUSCAR EN LOS LOGS

### Logs de Connection Pooling

**Buscar estas líneas:**

```
✅ Módulo de connection pooling cargado y activo
[CONNECTION_POOL] Pool ADMIN inicializado. Size=10, MaxOverflow=5
[POOL] Conexión obtenida del pool para cliente X
```

**Si pooling está desactivado:**
```
ℹ️ Módulo de connection pooling cargado pero desactivado
```

**Si SQLAlchemy no está instalado:**
```
[CONNECTION_POOL] SQLAlchemy no instalado. Connection pooling desactivado automáticamente
```

---

### Logs de Redis Cache

**Buscar estas líneas:**

```
✅ Módulo de Redis cache cargado y activo
[REDIS_CACHE] Conectado exitosamente. Host=localhost:6379, DB=0
[REDIS_CACHE] Cache Redis HIT para connection_metadata:2
```

**Si Redis no está disponible:**
```
ℹ️ Módulo de Redis cache cargado pero desactivado (usando fallback en memoria)
[REDIS_CACHE] Error conectando a Redis: Connection refused. Cache desactivado automáticamente
```

**Si Redis está funcionando:**
```
[REDIS_CACHE] Conectado exitosamente. Host=localhost:6379, DB=0
[REDIS_CACHE] Cache Redis HIT para connection_metadata:2
```

---

### Logs de Rate Limiting (Fase 1)

**Buscar estas líneas:**

```
✅ Módulo de rate limiting cargado y activo
✅ Rate limiting configurado y activo
[RATE_LIMITING] Activado. Límites: Login=10/minute, API=200/minute
```

**Si está desactivado:**
```
ℹ️ Módulo de rate limiting cargado pero desactivado
```

---

## 🧪 VERIFICACIÓN RÁPIDA

### Paso 1: Iniciar la aplicación

```bash
python -m uvicorn app.main:app --reload
```

### Paso 2: Buscar en la consola

Al iniciar, deberías ver inmediatamente:

```
✅ Módulo de connection pooling cargado y activo
✅ Módulo de Redis cache cargado y activo
✅ Rate limiting configurado y activo
```

### Paso 3: Si no ves los mensajes

**Opción 1: Verificar nivel de log**

Los mensajes pueden estar en nivel DEBUG. Cambiar a INFO:

```python
# app/core/config.py
LOG_LEVEL: str = "INFO"  # Asegurar que sea INFO o DEBUG
```

**Opción 2: Buscar en archivo**

```powershell
# Buscar "pooling" en logs
Select-String -Path logs\app.log -Pattern "pooling"

# Buscar "Redis" en logs
Select-String -Path logs\app.log -Pattern "Redis"

# Buscar "rate limiting" en logs
Select-String -Path logs\app.log -Pattern "rate limiting"
```

---

## 📊 EJEMPLO DE LOGS ESPERADOS

### Al Iniciar la Aplicación

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
✅ Módulo de connection pooling cargado y activo
[CONNECTION_POOL] Pool ADMIN inicializado. Size=10, MaxOverflow=5
✅ Módulo de Redis cache cargado y activo
[REDIS_CACHE] Conectado exitosamente. Host=localhost:6379, DB=0
✅ Módulo de rate limiting cargado y activo
✅ Rate limiting configurado y activo
[RATE_LIMITING] Activado. Límites: Login=10/minute, API=200/minute
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Durante Uso Normal

```
[POOL] Conexión obtenida del pool para cliente 2 (DEFAULT/TENANT)
[METADATA] Cache Redis HIT para cliente 2
[POOL] Conexión devuelta al pool (default)
```

---

## 🔧 SI NO VES LOS LOGS

### Problema 1: Logs no aparecen en consola

**Solución:** Verificar que `setup_logging()` se ejecuta:

```python
# app/main.py debe tener:
setup_logging()  # Al inicio del archivo
```

### Problema 2: Solo veo errores

**Solución:** Cambiar nivel de log a DEBUG:

```env
# .env
LOG_LEVEL=DEBUG
```

### Problema 3: Archivo de logs no se crea

**Solución:** Verificar permisos de escritura en carpeta `logs/`:

```powershell
# Verificar que existe
Test-Path logs

# Si no existe, crearlo
New-Item -ItemType Directory -Path logs
```

---

## 📝 COMANDOS ÚTILES

### Ver logs en tiempo real

**PowerShell:**
```powershell
Get-Content logs\app.log -Wait -Tail 50
```

**CMD (Windows):**
```cmd
powershell -Command "Get-Content logs\app.log -Wait -Tail 50"
```

### Buscar mensajes específicos

**PowerShell:**
```powershell
# Buscar "pooling"
Select-String -Path logs\app.log -Pattern "pooling" -Context 2

# Buscar "Redis"
Select-String -Path logs\app.log -Pattern "Redis" -Context 2

# Buscar errores
Select-String -Path logs\app.log -Pattern "ERROR" -Context 5
```

### Ver últimas líneas

**PowerShell:**
```powershell
# Últimas 100 líneas
Get-Content logs\app.log -Tail 100
```

---

## ✅ RESUMEN

**Dónde ver logs:**

1. ✅ **Consola** - Al iniciar la aplicación (más fácil)
2. ✅ **Archivo** - `logs/app.log` (más completo)

**Qué buscar:**

- `✅ Módulo de connection pooling cargado y activo`
- `✅ Módulo de Redis cache cargado y activo`
- `✅ Rate limiting configurado y activo`

**Si no aparecen:**

- Verificar nivel de log (`LOG_LEVEL=INFO` o `DEBUG`)
- Buscar en archivo `logs/app.log`
- Verificar que las dependencias están instaladas

---

**¡Listo para ver los logs! 📋**

