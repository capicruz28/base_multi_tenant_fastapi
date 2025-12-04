# FASE 3 — PLAN DE ACTUALIZACIÓN DE SCHEMAS

## 📋 Objetivo

Actualizar todos los Pydantic schemas para usar `UUID` o `str` en lugar de `int` para los IDs de las entidades.

## 🔍 Análisis de Schemas a Actualizar

### Schemas por Módulo

#### 1. **app/modules/users/presentation/schemas.py**
- `UsuarioBase`, `UsuarioCreate`, `UsuarioUpdate`, `UsuarioRead`
- `usuario_id: int` → `usuario_id: UUID | str`
- `cliente_id: int` → `cliente_id: UUID | str`

#### 2. **app/modules/rbac/presentation/schemas.py**
- `RolBase`, `RolCreate`, `RolUpdate`, `RolRead`
- `rol_id: int` → `rol_id: UUID | str`
- `cliente_id: int | None` → `cliente_id: UUID | str | None`

- `PermisoBase`, `PermisoRead`, `PermisoCreate`, `PermisoUpdate`
- `permiso_id: int` → `permiso_id: UUID | str`
- `rol_id: int` → `rol_id: UUID | str`
- `menu_id: int` → `menu_id: UUID | str`

#### 3. **app/modules/menus/presentation/schemas.py**
- `AreaBase`, `AreaCreate`, `AreaUpdate`, `AreaRead`
- `area_id: int` → `area_id: UUID | str`
- `cliente_id: int | None` → `cliente_id: UUID | str | None`

- `MenuBase`, `MenuCreate`, `MenuUpdate`, `MenuRead`
- `menu_id: int` → `menu_id: UUID | str`
- `area_id: int | None` → `area_id: UUID | str | None`
- `padre_menu_id: int | None` → `padre_menu_id: UUID | str | None`
- `cliente_id: int | None` → `cliente_id: UUID | str | None`

#### 4. **app/modules/tenant/presentation/schemas.py**
- `ClienteBase`, `ClienteCreate`, `ClienteUpdate`, `ClienteRead`
- `cliente_id: int` → `cliente_id: UUID | str`

- `ModuloBase`, `ModuloCreate`, `ModuloUpdate`, `ModuloRead`
- `modulo_id: int` → `modulo_id: UUID | str`

- `ModuloActivoBase`, `ModuloActivoCreate`, `ModuloActivoUpdate`, `ModuloActivoRead`
- `cliente_modulo_activo_id: int` → `cliente_modulo_activo_id: UUID | str`
- `cliente_id: int` → `cliente_id: UUID | str`
- `modulo_id: int` → `modulo_id: UUID | str`

- `ConexionBase`, `ConexionCreate`, `ConexionUpdate`, `ConexionRead`
- `conexion_id: int` → `conexion_id: UUID | str`
- `cliente_id: int` → `cliente_id: UUID | str`

#### 5. **app/modules/auth/presentation/schemas.py**
- `RefreshTokenBase`, `RefreshTokenRead`
- `token_id: int` → `token_id: UUID | str`
- `usuario_id: int` → `usuario_id: UUID | str`
- `cliente_id: int` → `cliente_id: UUID | str`

#### 6. **app/modules/superadmin/presentation/schemas.py**
- Todos los schemas que usen IDs de entidades

## 🎯 Estrategia de Actualización

### Opción 1: UUID Type (Recomendada)
```python
from uuid import UUID

class UsuarioRead(BaseModel):
    usuario_id: UUID
    cliente_id: UUID
    # ...
```

**Ventajas:**
- Type safety completo
- Validación automática de formato UUID
- Serialización JSON automática

**Desventajas:**
- Requiere conversión explícita en algunos casos
- Frontend debe enviar UUIDs en formato correcto

### Opción 2: str Type (Más Flexible)
```python
class UsuarioRead(BaseModel):
    usuario_id: str
    cliente_id: str
    # ...
```

**Ventajas:**
- Más flexible para APIs
- Fácil de usar en frontend
- Compatible con URLs y query params

**Desventajas:**
- Menos type safety
- Requiere validación manual

### Opción 3: Union[UUID, str] (Híbrida)
```python
from typing import Union
from uuid import UUID

class UsuarioRead(BaseModel):
    usuario_id: Union[UUID, str]
    cliente_id: Union[UUID, str]
    # ...
```

**Ventajas:**
- Máxima flexibilidad
- Acepta ambos formatos

**Desventajas:**
- Más complejo
- Puede ocultar errores de tipo

## ✅ Decisión: UUID Type (Opción 1)

Usaremos `UUID` type porque:
1. Type safety completo
2. Validación automática
3. Mejor para sincronización
4. Pydantic maneja serialización automáticamente

## 📝 Cambios Necesarios

### 1. Imports
```python
from uuid import UUID
from typing import Optional
```

### 2. Validadores
- Eliminar validadores que verifican `valor >= 1` para IDs
- Agregar validadores opcionales para formato UUID si es necesario

### 3. Ejemplos en Field()
- Cambiar `examples=[1, 2, 3]` → `examples=["550e8400-e29b-41d4-a716-446655440000"]`

### 4. Documentación
- Actualizar `description` para mencionar UUID

## 🔄 Orden de Actualización

1. **Schemas base** (sin dependencias):
   - `ClienteBase`, `ClienteRead`
   - `ModuloBase`, `ModuloRead`

2. **Schemas con dependencias simples**:
   - `UsuarioBase`, `UsuarioRead`
   - `RolBase`, `RolRead`
   - `AreaBase`, `AreaRead`

3. **Schemas con dependencias complejas**:
   - `MenuBase`, `MenuRead` (depende de Area y Menu recursivo)
   - `PermisoBase`, `PermisoRead` (depende de Rol y Menu)
   - `ModuloActivoBase`, `ModuloActivoRead` (depende de Cliente y Modulo)

4. **Schemas de relaciones**:
   - `UsuarioRolBase`, `UsuarioRolRead`
   - `RefreshTokenBase`, `RefreshTokenRead`

## ⚠️ Consideraciones

### Validación de UUID
Pydantic valida automáticamente el formato UUID, pero podemos agregar validadores custom si necesitamos:
```python
@field_validator('usuario_id')
@classmethod
def validate_uuid(cls, v: UUID) -> UUID:
    if v.version != 4:
        raise ValueError('Solo se aceptan UUIDv4')
    return v
```

### Serialización JSON
Pydantic serializa UUIDs a strings automáticamente en JSON, pero podemos configurar:
```python
class Config:
    json_encoders = {
        UUID: str
    }
```

### Compatibilidad con Frontend
- Frontend debe enviar UUIDs como strings en JSON
- URLs y query params deben usar strings
- Considerar helper functions para conversión

## 🚀 Próximos Pasos

1. Actualizar schemas base (Cliente, Modulo)
2. Actualizar schemas de usuarios y roles
3. Actualizar schemas de menús y áreas
4. Actualizar schemas de relaciones
5. Testing de serialización/deserialización
6. Actualizar validadores si es necesario




