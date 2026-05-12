-- ============================================================================
-- SCRIPT: Permisos RBAC — módulo CST (Costos y Costeo)
-- DESCRIPCIÓN: Alta idempotente (MERGE por codigo) de permisos
--              cst.centro_costo_tipo.* y cst.producto_costo.*.
-- DEPENDENCIAS: Ejecutar después de seeds base de módulos/permisos
--               y existencia del módulo CST en tabla modulo.
-- CST modulo_id: E1000014-0000-4000-8000-000000000014
-- USO: Ejecutar en entornos donde falten estos códigos; seguro re-ejecutar (MERGE).
-- ============================================================================

DECLARE @modulo_cst UNIQUEIDENTIFIER = CAST('E1000014-0000-4000-8000-000000000014' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'cst.centro_costo_tipo.leer' AS codigo, N'Leer tipos de centro de costo' AS nombre, N'Listar y consultar tipos de centro de costo (CST)' AS descripcion, @modulo_cst AS modulo_id, 'centro_costo_tipo' AS recurso, 'leer' AS accion UNION ALL
    SELECT 'cst.centro_costo_tipo.crear', N'Crear tipo de centro de costo', N'Alta de tipos de centro de costo', @modulo_cst, 'centro_costo_tipo', 'crear' UNION ALL
    SELECT 'cst.centro_costo_tipo.actualizar', N'Actualizar tipo de centro de costo', N'Modificar tipos y reactivar registros dados de baja', @modulo_cst, 'centro_costo_tipo', 'actualizar' UNION ALL
    SELECT 'cst.centro_costo_tipo.eliminar', N'Desactivar tipo de centro de costo', N'Baja lógica (es_activo=0) de tipos de centro de costo', @modulo_cst, 'centro_costo_tipo', 'eliminar' UNION ALL

    SELECT 'cst.producto_costo.leer', N'Leer costo de productos', N'Listar y consultar costeo por producto y período', @modulo_cst, 'producto_costo', 'leer' UNION ALL
    SELECT 'cst.producto_costo.crear', N'Crear registro de costo de producto', N'Alta de costos por producto/período', @modulo_cst, 'producto_costo', 'crear' UNION ALL
    SELECT 'cst.producto_costo.actualizar', N'Actualizar costo de producto', N'Modificar montos y datos de costeo', @modulo_cst, 'producto_costo', 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO
