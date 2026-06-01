-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: runtime
-- ============================================================================
DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

INSERT INTO cliente_modulo (
    cliente_modulo_id,
    cliente_id,
    modulo_id,
    esta_activo,
    fecha_activacion
)
SELECT
    NEWID(),
    c.cliente_id,
    @modulo_sys_admin_id,
    1,
    GETDATE()
FROM cliente c
WHERE c.es_activo = 1
AND NOT EXISTS (
    SELECT 1
    FROM cliente_modulo cm
    WHERE cm.cliente_id = c.cliente_id
    AND cm.modulo_id = @modulo_sys_admin_id
);

select * from cliente_modulo