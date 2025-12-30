# Tests para Módulo de Módulos y Menús

## Estructura de Tests

### Tests Unitarios (`tests/unit/`)
- `test_modulo_service.py` - Tests básicos de servicios
- `test_menu_transformer.py` - Tests del transformador de menú

### Tests de Integración (`tests/integration/`)
- `test_modulo_activacion.py` - Tests del flujo completo de activación

## Ejecutar Tests

### Todos los tests
```bash
pytest
```

### Solo tests unitarios
```bash
pytest tests/unit/
```

### Solo tests de integración
```bash
pytest tests/integration/ -m integration
```

### Test específico
```bash
pytest tests/unit/test_modulo_service.py::TestModuloService::test_crear_modulo_valido
```

## Configuración Requerida

### Variables de Entorno
Los tests requieren configuración de base de datos de prueba:
- `DATABASE_URL_TEST` - URL de conexión a BD de prueba
- `SYSTEM_CLIENT_ID` - ID del cliente sistema

### Mocks Necesarios
Algunos tests requieren mocks de:
- `ClienteService`
- `RolService`
- `PermisoService`
- Stored Procedures (`sp_obtener_menu_usuario`)

## Tests Críticos

### 1. Aplicación Automática de Plantillas
**Archivo**: `tests/integration/test_modulo_activacion.py::TestActivacionModulo::test_aplicacion_automatica_plantillas`

Valida que al activar un módulo:
- Se crean roles automáticamente según plantillas
- Se asignan permisos según JSON de plantillas
- Los roles pertenecen al cliente correcto

### 2. Transformación de Menú del Usuario
**Archivo**: `tests/unit/test_menu_transformer.py`

Valida que:
- El resultado del SP se transforma correctamente
- La estructura jerárquica es correcta
- Los permisos se agregan correctamente

### 3. Validación de Dependencias
**Archivo**: `tests/integration/test_modulo_activacion.py::TestActivacionModulo::test_validar_dependencias_activacion`

Valida que:
- No se puede activar un módulo sin dependencias
- Se validan correctamente los módulos requeridos

## Notas

- Los tests actuales son básicos y requieren configuración adicional
- Se recomienda usar fixtures de pytest para datos de prueba
- Los tests de integración requieren BD de prueba configurada

