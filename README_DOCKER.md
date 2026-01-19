# 🐳 Ejecución con Docker y Redis

## 🚀 Inicio Rápido

### Windows (PowerShell)
```powershell
.\start-docker.ps1
```

### Linux/Mac
```bash
chmod +x start-docker.sh
./start-docker.sh
```

### Manual
```bash
# 1. Configurar variables de entorno
cp .env.docker.example .env.docker
# Editar .env.docker con tus valores

# 2. Iniciar servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f backend
```

## 📋 Servicios

- **Backend:** http://localhost:8000
- **Redis:** localhost:6379
- **SQL Server (opcional):** localhost:1433

## 📚 Documentación Completa

Ver `GUIA_DOCKER.md` para documentación detallada.


