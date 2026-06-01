-- ============================================================================
-- S021 — Alineación rutas menú ERP al contrato FE (/app/*)
-- Idempotente: no modifica rutas ya bajo /app/, /admin/, /super-admin/
-- ============================================================================

UPDATE modulo_menu
SET ruta = '/app' + ruta
WHERE ruta IS NOT NULL
  AND LEN(LTRIM(RTRIM(ruta))) > 0
  AND ruta LIKE '/[a-z]%'  -- paths absolutos legacy
  AND ruta NOT LIKE '/app/%'
  AND ruta NOT LIKE '/admin/%'
  AND ruta NOT LIKE '/super-admin/%'
  AND ruta NOT LIKE '/api/%'
  AND (
        ruta LIKE '/org/%'
     OR ruta LIKE '/inv/%'
     OR ruta LIKE '/wms/%'
     OR ruta LIKE '/qms/%'
     OR ruta LIKE '/pur/%'
     OR ruta LIKE '/log/%'
     OR ruta LIKE '/mfg/%'
     OR ruta LIKE '/mrp/%'
     OR ruta LIKE '/mps/%'
     OR ruta LIKE '/mnt/%'
     OR ruta LIKE '/crm/%'
     OR ruta LIKE '/fin/%'
     OR ruta LIKE '/hr/%'
     OR ruta LIKE '/pos/%'
     OR ruta LIKE '/ecom/%'
  );
GO
