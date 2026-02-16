# 🐳 GUÍA RÁPIDA - Ejecutar Proyecto con Docker

**Para probar el proyecto antes de comenzar las correcciones**

---

## ⚡ INICIO RÁPIDO (3 pasos)

### Paso 1: Verificar Docker

```powershell
# Verificar que Docker esté corriendo
docker --version
docker-compose --version
```

### Paso 2: Configurar Variables de Entorno

```powershell
# Si no existe .env.docker, copiar desde el ejemplo
if (!(Test-Path .env.docker)) {
    Copy-Item .env.docker.example .env.docker
    Write-Host "Archivo .env.docker creado. Por favor, edítalo con tus valores."
}

# Editar .env.docker con tus valores (especialmente):
# - SECRET_KEY y REFRESH_SECRET_KEY
# - Configuración de base de datos
# - Variables multi-tenant (SUPERADMIN_CLIENTE_ID, BASE_DOMAIN, etc.)
```

**Generar SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Paso 3: Ejecutar con Script Automático (RECOMENDADO)

```powershell
# Ejecutar script de inicio
.\start-docker.ps1

# El script te preguntará:
# 1) docker-compose.yml (solo backend + redis, BD externa)
# 2) docker-compose.dev.yml (backend + redis + SQL Server completo)
```

---

## 🔧 OPCIÓN MANUAL (Sin Script)

### Opción A: Solo Backend + Redis (BD Externa)

```powershell
# Iniciar servicios
docker-compose up -d --build

# Ver logs
docker-compose logs -f backend
```

**Configuración requerida en `.env.docker`:**
```env
DB_SERVER=host.docker.internal  # Para conectar a SQL Server del HOST
# O la IP de tu servidor SQL Server
```

### Opción B: Todo en Docker (Backend + Redis + SQL Server)

```powershell
# Iniciar servicios (incluye SQL Server)
docker-compose -f docker-compose.dev.yml up -d --build

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

**Configuración requerida en `.env.docker`:**
```env
DB_SERVER=db_dev  # Nombre del servicio en docker-compose
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd
DB_DATABASE=tu_base_datos
```

---

## ✅ VERIFICAR QUE FUNCIONA

### 1. Ver Estado de Contenedores

```powershell
docker-compose ps

# Deberías ver:
# - fastapi_backend (running)
# - fastapi_redis (running)
# - fastapi_db_dev (running) - solo si usas docker-compose.dev.yml
```

### 2. Probar Health Check

```powershell
# Desde PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health

# O abrir en navegador:
# http://localhost:8000/health
```

### 3. Ver Documentación Swagger

Abrir en navegador: **http://localhost:8000/docs**

### 4. Ver Logs

```powershell
# Logs del backend
docker-compose logs -f backend

# Logs de todos los servicios
docker-compose logs -f

# Logs de Redis
docker-compose logs -f redis
```

---

## 📋 SERVICIOS DISPONIBLES

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| **Backend API** | 8000 | http://localhost:8000 | API FastAPI |
| **Swagger Docs** | 8000 | http://localhost:8000/docs | Documentación interactiva |
| **Health Check** | 8000 | http://localhost:8000/health | Estado del servidor |
| **Redis** | 6379 | localhost:6379 | Cache distribuido |
| **SQL Server** | 1433 | localhost:1433 | Base de datos (opcional) |

---

## 🛠️ COMANDOS ÚTILES

### Gestión Básica

```powershell
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Reiniciar un servicio
docker-compose restart backend

# Ver logs en tiempo real
docker-compose logs -f backend

# Ver estado
docker-compose ps
```

### Desarrollo

```powershell
# Reconstruir después de cambios
docker-compose build --no-cache backend
docker-compose up -d backend

# Entrar al contenedor
docker exec -it fastapi_backend bash

# Ejecutar tests
docker exec -it fastapi_backend pytest tests/ -v

# Ver variables de entorno del contenedor
docker exec fastapi_backend env | grep -E "DB_|REDIS_|SECRET_"
```

### Limpieza

```powershell
# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar contenedores + volúmenes (⚠️ elimina datos)
docker-compose down -v

# Limpiar imágenes no usadas
docker system prune -a
```

---

## 🔍 VERIFICAR REDIS

```powershell
# Probar conexión Redis
docker exec -it fastapi_redis redis-cli ping
# Debería responder: PONG

# Verificar desde el backend
docker exec fastapi_backend python -c "from app.infrastructure.cache.redis_cache import is_cache_enabled; print('Cache activo:', is_cache_enabled())"
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema: Backend no inicia

```powershell
# 1. Ver logs detallados
docker-compose logs backend

# 2. Verificar .env.docker existe y está configurado
Get-Content .env.docker

# 3. Verificar que las variables críticas estén configuradas:
# - SECRET_KEY
# - REFRESH_SECRET_KEY
# - DB_SERVER, DB_USER, DB_PASSWORD, DB_DATABASE
# - SUPERADMIN_CLIENTE_ID
# - BASE_DOMAIN

# 4. Reconstruir imagen
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Problema: Redis no se conecta

```powershell
# 1. Verificar que Redis esté corriendo
docker-compose ps redis

# 2. Verificar variables de entorno
docker exec fastapi_backend env | grep REDIS

# 3. Probar conexión manual
docker exec -it fastapi_redis redis-cli ping
```

### Problema: Base de datos no conecta

**Si usas SQL Server en el HOST:**
```env
# En .env.docker
DB_SERVER=host.docker.internal
DB_PORT=1433
```

**Si usas contenedor db_dev:**
```env
# En .env.docker
DB_SERVER=db_dev
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd
```

```powershell
# Verificar que db_dev esté saludable
docker-compose ps db_dev

# Ver logs de db_dev
docker-compose logs db_dev
```

### Problema: Puerto 8000 ya está en uso

```powershell
# Ver qué está usando el puerto
netstat -ano | findstr :8000

# O cambiar el puerto en docker-compose.yml:
# ports:
#   - "8001:8000"  # Cambiar 8000 por 8001
```

---

## ✅ CHECKLIST PRE-EJECUCIÓN

Antes de ejecutar, verifica:

- [ ] Docker Desktop está corriendo
- [ ] Docker Compose está instalado
- [ ] Archivo `.env.docker` existe y está configurado
- [ ] `SECRET_KEY` y `REFRESH_SECRET_KEY` están generados
- [ ] Configuración de BD está correcta
- [ ] `SUPERADMIN_CLIENTE_ID` está configurado (UUID válido)
- [ ] `BASE_DOMAIN` está configurado

---

## 📝 CONFIGURACIÓN MÍNIMA DE .env.docker

```env
# Seguridad (OBLIGATORIO)
SECRET_KEY=tu_secret_key_generado_32_caracteres_minimo
REFRESH_SECRET_KEY=tu_refresh_secret_key_diferente_32_caracteres_minimo

# Base de Datos
DB_SERVER=db_dev  # o host.docker.internal si BD externa
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd
DB_DATABASE=tu_base_datos
DB_DRIVER=ODBC Driver 17 for SQL Server

# Multi-Tenant (OBLIGATORIO)
SUPERADMIN_CLIENTE_ID=00000000-0000-0000-0000-000000000001
SUPERADMIN_CLIENTE_CODIGO=SYSTEM
SUPERADMIN_SUBDOMINIO=platform
BASE_DOMAIN=localhost

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
ENABLE_REDIS_CACHE=true

# Ambiente
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 🎯 PRÓXIMOS PASOS DESPUÉS DE EJECUTAR

1. **Verificar que el backend responde:**
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8000/health
   ```

2. **Abrir Swagger UI:**
   - Navegador: http://localhost:8000/docs

3. **Probar endpoints básicos:**
   - Health: http://localhost:8000/health
   - Docs: http://localhost:8000/docs

4. **Verificar logs:**
   ```powershell
   docker-compose logs -f backend
   ```

5. **Si todo funciona, proceder con las correcciones:**
   - Seguir el plan en `PLAN_TRABAJO_CORRECCIONES_CRITICAS.md`

---

## 📚 DOCUMENTACIÓN ADICIONAL

- `EJECUTAR_DOCKER.md` - Guía completa
- `GUIA_DOCKER.md` - Guía detallada
- `README_DOCKER.md` - Resumen rápido
- `.env.docker.example` - Ejemplo de configuración

---

**¿Listo para probar?** Ejecuta `.\start-docker.ps1` y sigue las instrucciones.
