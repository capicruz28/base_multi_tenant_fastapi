# 📋 Especificación: Endpoint de Branding por Subdominio (Pre-Login)

## 🎯 Objetivo

Crear un endpoint público que permita obtener la configuración de branding de un tenant basándose en su subdominio, **sin requerir autenticación**. Esto permite mostrar el branding personalizado en la página de login antes de que el usuario se autentique.

## 📍 Endpoint

```
GET /api/v1/clientes/branding?subdominio={subdominio}
```

### Parámetros

- **Query Parameter**: `subdominio` (string, requerido)
  - Ejemplo: `?subdominio=techcorp`
  - Ejemplo: `?subdominio=acme`

### Características

- ✅ **Público**: No requiere autenticación (sin token JWT)
- ✅ **Sin cookies**: No requiere cookies de sesión
- ✅ **Read-only**: Solo lectura, no modifica datos

## 📤 Respuesta Exitosa (200 OK)

```json
{
  "logo_url": "https://cdn.example.com/logos/techcorp.png",
  "favicon_url": "https://cdn.example.com/favicons/techcorp.ico",
  "color_primario": "#1976D2",
  "color_secundario": "#424242",
  "tema_personalizado": {
    "fontFamily": "Roboto",
    "borderRadius": "8px"
  }
}
```

### Campos de Respuesta

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `logo_url` | `string \| null` | URL pública del logo del tenant | `"https://cdn.example.com/logos/techcorp.png"` |
| `favicon_url` | `string \| null` | URL del favicon del tenant | `"https://cdn.example.com/favicons/techcorp.ico"` |
| `color_primario` | `string` | Color primario en formato HEX | `"#1976D2"` |
| `color_secundario` | `string` | Color secundario en formato HEX | `"#424242"` |
| `tema_personalizado` | `object \| null` | Objeto JSON con configuraciones adicionales | Ver abajo |

### Estructura de `tema_personalizado`

```json
{
  "fontFamily": "Roboto",
  "borderRadius": "8px",
  "spacing": "normal"
}
```

## ❌ Respuestas de Error

### 404 Not Found

**Cuando**: El subdominio no existe o no tiene branding configurado

```json
{
  "detail": "No se encontró branding para el subdominio proporcionado"
}
```

**Comportamiento del Frontend**: Usará valores por defecto:
```json
{
  "logo_url": null,
  "favicon_url": null,
  "color_primario": "#1976D2",
  "color_secundario": "#424242",
  "tema_personalizado": null
}
```

### 400 Bad Request

**Cuando**: El parámetro `subdominio` es inválido o está vacío

```json
{
  "detail": "El subdominio es requerido"
}
```

### 500 Internal Server Error

**Cuando**: Error interno del servidor

```json
{
  "detail": "Error interno del servidor"
}
```

**Comportamiento del Frontend**: Lanzará una excepción (no usará valores por defecto)

## 🔍 Lógica de Implementación

### 1. Validación de Entrada

```python
# Validar que el subdominio sea válido
if not subdominio or not isinstance(subdominio, str):
    raise HTTPException(status_code=400, detail="El subdominio es requerido")

# Limpiar el subdominio (trim, lowercase)
subdominio = subdominio.strip().lower()
```

### 2. Búsqueda del Tenant

```python
# Buscar el cliente por subdominio
cliente = db.query(Cliente).filter(
    Cliente.subdominio == subdominio,
    Cliente.activo == True
).first()

if not cliente:
    raise HTTPException(status_code=404, detail="No se encontró branding para el subdominio proporcionado")
```

### 3. Obtener Branding

```python
# Obtener branding del cliente
# Asumiendo que tienes una relación o tabla de branding
branding = db.query(Branding).filter(
    Branding.cliente_id == cliente.cliente_id
).first()

# Si no hay branding configurado, retornar valores por defecto
if not branding:
    return {
        "logo_url": None,
        "favicon_url": None,
        "color_primario": "#1976D2",
        "color_secundario": "#424242",
        "tema_personalizado": None
    }
```

### 4. Parsear tema_personalizado

```python
# Si tema_personalizado es un JSON string, parsearlo
tema_personalizado = None
if branding.tema_personalizado:
    try:
        tema_personalizado = json.loads(branding.tema_personalizado)
    except json.JSONDecodeError:
        tema_personalizado = None
```

### 5. Construir Respuesta

```python
return {
    "logo_url": branding.logo_url,
    "favicon_url": branding.favicon_url,
    "color_primario": branding.color_primario or "#1976D2",
    "color_secundario": branding.color_secundario or "#424242",
    "tema_personalizado": tema_personalizado
}
```

## 🔒 Seguridad

### Consideraciones

1. **Rate Limiting**: Implementar rate limiting para prevenir abuso
   - Recomendado: 100 requests por minuto por IP
   
2. **Validación de Subdominio**: Validar que el subdominio solo contenga caracteres alfanuméricos y guiones
   ```python
   import re
   if not re.match(r'^[a-z0-9-]+$', subdominio):
       raise HTTPException(status_code=400, detail="Subdominio inválido")
   ```

3. **CORS**: Asegurar que el endpoint permita requests desde el frontend
   - Headers CORS apropiados si es necesario

4. **Cache**: Considerar cachear la respuesta (ej: Redis) para mejorar performance
   - TTL recomendado: 5-10 minutos

## 📝 Ejemplo de Implementación (FastAPI)

```python
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

router = APIRouter(prefix="/clientes", tags=["branding"])

@router.get("/branding", response_model=BrandingRead)
async def get_branding_by_subdomain(
    subdominio: str = Query(..., description="Subdominio del tenant"),
    db: Session = Depends(get_db)
):
    """
    Obtener branding por subdominio (público, sin autenticación)
    
    Este endpoint permite obtener la configuración de branding de un tenant
    basándose en su subdominio, sin requerir autenticación.
    Útil para mostrar branding personalizado en la página de login.
    """
    # Validar subdominio
    if not subdominio or not isinstance(subdominio, str):
        raise HTTPException(
            status_code=400,
            detail="El subdominio es requerido"
        )
    
    subdominio = subdominio.strip().lower()
    
    # Validar formato
    import re
    if not re.match(r'^[a-z0-9-]+$', subdominio):
        raise HTTPException(
            status_code=400,
            detail="Subdominio inválido"
        )
    
    # Buscar cliente por subdominio
    cliente = db.query(Cliente).filter(
        Cliente.subdominio == subdominio,
        Cliente.activo == True
    ).first()
    
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="No se encontró branding para el subdominio proporcionado"
        )
    
    # Obtener branding
    branding = db.query(Branding).filter(
        Branding.cliente_id == cliente.cliente_id
    ).first()
    
    # Si no hay branding, retornar valores por defecto
    if not branding:
        return {
            "logo_url": None,
            "favicon_url": None,
            "color_primario": "#1976D2",
            "color_secundario": "#424242",
            "tema_personalizado": None
        }
    
    # Parsear tema_personalizado si es JSON string
    tema_personalizado = None
    if branding.tema_personalizado:
        try:
            tema_personalizado = json.loads(branding.tema_personalizado)
        except (json.JSONDecodeError, TypeError):
            tema_personalizado = None
    
    return {
        "logo_url": branding.logo_url,
        "favicon_url": branding.favicon_url,
        "color_primario": branding.color_primario or "#1976D2",
        "color_secundario": branding.color_secundario or "#424242",
        "tema_personalizado": tema_personalizado
    }
```

## 🧪 Casos de Prueba

### Caso 1: Subdominio válido con branding
```
GET /api/v1/clientes/branding?subdominio=techcorp
→ 200 OK con datos de branding
```

### Caso 2: Subdominio válido sin branding
```
GET /api/v1/clientes/branding?subdominio=techcorp
→ 200 OK con valores por defecto
```

### Caso 3: Subdominio inexistente
```
GET /api/v1/clientes/branding?subdominio=inexistente
→ 404 Not Found
```

### Caso 4: Subdominio inválido
```
GET /api/v1/clientes/branding?subdominio=tech@corp
→ 400 Bad Request
```

### Caso 5: Subdominio vacío
```
GET /api/v1/clientes/branding?subdominio=
→ 400 Bad Request
```

## ✅ Checklist de Implementación

- [ ] Crear endpoint `GET /api/v1/clientes/branding?subdominio={subdominio}`
- [ ] Validar parámetro `subdominio`
- [ ] Buscar cliente por subdominio
- [ ] Obtener branding del cliente
- [ ] Parsear `tema_personalizado` si es JSON string
- [ ] Retornar valores por defecto si no hay branding (200 OK)
- [ ] Manejar errores 404, 400, 500
- [ ] Implementar rate limiting
- [ ] Agregar documentación OpenAPI/Swagger
- [ ] Agregar tests unitarios
- [ ] Agregar tests de integración

## 📚 Referencias

- Endpoint autenticado existente: `GET /api/v1/clientes/tenant/branding`
- Frontend espera este endpoint en: `src/features/tenant/services/branding.service.ts`
- El frontend ya está preparado para usar este endpoint

