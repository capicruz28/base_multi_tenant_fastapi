═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                     Sistema ERP Integral en la Nube
                           Versión 1.0 - 2026
═══════════════════════════════════════════════════════════════════════

ÍNDICE GENERAL

PARTE 1: INTRODUCCIÓN Y CONFIGURACIÓN INICIAL
  1.1 Bienvenida y visión general del sistema
  1.2 Arquitectura y flujo de datos
  1.3 Conceptos clave
  
PARTE 2: MÓDULOS FUNDAMENTALES (STARTER)
  2.1 ORG - Organización
  2.2 INV - Inventarios
  2.3 PUR - Compras
  2.4 SLS - Ventas
  2.5 INV_BILL - Facturación Electrónica

PARTE 3: MÓDULOS DE LOGÍSTICA AVANZADA
  3.1 LOG - Logística & Distribución
  3.2 WMS - Gestión de Almacenes
  3.3 QMS - Control de Calidad

PARTE 4: MÓDULOS DE PRODUCCIÓN
  4.1 MFG - Manufactura
  4.2 MRP - Planeamiento de Materiales
  4.3 MPS - Plan Maestro de Producción
  4.4 MNT - Mantenimiento
  4.5 SVC - Órdenes de Servicio

PARTE 5: MÓDULOS COMERCIALES Y RETAIL
  5.1 CRM - Gestión de Clientes
  5.2 PRC - Precios & Promociones
  5.3 POS - Punto de Venta

PARTE 6: MÓDULOS DE GESTIÓN HUMANA Y FINANZAS
  6.1 HCM - Planillas & RRHH
  6.2 FIN - Contabilidad
  6.3 TAX - Libros Electrónicos
  6.4 BDG - Presupuestos

PARTE 7: MÓDULOS AVANZADOS Y COMPLEMENTARIOS
  7.1 CST - Costeo de Productos
  7.2 PM - Gestión de Proyectos
  7.3 TKT - Mesa de Ayuda
  7.4 BI - Reportes & Analytics
  7.5 DMS - Gestión Documental
  7.6 WFL - Flujos de Trabajo
  7.7 AUD - Auditoría

PARTE 8: CASOS DE USO INTEGRADOS
  8.1 Flujo completo: Empresa comercial
  8.2 Flujo completo: Empresa productora
  8.3 Flujo completo: Empresa de servicios
  8.4 Flujo completo: Empresa mixta (producción + tercerización)

═══════════════════════════════════════════════════════════════════════

PARTE 1: INTRODUCCIÓN Y CONFIGURACIÓN INICIAL

═══════════════════════════════════════════════════════════════════════

1.1 BIENVENIDA Y VISIÓN GENERAL DEL SISTEMA
───────────────────────────────────────────────────────────────────────

CAXIS es un sistema ERP (Enterprise Resource Planning) diseñado para 
gestionar todas las operaciones de su empresa desde un solo lugar. 
Funciona 100% en la nube, sin necesidad de instalaciones locales.

¿QUÉ PUEDE HACER CON CAXIS?

✓ Controlar inventarios en tiempo real
✓ Gestionar compras y ventas de forma integrada
✓ Emitir facturas electrónicas válidas ante SUNAT
✓ Planificar y ejecutar producción
✓ Gestionar planillas y recursos humanos
✓ Llevar contabilidad automática
✓ Analizar costos reales de productos
✓ Y mucho más...

PRINCIPIO CLAVE: "UN SOLO REGISTRO, MÚLTIPLES USOS"

Cuando registra una compra, automáticamente:
→ Actualiza el inventario
→ Genera el asiento contable
→ Afecta el presupuesto
→ Actualiza las cuentas por pagar

No más duplicar información entre sistemas.

───────────────────────────────────────────────────────────────────────

1.2 ARQUITECTURA Y FLUJO DE DATOS
───────────────────────────────────────────────────────────────────────

CAXIS organiza la información en 27 módulos especializados que trabajan
juntos como un ecosistema:

NIVEL 1 - BASE (OBLIGATORIO)
┌─────────────────────────────────────────────────────────────────┐
│ ORG - Organización                                              │
│ Define: Empresa, sucursales, departamentos, centros de costo    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
NIVEL 2 - OPERACIONES BÁSICAS
┌──────────────┬──────────────┬──────────────┬──────────────────┐
│ INV          │ PUR          │ SLS          │ INV_BILL         │
│ Inventarios  │ Compras      │ Ventas       │ Facturación      │
└──────────────┴──────────────┴──────────────┴──────────────────┘
                              ↓
NIVEL 3 - OPERACIONES AVANZADAS
┌──────────────┬──────────────┬──────────────┬──────────────────┐
│ MFG          │ LOG          │ HCM          │ FIN              │
│ Producción   │ Logística    │ Planillas    │ Contabilidad     │
└──────────────┴──────────────┴──────────────┴──────────────────┘
                              ↓
NIVEL 4 - ANÁLISIS Y CONTROL
┌──────────────┬──────────────┬──────────────────────────────────┐
│ CST          │ BDG          │ BI                               │
│ Costos       │ Presupuestos │ Reportes                         │
└──────────────┴──────────────┴──────────────────────────────────┘

REGLA DE ORO: Configure los módulos en este orden. No active producción
              sin tener inventarios configurados primero.

───────────────────────────────────────────────────────────────────────

1.3 CONCEPTOS CLAVE
───────────────────────────────────────────────────────────────────────

Antes de empezar, familiarícese con estos conceptos:

MULTI-TENANT
  Su empresa es un "tenant" (inquilino). Sus datos están completamente
  separados de otros clientes. Nadie más puede ver su información.

CLIENTE vs EMPRESA vs SUCURSAL
  CLIENTE: Su organización completa (puede tener varias empresas)
  EMPRESA: Una razón social con RUC propio
  SUCURSAL: Una ubicación física de la empresa

CENTRO DE COSTO
  Unidad a la que se asignan gastos para control. Ejemplos:
  • CC-PRODUCCION
  • CC-ADMINISTRACION
  • CC-VENTAS
  
MOVIMIENTO DE INVENTARIO
  Cualquier entrada o salida de productos del almacén. NUNCA modifique
  el stock manualmente. Siempre use movimientos.

DOCUMENTO MAESTRO-DETALLE
  Cabecera (quién, cuándo, total) + Detalle (qué productos, cantidades).
  Ejemplo: Factura (cabecera) con sus líneas de productos (detalle).

═══════════════════════════════════════════════════════════════════════

PARTE 2: MÓDULOS FUNDAMENTALES (STARTER)

═══════════════════════════════════════════════════════════════════════

2.1 MÓDULO ORG — ORGANIZACIÓN
───────────────────────────────────────────────────────────────────────

OBJETIVO: Configurar la estructura organizacional de su empresa.
PREREQUISITO: Ninguno (es el primer módulo)
TIEMPO ESTIMADO: 30-60 minutos

▸ PASO 1: CONFIGURAR MI EMPRESA

Navegue a: ORG > Mi Empresa

Complete los datos obligatorios:
┌─────────────────────────────────────────────────────────────────┐
│ RUC/NIT:           20XXXXXXXXX                                  │
│ Razón Social:      MI EMPRESA SAC                               │
│ Nombre Comercial:  Mi Empresa                                   │
│ Tipo Empresa:      SAC                                          │
│ País:              Perú                                         │
│                                                                 │
│ CONFIGURACIÓN MULTI-MONEDA:                                     │
│   Moneda Base:     PEN - Sol Peruano (seleccionar catálogo)     │
│   Multi-moneda:    ☐ No  ◉ Sí                                  │
└─────────────────────────────────────────────────────────────────┘

⚠ IMPORTANTE: El RUC no se puede cambiar después. Verifique bien.

💡 SWITCH MULTI-MONEDA:

  Si ACTIVA multi-moneda (☑):
    → Documentos muestran campo "Moneda" y "Tipo de Cambio"
    → Puede facturar en USD, EUR, etc.
    → Reportes se convierten automáticamente a moneda base
    → Usa las monedas creadas en el catálogo
  
  Si DESACTIVA multi-moneda (☐):
    → Todo el sistema trabaja solo en moneda base (PEN)
    → Campos de moneda ocultos en formularios
    → Interfaz más simple y rápida
    → Recomendado para empresas 100% locales

💡 BUENAS PRÁCTICAS:
  • Use MAYÚSCULAS en razón social (como aparece en SUNAT)
  • Suba su logo en formato PNG, 500x500px mínimo
  • Active "Multi-moneda" SOLO si realmente opera internacionalmente
  • Empresa local Perú → Multi-moneda: NO
  • Empresa exportadora → Multi-moneda: SÍ

▸ PASO 2: CREAR SUCURSALES

Navegue a: ORG > Sucursales > [+ Nueva Sucursal]

Ejemplo de nomenclatura recomendada:
┌─────────────────────────────────────────────────────────────────┐
│ Código:      SUC-LIMA-01                                        │
│ Nombre:      Sede Principal Lima                                │
│ Dirección:   Av. Los Cedros 123, San Isidro                    │
│ Teléfono:    01-1234567                                         │
│ Responsable: Juan Pérez (Gerente de Operaciones)               │
│ Es principal: ✓ (marcar solo una como principal)               │
└─────────────────────────────────────────────────────────────────┘

Si tiene varias sedes:
  SUC-LIMA-01, SUC-CALLAO-01, SUC-AREQUIPA-01

💡 RECOMENDACIÓN: Cree una sucursal "VIRTUAL" para operaciones
   digitales o e-commerce.

▸ PASO 3: DEFINIR DEPARTAMENTOS

Navegue a: ORG > Departamentos > [+ Nuevo Departamento]

Estructura jerárquica recomendada:
┌─────────────────────────────────────────────────────────────────┐
│ DIRECCIÓN GENERAL                                               │
│   ├─ ADMINISTRACIÓN Y FINANZAS                                  │
│   │    ├─ Contabilidad                                         │
│   │    └─ Tesorería                                            │
│   ├─ OPERACIONES                                                │
│   │    ├─ Producción                                           │
│   │    ├─ Logística                                            │
│   │    └─ Almacén                                              │
│   └─ COMERCIAL                                                  │
│        ├─ Ventas                                                │
│        └─ Marketing                                             │
└─────────────────────────────────────────────────────────────────┘

Códigos sugeridos:
  DIR-GRAL, ADMIN-FIN, OPER-PROD, COMER-VENT

⚠ IMPORTANTE: Los departamentos se usan en toda la gestión de RRHH.
              Tómese el tiempo para definirlos bien.

▸ PASO 4: CREAR CARGOS

Navegue a: ORG > Cargos > [+ Nuevo Cargo]

Ejemplos por área:
┌─────────────────────────────────────────────────────────────────┐
│ PRODUCCIÓN:                                                     │
│   • OPERARIO-CORTE      → Operario de corte                    │
│   • OPERARIO-COSTURA    → Operario de costura                  │
│   • SUPERVISOR-PROD     → Supervisor de producción             │
│                                                                 │
│ ADMINISTRACIÓN:                                                 │
│   • CONTADOR            → Contador                             │
│   • ASIST-ADMIN         → Asistente administrativo             │
│                                                                 │
│ VENTAS:                                                         │
│   • VENDEDOR-CAMPO      → Vendedor de campo                    │
│   • VENDEDOR-TIENDA     → Vendedor de tienda                   │
│   • JEFE-VENTAS         → Jefe de ventas                       │
└─────────────────────────────────────────────────────────────────┘

💡 TIP: Use códigos descriptivos. Los verá constantemente en reportes.

▸ PASO 5: CONFIGURAR CENTROS DE COSTO

Navegue a: ORG > Centros de Costo > [+ Nuevo Centro]

Nomenclatura estándar:
┌─────────────────────────────────────────────────────────────────┐
│ Código         Nombre                    Tipo                   │
│ ──────────────────────────────────────────────────────────────  │
│ CC-PROD        Producción                Productivo             │
│ CC-ADMIN       Administración            No productivo          │
│ CC-VENTAS      Ventas                    No productivo          │
│ CC-LOGIST      Logística                 Productivo             │
│ CC-MANTO       Mantenimiento             Productivo             │
└─────────────────────────────────────────────────────────────────┘

⚠ CLAVE: Los centros de costo se usan en:
  • Asientos contables
  • Control de gastos
  • Costeo de producción
  • Presupuestos

💡 RECOMENDACIÓN: No cree más de 15 centros de costo. Manténgalo
   simple y manejable.

▸ PASO 6: PARÁMETROS DEL SISTEMA

Navegue a: ORG > Parámetros del Sistema

Configure según su industria:
┌─────────────────────────────────────────────────────────────────┐
│ INVENTARIOS:                                                    │
│   Método costeo:           Promedio ponderado ◉                 │
│   Decimales cantidad:      2                                    │
│   Decimales precio:        2                                    │
│   Control lotes:           ☐ No (activar solo si necesita)     │
│   Control series:          ☐ No                                 │
│                                                                 │
│ FACTURACIÓN:                                                    │
│   IGV:                     18%                                  │
│   Moneda documentos:       PEN                                  │
│   Redondeo:                Matemático                           │
│                                                                 │
│ PRODUCCIÓN:                                                     │
│   Consumo automático:      ☑ Sí (basado en BOM)                │
│   Actualizar costos:       Al cerrar OP                         │
└─────────────────────────────────────────────────────────────────┘

⚠ IMPORTANTE: Estos parámetros afectan cómo funciona todo el sistema.
              No los cambie sin consultar con su contador.

✓ CHECKLIST - ORG COMPLETADO:
  ☐ Datos de empresa verificados
  ☐ Al menos 1 sucursal creada
  ☐ Estructura de departamentos definida
  ☐ Cargos principales registrados
  ☐ Centros de costo configurados
  ☐ Parámetros del sistema ajustados

───────────────────────────────────────────────────────────────────────

2.2 MÓDULO INV — INVENTARIOS
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar productos, almacenes y movimientos de stock.
PREREQUISITO: ORG completado
TIEMPO ESTIMADO: 2-4 horas

▸ PASO 1: CONFIGURAR CATEGORÍAS DE PRODUCTOS

Navegue a: INV > Categorías > [+ Nueva Categoría]

Estructura jerárquica recomendada (ejemplo textil):
┌─────────────────────────────────────────────────────────────────┐
│ MATERIAS PRIMAS                                                 │
│   ├─ Telas                                                      │
│   │    ├─ Telas de Algodón                                     │
│   │    └─ Telas Sintéticas                                     │
│   ├─ Hilos                                                      │
│   └─ Insumos                                                    │
│        ├─ Botones                                               │
│        ├─ Cierres                                               │
│        └─ Etiquetas                                             │
│                                                                 │
│ PRODUCTOS TERMINADOS                                            │
│   ├─ Polos                                                      │
│   ├─ Camisas                                                    │
│   └─ Pantalones                                                 │
└─────────────────────────────────────────────────────────────────┘

Códigos sugeridos:
  MP-TELA, MP-HILO, MP-INSU, PT-POLO, PT-CAMIS

💡 TIP: No cree más de 3 niveles de jerarquía. Manténgalo simple.

▸ PASO 2: CREAR UNIDADES DE MEDIDA

Navegue a: INV > Unidades de Medida > [+ Nueva Unidad]

Unidades estándar recomendadas:
┌─────────────────────────────────────────────────────────────────┐
│ Código    Nombre           Tipo        Uso típico               │
│ ──────────────────────────────────────────────────────────────  │
│ UND       Unidad           Base        Prendas, accesorios      │
│ KG        Kilogramo        Peso        Materiales a granel      │
│ MT        Metro            Longitud    Telas, hilos             │
│ LT        Litro            Volumen     Líquidos                 │
│ RLL       Rollo            Empaque     Telas en rollos          │
│ DOC       Docena           Agrupación  Ventas por docena        │
│ CJA       Caja             Empaque     Empaques de productos    │
└─────────────────────────────────────────────────────────────────┘

Configurar factores de conversión:
  1 RLL = 50 MT (1 rollo de tela = 50 metros)
  1 DOC = 12 UND (1 docena = 12 unidades)
  1 CJA = 24 UND (1 caja = 24 unidades)

⚠ IMPORTANTE: Una vez que use una unidad en transacciones, no puede
              cambiar sus factores de conversión.

▸ PASO 3: CREAR ALMACENES

Navegue a: INV > Almacenes > [+ Nuevo Almacén]

Configuración típica:
┌─────────────────────────────────────────────────────────────────┐
│ Código:         ALM-MP-01                                       │
│ Nombre:         Almacén de Materia Prima                        │
│ Tipo:           Físico ◉  Virtual ○                            │
│ Sucursal:       SUC-LIMA-01                                     │
│ Responsable:    María López                                     │
│ Dirección:      Av. Industrial 456, Ate                         │
│ Control stock:  ☑ Sí                                            │
└─────────────────────────────────────────────────────────────────┘

Almacenes recomendados:
  ALM-MP-01    → Materia prima
  ALM-PT-01    → Productos terminados
  ALM-TRANS-01 → Almacén en tránsito
  ALM-CONSIG   → Mercadería en consignación

💡 BUENAS PRÁCTICAS:
  • Cree almacenes virtuales para stock en tránsito
  • Use un almacén por tipo de producto (MP vs PT)
  • Asigne un responsable claro por almacén

▸ PASO 4: REGISTRAR PRODUCTOS

Navegue a: INV > Productos > [+ Nuevo Producto]

EJEMPLO 1 - MATERIA PRIMA (Tela):
┌─────────────────────────────────────────────────────────────────┐
│ DATOS GENERALES:                                                │
│   Código/SKU:        TELA-JERSEY-BL-24                          │
│   Código Barras:     7501234567890                              │
│   Nombre:            Jersey 24/1 Blanco                         │
│   Categoría:         MP-TELA > Telas de Algodón                │
│   Tipo producto:     Materia Prima                              │
│   Unidad base:       MT (Metro)                                 │
│                                                                 │
│ COSTOS Y PRECIOS:                                               │
│   Costo estándar:    S/ 8.50 por MT                            │
│   Precio venta:      S/ 12.00 por MT                           │
│   Método costeo:     Promedio ponderado                         │
│                                                                 │
│ CONTROL DE STOCK:                                               │
│   Stock mínimo:      200 MT                                     │
│   Stock máximo:      1000 MT                                    │
│   Control lotes:     ☑ Sí (por rollo/lote de producción)       │
│                                                                 │
│ ATRIBUTOS PERSONALIZADOS:                                       │
│   Composición:       100% Algodón peinado                       │
│   Ancho:             1.80 metros                                │
│   Gramaje:           180 g/m²                                   │
│   Proveedor habitual: TEXTILES DEL NORTE SAC                   │
└─────────────────────────────────────────────────────────────────┘

EJEMPLO 2 - PRODUCTO TERMINADO (Prenda):
┌─────────────────────────────────────────────────────────────────┐
│ DATOS GENERALES:                                                │
│   Código/SKU:        POLO-H-M-BLANCO                            │
│   Código Barras:     7501234567901                              │
│   Nombre:            Polo Hombre Talla M Blanco                 │
│   Categoría:         PT-POLO                                    │
│   Tipo producto:     Producto Terminado                         │
│   Unidad base:       UND                                        │
│                                                                 │
│ COSTOS Y PRECIOS:                                               │
│   Costo estándar:    S/ 15.00 (calculado desde BOM)            │
│   Precio venta:      S/ 35.00                                   │
│   Margen:            57% (automático)                           │
│                                                                 │
│ CONTROL DE STOCK:                                               │
│   Stock mínimo:      50 UND                                     │
│   Stock máximo:      500 UND                                    │
│                                                                 │
│ ATRIBUTOS PERSONALIZADOS:                                       │
│   Talla:             M                                          │
│   Color:             Blanco                                     │
│   Colección:         Verano 2026                                │
│   Género:            Hombre                                     │
└─────────────────────────────────────────────────────────────────┘

💡 NOMENCLATURA DE SKU - MEJORES PRÁCTICAS:

Para TELAS:
  TELA-[TIPO]-[COLOR]-[TÍTULO]
  Ejemplo: TELA-JERSEY-BL-24, TELA-PIQUE-AZ-30

Para PRENDAS:
  [TIPO]-[GÉNERO]-[TALLA]-[COLOR]
  Ejemplo: POLO-H-M-BLANCO, CAMIS-M-S-AZUL

⚠ REGLAS DE ORO:
  • SKU único: nunca repetir
  • Sin espacios ni caracteres especiales (-, _ permitidos)
  • Descriptivo pero conciso (máx 20 caracteres)
  • Use MAYÚSCULAS para consistencia

▸ PASO 5: CONFIGURAR TIPOS DE MOVIMIENTO

Navegue a: INV > Tipos de Movimiento > [+ Nuevo Tipo]

Tipos estándar recomendados:
┌─────────────────────────────────────────────────────────────────┐
│ Código       Nombre                  Clase      Afecta Costo    │
│ ──────────────────────────────────────────────────────────────  │
│ ENT-COMP     Entrada por Compra      Entrada    Sí              │
│ ENT-PROD     Entrada por Producción  Entrada    Sí              │
│ ENT-AJUS     Ajuste de Entrada       Ajuste     Sí              │
│ ENT-DEV      Devolución de Cliente   Entrada    Sí              │
│                                                                 │
│ SAL-VENT     Salida por Venta        Salida     Sí              │
│ SAL-PROD     Consumo Producción      Salida     Sí              │
│ SAL-AJUS     Ajuste de Salida        Ajuste     Sí              │
│ SAL-MERM     Merma/Pérdida           Salida     Sí              │
│ SAL-DEV      Devolución Proveedor    Salida     Sí              │
│                                                                 │
│ TRA-ENTR     Transferencia Entre     Transfer   No              │
│              Almacenes                                          │
└─────────────────────────────────────────────────────────────────┘

⚠ IMPORTANTE: Configure correctamente "Afecta costo". Si un movimiento
              no afecta costo, no cambia el valor del inventario.

▸ PASO 6: REGISTRAR STOCK INICIAL

Navegue a: INV > Inventario Físico > [+ Nueva Toma]

Proceso recomendado:
  1. Crear toma de inventario física
  2. Imprimir conteo (PDF con lista de productos)
  3. Personal cuenta físicamente
  4. Ingresar cantidades contadas
  5. Sistema calcula diferencias
  6. Aprobar → genera ajustes automáticos

Ejemplo:
┌─────────────────────────────────────────────────────────────────┐
│ Toma de inventario: INV-FISICA-2026-001                        │
│ Almacén: ALM-MP-01                                              │
│ Fecha: 15/02/2026                                               │
│                                                                 │
│ Producto              Stock   Contado  Diferencia  Acción      │
│                       Sistema                                   │
│ ───────────────────────────────────────────────────────────────│
│ TELA-JERSEY-BL-24     0 MT    450 MT   +450 MT    Ajustar      │
│ HILO-POLY-BL-001      0 MT    1200 MT  +1200 MT   Ajustar      │
│ BOTON-BLANCO-15MM     0 UND   5000 UND +5000 UND  Ajustar      │
│                                                                 │
│ [Aprobar y Generar Ajustes]                                     │
└─────────────────────────────────────────────────────────────────┘

Al aprobar, el sistema genera automáticamente movimientos tipo 
"ENT-AJUS" por las diferencias positivas.

💡 TIP: Haga tomas físicas completas al menos 2 veces al año.

✓ CHECKLIST - INV COMPLETADO:
  ☐ Categorías de productos creadas
  ☐ Unidades de medida configuradas con conversiones
  ☐ Almacenes físicos y virtuales definidos
  ☐ Catálogo de productos completo
  ☐ Tipos de movimiento estándar creados
  ☐ Stock inicial cargado y verificado

═══════════════════════════════════════════════════════════════════════

[CONTINÚA EN ARCHIVO PARTE 2...]

Este es el inicio del manual. ¿Desea que continúe con:
- PARTE 2: PUR (Compras) y SLS (Ventas) en detalle
- O prefieres que genere el manual completo de una vez en un solo archivo?

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 2 DE 8
              MÓDULOS FUNDAMENTALES: COMPRAS, VENTAS Y FACTURACIÓN
═══════════════════════════════════════════════════════════════════════

2.3 MÓDULO PUR — COMPRAS
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar proveedores, cotizaciones, órdenes de compra y recepciones.
PREREQUISITO: ORG + INV completados
TIEMPO ESTIMADO: 3-5 horas

▸ PASO 1: REGISTRAR PROVEEDORES

Navegue a: PUR > Proveedores > [+ Nuevo Proveedor]

EJEMPLO - PROVEEDOR DE TELAS:
┌─────────────────────────────────────────────────────────────────┐
│ DATOS GENERALES:                                                │
│   RUC:               20123456789                                │
│   Razón Social:      TEXTILES DEL NORTE SAC                     │
│   Nombre Comercial:  Textiles del Norte                         │
│   Tipo proveedor:    Nacional ◉  Extranjero ○                  │
│                                                                 │
│ CONTACTO:                                                       │
│   Dirección:         Jr. Gamarra 456, La Victoria              │
│   Teléfono:          01-3456789                                 │
│   Email:             ventas@textilesnorte.com                   │
│   Página web:        www.textilesnorte.com                      │
│                                                                 │
│ CONDICIONES COMERCIALES:                                        │
│   Condición pago:    Crédito 30 días                           │
│   Moneda:            PEN                                        │
│   Categoría:         A (proveedor principal)                    │
│   Límite crédito:    S/ 50,000                                  │
│                                                                 │
│ DATOS BANCARIOS:                                                │
│   Banco:             BCP                                        │
│   Cuenta:            191-1234567-0-89                           │
│   CCI:               002-191-001234567089-15                    │
└─────────────────────────────────────────────────────────────────┘

💡 CLASIFICACIÓN DE PROVEEDORES:
  • Categoría A: Proveedores estratégicos (>70% del volumen)
  • Categoría B: Proveedores importantes (20-70%)
  • Categoría C: Proveedores ocasionales (<20%)

▸ PASO 2: AGREGAR CONTACTOS DEL PROVEEDOR

Navegue a: PUR > Proveedores > [Seleccionar] > Pestaña "Contactos"

Ejemplo:
┌─────────────────────────────────────────────────────────────────┐
│ Nombre:       Carlos Mendoza                                    │
│ Cargo:        Jefe de Ventas                                    │
│ Email:        cmendoza@textilesnorte.com                        │
│ Teléfono:     987654321                                         │
│ Es principal: ☑ Sí                                              │
└─────────────────────────────────────────────────────────────────┘

⚠ IMPORTANTE: Mantenga actualizada esta información. Los emails se
              usan para enviar OC automáticamente.

▸ PASO 3: DEFINIR PRODUCTOS POR PROVEEDOR

Navegue a: PUR > Productos por Proveedor > [+ Nuevo]

Vincule productos con precios específicos:
┌─────────────────────────────────────────────────────────────────┐
│ Proveedor:          TEXTILES DEL NORTE SAC                      │
│ Producto:           TELA-JERSEY-BL-24                           │
│ Código proveedor:   TDN-JER-BL-24/1                            │
│ Precio:             S/ 8.50 por MT                              │
│ Unidad compra:      RLL (Rollo de 50 MT)                       │
│ Tiempo entrega:     7 días                                      │
│ Cantidad mínima:    100 MT (2 rollos)                           │
│ Es proveedor ppal:  ☑ Sí                                        │
└─────────────────────────────────────────────────────────────────┘

💡 TIP: Si un producto tiene varios proveedores, registre todos con
   sus precios. El sistema mostrará opciones al cotizar.

▸ PASO 4: CREAR SOLICITUD DE COMPRA (OPCIONAL)

Navegue a: PUR > Solicitudes de Compra > [+ Nueva Solicitud]

Cuando un departamento necesita algo:
┌─────────────────────────────────────────────────────────────────┐
│ Número:            SC-2026-001                                  │
│ Solicitante:       María López (Jefe de Producción)            │
│ Departamento:      OPER-PROD                                    │
│ Fecha necesidad:   25/02/2026                                   │
│ Prioridad:         Alta ◉  Media ○  Baja ○                     │
│                                                                 │
│ DETALLE:                                                        │
│ Producto              Cantidad  Justificación                   │
│ ─────────────────────────────────────────────────────────────  │
│ TELA-JERSEY-BL-24     500 MT    OP-2026-015 (200 polos)       │
│ HILO-POLY-BL-001      50 KG     Stock bajo mínimo              │
│                                                                 │
│ Estado: Pendiente    [Aprobar] [Rechazar]                      │
└─────────────────────────────────────────────────────────────────┘

Flujo:
  Solicitante crea SC → Jefe aprueba → Compras genera OC

⚠ NOTA: Las solicitudes son OPCIONALES. Puede ir directo a OC.

▸ PASO 5: SOLICITAR COTIZACIONES

Navegue a: PUR > Cotizaciones > [+ Nueva Cotización]

Solicite precios a varios proveedores:
┌─────────────────────────────────────────────────────────────────┐
│ Número:              COT-2026-001                               │
│ Fecha solicitud:     15/02/2026                                 │
│ Fecha límite resp:   20/02/2026                                 │
│                                                                 │
│ PROVEEDORES INVITADOS:                                          │
│   ☑ TEXTILES DEL NORTE SAC                                     │
│   ☑ FABRICA DE TELAS LIMA SAC                                  │
│   ☑ IMPORTADORA TEXTIL PERÚ SRL                                │
│                                                                 │
│ PRODUCTOS SOLICITADOS:                                          │
│ Producto              Cantidad    Entrega deseada               │
│ ─────────────────────────────────────────────────────────────  │
│ TELA-JERSEY-BL-24     500 MT      25/02/2026                   │
│ TELA-PIQUE-AZ-30      300 MT      25/02/2026                   │
│                                                                 │
│ [Enviar Cotización por Email]                                  │
└─────────────────────────────────────────────────────────────────┘

Cuando respondan, registre sus ofertas:
┌─────────────────────────────────────────────────────────────────┐
│ Proveedor: TEXTILES DEL NORTE SAC                               │
│                                                                 │
│ Producto              Cantidad  Precio Unit  Total   Entrega   │
│ ─────────────────────────────────────────────────────────────  │
│ TELA-JERSEY-BL-24     500 MT    S/ 8.50     S/ 4,250  7 días  │
│ TELA-PIQUE-AZ-30      300 MT    S/ 9.20     S/ 2,760  7 días  │
│                                                                 │
│ Subtotal:                                    S/ 7,010          │
│ IGV 18%:                                     S/ 1,262          │
│ TOTAL:                                       S/ 8,272          │
│                                                                 │
│ Condición pago: 30 días                                         │
│ Validez oferta: 15 días                                         │
└─────────────────────────────────────────────────────────────────┘

💡 COMPARACIÓN AUTOMÁTICA: El sistema muestra las 3 cotizaciones
   lado a lado para que elija la mejor opción.

▸ PASO 6: GENERAR ORDEN DE COMPRA

Navegue a: PUR > Órdenes de Compra > [+ Nueva OC]

Desde cotización ganadora o directamente:
┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Número:            OC-2026-001                                │
│   Fecha emisión:     16/02/2026                                 │
│   Proveedor:         TEXTILES DEL NORTE SAC                     │
│   Moneda:            PEN                                        │
│   Tipo cambio:       --                                         │
│   Contacto:          Carlos Mendoza (cmendoza@...)             │
│                                                                 │
│ CONDICIONES:                                                    │
│   Forma pago:        Crédito 30 días                           │
│   Lugar entrega:     ALM-MP-01, Av. Industrial 456             │
│   Fecha entrega:     23/02/2026                                 │
│                                                                 │
│ DETALLE:                                                        │
│ Producto            Cant  UM   Precio   Subtotal  Almacén      │
│ ──────────────────────────────────────────────────────────────│
│ TELA-JERSEY-BL-24   500   MT   8.50     4,250.00  ALM-MP-01   │
│ TELA-PIQUE-AZ-30    300   MT   9.20     2,760.00  ALM-MP-01   │
│                                                                 │
│ Subtotal:                                 S/ 7,010.00          │
│ IGV 18%:                                  S/ 1,261.80          │
│ TOTAL:                                    S/ 8,271.80          │
│                                                                 │
│ Estado: Borrador    [Aprobar] [Enviar Email]                   │
└─────────────────────────────────────────────────────────────────┘

Flujo de estados:
  Borrador → Aprobada → Enviada → Recepcionada → Cerrada

💡 NUMERACIÓN AUTOMÁTICA: El sistema genera OC-2026-001, OC-2026-002
   automáticamente. No se puede repetir.

⚠ IMPORTANTE: Una OC aprobada NO actualiza el stock. Solo la 
              RECEPCIÓN lo hace.

▸ PASO 7: RECEPCIONAR MERCADERÍA

Navegue a: PUR > Recepciones > [+ Nueva Recepción]

Cuando llega la mercadería:
┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Número:            REC-2026-001                               │
│   Fecha recepción:   23/02/2026                                 │
│   OC relacionada:    OC-2026-001                                │
│   Proveedor:         TEXTILES DEL NORTE SAC                     │
│   Guía remisión:     001-1234 (del proveedor)                  │
│   Almacén destino:   ALM-MP-01                                  │
│                                                                 │
│ DETALLE:                                                        │
│ Producto            Ordenado  Recibido  Diferencia  Estado     │
│ ──────────────────────────────────────────────────────────────│
│ TELA-JERSEY-BL-24   500 MT    500 MT    0 MT        ✓ OK      │
│ TELA-PIQUE-AZ-30    300 MT    295 MT    -5 MT       ⚠ Falta   │
│                                                                 │
│ Observaciones: Rollo de PIQUE-AZ vino con 5m menos.            │
│                Proveedor enviará diferencia mañana.             │
│                                                                 │
│ ☑ Generar inspección de calidad (QMS)                          │
│                                                                 │
│ [Procesar Recepción]                                            │
└─────────────────────────────────────────────────────────────────┘

Al procesar:
  1. ✅ Genera movimiento INV tipo "ENT-COMP"
  2. ✅ Actualiza stock en ALM-MP-01
  3. ✅ Actualiza costo promedio de productos
  4. ✅ Marca cantidad recepcionada en la OC
  5. ✅ Si está completa, cierra la OC automáticamente

💡 RECEPCIONES PARCIALES: Puede recepcionar en varias veces. La OC
   se cierra solo cuando cantidad recepcionada = ordenada.

⚠ CONTROL DE CALIDAD: Si activa inspección, el stock queda en
   "cuarentena" hasta que QMS lo apruebe.

✓ CHECKLIST - PUR COMPLETADO:
  ☐ Proveedores principales registrados
  ☐ Contactos de proveedores actualizados
  ☐ Productos vinculados a proveedores con precios
  ☐ Primera OC generada y aprobada
  ☐ Primera recepción procesada con éxito
  ☐ Stock actualizado correctamente en inventarios

───────────────────────────────────────────────────────────────────────

2.4 MÓDULO SLS — VENTAS
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar clientes, cotizaciones, pedidos y despachos.
PREREQUISITO: ORG + INV completados
TIEMPO ESTIMADO: 3-4 horas

▸ PASO 1: REGISTRAR CLIENTES

Navegue a: SLS > Clientes > [+ Nuevo Cliente]

EJEMPLO - CLIENTE CORPORATIVO:
┌─────────────────────────────────────────────────────────────────┐
│ DATOS GENERALES:                                                │
│   Tipo documento:    RUC ◉  DNI ○                              │
│   RUC:               20987654321                                │
│   Razón Social:      DISTRIBUIDORA TEXTIL LIMA SAC              │
│   Nombre Comercial:  Textil Lima                                │
│                                                                 │
│ CONTACTO:                                                       │
│   Dirección:         Av. Argentina 789, Cercado Lima           │
│   Teléfono:          01-5678901                                 │
│   Email:             compras@textillima.com                     │
│                                                                 │
│ CONDICIONES COMERCIALES:                                        │
│   Condición pago:    Crédito 45 días                           │
│   Lista de precios:  LISTA-MAYORISTA                            │
│   Vendedor asignado: Juan Torres                                │
│   Clasificación:     A (cliente estratégico)                    │
│                                                                 │
│ CONTROL DE CRÉDITO:                                             │
│   Límite crédito:    S/ 80,000                                  │
│   Crédito usado:     S/ 0                                       │
│   Saldo disponible:  S/ 80,000                                  │
│   Estado crédito:    ✓ Activo                                   │
└─────────────────────────────────────────────────────────────────┘

💡 CLASIFICACIÓN ABC DE CLIENTES:
  • A: 80% de las ventas (top 20% de clientes)
  • B: 15% de las ventas
  • C: 5% de las ventas (resto)

⚠ LÍMITE DE CRÉDITO: El sistema BLOQUEA pedidos si el cliente
   excede su límite. Configure con cuidado.

▸ PASO 2: AGREGAR CONTACTOS Y DIRECCIONES

Navegue a: SLS > Clientes > [Seleccionar] > Pestaña "Contactos"

Ejemplo:
┌─────────────────────────────────────────────────────────────────┐
│ CONTACTO:                                                       │
│   Nombre:        Roberto Álvarez                                │
│   Cargo:         Jefe de Compras                                │
│   Email:         ralvarez@textillima.com                        │
│   Teléfono:      987123456                                      │
│   Es principal:  ☑ Sí                                           │
└─────────────────────────────────────────────────────────────────┘

Pestaña "Direcciones de Entrega":
┌─────────────────────────────────────────────────────────────────┐
│ Nombre:          Almacén Central                                │
│ Dirección:       Av. Argentina 789, Cercado Lima               │
│ Referencia:      Frente al Mercado Central                      │
│ Contacto:        Roberto Álvarez (987123456)                    │
│ Es principal:    ☑ Sí                                           │
└─────────────────────────────────────────────────────────────────┘

💡 TIP: Un cliente puede tener múltiples direcciones de entrega
   (almacenes, tiendas). Regístrelas todas.

▸ PASO 3: CREAR COTIZACIÓN DE VENTA

Navegue a: SLS > Cotizaciones > [+ Nueva Cotización]

┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Número:            COT-V-2026-001                             │
│   Fecha:             17/02/2026                                 │
│   Cliente:           DISTRIBUIDORA TEXTIL LIMA SAC              │
│   Contacto:          Roberto Álvarez                            │
│   Vendedor:          Juan Torres                                │
│   Validez:           15 días                                    │
│   Moneda:            PEN                                        │
│                                                                 │
│ DETALLE:                                                        │
│ Producto            Cant  UM   Precio   Desc%  Subtotal        │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     200   UND  35.00    10%    6,300.00       │
│ POLO-H-L-AZUL       150   UND  35.00    10%    4,725.00       │
│ CAMIS-M-M-BLANCA    100   UND  45.00    10%    4,050.00       │
│                                                                 │
│ Subtotal:                                       S/ 15,075.00    │
│ Descuento global:                   5%          S/ 753.75      │
│ Base imponible:                                 S/ 14,321.25    │
│ IGV 18%:                                        S/ 2,577.83     │
│ TOTAL:                                          S/ 16,899.08    │
│                                                                 │
│ Condición pago: Crédito 45 días                                │
│ Tiempo entrega: 7 días hábiles                                 │
│                                                                 │
│ [Enviar Cotización por Email] [Convertir a Pedido]             │
└─────────────────────────────────────────────────────────────────┘

💡 DESCUENTOS:
  • Por línea: Descuento específico a un producto
  • Global: Descuento adicional sobre el total

⚠ NOTA: Una cotización NO reserva stock ni genera compromisos.
        Es solo una propuesta.

▸ PASO 4: CONVERTIR COTIZACIÓN EN PEDIDO

Cuando el cliente acepta, convierta a pedido:

Navegue a: SLS > Pedidos > [+ Nuevo Pedido]
           O desde la cotización: [Convertir a Pedido]

┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Número:            PED-2026-001                               │
│   Fecha pedido:      18/02/2026                                 │
│   Cliente:           DISTRIBUIDORA TEXTIL LIMA SAC              │
│   OC Cliente:        OC-DTL-2026-045 (referencia del cliente)  │
│   Vendedor:          Juan Torres                                │
│   Moneda:            PEN                                        │
│                                                                 │
│ ENTREGA:                                                        │
│   Dirección:         Almacén Central (Av. Argentina 789)       │
│   Fecha compromiso:  25/02/2026                                 │
│                                                                 │
│ DETALLE:                                                        │
│ Producto          Cant  UM  Precio  Stock  Reservar  Despachar │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO   200  UND  31.50   180    200      0         │
│ POLO-H-L-AZUL     150  UND  31.50   150    150      0         │
│ CAMIS-M-M-BLANCA  100  UND  40.50   120    100      0         │
│                                                                 │
│ ⚠ ALERTA: POLO-H-M-BLANCO tiene stock de 180, pedido 200      │
│           Faltante: 20 UND                                      │
│                                                                 │
│ Total:                                          S/ 16,899.08    │
│                                                                 │
│ ☑ Reservar stock automáticamente                               │
│                                                                 │
│ Estado: Pendiente   [Aprobar Pedido]                           │
└─────────────────────────────────────────────────────────────────┘

Al aprobar el pedido:
  1. ✅ Reserva stock (inv_stock.cantidad_reservada += cantidad)
  2. ✅ Valida límite de crédito del cliente
  3. ✅ Genera compromiso de despacho
  4. ✅ Actualiza saldo del cliente

⚠ CRÍTICO: Stock reservado NO está disponible para otros pedidos.
           Si cancela el pedido, la reserva se libera automáticamente.

▸ PASO 5: PREPARAR DESPACHO

Navegue a: LOG > Despachos > [+ Nuevo Despacho]
           O desde el pedido: [Generar Despacho]

┌─────────────────────────────────────────────────────────────────┐
│ Número despacho:     DESP-2026-001                              │
│ Pedido origen:       PED-2026-001                               │
│ Cliente:             DISTRIBUIDORA TEXTIL LIMA SAC              │
│ Fecha despacho:      25/02/2026                                 │
│                                                                 │
│ LOGÍSTICA:                                                      │
│   Transportista:     TRANSPORTES RÁPIDOS SAC                    │
│   Vehículo:          Placa ABC-123 (Furgón 2 TM)               │
│   Conductor:         José Ramirez (DNI 12345678)                │
│   Ruta:              RUTA-LIMA-CENTRO                           │
│                                                                 │
│ PRODUCTOS A DESPACHAR:                                          │
│ Producto            Pedido   A despachar  Almacén               │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     200 UND  200 UND      ALM-PT-01           │
│ POLO-H-L-AZUL       150 UND  150 UND      ALM-PT-01           │
│ CAMIS-M-M-BLANCA    100 UND  100 UND      ALM-PT-01           │
│                                                                 │
│ ☑ Generar Guía de Remisión Electrónica                         │
│ ☑ Liberar reserva de stock                                     │
│ ☑ Generar salida de inventario                                 │
│                                                                 │
│ [Procesar Despacho]                                             │
└─────────────────────────────────────────────────────────────────┘

Al procesar:
  1. ✅ Genera Guía de Remisión (LOG)
  2. ✅ Genera movimiento INV tipo "SAL-VENT"
  3. ✅ Descuenta stock físico
  4. ✅ Libera la reserva
  5. ✅ Actualiza estado del pedido

💡 DESPACHOS PARCIALES: Puede despachar en varias veces si no tiene
   todo el stock disponible.

✓ CHECKLIST - SLS COMPLETADO:
  ☐ Clientes principales registrados
  ☐ Límites de crédito configurados
  ☐ Direcciones de entrega cargadas
  ☐ Primera cotización generada
  ☐ Primera venta convertida en pedido
  ☐ Reserva de stock funcionando correctamente
  ☐ Despacho realizado con éxito

───────────────────────────────────────────────────────────────────────

2.5 MÓDULO INV_BILL — FACTURACIÓN ELECTRÓNICA
───────────────────────────────────────────────────────────────────────

OBJETIVO: Emitir comprobantes electrónicos válidos (facturas, boletas, NC, ND).
PREREQUISITO: ORG + SLS completados + Certificado digital
TIEMPO ESTIMADO: 2-3 horas

▸ PASO 1: CONFIGURAR SERIES DE COMPROBANTES

Navegue a: INV_BILL > Series > [+ Nueva Serie]

Configure las series autorizadas por SUNAT:
┌─────────────────────────────────────────────────────────────────┐
│ SERIE DE FACTURAS:                                              │
│   Serie:             F001                                       │
│   Tipo comprobante:  Factura                                    │
│   Sucursal:          SUC-LIMA-01                                │
│   Numeración inicio: 1                                          │
│   Numeración actual: 1                                          │
│   Estado:            ✓ Activa                                   │
│   Predeterminada:    ☑ Sí                                       │
└─────────────────────────────────────────────────────────────────┘

Series recomendadas por sucursal:
  F001, F002, F003  → Facturas
  B001, B002        → Boletas
  FC01              → Notas de crédito (facturas)
  FD01              → Notas de débito (facturas)
  BC01              → Notas de crédito (boletas)

⚠ IMPORTANTE: Las series deben estar autorizadas previamente en SUNAT.
              No invente series.

▸ PASO 2: EMITIR FACTURA DESDE PEDIDO

Navegue a: SLS > Pedidos > [Seleccionar pedido] > [Generar Factura]
           O: INV_BILL > Comprobantes > [+ Nuevo Comprobante]

EJEMPLO - FACTURA ELECTRÓNICA:
┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Serie-Número:      F001-00001                                 │
│   Tipo:              Factura Electrónica                        │
│   Fecha emisión:     25/02/2026                                 │
│   Fecha vencimiento: 11/04/2026 (45 días)                       │
│   Moneda:            PEN                                        │
│                                                                 │
│ CLIENTE:                                                        │
│   RUC:               20987654321                                │
│   Razón Social:      DISTRIBUIDORA TEXTIL LIMA SAC              │
│   Dirección:         Av. Argentina 789, Cercado Lima           │
│                                                                 │
│ ORIGEN:                                                         │
│   Pedido:            PED-2026-001                               │
│   Guía remisión:     T001-00001                                 │
│   OC Cliente:        OC-DTL-2026-045                            │
│                                                                 │
│ DETALLE:                                                        │
│ Producto            Cant  UM  Valor Unit  Subtotal   IGV       │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     200  UND   26.69     5,338.00   960.84    │
│ POLO-H-L-AZUL       150  UND   26.69     4,003.50   720.63    │
│ CAMIS-M-M-BLANCA    100  UND   34.32     3,432.00   617.76    │
│                                                                 │
│ Valor Venta:                              S/ 12,773.50          │
│ IGV 18%:                                  S/ 2,299.23           │
│ Importe Total:                            S/ 15,072.73          │
│                                                                 │
│ FORMA DE PAGO:                                                  │
│   Condición:         Crédito                                    │
│   Cuota 1:           S/ 15,072.73  -  Vencimiento: 11/04/2026  │
│                                                                 │
│ Estado SUNAT:        ⏳ Pendiente envío                         │
│                                                                 │
│ [Emitir y Enviar a SUNAT] [Vista Previa PDF]                   │
└─────────────────────────────────────────────────────────────────┘

⚠ CÁLCULO DE IGV:
  • Valor Venta = Total / 1.18
  • IGV = Total - Valor Venta
  • El sistema calcula automáticamente

💡 DIFERENCIA FACTURA vs PEDIDO:
  Pedido muestra precios CON IGV (S/ 35.00)
  Factura separa Valor Venta + IGV (S/ 29.66 + S/ 5.34)

▸ PASO 3: ENVÍO A SUNAT (INTEGRACIÓN OSE)

Al hacer clic en [Emitir y Enviar]:

Flujo automático:
  1. Sistema genera XML según formato SUNAT UBL 2.1
  2. Firma digitalmente con certificado .pfx
  3. Envía a OSE (Nubefact, SUNAT SOL, etc.) vía API
  4. Recibe CDR (Constancia de Recepción) de SUNAT
  5. Actualiza estado del comprobante
  6. Genera PDF con código QR
  7. Envía email al cliente con PDF + XML

Estados posibles:
┌─────────────────────────────────────────────────────────────────┐
│ ⏳ Pendiente       → Aún no enviado                             │
│ 🔄 Procesando      → Enviando a SUNAT                           │
│ ✅ Aceptado        → SUNAT aprobó el comprobante                │
│ ⚠️ Rechazado       → SUNAT rechazó (error en datos)            │
│ ❌ Anulado         → Comprobante anulado con NC                 │
└─────────────────────────────────────────────────────────────────┘

Ejemplo de respuesta exitosa:
┌─────────────────────────────────────────────────────────────────┐
│ F001-00001                                                      │
│ Estado SUNAT:    ✅ Aceptado                                    │
│ Fecha envío:     25/02/2026 14:35:22                            │
│ Código CDR:      0 (Aceptado)                                   │
│ Hash:            7f8a9b2c...                                    │
│                                                                 │
│ [📄 Descargar PDF] [📦 Descargar XML] [✉️ Reenviar Email]      │
└─────────────────────────────────────────────────────────────────┘

⚠ ERRORES COMUNES:
  • RUC inválido → Verifique en consulta RUC SUNAT
  • Certificado vencido → Renueve antes que expire
  • Serie no autorizada → Autorice en SUNAT primero

▸ PASO 4: EMITIR NOTA DE CRÉDITO

Cuando hay devolución o anulación:

Navegue a: INV_BILL > Comprobantes > [Seleccionar factura] 
           > [Generar Nota de Crédito]

EJEMPLO - NC POR ANULACIÓN:
┌─────────────────────────────────────────────────────────────────┐
│ Serie-Número:        FC01-00001                                 │
│ Tipo:                Nota de Crédito Electrónica                │
│ Fecha emisión:       26/02/2026                                 │
│ Motivo:              01 - Anulación de la operación             │
│                                                                 │
│ COMPROBANTE QUE MODIFICA:                                       │
│   Tipo:              Factura                                    │
│   Serie-Número:      F001-00001                                 │
│   Fecha:             25/02/2026                                 │
│                                                                 │
│ DETALLE (copia del comprobante original):                       │
│ Producto            Cant  Valor Unit  Subtotal   IGV           │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     200   26.69      5,338.00   960.84        │
│ POLO-H-L-AZUL       150   26.69      4,003.50   720.63        │
│ CAMIS-M-M-BLANCA    100   34.32      3,432.00   617.76        │
│                                                                 │
│ Valor Venta:                          S/ 12,773.50              │
│ IGV 18%:                              S/ 2,299.23               │
│ Importe Total:                        S/ 15,072.73              │
│                                                                 │
│ Sustento: Cliente rechazó mercadería por cambio en pedido.     │
│                                                                 │
│ [Emitir NC y Enviar a SUNAT]                                    │
└─────────────────────────────────────────────────────────────────┘

MOTIVOS SUNAT PERMITIDOS:
  01 - Anulación de la operación
  02 - Anulación por error en el RUC
  03 - Corrección por error en la descripción
  04 - Descuento global
  05 - Descuento por ítem
  06 - Devolución total
  07 - Devolución por ítem
  13 - Otros conceptos

💡 EFECTO CONTABLE: La NC INVIERTE el asiento de la factura:
  Factura:  Cuenta por cobrar (+) / Ventas (-)
  NC:       Ventas (+) / Cuenta por cobrar (-)

⚠ IMPORTANTE: Una NC NO devuelve mercadería al almacén automáticamente.
              Debe generar movimiento INV tipo "ENT-DEV" aparte.

▸ PASO 5: EMITIR BOLETA (CONSUMIDOR FINAL)

Para ventas menores a personas naturales sin RUC:

┌─────────────────────────────────────────────────────────────────┐
│ Serie-Número:        B001-00001                                 │
│ Tipo:                Boleta de Venta Electrónica                │
│ Fecha emisión:       26/02/2026                                 │
│                                                                 │
│ CLIENTE:                                                        │
│   Tipo doc:          DNI ◉  RUC ○  CE ○                        │
│   DNI:               12345678                                   │
│   Nombre:            María Fernández                            │
│                                                                 │
│ DETALLE:                                                        │
│ Descripción         Cant  UM  Valor Unit  Subtotal             │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     3    UND   29.66      88.98               │
│                                                                 │
│ Valor Venta:                               S/ 88.98            │
│ IGV 18%:                                   S/ 16.02            │
│ Importe Total:                             S/ 105.00           │
│                                                                 │
│ Forma pago:          Contado - Efectivo                         │
│                                                                 │
│ [Emitir Boleta]                                                 │
└─────────────────────────────────────────────────────────────────┘

💡 BOLETAS vs FACTURAS:
  • Boleta: DNI, consumidor final, hasta S/ 700 sin identidad
  • Factura: RUC, empresa, obligatorio para sustento tributario

⚠ SUNAT 2026: Boletas mayores a S/ 700 requieren DNI obligatorio.

✓ CHECKLIST - INV_BILL COMPLETADO:
  ☐ Series configuradas y autorizadas
  ☐ Certificado digital instalado (.pfx)
  ☐ Integración con OSE funcionando
  ☐ Primera factura emitida y aceptada por SUNAT
  ☐ PDF generado correctamente con QR
  ☐ Email enviado al cliente
  ☐ Nota de crédito emitida correctamente

═══════════════════════════════════════════════════════════════════════

FIN DE LA PARTE 2

PRÓXIMA PARTE 3:
  - LOG (Logística & Distribución)
  - WMS (Gestión de Almacenes)
  - QMS (Control de Calidad)

═══════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 3 DE 8
                  MÓDULOS DE LOGÍSTICA AVANZADA
═══════════════════════════════════════════════════════════════════════

PARTE 3: MÓDULOS DE LOGÍSTICA AVANZADA

═══════════════════════════════════════════════════════════════════════

3.1 MÓDULO LOG — LOGÍSTICA & DISTRIBUCIÓN
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar transportistas, vehículos, rutas y guías de remisión electrónicas.
PREREQUISITO: ORG + INV + SLS completados
TIEMPO ESTIMADO: 2-3 horas

▸ PASO 1: REGISTRAR TRANSPORTISTAS

Navegue a: LOG > Transportistas > [+ Nuevo Transportista]

EJEMPLO - EMPRESA DE TRANSPORTE:
┌─────────────────────────────────────────────────────────────────┐
│ RUC:                20456789012                                 │
│ Razón Social:       TRANSPORTES RÁPIDOS SAC                     │
│ Nombre Comercial:   Rápidos Express                             │
│ MTC Registro:       RE-12345                                    │
│                                                                 │
│ Contacto:           José Mendoza (Coordinador)                  │
│ Teléfono:           01-7654321                                  │
│ Email:              operaciones@rapidosexpress.com              │
│                                                                 │
│ Certificados:                                                   │
│ ☑ SCTR vigente (venc: 31/12/2026)                              │
│ ☑ Póliza seguro carga (venc: 31/12/2026)                       │
│ ☑ Habilitación MTC vigente                                     │
└─────────────────────────────────────────────────────────────────┘

💡 DOCUMENTOS OBLIGATORIOS POR LEY:
  • MTC Registro: Habilitación del Ministerio de Transportes
  • SCTR: Seguro obligatorio para personal
  • Póliza de seguro de carga

▸ PASO 2: REGISTRAR VEHÍCULOS

Navegue a: LOG > Vehículos > [+ Nuevo Vehículo]

┌─────────────────────────────────────────────────────────────────┐
│ Placa:              ABC-123                                     │
│ Marca:              HYUNDAI                                     │
│ Modelo:             HD78                                        │
│ Año fabricación:    2022                                        │
│ Color:              Blanco                                      │
│                                                                 │
│ Tipo vehículo:      Furgón ◉  Camión ○  Camioneta ○           │
│ Capacidad carga:    2.5 TM                                      │
│ Capacidad volumen:  15 m³                                       │
│                                                                 │
│ Propietario:        TRANSPORTES RÁPIDOS SAC                     │
│ Conductor habitual: José Ramírez (DNI 12345678)                │
│                                                                 │
│ GPS:                                                            │
│ ☑ Tiene GPS instalado                                          │
│ ID dispositivo:     GPS-ABC123                                  │
│ Proveedor GPS:      TRACK PERU                                 │
│                                                                 │
│ SOAT vigente:       ✓ (venc: 15/08/2026)                       │
│ Revisión técnica:   ✓ (venc: 20/06/2026)                       │
└─────────────────────────────────────────────────────────────────┘

⚠ ALERTAS AUTOMÁTICAS: El sistema avisa 30 días antes del vencimiento
   de SOAT y revisión técnica.

▸ PASO 3: DEFINIR RUTAS

Navegue a: LOG > Rutas > [+ Nueva Ruta]

EJEMPLO - RUTA LIMA CENTRO:
┌─────────────────────────────────────────────────────────────────┐
│ Código:             RUTA-LIMA-CENTRO                            │
│ Nombre:             Lima Centro - Zona Comercial               │
│ Tipo:               Urbana ◉  Interprovincial ○                │
│                                                                 │
│ PUNTOS DE ENTREGA (orden de visita):                            │
│ 1. Cercado de Lima    → Zona 1                                 │
│ 2. La Victoria        → Zona 2                                 │
│ 3. Breña              → Zona 3                                 │
│ 4. Pueblo Libre       → Zona 4                                 │
│                                                                 │
│ Distancia total:    25 km                                       │
│ Tiempo estimado:    3 horas (con paradas)                       │
│ Días operación:     Lunes a Sábado                              │
│ Horario inicio:     08:00 AM                                    │
│                                                                 │
│ Vehículo sugerido:  Furgón (2-3 TM)                            │
└─────────────────────────────────────────────────────────────────┘

💡 TIP: Las rutas agilizan la programación de despachos. El sistema
   sugerirá la ruta automáticamente según dirección del cliente.

▸ PASO 4: GENERAR GUÍA DE REMISIÓN ELECTRÓNICA

Navegue a: LOG > Guías de Remisión > [+ Nueva Guía]
           O desde Despacho: [Generar GR]

EJEMPLO - GR ELECTRÓNICA SUNAT:
┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Serie-Número:      T001-00001                                 │
│   Tipo:              Guía Remisión Electrónica - Transportista │
│   Fecha emisión:     26/02/2026                                 │
│   Fecha inicio traslado: 26/02/2026 09:00                       │
│                                                                 │
│ MOTIVO TRASLADO:                                                │
│   Código SUNAT:      01 - Venta                                 │
│   Peso bruto total:  85.5 KG                                    │
│   Número bultos:     12 cajas                                   │
│                                                                 │
│ PUNTO DE PARTIDA:                                               │
│   Dirección:         Av. Industrial 456, Ate                    │
│   Ubigeo:            150103 (Lima/Lima/Ate)                     │
│                                                                 │
│ PUNTO DE LLEGADA:                                               │
│   Destinatario:      DISTRIBUIDORA TEXTIL LIMA SAC              │
│   RUC:               20987654321                                │
│   Dirección:         Av. Argentina 789, Cercado Lima           │
│   Ubigeo:            150101 (Lima/Lima/Lima)                    │
│                                                                 │
│ TRANSPORTE:                                                     │
│   Modalidad:         Transporte Privado                         │
│   Transportista:     TRANSPORTES RÁPIDOS SAC                    │
│   RUC:               20456789012                                │
│   Placa:             ABC-123                                    │
│   Conductor:         José Ramírez                               │
│   DNI Conductor:     12345678                                   │
│   Licencia:          A-IIa (venc: 15/05/2028)                  │
│                                                                 │
│ DETALLE:                                                        │
│ Producto            Cantidad  UM   Peso (KG)                    │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     200      UND   40.0                        │
│ POLO-H-L-AZUL       150      UND   30.0                        │
│ CAMIS-M-M-BLANCA    100      UND   15.5                        │
│                                                                 │
│ DOCUMENTOS RELACIONADOS:                                        │
│   Factura:           F001-00001                                 │
│   Pedido:            PED-2026-001                               │
│                                                                 │
│ Estado SUNAT:        ⏳ Pendiente envío                         │
│                                                                 │
│ [Emitir y Enviar a SUNAT] [Imprimir]                           │
└─────────────────────────────────────────────────────────────────┘

MOTIVOS DE TRASLADO SUNAT:
  01 - Venta
  02 - Compra
  04 - Traslado entre establecimientos
  08 - Importación
  09 - Exportación
  13 - Otros

⚠ OBLIGATORIO: Licencia del conductor debe estar vigente y
   corresponder al tipo de vehículo.

💡 PESO BRUTO: Debe incluir el peso del embalaje. Si cada prenda pesa
   0.2 KG, considere +10% por cajas.

▸ PASO 5: PROGRAMAR DESPACHO CON RUTA

Navegue a: LOG > Despachos > [+ Nuevo Despacho]

┌─────────────────────────────────────────────────────────────────┐
│ Número:             DESP-2026-001                               │
│ Fecha programada:   26/02/2026                                  │
│ Hora salida:        09:00 AM                                    │
│                                                                 │
│ LOGÍSTICA:                                                      │
│   Ruta asignada:    RUTA-LIMA-CENTRO                           │
│   Transportista:    TRANSPORTES RÁPIDOS SAC                     │
│   Vehículo:         ABC-123 (Furgón 2.5 TM)                    │
│   Conductor:        José Ramírez                                │
│                                                                 │
│ PEDIDOS INCLUIDOS:                                              │
│ # Pedido        Cliente              Dirección         Peso     │
│ ──────────────────────────────────────────────────────────────│
│ PED-2026-001    TEXTIL LIMA SAC      Av. Argentina    85.5 KG  │
│ PED-2026-005    COMERCIAL XYZ SRL    Jr. Cusco        42.0 KG  │
│ PED-2026-007    VENTAS ABC EIRL      Av. Grau         28.5 KG  │
│                                                                 │
│ Total peso:         156.0 KG (63% capacidad)                    │
│ Total bultos:       28 cajas                                    │
│                                                                 │
│ ☑ Generar GR por cada pedido                                   │
│                                                                 │
│ [Confirmar Despacho]                                            │
└─────────────────────────────────────────────────────────────────┘

Al confirmar:
  1. ✅ Genera una GR por cada pedido
  2. ✅ Envía GRs a SUNAT automáticamente
  3. ✅ Notifica al conductor por email/SMS
  4. ✅ Cambia estado de pedidos a "En tránsito"

💡 OPTIMIZACIÓN: El sistema sugiere agrupar pedidos de la misma ruta
   para maximizar el uso del vehículo.

✓ CHECKLIST - LOG COMPLETADO:
  ☐ Transportistas registrados con documentos vigentes
  ☐ Flota de vehículos configurada
  ☐ Rutas principales definidas
  ☐ Primera GR emitida y aceptada por SUNAT
  ☐ Despacho multi-pedido programado correctamente

───────────────────────────────────────────────────────────────────────

3.2 MÓDULO WMS — GESTIÓN DE ALMACENES
───────────────────────────────────────────────────────────────────────

OBJETIVO: Control avanzado con ubicaciones específicas (pasillo-rack-nivel).
PREREQUISITO: INV completado + Almacén físico definido
TIEMPO ESTIMADO: 4-6 horas

▸ PASO 1: DIVIDIR ALMACÉN EN ZONAS

Navegue a: WMS > Zonas > [+ Nueva Zona]

Zonas típicas recomendadas:
┌─────────────────────────────────────────────────────────────────┐
│ Código:         ZONA-RECEP                                      │
│ Nombre:         Zona de Recepción                               │
│ Almacén:        ALM-PT-01                                       │
│ Tipo zona:      Recepción                                       │
│ Área (m²):      50                                              │
│                                                                 │
│ OTRAS ZONAS:                                                    │
│ ZONA-PICK       → Picking (productos de alta rotación)         │
│ ZONA-BULK       → Almacenamiento masivo                         │
│ ZONA-DESP       → Zona de despacho                             │
│ ZONA-CUAR       → Cuarentena (productos pendientes QC)         │
└─────────────────────────────────────────────────────────────────┘

💡 LAYOUT RECOMENDADO:
  Recepción → Cuarentena → Bulk → Picking → Despacho

▸ PASO 2: CREAR UBICACIONES FÍSICAS

Navegue a: WMS > Ubicaciones > [+ Nueva Ubicación]

NOMENCLATURA ESTÁNDAR:
  [ZONA]-[PASILLO]-[RACK]-[NIVEL]-[POSICIÓN]

Ejemplo:
┌─────────────────────────────────────────────────────────────────┐
│ Código ubicación:   PICK-A-01-02-03                             │
│                                                                 │
│ Desglose:                                                       │
│   Zona:             PICK (Picking)                              │
│   Pasillo:          A                                           │
│   Rack:             01                                          │
│   Nivel:            02 (segundo nivel, 1.5m altura)            │
│   Posición:         03 (tercera posición)                       │
│                                                                 │
│ Almacén:            ALM-PT-01                                   │
│ Tipo ubicación:     Estantería fija                             │
│ Capacidad peso:     200 KG                                      │
│ Capacidad volumen:  2 m³                                        │
│                                                                 │
│ Restricciones:                                                  │
│ ☑ Solo productos terminados                                    │
│ ☐ Productos peligrosos                                         │
│ ☐ Control temperatura                                          │
└─────────────────────────────────────────────────────────────────┘

CREAR MÚLTIPLES UBICACIONES:
  PICK-A-01-01-01 hasta PICK-A-01-04-10
  (4 niveles x 10 posiciones = 40 ubicaciones por rack)

💡 TIP: Use importación masiva desde Excel para crear 100+ ubicaciones
   rápidamente.

▸ PASO 3: ASIGNAR PRODUCTOS A UBICACIONES

Navegue a: WMS > Stock por Ubicación > [+ Asignar Producto]

┌─────────────────────────────────────────────────────────────────┐
│ Producto:           POLO-H-M-BLANCO                             │
│ Ubicación:          PICK-A-01-02-03                             │
│ Cantidad:           150 UND                                     │
│ Lote:               LOTE-2026-015                               │
│                                                                 │
│ Es ubicación ppal:  ☑ Sí (para reposición automática)          │
└─────────────────────────────────────────────────────────────────┘

Un producto puede estar en VARIAS ubicaciones:
  PICK-A-01-02-03  → 150 UND (picking)
  BULK-C-05-01-02  → 350 UND (reserva)
  Total producto:     500 UND

💡 ESTRATEGIA ABC:
  • Productos A (alta rotación)  → PICK nivel 2-3 (fácil acceso)
  • Productos B (media rotación) → PICK nivel 1 o 4
  • Productos C (baja rotación)  → BULK

▸ PASO 4: PROCESO DE PUTAWAY (ALMACENAR)

Cuando llega mercadería nueva:

Navegue a: WMS > Tareas > [Filtrar: Putaway]

┌─────────────────────────────────────────────────────────────────┐
│ TAREA: PUT-2026-001                                             │
│ Tipo:               Putaway (almacenar)                         │
│ Origen:             Recepción REC-2026-001                      │
│ Prioridad:          Alta                                        │
│ Estado:             Pendiente                                   │
│                                                                 │
│ DETALLE:                                                        │
│ Producto            Cantidad  Desde           Hacia             │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     200 UND   ZONA-RECEP      PICK-A-01-02-03  │
│ POLO-H-L-AZUL       150 UND   ZONA-RECEP      PICK-A-01-02-04  │
│                                                                 │
│ Asignado a:         Pedro Sánchez (Almacenero)                  │
│ Iniciado:           --                                          │
│ Completado:         --                                          │
│                                                                 │
│ [Iniciar Tarea] [Imprimir Etiquetas]                           │
└─────────────────────────────────────────────────────────────────┘

FLUJO DEL OPERARIO:
  1. Escanea código de barra del producto
  2. Sistema muestra ubicación destino: PICK-A-01-02-03
  3. Lleva el producto a la ubicación
  4. Escanea código de barra de la ubicación (confirmación)
  5. Sistema registra almacenamiento

⚠ IMPORTANTE: El stock NO se actualiza hasta que la tarea se complete.

▸ PASO 5: PROCESO DE PICKING (RECOGER)

Cuando hay un pedido que despachar:

Navegue a: WMS > Tareas > [Filtrar: Picking]

┌─────────────────────────────────────────────────────────────────┐
│ TAREA: PICK-2026-001                                            │
│ Tipo:               Picking                                     │
│ Pedido:             PED-2026-010                                │
│ Cliente:            DISTRIBUIDORA TEXTIL LIMA SAC               │
│ Prioridad:          Alta                                        │
│ Estado:             En proceso                                  │
│                                                                 │
│ LISTA DE PICKING (orden optimizado):                            │
│ Paso  Ubicación        Producto           Cant   ☑              │
│ ──────────────────────────────────────────────────────────────│
│  1    PICK-A-01-02-03  POLO-H-M-BLANCO    50    ☑             │
│  2    PICK-A-01-02-04  POLO-H-L-AZUL      30    ☑             │
│  3    PICK-B-03-01-05  CAMIS-M-M-BLANCA   20    ☐             │
│                                                                 │
│ Asignado a:         María López (Picking)                       │
│ Iniciado:           26/02/2026 10:15                            │
│ Destino:            ZONA-DESP                                   │
│                                                                 │
│ [Completar Tarea]                                               │
└─────────────────────────────────────────────────────────────────┘

💡 OPTIMIZACIÓN DE RUTA: El sistema ordena los productos para minimizar
   el recorrido del operario (pasillo A, luego B, luego C).

▸ PASO 6: REABASTECIMIENTO AUTOMÁTICO

Configurar reglas:

┌─────────────────────────────────────────────────────────────────┐
│ Producto:           POLO-H-M-BLANCO                             │
│ Ubicación picking:  PICK-A-01-02-03                             │
│                                                                 │
│ Stock mínimo:       50 UND                                      │
│ Reabastecer hasta:  150 UND                                     │
│ Desde ubicación:    BULK-C-05-01-02                             │
│                                                                 │
│ ☑ Generar tarea automáticamente cuando stock < mínimo          │
└─────────────────────────────────────────────────────────────────┘

Cuando stock en PICK baja de 50, el sistema crea automáticamente:
  Tarea: REAB-2026-001
  Mover: 100 UND desde BULK a PICK

✓ CHECKLIST - WMS COMPLETADO:
  ☐ Almacén dividido en zonas funcionales
  ☐ Ubicaciones creadas con nomenclatura estándar
  ☐ Productos asignados a ubicaciones estratégicas
  ☐ Primera tarea de putaway completada
  ☐ Primera tarea de picking ejecutada
  ☐ Reabastecimiento automático configurado

───────────────────────────────────────────────────────────────────────

3.3 MÓDULO QMS — CONTROL DE CALIDAD
───────────────────────────────────────────────────────────────────────

OBJETIVO: Inspecciones de calidad con muestreo AQL y control de no conformidades.
PREREQUISITO: INV + PUR completados
TIEMPO ESTIMADO: 2-3 horas

▸ PASO 1: DEFINIR PARÁMETROS DE CALIDAD

Navegue a: QMS > Parámetros de Calidad > [+ Nuevo Parámetro]

EJEMPLO - INSPECCIÓN DE TELAS:
┌─────────────────────────────────────────────────────────────────┐
│ Código:             PARAM-TELA-001                              │
│ Nombre:             Inspección de Telas                         │
│ Aplica a categoría: MP-TELA                                     │
│                                                                 │
│ CARACTERÍSTICAS A MEDIR:                                        │
│ 1. Color                → Visual    → Muestra estándar         │
│ 2. Ancho                → Métrico   → 1.80 m ± 2 cm            │
│ 3. Gramaje              → Métrico   → 180 g/m² ± 5%            │
│ 4. Resistencia          → Test      → > 20 N                   │
│ 5. Pilling              → Visual    → Grado 4 mínimo           │
│                                                                 │
│ Método inspección:      100% ○  Muestreo ◉                     │
└─────────────────────────────────────────────────────────────────┘

💡 TIPOS DE CARACTERÍSTICAS:
  • Variables: Se miden (peso, largo, ancho)
  • Atributos: Pasa/No pasa (color, defectos visuales)

▸ PASO 2: CREAR PLAN DE INSPECCIÓN

Navegue a: QMS > Planes de Inspección > [+ Nuevo Plan]

┌─────────────────────────────────────────────────────────────────┐
│ Código:             PLAN-RECEP-TELA                             │
│ Nombre:             Plan de Recepción de Telas                  │
│ Tipo inspección:    Recepción de Compra                         │
│ Proveedor:          TEXTILES DEL NORTE SAC                      │
│                                                                 │
│ MUESTREO AQL (Acceptable Quality Level):                        │
│   Nivel inspección: II (normal)                                 │
│   Tamaño lote:      Variable (según recepción)                  │
│   AQL aceptable:    2.5% (máx defectos permitidos)             │
│                                                                 │
│ TABLA DE MUESTREO (según MIL-STD-105E):                         │
│ Tamaño Lote    Muestra    Acepta si    Rechaza si               │
│ ──────────────────────────────────────────────────────────────│
│ 2-8            2          0 defectos   1+ defectos              │
│ 9-15           3          0 defectos   1+ defectos              │
│ 16-25          5          0 defectos   1+ defectos              │
│ 26-50          8          1 defecto    2+ defectos              │
│ 51-90          13         1 defecto    2+ defectos              │
│ 91-150         20         2 defectos   3+ defectos              │
│ 151-280        32         3 defectos   4+ defectos              │
│ 281-500        50         5 defectos   6+ defectos              │
│                                                                 │
│ Parámetros a verificar:                                         │
│ ☑ PARAM-TELA-001 (Inspección de Telas)                         │
└─────────────────────────────────────────────────────────────────┘

⚠ AQL 2.5%: Significa que toleramos hasta 2.5% de defectos en el lote.
   Valores típicos: 0.65% (muy estricto), 1.5%, 2.5%, 4.0% (permisivo)

▸ PASO 3: EJECUTAR INSPECCIÓN

Navegue a: QMS > Inspecciones > [+ Nueva Inspección]

┌─────────────────────────────────────────────────────────────────┐
│ Número:             INSP-2026-001                               │
│ Tipo:               Recepción de Compra                         │
│ Fecha:              26/02/2026                                  │
│                                                                 │
│ ORIGEN:                                                         │
│   Recepción:        REC-2026-001                                │
│   Proveedor:        TEXTILES DEL NORTE SAC                      │
│   OC:               OC-2026-001                                 │
│                                                                 │
│ PRODUCTO INSPECCIONADO:                                         │
│   Producto:         TELA-JERSEY-BL-24                           │
│   Lote:             LOTE-TDN-2026-045                           │
│   Cantidad total:   500 MT (10 rollos)                          │
│                                                                 │
│ PLAN APLICADO:      PLAN-RECEP-TELA                             │
│ Tamaño muestra:     13 MT (según tabla AQL)                     │
│                                                                 │
│ Inspector:          Carlos Vega (QC Supervisor)                 │
│                                                                 │
│ [Iniciar Inspección]                                            │
└─────────────────────────────────────────────────────────────────┘

REGISTRO DE RESULTADOS:
┌─────────────────────────────────────────────────────────────────┐
│ MUESTRA 1 - Rollo #3:                                           │
│   Color:         ✓ Conforme (match con muestra estándar)       │
│   Ancho:         ✓ 1.81 m (dentro tolerancia ±2cm)             │
│   Gramaje:       ✓ 178 g/m² (dentro tolerancia ±5%)            │
│   Resistencia:   ✓ 22 N (> 20 N mínimo)                        │
│   Pilling:       ✓ Grado 4 (cumple mínimo)                     │
│   Estado:        ✓ CONFORME                                     │
│                                                                 │
│ MUESTRA 2 - Rollo #7:                                           │
│   Color:         ✗ No conforme (tono amarillento)              │
│   Estado:        ✗ NO CONFORME                                  │
│                                                                 │
│ [...continuar con 11 muestras más...]                           │
│                                                                 │
│ RESULTADO FINAL:                                                │
│   Muestras tomadas:      13                                     │
│   Conformes:             12                                     │
│   No conformes:          1                                      │
│   % Defectos:            7.7% (1/13)                            │
│                                                                 │
│   Criterio AQL 2.5%:     Rechaza si ≥ 2 defectos               │
│   Decisión:              ✓ LOTE ACEPTADO                        │
│                                                                 │
│ Observaciones: Rollo #7 presenta desviación de color.          │
│                Segregar para devolución al proveedor.           │
│                                                                 │
│ [Aprobar Lote] [Rechazar Lote]                                 │
└─────────────────────────────────────────────────────────────────┘

Al aprobar:
  • Stock pasa de "Cuarentena" a "Disponible"
  • Se puede usar en producción o venta

Al rechazar:
  • Stock queda bloqueado
  • Se genera automáticamente NC (No Conformidad)

▸ PASO 4: GESTIONAR NO CONFORMIDADES

Si se detecta un problema:

Navegue a: QMS > No Conformidades > [+ Nueva NC]

┌─────────────────────────────────────────────────────────────────┐
│ Número:             NC-2026-001                                 │
│ Fecha detección:    26/02/2026                                  │
│ Tipo:               Proveedor externo                           │
│ Severidad:          Media ◉  Alta ○  Baja ○                    │
│                                                                 │
│ ORIGEN:                                                         │
│   Inspección:       INSP-2026-001                               │
│   Producto:         TELA-JERSEY-BL-24                           │
│   Lote:             LOTE-TDN-2026-045                           │
│   Proveedor:        TEXTILES DEL NORTE SAC                      │
│                                                                 │
│ DESCRIPCIÓN:                                                    │
│ Rollo #7 (50 metros) presenta desviación de color. Tono        │
│ amarillento en lugar de blanco puro. No cumple especificación. │
│                                                                 │
│ CANTIDAD AFECTADA:  50 MT (1 rollo de 10)                       │
│                                                                 │
│ ANÁLISIS DE CAUSA RAÍZ (5 Porqués):                             │
│ 1. ¿Por qué? → Color desviado                                  │
│ 2. ¿Por qué? → Proceso de blanqueado incompleto                │
│ 3. ¿Por qué? → Control de temperatura inadecuado               │
│ 4. ¿Por qué? → Sensor de temperatura descalibrado              │
│ 5. ¿Por qué? → Falta mantenimiento preventivo                  │
│                                                                 │
│ CAUSA RAÍZ: Falta de programa de mantenimiento preventivo      │
│             en equipos de blanqueado del proveedor              │
│                                                                 │
│ ACCIÓN CORRECTIVA:                                              │
│ ☑ Devolver rollo #7 al proveedor                               │
│ ☑ Solicitar reemplazo                                          │
│ ☑ Auditar proceso de blanqueado en próxima visita              │
│                                                                 │
│ ACCIÓN PREVENTIVA:                                              │
│ ☑ Solicitar certificado de calibración de equipos              │
│ ☑ Aumentar frecuencia de inspección a 100% por 3 meses         │
│                                                                 │
│ Responsable:        Carlos Vega (QC Supervisor)                 │
│ Fecha compromiso:   05/03/2026                                  │
│ Estado:             Abierta                                     │
│                                                                 │
│ [Cerrar NC] [Generar Reporte]                                  │
└─────────────────────────────────────────────────────────────────┘

💡 METODOLOGÍA 5 PORQUÉS: Preguntar "¿por qué?" sucesivamente hasta
   encontrar la causa raíz real del problema.

⚠ SEGUIMIENTO: Las NC abiertas aparecen en el dashboard. El sistema
   alerta si no se cierra en el plazo comprometido.

✓ CHECKLIST - QMS COMPLETADO:
  ☐ Parámetros de calidad definidos por tipo de producto
  ☐ Planes de inspección con muestreo AQL configurados
  ☐ Primera inspección de recepción ejecutada
  ☐ Lote aprobado o rechazado según criterios
  ☐ No conformidad registrada con análisis causa raíz
  ☐ Acciones correctivas y preventivas definidas

═══════════════════════════════════════════════════════════════════════

FIN DE LA PARTE 3

PRÓXIMA PARTE 4:
  - MFG (Manufactura)
  - MRP (Planeamiento de Materiales)
  - MPS (Plan Maestro de Producción)
  - MNT (Mantenimiento)
  - SVC (Órdenes de Servicio)

═══════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 4 DE 8
                     MÓDULOS DE PRODUCCIÓN
═══════════════════════════════════════════════════════════════════════

PARTE 4: MÓDULOS DE PRODUCCIÓN

═══════════════════════════════════════════════════════════════════════

4.1 MÓDULO MFG — MANUFACTURA
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar producción con BOM, órdenes de producción y costeo real.
PREREQUISITO: ORG + INV completados
TIEMPO ESTIMADO: 6-8 horas (módulo complejo)

▸ PASO 1: CREAR CENTROS DE TRABAJO

Navegue a: MFG > Centros de Trabajo > [+ Nuevo Centro]

EJEMPLO - EMPRESA TEXTIL:
┌─────────────────────────────────────────────────────────────────┐
│ Código:             CT-CORTE-01                                 │
│ Nombre:             Mesa de Corte #1                            │
│ Tipo:               Máquina                                     │
│ Sucursal:           SUC-LIMA-01                                 │
│ Departamento:       OPER-PROD                                   │
│                                                                 │
│ CAPACIDAD:                                                      │
│   Horas diarias:    8 hrs                                       │
│   Días semana:      6 días                                      │
│   Eficiencia:       85% (pérdidas por setup, mantenimiento)     │
│   Capacidad real:   40.8 hrs/semana                             │
│                                                                 │
│ COSTOS:                                                         │
│   Costo hora MOD:   S/ 12.00 (operarios)                       │
│   Costo hora CIF:   S/ 8.50 (depreciación, energía, manto)     │
│   Costo total/hora: S/ 20.50                                    │
│                                                                 │
│ Activo vinculado:   ACT-CORTADORA-AUTOMATICA-01 (MNT)          │
│ Estado:             ✓ Activo                                    │
└─────────────────────────────────────────────────────────────────┘

CENTROS TÍPICOS EN TEXTIL:
  CT-CORTE-01     → Corte de tela
  CT-COSTURA-01   → Costura recta
  CT-COSTURA-02   → Costura overlock
  CT-ESTAMPADO    → Estampado/serigrafía
  CT-EMPAQUE      → Empaque final

💡 IMPORTANTE: El costo/hora incluye:
  • MOD: Sueldos de operarios asignados
  • CIF: Depreciación máquina + energía + mantenimiento + supervisión

▸ PASO 2: DEFINIR OPERACIONES

Navegue a: MFG > Operaciones > [+ Nueva Operación]

┌─────────────────────────────────────────────────────────────────┐
│ Código:             OP-CORTE-POLO                               │
│ Nombre:             Corte de polo (molde estándar)              │
│ Descripción:        Cortar piezas según molde: delantero,       │
│                     espalda, mangas (x2), cuello                │
│                                                                 │
│ Centro trabajo:     CT-CORTE-01                                 │
│ Tiempo estándar:    0.10 hrs/prenda (6 min)                     │
│ Setup time:         0.25 hrs (15 min preparación)               │
│                                                                 │
│ Habilidades requeridas:                                         │
│ • Lectura de moldes                                             │
│ • Manejo de cortadora automática                                │
└─────────────────────────────────────────────────────────────────┘

OTRAS OPERACIONES:
  OP-COSTURA-POLO     → 0.25 hrs/prenda
  OP-OJALADO          → 0.05 hrs/prenda
  OP-PLANCHADO        → 0.08 hrs/prenda
  OP-EMPAQUE          → 0.03 hrs/prenda

▸ PASO 3: CREAR LISTA DE MATERIALES (BOM)

Navegue a: MFG > Lista de Materiales > [+ Nueva BOM]

EJEMPLO - BOM DE POLO BLANCO TALLA M:
┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Producto:         POLO-H-M-BLANCO                             │
│   Versión BOM:      1.0                                         │
│   Fecha vigencia:   01/02/2026                                  │
│   Estado:           ✓ Activa                                    │
│   Cantidad base:    1 UND (1 polo)                              │
│                                                                 │
│ COMPONENTES:                                                    │
│ #  Componente           Cantidad  UM   Desperdicio  Subtotal   │
│ ──────────────────────────────────────────────────────────────│
│ 1  TELA-JERSEY-BL-24    1.20     MT    5%          1.26 MT    │
│ 2  HILO-POLY-BL-001     0.025    KG    10%         0.0275 KG  │
│ 3  BOTON-BLANCO-15MM    4        UND   2%          4.08 UND   │
│ 4  ETIQUETA-MARCA       1        UND   0%          1 UND      │
│ 5  ETIQUETA-TALLA-M     1        UND   0%          1 UND      │
│ 6  BOLSA-INDIVIDUAL     1        UND   0%          1 UND      │
│                                                                 │
│ COSTO ESTIMADO MATERIALES:                                      │
│   TELA-JERSEY-BL-24:    1.26 MT × S/ 8.50  = S/ 10.71         │
│   HILO-POLY-BL-001:     0.0275 KG × S/ 45  = S/ 1.24          │
│   BOTON-BLANCO-15MM:    4.08 UND × S/ 0.15 = S/ 0.61          │
│   ETIQUETA-MARCA:       1 UND × S/ 0.30    = S/ 0.30          │
│   ETIQUETA-TALLA-M:     1 UND × S/ 0.10    = S/ 0.10          │
│   BOLSA-INDIVIDUAL:     1 UND × S/ 0.20    = S/ 0.20          │
│   ─────────────────────────────────────────                    │
│   TOTAL MATERIAL:                            S/ 13.16          │
└─────────────────────────────────────────────────────────────────┘

⚠ DESPERDICIO: Incluya siempre el % de merma real.
  • Tela: 5% (recortes, defectos)
  • Hilo: 10% (puntas, roturas)
  • Botones: 2% (rotos al coser)

💡 CANTIDAD BASE: Siempre use cantidad = 1 para facilitar cálculos.
   Si quiere producir 100 polos, el sistema multiplica automáticamente.

▸ PASO 4: CREAR RUTA DE FABRICACIÓN

Navegue a: MFG > Rutas de Fabricación > [+ Nueva Ruta]

┌─────────────────────────────────────────────────────────────────┐
│ Producto:           POLO-H-M-BLANCO                             │
│ Versión ruta:       1.0                                         │
│ Fecha vigencia:     01/02/2026                                  │
│                                                                 │
│ SECUENCIA DE OPERACIONES:                                       │
│ Seq  Operación          Centro        Tiempo  Setup  Crítica   │
│ ──────────────────────────────────────────────────────────────│
│ 10   OP-CORTE-POLO      CT-CORTE-01   0.10h  0.25h  ☑         │
│ 20   OP-COSTURA-POLO    CT-COSTURA-01 0.25h  0.50h  ☑         │
│ 30   OP-OJALADO         CT-COSTURA-02 0.05h  0.10h  ☐         │
│ 40   OP-PLANCHADO       CT-PLANCHADO  0.08h  0.00h  ☐         │
│ 50   OP-EMPAQUE         CT-EMPAQUE    0.03h  0.00h  ☐         │
│                                                                 │
│ Tiempo total/prenda:    0.51 hrs (30.6 minutos)                │
│ Setup total lote:       0.85 hrs (51 minutos)                  │
│                                                                 │
│ COSTO MOD ESTIMADO (100 polos):                                 │
│   Operación          Tiempo   Costo/h  Total                   │
│   Corte:             10.0h    S/ 20.50  S/ 205.00              │
│   Costura:           25.0h    S/ 18.00  S/ 450.00              │
│   Ojalado:           5.0h     S/ 18.00  S/ 90.00               │
│   Planchado:         8.0h     S/ 15.00  S/ 120.00              │
│   Empaque:           3.0h     S/ 12.00  S/ 36.00               │
│   Setup total:       0.85h    (promedio) S/ 15.50              │
│   ─────────────────────────────────────────                    │
│   TOTAL MOD:                             S/ 916.50             │
│   Costo MOD/prenda:                      S/ 9.17               │
└─────────────────────────────────────────────────────────────────┘

💡 OPERACIÓN CRÍTICA: Marca las operaciones cuello de botella.
   El sistema alertará si hay sobrecarga en estos centros.

▸ PASO 5: CREAR ORDEN DE PRODUCCIÓN

Navegue a: MFG > Órdenes de Producción > [+ Nueva OP]

┌─────────────────────────────────────────────────────────────────┐
│ CABECERA:                                                       │
│   Número OP:        OP-2026-001                                 │
│   Producto:         POLO-H-M-BLANCO                             │
│   Cantidad:         200 UND                                     │
│                                                                 │
│ FECHAS:                                                         │
│   Fecha creación:   27/02/2026                                  │
│   Inicio prog:      28/02/2026                                  │
│   Fin prog:         05/03/2026                                  │
│                                                                 │
│ ORIGEN:                                                         │
│   Tipo:             Por pedido ◉  Para inventario ○            │
│   Pedido origen:    PED-2026-015                                │
│   Cliente:          COMERCIAL TEXTIL ABC SAC                    │
│                                                                 │
│ MATERIALES REQUERIDOS (según BOM):                              │
│ Componente           Necesario  Stock   Reservar  Faltante     │
│ ──────────────────────────────────────────────────────────────│
│ TELA-JERSEY-BL-24    252 MT     480 MT  252 MT    --          │
│ HILO-POLY-BL-001     5.5 KG     12 KG   5.5 KG    --          │
│ BOTON-BLANCO-15MM    816 UND    5000    816 UND   --          │
│ ETIQUETA-MARCA       200 UND    150     200 UND   50 UND ⚠    │
│ ETIQUETA-TALLA-M     200 UND    500     200 UND   --          │
│ BOLSA-INDIVIDUAL     200 UND    1000    200 UND   --          │
│                                                                 │
│ ⚠ ALERTA: ETIQUETA-MARCA tiene faltante de 50 UND             │
│          Generar solicitud de compra automática                 │
│                                                                 │
│ COSTOS ESTIMADOS:                                               │
│   Material directo:  S/ 2,632.00 (200 × S/ 13.16)             │
│   MOD:               S/ 1,834.00 (200 × S/ 9.17)               │
│   CIF:               S/ 918.00 (estimado 50% MOD)              │
│   ─────────────────────────────────────────                    │
│   COSTO TOTAL:       S/ 5,384.00                                │
│   Costo unitario:    S/ 26.92 por polo                          │
│                                                                 │
│ Estado:             Planificada                                 │
│                                                                 │
│ [Liberar OP] [Generar SC Faltantes]                            │
└─────────────────────────────────────────────────────────────────┘

FLUJO DE ESTADOS:
  Planificada → Liberada → En proceso → En control calidad → Terminada

Al LIBERAR la OP:
  1. ✅ Reserva materiales en inventario
  2. ✅ Genera órdenes de compra sugeridas para faltantes
  3. ✅ Crea tareas en centros de trabajo
  4. ✅ OP lista para iniciar producción

▸ PASO 6: REGISTRAR CONSUMO DE MATERIALES

Navegue a: MFG > Consumo de Materiales > [+ Nuevo Consumo]
           O desde OP: [Registrar Consumo]

┌─────────────────────────────────────────────────────────────────┐
│ OP:                 OP-2026-001                                 │
│ Fecha consumo:      28/02/2026                                  │
│ Turno:              Mañana                                      │
│ Supervisor:         Pedro Gómez                                 │
│                                                                 │
│ MATERIALES CONSUMIDOS:                                          │
│ Componente           Planeado  Consumido  Diferencia  Estado   │
│ ──────────────────────────────────────────────────────────────│
│ TELA-JERSEY-BL-24    252 MT    255 MT     +3 MT      ⚠ Exceso │
│ HILO-POLY-BL-001     5.5 KG    5.2 KG     -0.3 KG    ✓ OK     │
│ BOTON-BLANCO-15MM    816 UND   820 UND    +4 UND     ✓ OK     │
│ ETIQUETA-MARCA       200 UND   200 UND    --         ✓ OK     │
│ ETIQUETA-TALLA-M     200 UND   200 UND    --         ✓ OK     │
│ BOLSA-INDIVIDUAL     200 UND   200 UND    --         ✓ OK     │
│                                                                 │
│ Observaciones: Exceso de tela por defectos en 3 rollos         │
│                que no pasaron control de calidad.               │
│                                                                 │
│ ☑ Generar movimiento de inventario (SAL-PROD)                  │
│ ☑ Actualizar costo real de la OP                               │
│                                                                 │
│ [Registrar Consumo]                                             │
└─────────────────────────────────────────────────────────────────┘

Al registrar:
  • ✅ Descuenta materiales del inventario
  • ✅ Libera la reserva
  • ✅ Actualiza costo real de materiales

💡 VARIACIONES: Las diferencias entre planeado vs consumido se reflejan
   en el análisis de variaciones de costo (módulo CST).

▸ PASO 7: REGISTRAR AVANCE POR OPERACIÓN

Navegue a: MFG > OP > [Seleccionar OP-2026-001] > Pestaña "Operaciones"

┌─────────────────────────────────────────────────────────────────┐
│ OP: OP-2026-001 - POLO-H-M-BLANCO - 200 UND                     │
│                                                                 │
│ AVANCE POR OPERACIÓN:                                           │
│ Seq  Operación      Centro      Planeado  Producido  Pendiente │
│ ──────────────────────────────────────────────────────────────│
│ 10   Corte          CT-CORTE    200       200       0    ✓    │
│ 20   Costura        CT-COSTURA  200       150       50   🔄   │
│ 30   Ojalado        CT-COSTURA2 200       0         200  ⏳   │
│ 40   Planchado      CT-PLANCHA  200       0         200  ⏳   │
│ 50   Empaque        CT-EMPAQUE  200       0         200  ⏳   │
│                                                                 │
│ [Registrar Avance Operación 20]                                 │
└─────────────────────────────────────────────────────────────────┘

REGISTRAR AVANCE - OPERACIÓN 20 (COSTURA):
┌─────────────────────────────────────────────────────────────────┐
│ Fecha:              28/02/2026                                  │
│ Turno:              Mañana (8:00 - 17:00)                       │
│ Operario:           María Sánchez                               │
│                                                                 │
│ Cantidad producida: 150 UND                                     │
│ Cantidad buena:     145 UND                                     │
│ Cantidad scrap:     5 UND (costura defectuosa)                  │
│                                                                 │
│ TIEMPO:                                                         │
│   Hora inicio:      08:30                                       │
│   Hora fin:         16:45                                       │
│   Tiempo total:     8.25 hrs                                    │
│   Tiempo productivo: 7.5 hrs (descontando breaks)              │
│                                                                 │
│ Tiempo estándar:    150 × 0.25h = 37.5 hrs                     │
│ Tiempo real:        7.5 hrs                                     │
│ Eficiencia:         500% ⚠ ERROR - REVISAR                     │
│                                                                 │
│ ⚠ El operario reportó trabajo de 1 persona pero el estándar   │
│   es para lote completo. Ajustar: 7.5h × 5 operarios = 37.5h  │
│                                                                 │
│ [Corregir] Operarios trabajando: 5 personas                     │
│ Tiempo real ajustado: 37.5 hrs                                  │
│ Eficiencia real: 100% ✓                                         │
│                                                                 │
│ [Registrar]                                                     │
└─────────────────────────────────────────────────────────────────┘

💡 CAPTURA DE MOD: El tiempo real capturado se usa para costear
   mano de obra directa de la OP.

▸ PASO 8: FINALIZAR ORDEN DE PRODUCCIÓN

Cuando todas las operaciones están completas:

Navegue a: MFG > OP > [Seleccionar OP-2026-001] > [Finalizar OP]

┌─────────────────────────────────────────────────────────────────┐
│ OP-2026-001 - RESUMEN DE PRODUCCIÓN                             │
│                                                                 │
│ Cantidad programada:    200 UND                                 │
│ Cantidad producida:     195 UND                                 │
│ Cantidad scrap:         5 UND (2.5%)                            │
│                                                                 │
│ COSTOS REALES:                                                  │
│                        Planeado    Real      Variación          │
│ ──────────────────────────────────────────────────────────────│
│ Material directo:      S/ 2,632    S/ 2,680  +S/ 48 (1.8%)    │
│ Mano obra directa:     S/ 1,834    S/ 1,834  --                │
│ CIF:                   S/ 918      S/ 945    +S/ 27 (2.9%)    │
│ ─────────────────────────────────────────────                  │
│ TOTAL:                 S/ 5,384    S/ 5,459  +S/ 75 (1.4%)    │
│                                                                 │
│ Costo unitario planeado:  S/ 26.92                              │
│ Costo unitario real:      S/ 28.00 (+S/ 1.08)                  │
│                                                                 │
│ ACCIONES AL FINALIZAR:                                          │
│ ☑ Generar entrada de inventario (195 UND)                      │
│ ☑ Actualizar costo promedio del producto                       │
│ ☑ Cerrar reservas de materiales                                │
│ ☑ Generar asiento contable                                     │
│ ☑ Enviar a inspección de calidad (QMS)                         │
│                                                                 │
│ [Finalizar y Generar Movimiento]                                │
└─────────────────────────────────────────────────────────────────┘

Al finalizar:
  • Producto terminado entra al almacén ALM-PT-01
  • Costo se actualiza a S/ 28.00 (costo real)
  • QMS puede inspeccionar antes de liberar para venta

✓ CHECKLIST - MFG COMPLETADO:
  ☐ Centros de trabajo configurados con costos
  ☐ Operaciones definidas con tiempos estándar
  ☐ BOM creada con todos los componentes y desperdicios
  ☐ Ruta de fabricación secuenciada
  ☐ Primera OP generada y liberada
  ☐ Consumo de materiales registrado
  ☐ Avance por operación capturado
  ☐ OP finalizada con entrada de PT al almacén

───────────────────────────────────────────────────────────────────────

4.2 MÓDULO MRP — PLANEAMIENTO DE MATERIALES
───────────────────────────────────────────────────────────────────────

OBJETIVO: Calcular automáticamente necesidades de materiales y generar órdenes sugeridas.
PREREQUISITO: MFG completado (BOM activos)
TIEMPO ESTIMADO: 2-3 horas

▸ PASO 1: CREAR PLAN MAESTRO MRP

Navegue a: MRP > Plan Maestro > [+ Nuevo Plan]

┌─────────────────────────────────────────────────────────────────┐
│ Código plan:        MRP-2026-03                                 │
│ Descripción:        Plan de Marzo 2026                          │
│ Fecha inicio:       01/03/2026                                  │
│ Fecha fin:          31/03/2026                                  │
│ Horizonte:          4 semanas                                   │
│                                                                 │
│ CONFIGURACIÓN:                                                  │
│   Bucket (periodo):   Semanal ◉  Diario ○  Mensual ○          │
│   Considerar:         ☑ Pedidos confirmados                    │
│                       ☑ Pronóstico de demanda                  │
│                       ☑ Stock de seguridad                     │
│   Método:             Regenerativo ◉  Neto ○                   │
│                                                                 │
│ [Ejecutar MRP]                                                  │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 2: REVISAR NECESIDADES BRUTAS

Navegue a: MRP > Necesidades Brutas

┌─────────────────────────────────────────────────────────────────┐
│ Producto: POLO-H-M-BLANCO                                       │
│                                                                 │
│ Periodo    Pedidos  Pronóstico  Stock Seg  Necesidad Bruta     │
│ ──────────────────────────────────────────────────────────────│
│ Sem 1      200      150         50         400                 │
│ Sem 2      150      150         50         350                 │
│ Sem 3      100      150         50         300                 │
│ Sem 4      180      150         50         380                 │
│                                                                 │
│ Total necesidad: 1,430 UND                                      │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 3: EXPLOSIÓN DE MATERIALES

El sistema calcula automáticamente:

┌─────────────────────────────────────────────────────────────────┐
│ EXPLOSIÓN MULTINIVEL - POLO-H-M-BLANCO (1,430 UND)             │
│                                                                 │
│ Nivel 0: POLO-H-M-BLANCO                1,430 UND               │
│   │                                                             │
│   ├─ TELA-JERSEY-BL-24                  1,801.8 MT             │
│   │  (1430 × 1.26)                                             │
│   │                                                             │
│   ├─ HILO-POLY-BL-001                   39.33 KG               │
│   │  (1430 × 0.0275)                                           │
│   │                                                             │
│   ├─ BOTON-BLANCO-15MM                  5,834 UND              │
│   │  (1430 × 4.08)                                             │
│   │                                                             │
│   ├─ ETIQUETA-MARCA                     1,430 UND              │
│   ├─ ETIQUETA-TALLA-M                   1,430 UND              │
│   └─ BOLSA-INDIVIDUAL                   1,430 UND              │
│                                                                 │
│ Considerando:                                                   │
│   Stock actual:      500 UND POLO-H-M-BLANCO                   │
│   Stock seguridad:   50 UND                                    │
│   En tránsito:       0 UND                                     │
│                                                                 │
│ Necesidad neta: 1,430 - 500 + 50 = 980 UND a producir          │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 4: REVISAR ÓRDENES SUGERIDAS

Navegue a: MRP > Órdenes Sugeridas

┌─────────────────════════════════════════════════════════════════┐
│ ÓRDENES DE PRODUCCIÓN SUGERIDAS:                               │
│ Producto         Cantidad  Fecha inicio  Tipo         Acción   │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO  400 UND   22/02/2026    OP Planificada  [✓]  │
│ POLO-H-M-BLANCO  350 UND   29/02/2026    OP Planificada  [✓]  │
│ POLO-H-M-BLANCO  230 UND   07/03/2026    OP Planificada  [✓]  │
│                                                                 │
│ ÓRDENES DE COMPRA SUGERIDAS:                                   │
│ Componente            Cantidad  Fecha entrega  Acción          │
│ ──────────────────────────────────────────────────────────────│
│ TELA-JERSEY-BL-24     1,800 MT  20/02/2026    [Generar OC]    │
│ HILO-POLY-BL-001      40 KG     20/02/2026    [Generar OC]    │
│ BOTON-BLANCO-15MM     5,850 UND 22/02/2026    [Generar OC]    │
│ ETIQUETA-MARCA        1,500 UND 22/02/2026    [Generar OC]    │
│                                                                 │
│ [Aprobar y Generar Todas]                                       │
└─────────────────────────────────────────────────────────────────┘

💡 FECHAS CALCULADAS: El MRP calcula hacia atrás (backward scheduling)
   desde la fecha de entrega requerida, considerando lead times.

⚠ RECOMENDACIÓN: Revise las sugerencias antes de aprobar. El MRP
   es una guía, no una orden absoluta.

✓ CHECKLIST - MRP COMPLETADO:
  ☐ Plan maestro MRP configurado
  ☐ Necesidades brutas calculadas correctamente
  ☐ Explosión de materiales ejecutada
  ☐ Órdenes sugeridas generadas
  ☐ Primera OC generada desde MRP

───────────────────────────────────────────────────────────────────────

4.3 MÓDULO MPS — PLAN MAESTRO DE PRODUCCIÓN
───────────────────────────────────────────────────────────────────────

OBJETIVO: Programar QUÉ producir y CUÁNDO, balanceando demanda vs capacidad.
PREREQUISITO: MFG + MRP completados
TIEMPO ESTIMADO: 2 horas

▸ PASO 1: CREAR PRONÓSTICO DE DEMANDA

Navegue a: MPS > Pronósticos > [+ Nuevo Pronóstico]

┌─────────────────────────────────────────────────────────────────┐
│ Producto:           POLO-H-M-BLANCO                             │
│ Periodo:            Marzo 2026                                  │
│ Método:             Promedio móvil 3 meses                      │
│                                                                 │
│ HISTÓRICO (últimos 3 meses):                                    │
│   Diciembre 2025:   580 UND                                     │
│   Enero 2026:       620 UND                                     │
│   Febrero 2026:     650 UND                                     │
│   Promedio:         617 UND/mes                                 │
│                                                                 │
│ AJUSTES:                                                        │
│   Tendencia:        +5% (temporada alta primavera)             │
│   Eventos:          +50 UND (campaña escolar)                  │
│                                                                 │
│ PRONÓSTICO FINAL:                                               │
│   Marzo 2026:       650 UND (617 × 1.05 + 50)                  │
│                                                                 │
│ Desglose semanal:                                               │
│   Semana 1:         150 UND                                     │
│   Semana 2:         160 UND                                     │
│   Semana 3:         170 UND                                     │
│   Semana 4:         170 UND                                     │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 2: CREAR PLAN DE PRODUCCIÓN

Navegue a: MPS > Planes de Producción > [+ Nuevo Plan]

┌─────────────────────────────────────────────────────────────────┐
│ Producto:           POLO-H-M-BLANCO                             │
│ Periodo:            Marzo 2026                                  │
│                                                                 │
│ BALANCE DEMANDA vs CAPACIDAD:                                   │
│         Pronóstico  Pedidos  Total    Capacidad  Balance       │
│         Demanda     Firmes   Demanda  Disponible                │
│ ──────────────────────────────────────────────────────────────│
│ Sem 1   150         200      350      300        -50 ⚠        │
│ Sem 2   160         100      260      300        +40           │
│ Sem 3   170         80       250      300        +50           │
│ Sem 4   170         120      290      300        +10           │
│                                                                 │
│ ⚠ SOBRECARGA en Semana 1: Falta capacidad de 50 UND           │
│                                                                 │
│ ACCIONES SUGERIDAS:                                             │
│ • Adelantar 50 UND de Sem 1 a última semana de Febrero         │
│ • O programar horas extra en centros críticos                  │
│                                                                 │
│ PLAN AJUSTADO:                                                  │
│ Sem 1:  300 UND (máxima capacidad)                             │
│ Sem 2:  260 UND                                                 │
│ Sem 3:  250 UND                                                 │
│ Sem 4:  290 UND                                                 │
│                                                                 │
│ Faltante Sem 1 (50 UND) → Producir en Febrero con HE           │
│                                                                 │
│ [Aprobar Plan]                                                  │
└─────────────────────────────────────────────────────────────────┘

💡 MPS vs MRP:
  • MPS: Qué producir (productos terminados)
  • MRP: Qué comprar (componentes)

✓ CHECKLIST - MPS COMPLETADO:
  ☐ Pronóstico de demanda creado
  ☐ Plan de producción balanceado vs capacidad
  ☐ Sobrecargas identificadas y resueltas

───────────────────────────────────────────────────────────────────────

4.4 MÓDULO MNT — MANTENIMIENTO
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar mantenimiento preventivo y correctivo de maquinaria.
PREREQUISITO: MFG completado (centros de trabajo)
TIEMPO ESTIMADO: 2 horas

▸ PASO 1: REGISTRAR ACTIVOS

Navegue a: MNT > Activos > [+ Nuevo Activo]

┌─────────────────────────────────────────────────────────────────┐
│ Código:             ACT-CORTADORA-01                            │
│ Nombre:             Cortadora Automática Eastman                │
│ Categoría:          Maquinaria de producción                    │
│ Fabricante:         Eastman Machine Company                     │
│ Modelo:             Brute 629X                                  │
│ Año fabricación:    2020                                        │
│                                                                 │
│ Centro trabajo:     CT-CORTE-01                                 │
│ Ubicación:          Planta Lima - Área Corte                    │
│ Responsable:        Pedro Gómez (Jefe Producción)               │
│                                                                 │
│ CRITICIDAD:         Alta ◉  Media ○  Baja ○                    │
│   Justificación:    Único equipo de corte. Parada = stop total │
│                                                                 │
│ DATOS TÉCNICOS:                                                 │
│   Potencia:         2.5 HP                                      │
│   Voltaje:          220V trifásico                              │
│   Peso:             180 KG                                      │
│   Manual:           [📄 manual_eastman_629x.pdf]                │
│                                                                 │
│ DATOS FINANCIEROS:                                              │
│   Valor compra:     USD 15,000                                  │
│   Fecha compra:     15/01/2020                                  │
│   Vida útil:        10 años                                     │
│   Valor residual:   USD 1,500                                   │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 2: CREAR PLAN DE MANTENIMIENTO PREVENTIVO

Navegue a: MNT > Planes > [+ Nuevo Plan]

┌─────────────────────────────────────────────────────────────────┐
│ Activo:             ACT-CORTADORA-01                            │
│ Tipo plan:          Preventivo                                  │
│ Frecuencia:         Cada 500 horas ◉  Cada X días ○            │
│                                                                 │
│ ACTIVIDADES:                                                    │
│ 1. Lubricación de rodamientos         (30 min)                 │
│ 2. Limpieza de cuchillas              (45 min)                 │
│ 3. Verificación de tensión de correas (15 min)                 │
│ 4. Inspección de sistema eléctrico    (30 min)                 │
│ 5. Calibración de altura de corte     (20 min)                 │
│                                                                 │
│ Tiempo total:       2.5 hrs                                     │
│ Técnico asignado:   Carlos Ramírez (Mantenimiento)             │
│                                                                 │
│ REPUESTOS REQUERIDOS:                                           │
│ • Aceite lubricante SAE 20W:  0.5 LT                           │
│ • Cuchilla de repuesto:       1 UND (cada 2000 hrs)            │
│                                                                 │
│ Próximo mantenimiento:  15/03/2026 (en 15 días)                │
│                                                                 │
│ [Activar Plan]                                                  │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 3: EJECUTAR ORDEN DE TRABAJO

Cuando llega la fecha:

Navegue a: MNT > Órdenes de Trabajo > [Filtrar: Pendientes]

┌─────────────────────────────────────────────────────────────────┐
│ OT:                 OT-MNT-2026-001                             │
│ Tipo:               Preventivo                                  │
│ Activo:             ACT-CORTADORA-01                            │
│ Plan origen:        PLAN-PREV-CORT-01                           │
│ Prioridad:          Media                                       │
│ Fecha programada:   15/03/2026                                  │
│                                                                 │
│ ACTIVIDADES (checklist):                                        │
│ ☑ Lubricación de rodamientos                                   │
│ ☑ Limpieza de cuchillas                                        │
│ ☑ Verificación de tensión de correas                           │
│ ☑ Inspección de sistema eléctrico                              │
│ ☑ Calibración de altura de corte                               │
│                                                                 │
│ REPUESTOS UTILIZADOS:                                           │
│ • Aceite SAE 20W:     0.5 LT  S/ 15.00                         │
│                                                                 │
│ TIEMPO:                                                         │
│   Inicio:           15/03/2026 08:00                            │
│   Fin:              15/03/2026 10:45                            │
│   Total:            2.75 hrs (15 min extra por ajuste)         │
│   Costo MOD:        S/ 82.50 (2.75h × S/ 30/h)                 │
│                                                                 │
│ Técnico:            Carlos Ramírez                              │
│ Observaciones:      Se detectó desgaste leve en correa.        │
│                     Programar reemplazo en próximo manto.       │
│                                                                 │
│ [Cerrar OT]                                                     │
└─────────────────────────────────────────────────────────────────┘

Al cerrar:
  • Descuenta repuestos del inventario
  • Actualiza historial del activo
  • Programa próximo mantenimiento (+500 horas)

✓ CHECKLIST - MNT COMPLETADO:
  ☐ Activos críticos registrados
  ☐ Planes preventivos configurados
  ☐ Primera OT ejecutada y cerrada
  ☐ Historial de mantenimiento actualizado

───────────────────────────────────────────────────────────────────────

4.5 MÓDULO SVC — ÓRDENES DE SERVICIO (TERCERIZACIÓN)
───────────────────────────────────────────────────────────────────────

OBJETIVO: Gestionar servicios a talleres externos (corte, costura, bordado).
PREREQUISITO: ORG + INV + PUR completados
TIEMPO ESTIMADO: 2-3 horas

▸ PASO 1: CREAR ORDEN DE SERVICIO A TALLER

Navegue a: SVC > Órdenes de Servicio > [+ Nueva OS]

┌─────────────────────────────────────────────────────────────────┐
│ Número:             OS-2026-001                                 │
│ Tipo:               Servicio a proveedor (tercerización)        │
│ Proveedor:          TALLER DE COSTURA FLORES SAC                │
│ Contacto:           Rosa Flores (987654321)                     │
│                                                                 │
│ SERVICIO SOLICITADO:                                            │
│   Tipo proceso:     Costura de polos                            │
│   Producto:         POLO-H-M-BLANCO                             │
│   Cantidad:         300 UND                                     │
│                                                                 │
│ MATERIAL A ENVIAR:                                              │
│ • Piezas cortadas:  300 sets (delantero+espalda+mangas)        │
│ • Hilo:             8 KG                                        │
│ • Botones:          1,200 UND                                   │
│                                                                 │
│ FECHAS:                                                         │
│   Envío material:   01/03/2026                                  │
│   Retorno esperado: 08/03/2026                                  │
│                                                                 │
│ COSTO:                                                          │
│   Precio unitario:  S/ 5.50 por polo cosido                    │
│   Total servicio:   S/ 1,650.00                                 │
│                                                                 │
│ Vinculada a OP:     OP-2026-005                                 │
│                                                                 │
│ [Aprobar y Generar Envío]                                       │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 2: REGISTRAR ENVÍO DE MATERIAL AL TALLER

Al aprobar, se crea automáticamente:

┌─────────────────────────────────────────────────────────────────┐
│ ENVÍO:              ENV-TALL-2026-001                           │
│ OS origen:          OS-2026-001                                 │
│ Taller:             TALLER DE COSTURA FLORES SAC                │
│ Fecha envío:        01/03/2026                                  │
│                                                                 │
│ MATERIALES ENVIADOS:                                            │
│ Material              Cantidad  Almacén origen                  │
│ ──────────────────────────────────────────────────────────────│
│ PIEZAS-POLO-BL-M      300 SET   ALM-SEMIELABORADO             │
│ HILO-POLY-BL-001      8 KG      ALM-MP-01                      │
│ BOTON-BLANCO-15MM     1200 UND  ALM-MP-01                      │
│                                                                 │
│ ACCIONES AUTOMÁTICAS:                                           │
│ ✅ Movimiento INV tipo "SAL-SVC"                                │
│ ✅ Stock descontado de almacenes                                │
│ ✅ Stock registrado en inv_stock_tercero                        │
│    (Taller FLORES tiene: 300 sets + 8 KG hilo + 1200 botones)  │
│                                                                 │
│ Guía remisión:      GR-T001-00015                              │
│ Estado:             Material en taller                          │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 3: REGISTRAR RETORNO DEL TALLER

Cuando el taller devuelve la mercadería:

┌─────────────────────────────────────────────────────────────────┐
│ RETORNO:            RET-TALL-2026-001                           │
│ Envío origen:       ENV-TALL-2026-001                           │
│ Fecha retorno:      08/03/2026                                  │
│                                                                 │
│ PRODUCTOS RECIBIDOS:                                            │
│ Producto            Enviado  Recibido  Diferencia               │
│ ──────────────────────────────────────────────────────────────│
│ POLO-H-M-BLANCO     300 UND  295 UND   -5 UND ⚠               │
│                                                                 │
│ MATERIAL SOBRANTE DEVUELTO:                                     │
│ HILO-POLY-BL-001    --       0.5 KG    (sobrante)              │
│ BOTON-BLANCO-15MM   --       50 UND    (sobrante)              │
│                                                                 │
│ MERMA/SCRAP:                                                    │
│ 5 polos con costura defectuosa → Taller asume                  │
│ Hilo consumido: 7.5 KG                                          │
│ Botones consumidos: 1150 UND                                    │
│                                                                 │
│ ACCIONES:                                                       │
│ ✅ Entrada de 295 UND POLO-H-M-BLANCO a ALM-PT-01               │
│ ✅ Entrada de sobrantes (hilo y botones)                        │
│ ✅ Descuento de inv_stock_tercero                               │
│ ✅ Actualización de estado OS a "Completada"                    │
│                                                                 │
│ [Procesar Retorno]                                              │
└─────────────────────────────────────────────────────────────────┘

▸ PASO 4: VINCULAR CON ORDEN DE COMPRA (PAGO)

Para pagar al taller, genere OC:

┌─────────────────────────────────────────────────────────────────┐
│ OC:                 OC-2026-025                                 │
│ Proveedor:          TALLER DE COSTURA FLORES SAC                │
│ Concepto:           Servicio de costura - OS-2026-001           │
│                                                                 │
│ DETALLE:                                                        │
│ Descripción              Cantidad  Precio    Total              │
│ ──────────────────────────────────────────────────────────────│
│ Costura de polos         295 UND   S/ 5.50  S/ 1,622.50       │
│                                                                 │
│ Subtotal:                                    S/ 1,622.50        │
│ IGV 18%:                                     S/ 292.05          │
│ Total:                                       S/ 1,914.55        │
│                                                                 │
│ Condición pago:     Contado                                     │
│                                                                 │
│ [Aprobar OC]                                                    │
└─────────────────────────────────────────────────────────────────┘

💡 COSTO MIXTO: El costo del polo incluirá:
  • Material directo (tela, botones)
  • MOD interna (corte)
  • Servicio externo (costura = S/ 5.50)
  • MOD interna (empaque)

✓ CHECKLIST - SVC COMPLETADO:
  ☐ Orden de servicio a taller creada
  ☐ Material enviado con control en inv_stock_tercero
  ☐ Retorno registrado con mermas identificadas
  ☐ OC generada para pagar el servicio

═══════════════════════════════════════════════════════════════════════

FIN DE LA PARTE 4

PRÓXIMA PARTE 5:
  - CRM (Gestión de Clientes)
  - PRC (Precios & Promociones)
  - POS (Punto de Venta)

═══════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 5 DE 8
                MÓDULOS COMERCIALES Y RETAIL
═══════════════════════════════════════════════════════════════════════

PARTE 5: MÓDULOS COMERCIALES Y RETAIL

5.1 MÓDULO CRM — GESTIÓN DE CLIENTES
───────────────────────────────────────────────────────────────────────
OBJETIVO: Pipeline de ventas con leads, oportunidades y campañas.
PREREQUISITO: SLS completado
TIEMPO: 2-3 horas

▸ PASO 1: CREAR CAMPAÑA DE MARKETING
Navegue a: CRM > Campañas > [+ Nueva Campaña]

Código:          CAMP-2026-VERANO
Nombre:          Campaña Verano 2026
Tipo:            Email Marketing + Redes Sociales
Presupuesto:     S/ 5,000
Fecha inicio:    01/03/2026
Fecha fin:       31/03/2026
Objetivo:        500 leads, 100 conversiones

Canales:
☑ Facebook Ads (S/ 2,000)
☑ Email marketing (S/ 1,500)
☑ Google Ads (S/ 1,500)

Métricas:
  Inversión:     S/ 5,000
  Leads:         450
  Conversiones:  85
  ROI:           S/ 25,500 (ventas) / S/ 5,000 = 510%

▸ PASO 2: REGISTRAR LEADS
Navegue a: CRM > Leads > [+ Nuevo Lead]

Nombre:            Carlos Mendoza
Empresa:           DISTRIBUIDORA DEL NORTE SAC
RUC:               20123456789
Email:             cmendoza@disnorte.com
Teléfono:          987654321

Origen:            Facebook Ads
Campaña:           CAMP-2026-VERANO
Interés:           Polos para dotación empresarial

Lead scoring:      75/100 (alto)
  Tamaño empresa:  +30 (mediana)
  Presupuesto:     +25 (S/ 20,000+)
  Decisor:         +20 (es gerente comercial)

Estado:            Nuevo → [Calificar]

▸ PASO 3: CONVERTIR A OPORTUNIDAD
Al calificar el lead:

OPORTUNIDAD: OPP-2026-001
Cliente potencial: DISTRIBUIDORA DEL NORTE SAC
Valor estimado:    S/ 18,000
Prob. cierre:      60%
Valor ponderado:   S/ 10,800

PIPELINE:
  1. Prospección        ← Estado actual
  2. Calificación
  3. Cotización enviada
  4. Negociación
  5. Cierre ganado / perdido

Actividades programadas:
  [x] Llamada inicial (completada)
  [ ] Envío de catálogo (pendiente 02/03)
  [ ] Visita presencial (pendiente 05/03)
  [ ] Cotización formal (pendiente 08/03)

Fecha cierre esperada: 20/03/2026

▸ PASO 4: SEGUIMIENTO DE ACTIVIDADES
Navegue a: CRM > Actividades

ACTIVIDAD: ACT-2026-015
Tipo:        Reunión presencial
Oportunidad: OPP-2026-001
Fecha:       05/03/2026 10:00
Duración:    1.5 hrs
Participantes: Juan Torres (vendedor), Carlos Mendoza (cliente)

Resultado:
Cliente interesado en 500 polos. Solicita cotización formal con
3 opciones de tela. Decisión en 15 días.

Próximos pasos:
  [ ] Enviar cotización antes del 08/03
  [ ] Follow-up por email el 10/03
  [ ] Llamada de cierre el 18/03

✓ CHECKLIST - CRM:
  ☐ Campaña creada con presupuesto
  ☐ Leads capturados y calificados
  ☐ Oportunidades en pipeline
  ☐ Actividades registradas

5.2 MÓDULO PRC — PRECIOS & PROMOCIONES
───────────────────────────────────────────────────────────────────────
OBJETIVO: Listas de precios por segmento y promociones configurables.
PREREQUISITO: INV + SLS completados
TIEMPO: 1-2 horas

▸ PASO 1: CREAR LISTAS DE PRECIOS
Navegue a: PRC > Listas de Precios > [+ Nueva Lista]

LISTA: LISTA-MAYORISTA
Nombre:     Precios Mayoristas
Moneda:     PEN
Vigencia:   01/03/2026 - 31/05/2026
Es default: ☐ No

PRECIOS POR VOLUMEN:
Producto          1-49    50-99   100-499  500+
POLO-H-M-BLANCO   S/ 35   S/ 32   S/ 30    S/ 28
CAMIS-M-M-BLANCA  S/ 48   S/ 45   S/ 42    S/ 40

LISTA: LISTA-MINORISTA
Precios 15% más altos que mayorista

LISTA: LISTA-CORPORATIVO
Descuento especial 20% para clientes con contrato anual

▸ PASO 2: ASIGNAR LISTA A CLIENTES
En ficha de cliente:

Cliente:         DISTRIBUIDORA TEXTIL LIMA SAC
Lista asignada:  LISTA-MAYORISTA
Descuento adic:  5% (cliente premium)

El sistema aplica automáticamente en cotizaciones y pedidos.

▸ PASO 3: CREAR PROMOCIÓN
Navegue a: PRC > Promociones > [+ Nueva Promoción]

Código:      PROMO-3X2-POLOS
Nombre:      3x2 en Polos Seleccionados
Tipo:        3x2 (compra 3, paga 2)
Vigencia:    15/03/2026 - 31/03/2026

Aplicable a:
  ☑ POLO-H-M-BLANCO
  ☑ POLO-H-M-NEGRO
  ☑ POLO-H-L-AZUL

Condiciones:
  Mínimo:     3 UND (dispara automáticamente)
  Canales:    ☑ Tienda física  ☑ Online  ☐ Mayorista

Restricciones:
  ☐ No acumulable con otros descuentos
  ☑ Stock limitado: 500 UND total

Ejemplo de aplicación:
  Cliente compra 9 polos → Paga 6 polos
  Cliente compra 5 polos → Paga 4 polos (1 gratis)

✓ CHECKLIST - PRC:
  ☐ Listas de precios por segmento
  ☐ Precios escalonados configurados
  ☐ Promociones activas
  ☐ Aplicación automática en pedidos

5.3 MÓDULO POS — PUNTO DE VENTA
───────────────────────────────────────────────────────────────────────
OBJETIVO: Ventas rápidas con control de caja.
PREREQUISITO: INV + INV_BILL completados
TIEMPO: 1-2 horas

▸ PASO 1: CONFIGURAR PUNTO DE VENTA
Navegue a: POS > Puntos de Venta > [+ Nuevo POS]

Código:         POS-TIENDA-01
Nombre:         Caja Principal - Tienda Lima
Sucursal:       SUC-LIMA-01
Almacén:        ALM-PT-TIENDA
Serie boletas:  B001
Serie facturas: F001

Cajero asignado: Ana García
Supervisor:      María López

▸ PASO 2: APERTURA DE TURNO
Al inicio del día:

TURNO: TRN-2026-001
Fecha:          01/03/2026
Cajero:         Ana García
Hora apertura:  08:00

FONDO INICIAL:
  Efectivo:     S/ 200.00
  Total:        S/ 200.00

[Abrir Turno]

▸ PASO 3: REGISTRAR VENTA
Interfaz simplificada:

┌────────────────────────────────────────────────┐
│ CLIENTE: [ ] Buscar por DNI/RUC                │
│                                                │
│ PRODUCTOS:                                     │
│ [Escanear código de barras o buscar]          │
│                                                │
│ POLO-H-M-BLANCO    3 x S/ 35.00   S/ 105.00  │
│ [+] [-] [X]                                    │
│                                                │
│ CAMIS-M-M-BLANCA   1 x S/ 48.00   S/ 48.00   │
│ [+] [-] [X]                                    │
│                                                │
│ ─────────────────────────────────              │
│ Subtotal:                         S/ 153.00   │
│ IGV 18%:                          S/ 27.54    │
│ TOTAL:                            S/ 180.54   │
│                                                │
│ FORMA DE PAGO:                                 │
│ ◉ Efectivo  ○ Tarjeta  ○ Yape/Plin           │
│                                                │
│ Recibido: S/ 200.00                           │
│ Vuelto:   S/ 19.46                            │
│                                                │
│ [COBRAR F2] [CANCELAR ESC]                    │
└────────────────────────────────────────────────┘

Al cobrar:
  1. Genera boleta B001-00125
  2. Descuenta stock de ALM-PT-TIENDA
  3. Registra venta en pos_venta
  4. Imprime ticket
  5. Actualiza saldo de caja

▸ PASO 4: CIERRE DE TURNO
Al final del día:

TURNO: TRN-2026-001
Hora cierre:    18:00

ARQUEO DE CAJA:
                Sistema    Físico    Diferencia
Efectivo:       S/ 2,450   S/ 2,450  S/ 0.00  ✓
Tarjeta:        S/ 1,200   S/ 1,200  S/ 0.00  ✓
Yape/Plin:      S/ 350     S/ 350    S/ 0.00  ✓
───────────────────────────────────────────────
Total:          S/ 4,000   S/ 4,000  S/ 0.00  ✓

VENTAS DEL DÍA:
  Boletas emitidas:  45
  Facturas emitidas: 3
  Total ventas:      S/ 4,000
  Ticket promedio:   S/ 83.33

Depósito bancario: S/ 4,000 (total - fondo inicial)

[Cerrar Turno]

✓ CHECKLIST - POS:
  ☐ Punto de venta configurado
  ☐ Turno abierto con fondo inicial
  ☐ Ventas registradas correctamente
  ☐ Cierre de caja cuadrado

═══════════════════════════════════════════════════════════════════════
FIN PARTE 5 - PRÓXIMA: HCM, FIN, TAX, BDG
═══════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 6 DE 8
              MÓDULOS DE GESTIÓN HUMANA Y FINANZAS
═══════════════════════════════════════════════════════════════════════

PARTE 6: MÓDULOS DE GESTIÓN HUMANA Y FINANZAS

6.1 MÓDULO HCM — PLANILLAS & RECURSOS HUMANOS
───────────────────────────────────────────────────────────────────────
OBJETIVO: Gestión completa de empleados, asistencia, planillas con AFP/ONP.
PREREQUISITO: ORG completado
TIEMPO: 4-6 horas (módulo extenso)

▸ PASO 1: REGISTRAR EMPLEADOS
Navegue a: HCM > Empleados > [+ Nuevo Empleado]

DATOS PERSONALES:
  Código:            EMP-001
  DNI:               12345678
  Apellidos:         GARCÍA LÓPEZ
  Nombres:           JUAN CARLOS
  Fecha nacimiento:  15/05/1985 (40 años)
  Sexo:              Masculino
  Estado civil:      Casado
  Dirección:         Av. Los Pinos 456, San Juan de Lurigancho
  Teléfono:          987654321
  Email:             jgarcia@miempresa.com

DATOS LABORALES:
  Fecha ingreso:     01/02/2020
  Departamento:      OPER-PROD
  Cargo:             OPERARIO-COSTURA
  Centro de costo:   CC-PROD
  Sucursal:          SUC-LIMA-01

REMUNERACIÓN:
  Régimen:           Pequeña Empresa (MYPE)
  Sueldo básico:     S/ 1,500.00
  Asignación fam:    S/ 102.50 (tiene 2 hijos)
  Rem. bruta:        S/ 1,602.50

SISTEMA PENSIONARIO:
  Tipo:              AFP ◉  ONP ○  Sin sistema ○
  AFP:               Integra
  Comisión:          Flujo (1.55% + seguro)
  CUSPP:             12345678901234567890

DATOS BANCARIOS:
  Banco:             BCP
  Cuenta sueldo:     191-12345678-0-89
  CCI:               002-191-001234567889-15

CONTACTO EMERGENCIA:
  Nombre:            María López (esposa)
  Teléfono:          912345678
  Parentesco:        Cónyuge

💡 RÉGIMEN MYPE: Gratificación 50%, vacaciones 15 días, CTS reducida.

▸ PASO 2: REGISTRAR CONTRATO
Navegue a: HCM > Empleados > [Seleccionar] > Pestaña "Contratos"

Número:            CTRO-2020-001
Tipo:              Plazo Indeterminado ◉  Plazo Fijo ○  Part-time ○
Fecha inicio:      01/02/2020
Fecha fin:         -- (indefinido)
Periodo prueba:    3 meses (finalizado)

CONDICIONES:
  Jornada:         48 hrs/semana (Lun-Sáb 8hrs)
  Horario:         08:00 - 17:00 (1hr almuerzo)
  Rem. mensual:    S/ 1,500.00

BENEFICIOS MYPE:
  ☑ Gratificación:  50% (Jul y Dic)
  ☑ Vacaciones:     15 días/año (no 30)
  ☑ CTS:            15 días/año (no 30)
  ☑ Seguro EsSalud: 9% empleador
  ☐ SCTR:           No aplica (oficina)

▸ PASO 3: CONFIGURAR CONCEPTOS DE PLANILLA
Navegue a: HCM > Conceptos de Planilla > [+ Nuevo Concepto]

EJEMPLOS DE CONCEPTOS PERÚ:

INGRESOS:
Código: ING-BASICO
Nombre: Sueldo Básico
Tipo:   Ingreso
Base:   Rem. básica del contrato
Fórmula: =remuneracion_basica
Afecto:
  ☑ AFP/ONP
  ☑ Renta 5ta
  ☑ EsSalud
  ☐ SCTR
Código PLAME: 0121

Código: ING-ASIG-FAM
Nombre: Asignación Familiar
Tipo:   Ingreso
Fórmula: =tiene_hijos ? 102.50 : 0
Afecto:
  ☑ AFP/ONP
  ☑ Renta 5ta
  ☑ EsSalud
Código PLAME: 0305

Código: ING-HE-25
Nombre: Horas Extras 25%
Tipo:   Ingreso
Fórmula: =horas_extras_25 * valor_hora * 1.25
Afecto:
  ☑ AFP/ONP
  ☑ Renta 5ta
  ☑ EsSalud
Código PLAME: 0203

DESCUENTOS:
Código: DSC-AFP-APORTE
Nombre: AFP - Aporte Obligatorio
Tipo:   Descuento
Fórmula: =rem_afecta * 0.10
Afecto: --
Código PLAME: 0601

Código: DSC-AFP-COM-FLUJO
Nombre: AFP - Comisión Flujo
Tipo:   Descuento
Fórmula: =rem_afecta * 0.0155
Código PLAME: 0602

Código: DSC-AFP-SEGURO
Nombre: AFP - Prima Seguro
Tipo:   Descuento
Fórmula: =rem_afecta * 0.0113
Código PLAME: 0603

Código: DSC-RENTA-5TA
Nombre: Retención Renta 5ta Categoría
Tipo:   Descuento
Fórmula: =calcular_renta_5ta(rem_anual_proyectada)
Código PLAME: 0608

APORTES EMPLEADOR:
Código: APO-ESSALUD
Nombre: EsSalud (9%)
Tipo:   Aporte empleador
Fórmula: =rem_afecta * 0.09
Código PLAME: 0804

💡 RENTA 5TA: Se calcula proyectando ingreso anual, descontando 7 UIT,
   aplicando tramos progresivos (8%, 14%, 17%, 20%, 30%).

▸ PASO 4: REGISTRAR ASISTENCIA
Navegue a: HCM > Asistencia > [+ Registrar Asistencia]

OPCIÓN A - MARCACIÓN INDIVIDUAL:
Fecha:             01/03/2026
Empleado:          GARCÍA LÓPEZ, JUAN CARLOS
Turno:             Mañana
Entrada:           07:58
Salida:            17:02
Tiempo trabajado:  8.07 hrs

Horas extras:
  HE 25%:          0
  HE 35%:          0
  HE 100%:         0

OPCIÓN B - IMPORTACIÓN MASIVA:
[Importar desde Excel] → Formato:
DNI      | Fecha      | Entrada | Salida | HE_25 | HE_35
12345678 | 01/03/2026 | 07:58   | 17:02  | 0     | 0
87654321 | 01/03/2026 | 08:05   | 17:30  | 0.5   | 0

OPCIÓN C - INTEGRACIÓN CON RELOJ BIOMÉTRICO:
Conectar dispositivo ZKTeco/Anviz vía IP
Sistema descarga marcaciones automáticamente

▸ PASO 5: GENERAR PLANILLA MENSUAL
Navegue a: HCM > Planillas > [+ Nueva Planilla]

Tipo planilla:     Mensual ◉  Gratificación ○  CTS ○
Periodo:           Febrero 2026
Fecha pago:        28/02/2026

Empleados:         [Seleccionar todos] (25 empleados)

[Calcular Planilla]

RESULTADO - EMPLEADO: GARCÍA LÓPEZ, JUAN

INGRESOS:
  Sueldo básico:           S/ 1,500.00
  Asignación familiar:     S/ 102.50
  HE 25% (4 hrs):          S/ 31.25
  ──────────────────────
  Total ingresos:          S/ 1,633.75

DESCUENTOS:
  AFP Aporte (10%):        S/ 163.38
  AFP Comisión (1.55%):    S/ 25.32
  AFP Seguro (1.13%):      S/ 18.46
  Renta 5ta:               S/ 0.00 (no supera mínimo)
  ──────────────────────
  Total descuentos:        S/ 207.16

NETO A PAGAR:              S/ 1,426.59

APORTES EMPLEADOR:
  EsSalud (9%):            S/ 147.04

COSTO TOTAL EMPRESA:       S/ 1,780.79

RESUMEN PLANILLA COMPLETA (25 empleados):
  Total rem. bruta:        S/ 42,850.00
  Total descuentos:        S/ 5,450.25
  Total neto a pagar:      S/ 37,399.75
  Total aportes empl:      S/ 3,856.50
  Costo total empresa:     S/ 46,706.50

[Aprobar Planilla]

Al aprobar:
  ✅ Genera archivo PLAME para SUNAT
  ✅ Genera TXT para pago masivo bancario
  ✅ Genera boletas de pago (PDF por empleado)
  ✅ Registra asiento contable
  ✅ Envía boletas por email

▸ PASO 6: GESTIONAR VACACIONES
Navegue a: HCM > Vacaciones > [Empleado]

Empleado:          GARCÍA LÓPEZ, JUAN
Fecha ingreso:     01/02/2020
Antigüedad:        6 años 1 mes

RÉGIMEN MYPE: 15 días/año

Periodo 2020-2021:
  Ganados:         15 días
  Tomados:         15 días
  Pendientes:      0 días

Periodo 2021-2022:
  Ganados:         15 días
  Tomados:         10 días
  Pendientes:      5 días ⚠

Periodo 2025-2026:
  Ganados:         15 días
  Tomados:         0 días
  Pendientes:      15 días

Total pendiente:   20 días

[Programar Vacaciones]
  Desde:           15/03/2026
  Hasta:           29/03/2026
  Total:           15 días (2 semanas)
  Tipo:            Vacaciones físicas

Al aprobar:
  ✅ Marca días en calendario
  ✅ Notifica al supervisor
  ✅ Actualiza saldo de vacaciones

▸ PASO 7: REGISTRAR PRÉSTAMOS
Navegue a: HCM > Préstamos > [+ Nuevo Préstamo]

Empleado:          GARCÍA LÓPEZ, JUAN
Tipo:              Adelanto de sueldo
Monto:             S/ 1,000.00
Fecha:             05/03/2026
Cuotas:            5 (descuento en 5 planillas)
Cuota mensual:     S/ 200.00

Inicio descuento:  Planilla Marzo 2026

Motivo:            Emergencia familiar

[Aprobar Préstamo]

El sistema descontará automáticamente S/ 200 en las próximas 5 planillas.

✓ CHECKLIST - HCM:
  ☐ Empleados registrados con datos completos
  ☐ Contratos generados según régimen
  ☐ Conceptos de planilla configurados (AFP/ONP/Renta 5ta)
  ☐ Asistencia registrada (manual o importada)
  ☐ Primera planilla calculada y aprobada
  ☐ Archivo PLAME generado
  ☐ Vacaciones controladas correctamente

───────────────────────────────────────────────────────────────────────

6.2 MÓDULO FIN — CONTABILIDAD
───────────────────────────────────────────────────────────────────────
OBJETIVO: Contabilidad completa con plan de cuentas y asientos automáticos.
PREREQUISITO: ORG completado
TIEMPO: 3-4 horas

▸ PASO 1: CONFIGURAR PLAN DE CUENTAS
Navegue a: FIN > Plan de Cuentas > [Importar PCGE]

El sistema ofrece planes predefinidos:
  ☑ PCGE Perú (Plan Contable General Empresarial)
  ☐ NIIF Internacional
  ☐ Plan personalizado

ESTRUCTURA PCGE (ejemplo):

ACTIVO
  10 EFECTIVO Y EQUIVALENTES DE EFECTIVO
     1041 Cuentas corrientes
          10411 Banco BCP - Cta Soles
          10412 Banco Interbank - Cta Dólares
  12 CUENTAS POR COBRAR COMERCIALES
     1212 Emitidas en cartera
  20 MERCADERÍAS
     2011 Mercaderías manufacturadas
  21 PRODUCTOS TERMINADOS
     2111 Productos manufacturados
  24 MATERIAS PRIMAS
     2411 Materias primas para productos textiles

PASIVO
  40 TRIBUTOS POR PAGAR
     4011 IGV
          40111 IGV - Cuenta propia
  41 REMUNERACIONES POR PAGAR
     4111 Sueldos por pagar
  42 CUENTAS POR PAGAR COMERCIALES
     4212 Emitidas

PATRIMONIO
  50 CAPITAL
     5011 Capital social

INGRESOS
  70 VENTAS
     7011 Mercaderías manufacturadas

GASTOS
  60 COMPRAS
     6011 Mercaderías
  62 GASTOS DE PERSONAL
     6211 Sueldos y salarios
     6271 Régimen de prestaciones de salud

💡 CUENTAS DINÁMICAS: Crea subcuentas según necesidad (por almacén,
   centro de costo, sucursal, etc.)

▸ PASO 2: CREAR PERIODOS CONTABLES
Navegue a: FIN > Periodos Contables > [+ Nuevo Periodo]

Año:               2026
Estado:            Abierto

Meses:
  Enero 2026       ✓ Cerrado
  Febrero 2026     ✓ Cerrado
  Marzo 2026       ◉ Abierto
  Abril 2026       ⏳ No iniciado
  ...

Al cerrar un mes:
  • No se pueden hacer más asientos en ese periodo
  • Se calculan resultados del ejercicio
  • Se genera libro mayor

▸ PASO 3: REGISTRAR ASIENTOS MANUALES
Navegue a: FIN > Asientos Contables > [+ Nuevo Asiento]

EJEMPLO - COMPRA DE MERCADERÍA:

Número:            00001-2026-03
Fecha:             01/03/2026
Glosa:             Por compra de telas según FC F001-1234
Doc. sustento:     F001-1234 (Factura proveedor)
Tipo cambio:       --

DETALLE:
Cuenta              Debe        Haber       Centro Costo
─────────────────────────────────────────────────────────
6011 Compras        S/ 5,000                CC-PROD
4011 IGV            S/ 900
4212 Proveedores                S/ 5,900

Total:              S/ 5,900    S/ 5,900    ✓ Cuadra

[Registrar Asiento]

⚠ VALIDACIÓN: El sistema verifica que DEBE = HABER siempre.

▸ PASO 4: ASIENTOS AUTOMÁTICOS
Los módulos generan asientos automáticamente:

DESDE FACTURACIÓN (INV_BILL):
Al emitir factura F001-00001 por S/ 10,620:

Cuenta              Debe        Haber
─────────────────────────────────────────
1212 Ctas x Cobrar  S/ 10,620
7011 Ventas                     S/ 9,000
4011 IGV                        S/ 1,620

DESDE PLANILLA (HCM):
Al aprobar planilla Febrero 2026:

Cuenta              Debe        Haber
─────────────────────────────────────────
6211 Sueldos        S/ 42,850
6271 EsSalud        S/ 3,856
4111 Rem. x Pagar               S/ 37,400
4031 ESSALUD x Pag              S/ 3,856
4032 AFP x Pagar                S/ 5,450

DESDE COMPRAS (PUR):
Al recepcionar OC-2026-001:

Cuenta              Debe        Haber
─────────────────────────────────────────
6011 Compras        S/ 7,010
4011 IGV            S/ 1,262
4212 Proveedores                S/ 8,272

💡 CONFIGURACIÓN: En cada módulo se define qué cuentas usar para
   cada tipo de operación.

▸ PASO 5: CONSULTAR LIBRO MAYOR
Navegue a: FIN > Libro Mayor

Cuenta:            1041 Banco BCP - Soles
Periodo:           Marzo 2026

Fecha      Nro Asiento  Glosa           Debe      Haber     Saldo
───────────────────────────────────────────────────────────────────
01/03/2026 00001        Dep. ventas     10,620              10,620
05/03/2026 00015        Pago OC-001               8,272     2,348
10/03/2026 00028        Pago planilla             37,400    -35,052
15/03/2026 00045        Dep. ventas     15,300              -19,752

Saldo inicial:     S/ 0
Total débitos:     S/ 25,920
Total créditos:    S/ 45,672
Saldo final:       S/ -19,752 ⚠ SOBREGIRO

▸ PASO 6: GENERAR ESTADOS FINANCIEROS
Navegue a: FIN > Estados Financieros

BALANCE GENERAL al 31/03/2026:

ACTIVO
  Efectivo y equivalentes          S/ 25,000
  Cuentas por cobrar               S/ 85,000
  Inventarios                      S/ 120,000
  Inmuebles, maq. y equipo         S/ 200,000
  ────────────────────────────────
  TOTAL ACTIVO                     S/ 430,000

PASIVO
  Cuentas por pagar                S/ 65,000
  Tributos por pagar               S/ 12,000
  Remuneraciones por pagar         S/ 8,000
  ────────────────────────────────
  TOTAL PASIVO                     S/ 85,000

PATRIMONIO
  Capital                          S/ 300,000
  Resultados acumulados            S/ 25,000
  Resultado del ejercicio          S/ 20,000
  ────────────────────────────────
  TOTAL PATRIMONIO                 S/ 345,000

TOTAL PASIVO + PATRIMONIO          S/ 430,000 ✓

ESTADO DE RESULTADOS - Marzo 2026:

INGRESOS
  Ventas netas                     S/ 180,000
  
COSTO DE VENTAS
  Costo de mercadería vendida      S/ (108,000)
  ────────────────────────────────
  UTILIDAD BRUTA                   S/ 72,000

GASTOS OPERATIVOS
  Gastos de personal               S/ (35,000)
  Gastos administrativos           S/ (12,000)
  Gastos de ventas                 S/ (8,000)
  ────────────────────────────────
  UTILIDAD OPERATIVA               S/ 17,000

RESULTADO DEL EJERCICIO            S/ 17,000

Margen bruto:      40%
Margen operativo:  9.4%

✓ CHECKLIST - FIN:
  ☐ Plan de cuentas PCGE cargado
  ☐ Periodos contables configurados
  ☐ Primer asiento manual registrado
  ☐ Asientos automáticos funcionando
  ☐ Libro mayor consultado
  ☐ Balance general cuadrado

───────────────────────────────────────────────────────────────────────

6.3 MÓDULO TAX — LIBROS ELECTRÓNICOS
───────────────────────────────────────────────────────────────────────
OBJETIVO: Generar PLE (Programa de Libros Electrónicos) SUNAT automáticamente.
PREREQUISITO: FIN + INV_BILL completados
TIEMPO: 1 hora

▸ PASO 1: GENERAR LIBRO ELECTRÓNICO
Navegue a: TAX > Libros Electrónicos > [+ Generar Libro]

Tipo libro:        Registro de Ventas e Ingresos (14.1)
Periodo:           Marzo 2026
RUC:               20123456789
Razón social:      MI EMPRESA SAC

[Generar PLE]

El sistema genera archivo TXT formato SUNAT:
  LE20123456789202603140100001111.txt

CONTENIDO (extracto):
20260301|F001|00001|20987654321|6|DISTRIB...|10620.00|9000.00|1620.00|...
20260305|B001|00125|12345678|1|JUAN...|180.54|153.00|27.54|...

VALIDACIONES AUTOMÁTICAS:
  ✓ Formato correcto (pipe-delimited)
  ✓ RUC válido
  ✓ Correlativo sin saltos
  ✓ Totales cuadran

[Descargar TXT] [Enviar a SUNAT]

▸ PASO 2: LIBROS DISPONIBLES
El sistema genera automáticamente:

  14.1 Registro de Ventas e Ingresos
  8.1  Registro de Compras
  5.1  Libro Diario
  6.1  Libro Mayor
  3.1  Libro de Inventarios y Balances

Todos los meses se generan y envían a SUNAT según cronograma.

✓ CHECKLIST - TAX:
  ☐ Registro de ventas generado
  ☐ Archivo TXT validado
  ☐ Enviado a SUNAT correctamente

───────────────────────────────────────────────────────────────────────

6.4 MÓDULO BDG — PRESUPUESTOS
───────────────────────────────────────────────────────────────────────
OBJETIVO: Control presupuestal por cuenta contable y centro de costo.
PREREQUISITO: FIN completado
TIEMPO: 1-2 horas

▸ PASO 1: CREAR PRESUPUESTO ANUAL
Navegue a: BDG > Presupuestos > [+ Nuevo Presupuesto]

Año:               2026
Descripción:       Presupuesto Operativo 2026

DETALLE POR CUENTA Y CENTRO DE COSTO:

Cuenta: 6211 Sueldos y Salarios
Centro: CC-PROD
  Enero:           S/ 40,000
  Febrero:         S/ 40,000
  Marzo:           S/ 42,000 (incluye gratificación)
  ...
  Total año:       S/ 500,000

Cuenta: 6011 Compras
Centro: CC-PROD
  Enero:           S/ 60,000
  Febrero:         S/ 55,000
  Marzo:           S/ 70,000
  ...
  Total año:       S/ 750,000

PRESUPUESTO TOTAL 2026: S/ 2,500,000

[Aprobar Presupuesto]

▸ PASO 2: SEGUIMIENTO PRESUPUESTAL
Navegue a: BDG > Ejecución Presupuestal

Periodo:           Marzo 2026
Centro de costo:   CC-PROD

Cuenta         Presupuesto  Ejecutado   %Ejec   Saldo
──────────────────────────────────────────────────────
6211 Sueldos   S/ 42,000    S/ 42,850   102%    -S/ 850  ⚠
6011 Compras   S/ 70,000    S/ 65,000   93%     S/ 5,000 ✓

⚠ ALERTA: Sueldos excedió presupuesto en 2%

ACUMULADO AÑO (Ene-Mar):
Presupuesto:       S/ 625,000
Ejecutado:         S/ 610,000
% Ejecución:       97.6%

✓ CHECKLIST - BDG:
  ☐ Presupuesto anual aprobado
  ☐ Seguimiento mensual configurado
  ☐ Alertas de sobregiro activadas

═══════════════════════════════════════════════════════════════════════
FIN PARTE 6 - PRÓXIMA: CST, PM, TKT, BI, DMS, WFL, AUD
═══════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 7 DE 8
              MÓDULOS AVANZADOS Y COMPLEMENTARIOS
═══════════════════════════════════════════════════════════════════════

PARTE 7: MÓDULOS AVANZADOS Y COMPLEMENTARIOS

7.1 MÓDULO CST — COSTEO DE PRODUCTOS
───────────────────────────────────────────────────────────────────────
OBJETIVO: Calcular costo real de productos (MPD + MOD + CIF).
PREREQUISITO: MFG + FIN completados
TIEMPO: 2 horas

▸ PASO 1: CONFIGURAR TIPOS DE CENTRO DE COSTO
Navegue a: CST > Tipos de Centro > [+ Nuevo Tipo]

Código:            TIPO-PRODUCTIVO
Nombre:            Centro Productivo
Distribución CIF:  Directo (asignable a productos)

Centros:
  • CC-CORTE
  • CC-COSTURA
  • CC-EMPAQUE

Código:            TIPO-NO-PRODUCTIVO
Nombre:            Centro No Productivo
Distribución CIF:  Indirecto (prorratear)

Centros:
  • CC-ADMIN
  • CC-VENTAS
  • CC-MANTENIMIENTO

▸ PASO 2: REVISAR COSTO DE PRODUCTO
Navegue a: CST > Costos de Productos > [POLO-H-M-BLANCO]

COSTO ESTÁNDAR (según BOM):
  Material directo:    S/ 13.16
  MOD (según ruta):    S/ 9.17
  CIF (50% MOD):       S/ 4.58
  ─────────────────────────
  Total estándar:      S/ 26.91

COSTO REAL (OP-2026-001 - 200 UND):
  Material directo:    S/ 13.40 (+S/ 0.24)
  MOD:                 S/ 9.17 (sin variación)
  CIF:                 S/ 4.72 (+S/ 0.14)
  ─────────────────────────
  Total real:          S/ 27.29

VARIACIONES:
  Material:            +S/ 0.24 (1.8%) ⚠
  MOD:                 S/ 0.00 (0%)
  CIF:                 +S/ 0.14 (3.1%)
  ─────────────────────────
  Total variación:     +S/ 0.38 (1.4%)

CAUSA RAÍZ VARIACIÓN MATERIAL:
  • 3 rollos de tela con defecto
  • Consumo real: 255 MT vs planeado 252 MT
  • Acción: Reclamo a proveedor + NC

▸ PASO 3: DISTRIBUIR CIF
El sistema distribuye automáticamente:

CENTROS PRODUCTIVOS (directo):
  CC-CORTE:    S/ 2,500 → Asignado a OPs proporcional
  CC-COSTURA:  S/ 4,800 → Asignado a OPs proporcional

CENTROS NO PRODUCTIVOS (indirecto):
  CC-ADMIN:    S/ 12,000 → Prorrateo según MOD
  CC-VENTAS:   S/ 8,000  → Prorrateo según MOD

Total CIF del mes: S/ 27,300

Asignación a POLO-H-M-BLANCO (OP-2026-001):
  MOD de la OP: 102 hrs
  MOD total mes: 2,400 hrs
  % Asignación: 4.25%
  CIF asignado: S/ 1,160 → S/ 5.80 por polo

✓ CHECKLIST - CST:
  ☐ Tipos de centro configurados
  ☐ Costo estándar vs real comparado
  ☐ Variaciones analizadas
  ☐ CIF distribuido correctamente

───────────────────────────────────────────────────────────────────────

7.2 MÓDULO PM — GESTIÓN DE PROYECTOS
───────────────────────────────────────────────────────────────────────
OBJETIVO: Control de proyectos con presupuesto vs real.
PREREQUISITO: ORG + FIN completados
TIEMPO: 1 hora

▸ PASO 1: CREAR PROYECTO
Navegue a: PM > Proyectos > [+ Nuevo Proyecto]

Código:            PROY-2026-001
Nombre:            Implementación Nuevo Almacén
Cliente:           Interno (mejora continua)
Responsable:       Pedro Gómez (Jefe Logística)

Fecha inicio:      01/03/2026
Fecha fin est:     31/05/2026
Duración:          3 meses

PRESUPUESTO:
  Materiales:      S/ 80,000
  MOD:             S/ 45,000
  Servicios:       S/ 25,000
  Equipos:         S/ 50,000
  ─────────────────────────
  Total:           S/ 200,000

▸ PASO 2: VINCULAR GASTOS
Los gastos se vinculan automáticamente:

  • Compras con proyecto_id = PROY-2026-001
  • Planillas con asignación de horas al proyecto
  • Facturas de servicios marcadas al proyecto

▸ PASO 3: SEGUIMIENTO
Navegue a: PM > Seguimiento > [PROY-2026-001]

Al 31/03/2026 (1 mes transcurrido):

Concepto        Presupuesto  Ejecutado   %Ejec   Avance
──────────────────────────────────────────────────────────
Materiales      S/ 80,000    S/ 25,000   31%     ✓
MOD             S/ 45,000    S/ 15,500   34%     ✓
Servicios       S/ 25,000    S/ 8,000    32%     ✓
Equipos         S/ 50,000    S/ 0        0%      ⚠
──────────────────────────────────────────────────────────
Total           S/ 200,000   S/ 48,500   24%

% Avance tiempo:    33% (1 de 3 meses)
% Avance costo:     24%
Estado:             ⚠ Ligeramente retrasado

ALERTA: Equipos aún no adquiridos. Verificar con compras.

✓ CHECKLIST - PM:
  ☐ Proyecto creado con presupuesto
  ☐ Gastos vinculados automáticamente
  ☐ Seguimiento mensual configurado

───────────────────────────────────────────────────────────────────────

7.3 MÓDULO TKT — MESA DE AYUDA
───────────────────────────────────────────────────────────────────────
OBJETIVO: Gestión de tickets de soporte interno.
PREREQUISITO: ORG completado
TIEMPO: 30 minutos

▸ PASO 1: CREAR TICKET
Navegue a: TKT > Tickets > [+ Nuevo Ticket]

Número:            TKT-2026-001
Solicitante:       Juan García (Operario)
Departamento:      OPER-PROD
Fecha:             01/03/2026 14:30

Asunto:            Impresora de etiquetas no imprime
Descripción:       La impresora Zebra del área de empaque no está
                   imprimiendo. Muestra luz roja intermitente.

Categoría:         Hardware - Impresoras
Prioridad:         Alta (afecta producción)
SLA:               4 horas

[Crear Ticket]

▸ PASO 2: ASIGNAR Y RESOLVER
Asignado a:        Carlos Vega (Soporte TI)
Estado:            En atención

ACTIVIDAD:
  14:45 - Técnico revisó impresora
  14:50 - Detectado: papel atascado en rodillo
  15:00 - Limpieza y reinicio exitoso
  15:10 - Ticket cerrado

Tiempo resolución: 40 minutos (dentro de SLA)
Estado:            ✓ Resuelto

▸ PASO 3: MÉTRICAS
Navegue a: TKT > Dashboard

Mes de Marzo 2026:
  Tickets abiertos:      45
  Tickets resueltos:     42
  Tickets pendientes:    3
  Tiempo promedio:       2.5 hrs
  % dentro SLA:          93%

✓ CHECKLIST - TKT:
  ☐ Primer ticket creado
  ☐ Asignación funcionando
  ☐ SLA configurado

───────────────────────────────────────────────────────────────────────

7.4 MÓDULO BI — REPORTES & ANALYTICS
───────────────────────────────────────────────────────────────────────
OBJETIVO: Reportes personalizados y dashboards.
PREREQUISITO: Todos los módulos operativos
TIEMPO: 2 horas

▸ PASO 1: CREAR REPORTE PERSONALIZADO
Navegue a: BI > Reportes > [+ Nuevo Reporte]

Nombre:            Top 10 Productos Más Vendidos
Descripción:       Ranking de productos por volumen de venta
Módulo origen:     SLS + INV_BILL

SQL Query:
SELECT 
  p.nombre_producto,
  SUM(cd.cantidad) as cantidad_vendida,
  SUM(cd.subtotal) as venta_total
FROM invbill_comprobante_detalle cd
INNER JOIN inv_producto p ON cd.producto_id = p.producto_id
INNER JOIN invbill_comprobante c ON cd.comprobante_id = c.comprobante_id
WHERE c.fecha_emision BETWEEN @fecha_inicio AND @fecha_fin
  AND c.estado = 'aceptado'
GROUP BY p.producto_id, p.nombre_producto
ORDER BY cantidad_vendida DESC
LIMIT 10

Parámetros:
  @fecha_inicio    (tipo: fecha)
  @fecha_fin       (tipo: fecha)

Visualización:   Gráfico de barras
Frecuencia:      Mensual (auto-genera 1ro de mes)
Destino:         Email gerencia + Dashboard

▸ PASO 2: CONFIGURAR DASHBOARD
Navegue a: BI > Dashboards > [+ Nuevo Dashboard]

Nombre:            Dashboard Ejecutivo
Usuarios:          Gerencia General, Gerencia Comercial

WIDGETS:
  1. Ventas del Mes (KPI card)
     Fuente: SELECT SUM(total) FROM invbill_comprobante WHERE mes_actual
  
  2. Top 10 Productos (gráfico barras)
     Fuente: Reporte personalizado anterior
  
  3. Margen Bruto % (gauge)
     Fuente: (Ventas - Costo) / Ventas
  
  4. Stock Crítico (tabla)
     Fuente: Productos con stock < stock_minimo

Actualización:     Cada 1 hora

✓ CHECKLIST - BI:
  ☐ Reporte personalizado creado
  ☐ Dashboard configurado
  ☐ Accesos por rol asignados

───────────────────────────────────────────────────────────────────────

7.5 MÓDULO DMS — GESTIÓN DOCUMENTAL
───────────────────────────────────────────────────────────────────────
OBJETIVO: Repositorio de documentos con versionamiento.
PREREQUISITO: ORG completado
TIEMPO: 30 minutos

▸ PASO 1: SUBIR DOCUMENTO
Navegue a: DMS > Documentos > [+ Subir Documento]

Nombre:            Manual de Operaciones Producción
Tipo:              PDF
Tamaño:            2.5 MB
Categoría:         Procedimientos
Tags:              producción, calidad, procesos

Acceso:
  ☑ Departamento: OPER-PROD
  ☐ Solo gerencia
  ☐ Toda la empresa

[Subir]

RESULTADO:
  Documento ID:    DOC-2026-001
  Versión:         1.0
  URL:             /docs/manual-operaciones-v1.pdf

▸ PASO 2: ACTUALIZAR VERSIÓN
Al modificar el documento:

Versión nueva:     2.0
Cambios:           Actualizado procedimiento de corte
Fecha:             15/03/2026

Historial:
  v1.0  01/03/2026  Creación inicial
  v2.0  15/03/2026  Actualización proc. corte

✓ CHECKLIST - DMS:
  ☐ Documentos subidos
  ☐ Versionamiento funcionando
  ☐ Control de acceso configurado

───────────────────────────────────────────────────────────────────────

7.6 MÓDULO WFL — FLUJOS DE TRABAJO
───────────────────────────────────────────────────────────────────────
OBJETIVO: Workflows de aprobación personalizados.
PREREQUISITO: ORG completado
TIEMPO: 1 hora

▸ PASO 1: CREAR WORKFLOW
Navegue a: WFL > Flujos > [+ Nuevo Flujo]

Nombre:            Aprobación de Órdenes de Compra
Aplica a:          PUR - Orden de Compra
Condición:         Monto > S/ 5,000

PASOS:
  1. Jefe de Área
     Rol: Jefe del departamento solicitante
     Acción: Aprobar / Rechazar
     Timeout: 24 horas
  
  2. Gerencia
     Rol: Gerente General
     Acción: Aprobar / Rechazar
     Timeout: 48 horas
     Condición: Si monto > S/ 20,000
  
  3. Finanzas
     Rol: Jefe de Finanzas
     Acción: Aprobar / Rechazar
     Timeout: 24 horas

Si timeout excedido → Escalamiento automático

NOTIFICACIONES:
  ☑ Email al aprobador
  ☑ Push notification
  ☑ SMS si crítico

[Activar Workflow]

▸ PASO 2: EJECUCIÓN
Cuando se crea OC-2026-050 por S/ 15,000:

Estado:            Pendiente aprobación
Paso actual:       1. Jefe de Área
Aprobador:         Pedro Gómez
Fecha envío:       16/03/2026 10:00
Vencimiento:       17/03/2026 10:00

Pedro aprueba → Pasa a:
Paso:              2. Gerencia (monto > S/ 5,000 pero < S/ 20,000)
                   PASO OMITIDO
                   
Paso actual:       3. Finanzas
Aprobador:         Ana Torres

Ana aprueba → OC APROBADA (lista para enviar)

✓ CHECKLIST - WFL:
  ☐ Workflow configurado
  ☐ Primer documento aprobado por workflow
  ☐ Notificaciones funcionando

───────────────────────────────────────────────────────────────────────

7.7 MÓDULO AUD — AUDITORÍA
───────────────────────────────────────────────────────────────────────
OBJETIVO: Trazabilidad completa de cambios.
PREREQUISITO: Sistema operativo
TIEMPO: Automático (sin configuración)

▸ REVISIÓN DE LOG
Navegue a: AUD > Log de Auditoría

EJEMPLO - CAMBIO EN PRODUCTO:

Fecha/Hora:        15/03/2026 14:35:22
Usuario:           jperez (Juan Pérez)
IP:                192.168.1.105
Módulo:            INV
Tabla:             inv_producto
Registro ID:       POLO-H-M-BLANCO
Acción:            UPDATE

VALORES MODIFICADOS:
Campo              Valor Anterior    Valor Nuevo
────────────────────────────────────────────────
precio_venta       S/ 35.00         S/ 38.00
stock_minimo       50               75

Razón:             Ajuste de precios Q1 2026

▸ FILTROS DISPONIBLES:
  • Por usuario
  • Por módulo
  • Por tabla
  • Por rango de fechas
  • Por tipo de acción (INSERT/UPDATE/DELETE)

▸ REPORTES DE AUDITORÍA:
  • Cambios en productos críticos
  • Modificaciones de precios
  • Eliminaciones de documentos
  • Accesos fuera de horario

💡 USO: Investigar errores, detectar fraudes, cumplir auditorías.

✓ CHECKLIST - AUD:
  ☐ Log funcionando automáticamente
  ☐ Consultas de trazabilidad exitosas
  ☐ Reportes de auditoría generados

═══════════════════════════════════════════════════════════════════════
FIN PARTE 7 - PRÓXIMA: CASOS DE USO INTEGRADOS
═══════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
                        MANUAL DE USUARIO CAXIS
                          PARTE 8 DE 8
                  CASOS DE USO INTEGRADOS
═══════════════════════════════════════════════════════════════════════

PARTE 8: CASOS DE USO INTEGRADOS - FLUJOS COMPLETOS

Esta sección muestra cómo los módulos trabajan juntos en escenarios reales.

═══════════════════════════════════════════════════════════════════════

8.1 CASO 1: EMPRESA COMERCIAL (Solo compra y vende)
───────────────────────────────────────────────────────────────────────

PERFIL: Distribuidora de ropa que NO produce, solo comercializa.
MÓDULOS: ORG + INV + PUR + SLS + INV_BILL + LOG + FIN

FLUJO COMPLETO: Desde compra hasta venta y facturación

──────────────────────────────────────────────────────────────────────
DÍA 1 - COMPRA AL PROVEEDOR
──────────────────────────────────────────────────────────────────────

1. NEGOCIACIÓN
   Usuario: Jefe de Compras
   Módulo: PUR > Cotizaciones
   Acción: Solicita cotización a 3 proveedores de polos

2. DECISIÓN
   Elige: CONFECCIONES DEL SUR SAC
   Precio: S/ 25.00 por polo (incluye IGV)

3. GENERAR OC
   Módulo: PUR > Órdenes de Compra
   Acción: Crea OC-2026-001
     Producto: POLO-H-M-BLANCO
     Cantidad: 500 UND
     Total: S/ 12,500 (inc. IGV)
   
   Al aprobar:
     ✅ OC enviada por email al proveedor
     ✅ Estado: Aprobada

──────────────────────────────────────────────────────────────────────
DÍA 7 - RECEPCIÓN DE MERCADERÍA
──────────────────────────────────────────────────────────────────────

4. LLEGADA DE MERCADERÍA
   Usuario: Almacenero
   Módulo: PUR > Recepciones
   Acción: Registra recepción REC-2026-001
     OC origen: OC-2026-001
     Cantidad: 500 UND (completo)
     Almacén: ALM-PT-01
     Guía proveedor: 001-5678
   
   Al procesar:
     ✅ Stock actualizado: +500 UND en ALM-PT-01
     ✅ Costo promedio: S/ 21.19 (sin IGV)
     ✅ Movimiento INV: ENT-COMP
     ✅ OC marcada como recepcionada
     ✅ Asiento contable:
        6011 Compras      S/ 10,593.22 (D)
        4011 IGV          S/ 1,906.78 (D)
        4212 Proveedores  S/ 12,500.00 (H)

──────────────────────────────────────────────────────────────────────
DÍA 8 - VENTA AL CLIENTE
──────────────────────────────────────────────────────────────────────

5. LLEGA PEDIDO
   Usuario: Vendedor
   Módulo: SLS > Pedidos
   Acción: Crea PED-2026-001
     Cliente: TEXTIL MAYORISTA SAC
     Producto: POLO-H-M-BLANCO
     Cantidad: 200 UND
     Precio: S/ 35.00 por polo
     Total: S/ 7,000 (inc. IGV)
   
   Al aprobar:
     ✅ Stock reservado: 200 UND
     ✅ Stock disponible: 300 UND

6. PREPARAR DESPACHO
   Usuario: Almacenero
   Módulo: LOG > Despachos
   Acción: Crea DESP-2026-001
     Pedido: PED-2026-001
     Transportista: TRANSPORTES RÁPIDOS SAC
     Vehículo: ABC-123
   
   Al procesar:
     ✅ Guía remisión: T001-00001
     ✅ Stock descontado: -200 UND
     ✅ Reserva liberada
     ✅ Movimiento INV: SAL-VENT
     ✅ GR enviada a SUNAT: Aceptada

──────────────────────────────────────────────────────────────────────
DÍA 8 - FACTURACIÓN
──────────────────────────────────────────────────────────────────────

7. EMITIR FACTURA
   Usuario: Facturador
   Módulo: INV_BILL > Comprobantes
   Acción: Genera factura desde PED-2026-001
     Serie-Número: F001-00001
     Valor venta: S/ 5,932.20
     IGV 18%: S/ 1,067.80
     Total: S/ 7,000.00
   
   Al emitir:
     ✅ XML generado y firmado
     ✅ Enviado a SUNAT: Aceptado
     ✅ PDF generado con QR
     ✅ Email a cliente
     ✅ Asiento contable:
        1212 Ctas x Cobrar  S/ 7,000.00 (D)
        7011 Ventas         S/ 5,932.20 (H)
        4011 IGV            S/ 1,067.80 (H)

──────────────────────────────────────────────────────────────────────
DÍA 45 - COBRANZA
──────────────────────────────────────────────────────────────────────

8. REGISTRO DE PAGO
   Usuario: Tesorería
   Módulo: FIN > Asientos
   Acción: Registra pago recibido
     Banco: BCP
     Monto: S/ 7,000.00
   
   Asiento:
     1041 Banco BCP      S/ 7,000.00 (D)
     1212 Ctas x Cobrar  S/ 7,000.00 (H)

──────────────────────────────────────────────────────────────────────
RESULTADO FINANCIERO DEL CASO 1
──────────────────────────────────────────────────────────────────────

Compra:          S/ 10,593.22 (200 polos × S/ 21.19 sin IGV)
Venta:           S/ 5,932.20
Margen bruto:    S/ 1,694.20
% Margen:        28.6%

✓ MÓDULOS INTEGRADOS EN ESTE FLUJO:
  PUR → INV → SLS → LOG → INV_BILL → FIN

═══════════════════════════════════════════════════════════════════════

8.2 CASO 2: EMPRESA PRODUCTORA (Producción propia completa)
───────────────────────────────────────────────────────────────────────

PERFIL: Fábrica de polos con producción 100% interna.
MÓDULOS: ORG + INV + PUR + MFG + QMS + SLS + INV_BILL + HCM + FIN + CST

FLUJO: Desde compra de materia prima hasta venta de producto terminado

──────────────────────────────────────────────────────────────────────
SEMANA 1 - PLANIFICACIÓN
──────────────────────────────────────────────────────────────────────

1. LLEGA PEDIDO CLIENTE
   Cliente solicita: 500 polos blancos talla M
   Fecha entrega: 20 días

2. CREAR ORDEN DE PRODUCCIÓN
   Módulo: MFG > Órdenes de Producción
   OP: OP-2026-001
     Producto: POLO-H-M-BLANCO
     Cantidad: 500 UND
     BOM activo: BOM-POLO-BL-M v1.0
   
   MATERIALES REQUERIDOS (explosión BOM):
     TELA-JERSEY-BL-24:   630 MT (500 × 1.26)
     HILO-POLY-BL-001:    13.75 KG (500 × 0.0275)
     BOTON-BLANCO-15MM:   2,040 UND (500 × 4.08)
     ETIQUETA-MARCA:      500 UND
     ETIQUETA-TALLA-M:    500 UND
     BOLSA-INDIVIDUAL:    500 UND
   
   VERIFICAR STOCK:
     ✓ TELA: Disponible 800 MT
     ✓ HILO: Disponible 20 KG
     ⚠ BOTONES: Stock 1,500 UND (falta 540)
     ✓ Resto: Disponible
   
   ACCIÓN: Generar SC de 600 botones

3. COMPRAR FALTANTES
   Módulo: PUR
   OC-2026-010: 600 botones
   Recepción: 2 días

──────────────────────────────────────────────────────────────────────
SEMANA 2 - PRODUCCIÓN
──────────────────────────────────────────────────────────────────────

4. LIBERAR OP
   Al liberar OP-2026-001:
     ✅ Materiales reservados en inventario
     ✅ Tareas generadas en centros de trabajo
     ✅ Estado: Liberada → En proceso

5. CONSUMO DE MATERIALES
   Módulo: MFG > Consumo Materiales
   Fecha: Día 1 de producción
   
   Materiales consumidos:
     TELA-JERSEY-BL-24:   635 MT (exceso +5 MT por defectos)
     HILO-POLY-BL-001:    13.5 KG
     BOTON-BLANCO-15MM:   2,045 UND
     ETIQUETA-MARCA:      500 UND
     ETIQUETA-TALLA-M:    500 UND
     BOLSA-INDIVIDUAL:    500 UND
   
   Al registrar:
     ✅ Stock descontado de almacenes
     ✅ Movimiento INV: SAL-PROD
     ✅ Costo MPD actualizado en OP

6. OPERACIONES DE PRODUCCIÓN
   
   Día 1-2: CORTE (CT-CORTE-01)
     Operarios: 2
     Tiempo: 50 hrs (500 polos × 0.10h)
     Costo MOD: S/ 1,025 (50h × S/ 20.50/h)
   
   Día 3-7: COSTURA (CT-COSTURA-01)
     Operarios: 5
     Tiempo: 125 hrs (500 polos × 0.25h)
     Costo MOD: S/ 2,250 (125h × S/ 18/h)
   
   Día 8: OJALADO (CT-COSTURA-02)
     Tiempo: 25 hrs
     Costo MOD: S/ 450
   
   Día 9: PLANCHADO (CT-PLANCHADO)
     Tiempo: 40 hrs
     Costo MOD: S/ 600
   
   Día 10: EMPAQUE (CT-EMPAQUE)
     Tiempo: 15 hrs
     Costo MOD: S/ 180

7. CONTROL DE CALIDAD
   Módulo: QMS > Inspecciones
   INSP-2026-010
     Muestra: 20 polos (según AQL 2.5%)
     Resultado: 19 OK, 1 con costura defectuosa
     Decisión: ✓ LOTE APROBADO
     Acción: 1 polo enviado a scrap

8. FINALIZAR OP
   Cantidad producida: 499 UND (1 scrap)
   
   COSTO REAL FINAL:
     MPD: S/ 6,850 (tela S/ 5,398 + hilo S/ 607 + botones S/ 306 + etc)
     MOD: S/ 4,505
     CIF: S/ 2,253 (50% MOD)
     ─────────────────
     Total: S/ 13,608
     Costo unitario: S/ 27.27 por polo
   
   Al finalizar:
     ✅ Entrada al almacén: +499 UND ALM-PT-01
     ✅ Movimiento INV: ENT-PROD
     ✅ Costo promedio actualizado
     ✅ Asiento contable:
        2111 Prod. Terminados  S/ 13,608 (D)
        2411 Materias Primas   S/ 6,850 (H)
        6211 MOD               S/ 4,505 (H)
        9200 CIF               S/ 2,253 (H)

──────────────────────────────────────────────────────────────────────
SEMANA 3 - VENTA Y FACTURACIÓN
──────────────────────────────────────────────────────────────────────

9. PROCESO IGUAL AL CASO 1
   Pedido → Despacho → Factura
   
   Factura F001-00050:
     Cantidad: 500 UND (de las 499 + 1 de otro lote)
     Precio venta: S/ 42.00 por polo
     Total: S/ 21,000 (inc. IGV)

──────────────────────────────────────────────────────────────────────
RESULTADO FINANCIERO DEL CASO 2
──────────────────────────────────────────────────────────────────────

Costo producción:  S/ 27.27 por polo
Precio venta:      S/ 35.59 por polo (sin IGV)
Margen bruto:      S/ 8.32 por polo
% Margen:          23.4%

Ventas totales (500):  S/ 17,796.61 (sin IGV)
Costo vendido:         S/ 13,635.00
Utilidad bruta:        S/ 4,161.61

✓ MÓDULOS INTEGRADOS:
  MFG → INV → QMS → PUR → HCM → SLS → INV_BILL → FIN → CST

═══════════════════════════════════════════════════════════════════════

8.3 CASO 3: EMPRESA MIXTA (Producción propia + Tercerización)
───────────────────────────────────────────────────────────────────────

PERFIL: Fábrica que corta internamente pero terceriza costura.
MÓDULOS: ORG + INV + PUR + MFG + SVC + SLS + INV_BILL + FIN + CST

FLUJO: Proceso combinado interno + taller externo

──────────────────────────────────────────────────────────────────────
PLANIFICACIÓN MIXTA
──────────────────────────────────────────────────────────────────────

1. ORDEN DE PRODUCCIÓN MIXTA
   OP: OP-2026-050
     Producto: POLO-H-M-BLANCO
     Cantidad: 800 UND
     Estrategia: MIXTA
       - Corte: Interno (CT-CORTE-01)
       - Costura: Externo (TALLER FLORES SAC)
       - Empaque: Interno (CT-EMPAQUE)

2. BOM AJUSTADO
   Componentes iguales, pero:
     ✓ Materiales consumidos internamente
     ✓ MOD solo para corte y empaque
     ✓ Costo de servicio externo: S/ 6.50 por polo cosido

──────────────────────────────────────────────────────────────────────
EJECUCIÓN - SEMANA 1
──────────────────────────────────────────────────────────────────────

3. CORTE INTERNO
   Centro: CT-CORTE-01
   Operación: Cortar 800 sets de piezas
   Tiempo: 80 hrs (800 × 0.10h)
   Costo MOD: S/ 1,640

4. CREAR ORDEN DE SERVICIO
   Módulo: SVC > Órdenes de Servicio
   OS: OS-2026-001
     Proveedor: TALLER FLORES SAC
     Tipo servicio: Costura de polos
     Cantidad: 800 UND
     Precio: S/ 6.50 por polo
     Total servicio: S/ 5,200
     Vinculada a: OP-2026-050

5. ENVÍO DE MATERIAL AL TALLER
   Módulo: SVC > Envío a Taller
   ENV-TALL-2026-001
   
   Materiales enviados:
     • 800 sets de piezas cortadas
     • 22 KG hilo
     • 3,264 botones
   
   Al procesar:
     ✅ Movimiento INV: SAL-SVC
     ✅ Stock descontado de ALM-MP-01
     ✅ Registrado en inv_stock_tercero:
        Taller FLORES tiene:
        - 800 sets piezas
        - 22 KG hilo
        - 3,264 botones
     ✅ Guía remisión: GR-T001-00020

──────────────────────────────────────────────────────────────────────
EJECUCIÓN - SEMANA 2
──────────────────────────────────────────────────────────────────────

6. TALLER COSE LOS POLOS
   (Proceso externo - 7 días)

7. RETORNO DEL TALLER
   Módulo: SVC > Retorno de Taller
   RET-TALL-2026-001
   
   Productos recibidos:
     POLO-H-M-BLANCO cosido: 795 UND
     (5 polos con defecto - taller asume)
   
   Material sobrante:
     Hilo: 0.8 KG (devuelto)
     Botones: 45 UND (devueltos)
   
   Al procesar:
     ✅ Entrada de 795 polos semi-terminados
     ✅ Entrada de sobrantes
     ✅ inv_stock_tercero actualizado
     ✅ Movimiento INV: ENT-SVC

8. EMPAQUE INTERNO
   Centro: CT-EMPAQUE
   Operación: Empacar 795 polos
   Tiempo: 24 hrs
   Costo MOD: S/ 288

9. FINALIZAR OP
   Cantidad final: 795 UND
   
   COSTO UNITARIO:
     MPD (tela, hilo, botones, etc):  S/ 13.50
     MOD interna (corte + empaque):   S/ 2.42
     Servicio externo (costura):      S/ 6.54
     CIF:                             S/ 1.21
     ─────────────────────────────────
     Total unitario:                  S/ 23.67
   
   (25% más barato que producción 100% interna)

10. PAGO AL TALLER
    Módulo: PUR > Órdenes de Compra
    OC-2026-080
      Concepto: Servicio costura OS-2026-001
      Cantidad: 795 UND efectivos
      Precio: S/ 6.50
      Total: S/ 5,167.50 + IGV

──────────────────────────────────────────────────────────────────────
RESULTADO FINANCIERO DEL CASO 3
──────────────────────────────────────────────────────────────────────

Costo mixto:       S/ 23.67 por polo
Precio venta:      S/ 38.00 por polo
Margen:            S/ 14.33 por polo (60% margen)

COMPARACIÓN:
  Producción 100% interna:  S/ 27.27 (CASO 2)
  Producción mixta:         S/ 23.67 (CASO 3)
  Ahorro:                   S/ 3.60 por polo (13%)

VENTAJAS MODELO MIXTO:
  ✓ Menor inversión en maquinaria de costura
  ✓ Flexibilidad (escalar rápido subcontratando)
  ✓ Menor costo fijo (menos personal permanente)
  ✓ Riesgo compartido

DESVENTAJAS:
  ⚠ Menos control de calidad
  ⚠ Dependencia de terceros
  ⚠ Riesgo de merma en tránsito

✓ MÓDULOS INTEGRADOS:
  MFG → SVC → INV → PUR → SLS → INV_BILL → FIN → CST

═══════════════════════════════════════════════════════════════════════

8.4 LECCIONES CLAVE Y MEJORES PRÁCTICAS
───────────────────────────────────────────────────────────────────────

CONFIGURACIÓN INICIAL (Crítico):
  1. Completar ORG antes de empezar operaciones
  2. Cargar catálogo de productos con SKU correctos
  3. Configurar tipos de movimiento estándar
  4. Crear BOM activos ANTES de producir
  5. Configurar conceptos de planilla según legislación

FLUJO DIARIO:
  1. Registrar asistencia TODOS los días
  2. Recepcionar compras el mismo día que llegan
  3. Emitir facturas INMEDIATAMENTE después del despacho
  4. Nunca modificar stock manualmente (usar movimientos)

CONTROLES MENSUALES:
  1. Cerrar periodo contable solo después de revisar
  2. Generar PLAME antes del día 10
  3. Hacer inventario físico (ciclo o completo)
  4. Revisar margen bruto por producto
  5. Analizar variaciones de costo producción

AUDITORÍA:
  1. Revisar log AUD mensualmente
  2. Verificar que todas las facturas tengan CDR
  3. Comprobar que OC recepcionadas = facturas proveedor
  4. Validar stock físico vs sistema trimestralmente

RESPALDOS:
  1. Backup diario automático (responsabilidad CAXIS cloud)
  2. Exportar reportes críticos mensualmente
  3. Guardar XMLs de comprobantes offline

═══════════════════════════════════════════════════════════════════════

CONCLUSIÓN DEL MANUAL

CAXIS es un sistema completo que maneja TODOS los procesos de su empresa:

  ✓ 27 módulos integrados
  ✓ 117 tablas de base de datos
  ✓ Flujos automatizados
  ✓ Cumplimiento legal Perú
  ✓ Multi-moneda y multi-sucursal
  ✓ Facturación electrónica SUNAT
  ✓ Costos reales de producción
  ✓ Control total de inventarios

SOPORTE:
  Email:    soporte@caxis.com
  WhatsApp: +51 XXX XXX XXX
  Portal:   help.caxis.com

═══════════════════════════════════════════════════════════════════════
                    FIN DEL MANUAL DE USUARIO CAXIS
                              Versión 1.0
                           Febrero 2026
═══════════════════════════════════════════════════════════════════════