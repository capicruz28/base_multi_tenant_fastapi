# 🐳 Guía de Ejecución con Docker y Redis

**Proyecto:** FastAPI Multi-Tenant Backend  
**Última actualización:** Diciembre 2024

---

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.docker.example .env.docker

# Editar .env.docker con tus valores
# (especialmente SECRET_KEY, REFRESH_SECRET_KEY, y configuraciones de BD)
```

### 2. Ejecutar con Docker Compose

```bash
# Opción 1: Usar docker-compose.yml (solo backend + redis)
docker-compose up -d

# Opción 2: Usar docker-compose.dev.yml (backend + redis + SQL Server)
docker-compose -f docker-compose.dev.yml up -d

# Ver logs
docker-compose logs -f backend

# Detener servicios
docker-compose down
```

---

## 📋 Servicios Disponibles

### Backend (FastAPI)
- **Puerto:** 8000
- **URL:** http://localhost:8000
- **Documentación:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Redis
- **Puerto:** 6379
- **Host interno:** `redis` (dentro de Docker)
- **Host externo:** `localhost` (desde tu máquina)

### SQL Server (Opcional - solo en docker-compose.dev.yml)
- **Puerto:** 1433
- **Usuario:** sa
- **Password:** YourStrong@Passw0rd
- **Host interno:** `db_dev` (dentro de Docker)

---

## 🔧 Configuración Detallada

### Variables de Entorno Importantes

#### Redis
```env
REDIS_HOST=redis          # Nombre del servicio en docker-compose
REDIS_PORT=6379
REDIS_PASSWORD=           # Vacío por defecto
REDIS_DB=0
ENABLE_REDIS_CACHE=true   # Activar cache con Redis
```

#### Base de Datos
```env
# Si usas SQL Server en el HOST (fuera de Docker):
DB_SERVER=host.docker.internal

# Si usas el contenedor db_dev:
DB_SERVER=db_dev
```

#### Seguridad
```env
ENABLE_QUERY_TENANT_VALIDATION=true
ALLOW_TENANT_FILTER_BYPASS=false
ENABLE_TENANT_TOKEN_VALIDATION=true
```

---

## 🧪 Verificar que Todo Funciona

### 1. Verificar Contenedores

```bash
# Ver estado de contenedores
docker-compose ps

# Deberías ver:
# - fastapi_backend (running)
# - fastapi_redis (running)
# - fastapi_db_dev (running, si usas docker-compose.dev.yml)
```

### 2. Verificar Redis

```bash
# Desde el host
docker exec -it fastapi_redis redis-cli ping
# Debería responder: PONG

# Verificar conexión desde el backend
docker exec -it fastapi_backend python -c "import redis; r = redis.Redis(host='redis', port=6379); print(r.ping())"
# Debería imprimir: True
```

### 3. Verificar Backend

```bash
# Health check
curl http://localhost:8000/health

# Ver logs del backend
docker-compose logs backend

# Acceder a documentación
# Abrir en navegador: http://localhost:8000/docs
```

---

## 🔍 Comandos Útiles

### Gestión de Contenedores

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Reiniciar un servicio específico
docker-compose restart backend

# Ver logs en tiempo real
docker-compose logs -f backend

# Ejecutar comando en el contenedor
docker-compose exec backend bash

# Ver uso de recursos
docker stats
```

### Desarrollo

```bash
# Reconstruir imagen (después de cambios en Dockerfile)
docker-compose build --no-cache backend

# Ver logs de todos los servicios
docker-compose logs -f

# Limpiar volúmenes (⚠️ elimina datos)
docker-compose down -v
```

### Debugging

```bash
# Entrar al contenedor del backend
docker exec -it fastapi_backend bash

# Ver variables de entorno
docker exec fastapi_backend env | grep REDIS

# Probar conexión a Redis desde el backend
docker exec -it fastapi_backend python -c "from app.infrastructure.cache.redis_cache import is_cache_enabled, get_cache_info; print(get_cache_info())"
```

---

## 🐛 Solución de Problemas

### Problema: Redis no se conecta

**Síntomas:**
- Logs muestran: "Error conectando a Redis"
- Cache no funciona

**Solución:**
1. Verificar que Redis esté corriendo:
   ```bash
   docker-compose ps redis
   ```

2. Verificar que REDIS_HOST esté configurado:
   ```bash
   docker exec fastapi_backend env | grep REDIS
   # Debería mostrar: REDIS_HOST=redis
   ```

3. Probar conexión manual:
   ```bash
   docker exec -it fastapi_redis redis-cli ping
   ```

### Problema: Backend no inicia

**Síntomas:**
- Contenedor se reinicia constantemente
- Logs muestran errores de importación

**Solución:**
1. Ver logs detallados:
   ```bash
   docker-compose logs backend
   ```

2. Verificar que .env.docker existe:
   ```bash
   ls -la .env.docker
   ```

3. Reconstruir imagen:
   ```bash
   docker-compose build --no-cache backend
   docker-compose up -d backend
   ```

### Problema: Base de datos no conecta

**Síntomas:**
- Errores de conexión a SQL Server
- Timeouts

**Solución:**
1. Si usas SQL Server en el HOST:
   ```env
   DB_SERVER=host.docker.internal
   ```

2. Si usas contenedor db_dev:
   ```env
   DB_SERVER=db_dev
   ```

3. Verificar que db_dev esté saludable:
   ```bash
   docker-compose ps db_dev
   ```

---

## 📊 Monitoreo

### Ver Métricas del Sistema

```bash
# Uso de CPU y memoria
docker stats

# Logs en tiempo real
docker-compose logs -f

# Estado de salud
curl http://localhost:8000/health
```

### Verificar Redis

```bash
# Conectar a Redis CLI
docker exec -it fastapi_redis redis-cli

# Dentro de Redis CLI:
# INFO stats          # Ver estadísticas
# KEYS *              # Ver todas las claves
# DBSIZE              # Ver número de claves
```

---

## 🔒 Seguridad en Producción

### Recomendaciones

1. **Cambiar passwords por defecto:**
   ```env
   MSSQL_SA_PASSWORD=PasswordSeguro123!
   REDIS_PASSWORD=PasswordSeguro123!
   ```

2. **Usar secrets de Docker:**
   ```yaml
   secrets:
     - db_password
     - redis_password
   ```

3. **No exponer puertos innecesarios:**
   - Remover `ports:` de redis en producción
   - Usar red interna solo

4. **Activar validación estricta:**
   ```env
   ENABLE_QUERY_TENANT_VALIDATION=true
   ALLOW_TENANT_FILTER_BYPASS=false
   ```

---

## 📝 Notas Importantes

1. **Hot Reload:** El código se monta como volumen, así que los cambios se reflejan automáticamente
2. **Persistencia:** Redis y SQL Server usan volúmenes para persistir datos
3. **Red:** Todos los servicios están en la red `app_network` y se comunican por nombre de servicio
4. **Health Checks:** Los servicios esperan a que Redis y DB estén saludables antes de iniciar

---

**Última actualización:** Diciembre 2024


