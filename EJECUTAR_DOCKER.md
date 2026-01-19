# 🐳 Cómo Ejecutar el Proyecto con Docker y Redis

**Fecha:** Diciembre 2024

---

## ⚡ Inicio Rápido (3 pasos)

### 1. Configurar Variables de Entorno

```bash
# Si no existe .env.docker, copiar desde el ejemplo
cp .env.docker.example .env.docker

# Editar .env.docker y configurar:
# - SECRET_KEY y REFRESH_SECRET_KEY (generar con: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - Configuración de base de datos
# - Variables multi-tenant
```

### 2. Ejecutar Servicios

**Opción A: Script Automático (Recomendado)**
```powershell
# Windows
.\start-docker.ps1

# Linux/Mac
chmod +x start-docker.sh
./start-docker.sh
```

**Opción B: Manual**
```bash
# Solo backend + Redis (BD externa)
docker-compose up -d

# Backend + Redis + SQL Server (todo en Docker)
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Verificar que Funciona

```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs
docker-compose logs -f backend

# Probar endpoints
curl http://localhost:8000/health
# Abrir en navegador: http://localhost:8000/docs
```

---

## 📋 Servicios Disponibles

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| **Backend** | 8000 | http://localhost:8000 | API FastAPI |
| **Docs** | 8000 | http://localhost:8000/docs | Swagger UI |
| **Health** | 8000 | http://localhost:8000/health | Health check |
| **Redis** | 6379 | localhost:6379 | Cache distribuido |
| **SQL Server** | 1433 | localhost:1433 | Base de datos (opcional) |

---

## 🔍 Verificar Redis

```bash
# Probar conexión desde el host
docker exec -it fastapi_redis redis-cli ping
# Debería responder: PONG

# Verificar desde el backend
docker exec -it fastapi_backend python -c "from app.infrastructure.cache.redis_cache import get_cache_info; print(get_cache_info())"
```

---

## 🛠️ Comandos Útiles

### Gestión Básica
```bash
# Iniciar
docker-compose up -d

# Detener
docker-compose down

# Reiniciar
docker-compose restart backend

# Ver logs
docker-compose logs -f backend

# Ver logs de todos los servicios
docker-compose logs -f
```

### Desarrollo
```bash
# Reconstruir después de cambios
docker-compose build --no-cache backend
docker-compose up -d backend

# Entrar al contenedor
docker exec -it fastapi_backend bash

# Ejecutar tests
docker exec -it fastapi_backend pytest tests/ -v
```

### Limpieza
```bash
# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar contenedores + volúmenes (⚠️ elimina datos)
docker-compose down -v

# Limpiar imágenes no usadas
docker system prune -a
```

---

## ⚙️ Configuración de Redis

El proyecto está configurado para usar Redis automáticamente cuando está disponible:

```env
# En .env.docker
REDIS_HOST=redis          # Nombre del servicio en docker-compose
REDIS_PORT=6379
ENABLE_REDIS_CACHE=true   # Activar cache
```

**Verificación:**
```bash
# Verificar que Redis está activo
docker exec fastapi_backend python -c "from app.infrastructure.cache.redis_cache import is_cache_enabled; print('Cache activo:', is_cache_enabled())"
```

---

## 🐛 Solución de Problemas

### Redis no se conecta
```bash
# 1. Verificar que Redis esté corriendo
docker-compose ps redis

# 2. Verificar variables de entorno
docker exec fastapi_backend env | grep REDIS

# 3. Probar conexión manual
docker exec -it fastapi_redis redis-cli ping
```

### Backend no inicia
```bash
# Ver logs detallados
docker-compose logs backend

# Verificar .env.docker
cat .env.docker

# Reconstruir imagen
docker-compose build --no-cache backend
```

### Base de datos no conecta
```bash
# Si usas SQL Server en el HOST:
# DB_SERVER=host.docker.internal

# Si usas contenedor db_dev:
# DB_SERVER=db_dev

# Verificar que db_dev esté saludable
docker-compose ps db_dev
```

---

## 📊 Monitoreo

```bash
# Uso de recursos
docker stats

# Logs en tiempo real
docker-compose logs -f

# Estado de salud
curl http://localhost:8000/health

# Métricas (requiere autenticación SuperAdmin)
curl http://localhost:8000/api/v1/metrics/summary
```

---

## ✅ Checklist de Verificación

- [ ] Docker y Docker Compose instalados
- [ ] Archivo `.env.docker` configurado
- [ ] Contenedores iniciados (`docker-compose ps`)
- [ ] Redis respondiendo (`redis-cli ping`)
- [ ] Backend accesible (http://localhost:8000/health)
- [ ] Documentación accesible (http://localhost:8000/docs)

---

## 📚 Documentación Adicional

- `GUIA_DOCKER.md` - Guía completa y detallada
- `README_DOCKER.md` - Resumen rápido
- `.env.docker.example` - Ejemplo de configuración

---

**Última actualización:** Diciembre 2024


