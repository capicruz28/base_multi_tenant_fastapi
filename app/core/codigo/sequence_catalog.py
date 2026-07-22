"""SequenceCatalog — contrato maestro del motor (F16A `21`, 63 entradas)."""

from __future__ import annotations

from app.core.codigo.enums import (
    AlignmentMode,
    CodePolicy,
    FormatterProfile,
    NormalizeCase,
    ParserProfile,
    ScopeType,
    SequenceFamily,
    StoreType,
    ValidatorProfile,
)
from app.core.codigo.sequence_definition import SequenceDefinition

# Versión del contrato del catálogo. Definida aquí (fuente natural) para que el
# catálogo no dependa de onboarding_seed y este pueda derivar del catálogo sin ciclo.
CATALOG_VERSION = "1.0.0"

_MODULE_BY_PREFIX: dict[str, str] = {
    "org_": "ORG",
    "inv_": "INV",
    "wms_": "WMS",
    "pur_": "PUR",
    "sls_": "SLS",
    "log_": "LOG",
    "mfg_": "MFG",
    "mnt_": "MNT",
    "mrp_": "MRP",
    "mps_": "MPS",
    "crm_": "CRM",
    "prc_": "PRC",
    "fin_": "FIN",
    "hcm_": "HCM",
    "qms_": "QMS",
    "pos_": "POS",
    "invbill_": "INVBILL",
    "bdg_": "BDG",
    "cst_": "CST",
    "pm_": "PM",
    "bi_": "BI",
    "wfl_": "WFL",
    "svc_": "SVC",
    "tkt_": "TKT",
}


def _modulo(sequence_key: str) -> str:
    if sequence_key.startswith("invbill_"):
        return "INVBILL"
    for prefix, code in _MODULE_BY_PREFIX.items():
        if sequence_key.startswith(prefix):
            return code
    raise ValueError(f"No modulo mapping for {sequence_key}")


def _def(
    sequence_key: str,
    code_column: str,
    policy: CodePolicy,
    scope: ScopeType,
    family: SequenceFamily,
    store: StoreType,
    fmt: FormatterProfile,
    par: ParserProfile,
    val: ValidatorProfile,
    preview: bool,
    manual: bool,
    align: AlignmentMode,
    prefix: str,
    pad: int,
    max_len: int,
    *,
    parser_partial: bool = False,
    supports_import: bool | None = None,
    normalize: NormalizeCase = NormalizeCase.UPPER,
    doc: str = "",
) -> SequenceDefinition:
    if supports_import is None:
        supports_import = policy == CodePolicy.AUTO_DEFAULT or align == AlignmentMode.IMPORT
    return SequenceDefinition(
        sequence_key=sequence_key,
        table_name=sequence_key,
        code_column=code_column,
        modulo_codigo=_modulo(sequence_key),
        catalog_version=CATALOG_VERSION,
        policy=policy,
        sequence_family=family,
        scope_type=scope,
        store_type=store,
        formatter_profile=fmt,
        parser_profile=par,
        validator_profile=val,
        supports_preview=preview,
        allow_manual=manual,
        alignment_mode=align,
        supports_import=supports_import,
        default_prefix=prefix,
        default_separator="",
        default_padding=pad,
        numero_inicial=1,
        max_output_length=max_len,
        normalize_case=normalize,
        parser_partial=parser_partial,
        documentation=doc,
    )


def _build_catalog() -> dict[str, SequenceDefinition]:
    entries: list[SequenceDefinition] = [
        # F1 — Maestros
        _def("org_empresa", "codigo_empresa", CodePolicy.AUTO_DEFAULT, ScopeType.TENANT, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "EMP", 3, 20),
        _def("org_sucursal", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "SUC", 3, 20),
        _def("org_centro_costo", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CC", 3, 20),
        _def("org_departamento", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "DEP", 3, 20),
        _def("org_cargo", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CAR", 3, 20),
        _def("inv_categoria_producto", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CAT", 3, 20),
        _def("inv_unidad_medida", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "UM", 3, 10),
        _def("inv_producto", "codigo_sku", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "P", 5, 50),
        _def("inv_almacen", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "ALM", 3, 20),
        _def("inv_tipo_movimiento", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "TM", 3, 20),
        _def("pur_proveedor", "codigo_proveedor", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "PROV", 4, 20),
        _def("sls_cliente", "codigo_cliente", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CLI", 4, 20),
        _def("hcm_empleado", "codigo_empleado", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "EMP", 4, 20),
        _def("log_transportista", "codigo_transportista", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "TR", 4, 20),
        _def("log_ruta", "codigo_ruta", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "RUT", 4, 20),
        _def("mfg_centro_trabajo", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CT", 3, 20),
        _def("mfg_operacion", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "OP", 3, 20),
        _def("mfg_lista_materiales", "codigo_bom", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "BOM", 4, 20),
        _def("mfg_ruta_fabricacion", "codigo_ruta", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "RF", 4, 20),
        _def("mnt_activo", "codigo_activo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "ACT", 4, 20),
        _def("mnt_plan_mantenimiento", "codigo_plan", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "PM", 4, 20),
        _def("mrp_plan_maestro", "codigo_plan", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "MRP", 4, 20),
        _def("mps_plan_produccion", "codigo_plan", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "MPS", 4, 20),
        _def("crm_campana", "codigo_campana", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CMP", 4, 20),
        _def("prc_lista_precio", "codigo_lista", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "LP", 4, 20),
        _def("prc_promocion", "codigo_promocion", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "PRM", 4, 20),
        _def("fin_plan_cuentas", "codigo_cuenta", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "", 6, 20, doc="Códigos jerárquicos sin prefijo"),
        _def("hcm_concepto_planilla", "codigo_concepto", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CON", 4, 20),
        _def("qms_parametro_calidad", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "QMP", 4, 20),
        _def("qms_plan_inspeccion", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "QPL", 4, 20),
        _def("pos_punto_venta", "codigo_punto_venta", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "PV", 3, 20),
        _def("bdg_presupuesto", "codigo_presupuesto", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "PRE", 4, 20),
        _def("cst_centro_costo_tipo", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "CCT", 3, 20),
        _def("pm_proyecto", "codigo_proyecto", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "PRY", 4, 20),
        _def("bi_reporte", "codigo_reporte", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "RPT", 4, 20),
        _def("wfl_flujo_trabajo", "codigo_flujo", CodePolicy.AUTO_DEFAULT, ScopeType.EMPRESA, SequenceFamily.F1, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "WFL", 4, 20),
        # F4 — WMS maestros
        _def("wms_zona_almacen", "codigo", CodePolicy.AUTO_DEFAULT, ScopeType.ALMACEN, SequenceFamily.F4, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_MASTER, True, True, AlignmentMode.YES, "ZON", 3, 20),
        _def("wms_ubicacion", "codigo_ubicacion", CodePolicy.AUTO_DEFAULT, ScopeType.ALMACEN, SequenceFamily.F4, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_UBICACION, True, True, AlignmentMode.PARTIAL, "", 3, 30, parser_partial=True),
        # F2 — Documentos
        _def("inv_movimiento", "numero_movimiento", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "MOV", 6, 20),
        _def("inv_inventario_fisico", "numero_inventario", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "IF", 5, 20),
        _def("pur_solicitud_compra", "numero_solicitud", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "SC", 6, 20),
        _def("pur_cotizacion", "numero_cotizacion", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "CC", 6, 20),
        _def("pur_orden_compra", "numero_oc", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "OC", 6, 20),
        _def("pur_recepcion", "numero_recepcion", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "REC", 6, 20),
        _def("log_despacho", "numero_despacho", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "DES", 6, 20),
        _def("mfg_orden_produccion", "numero_op", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "OP", 6, 20),
        _def("mnt_orden_trabajo", "numero_ot", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "OT", 6, 20),
        _def("sls_cotizacion", "numero_cotizacion", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "COT", 6, 20),
        _def("sls_pedido", "numero_pedido", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "PED", 6, 20),
        _def("crm_oportunidad", "numero_oportunidad", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "OPO", 6, 20),
        _def("pos_venta", "numero_venta", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "VTA", 6, 20),
        _def("hcm_contrato", "numero_contrato", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "CTR", 6, 20),
        _def("hcm_planilla", "numero_planilla", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "PLA", 6, 20),
        _def("hcm_prestamo", "numero_prestamo", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "PRE", 6, 20),
        _def("fin_asiento_contable", "numero_asiento", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "AS", 6, 20),
        _def("qms_inspeccion", "numero_inspeccion", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "INS", 6, 20),
        _def("qms_no_conformidad", "numero_nc", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "NC", 6, 20),
        _def("svc_orden_servicio", "numero_os", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "OS", 6, 20),
        _def("tkt_ticket", "numero_ticket", CodePolicy.AUTO_REQUIRED, ScopeType.EMPRESA, SequenceFamily.F2, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "TKT", 6, 20),
        _def("wms_tarea", "numero_tarea", CodePolicy.AUTO_REQUIRED, ScopeType.ALMACEN, SequenceFamily.F4, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "TAR", 6, 20),
        # F5 — POS turno
        _def("pos_turno_caja", "numero_turno", CodePolicy.AUTO_REQUIRED, ScopeType.PUNTO_VENTA, SequenceFamily.F5, StoreType.CFG, FormatterProfile.FMT_STANDARD, ParserProfile.PAR_PREFIX_NUM, ValidatorProfile.VAL_DOCUMENT, False, False, AlignmentMode.IMPORT, "TUR", 4, 20),
        # F3 — Fiscal
        _def("invbill_comprobante", "numero", CodePolicy.AUTO_REQUIRED, ScopeType.SERIE_FISCAL, SequenceFamily.F3, StoreType.FISCAL, FormatterProfile.FMT_FISCAL_8, ParserProfile.PAR_NONE, ValidatorProfile.VAL_FISCAL_NUM, False, False, AlignmentMode.NO, "", 8, 10, normalize=NormalizeCase.AS_IS),
        _def("log_guia_remision", "numero", CodePolicy.AUTO_REQUIRED, ScopeType.SERIE_FISCAL, SequenceFamily.F3, StoreType.FISCAL, FormatterProfile.FMT_FISCAL_8, ParserProfile.PAR_NONE, ValidatorProfile.VAL_FISCAL_NUM, False, False, AlignmentMode.NO, "", 8, 10, normalize=NormalizeCase.AS_IS),
    ]
    catalog = {e.sequence_key: e for e in entries}
    if len(catalog) != len(entries):
        raise RuntimeError("Duplicate sequence_key in catalog")
    if len(catalog) != 63:
        raise RuntimeError(f"Expected 63 catalog entries, got {len(catalog)}")
    return catalog


_CATALOG: dict[str, SequenceDefinition] = _build_catalog()


class SequenceCatalog:
    """Registro inmutable versionado de secuencias."""

    VERSION = CATALOG_VERSION

    @classmethod
    def get(cls, sequence_key: str) -> SequenceDefinition:
        try:
            return _CATALOG[sequence_key]
        except KeyError as exc:
            raise KeyError(f"sequence_key desconocido: {sequence_key}") from exc

    @classmethod
    def contains(cls, sequence_key: str) -> bool:
        return sequence_key in _CATALOG

    @classmethod
    def all_keys(cls) -> tuple[str, ...]:
        return tuple(sorted(_CATALOG.keys()))

    @classmethod
    def all_definitions(cls) -> tuple[SequenceDefinition, ...]:
        return tuple(_CATALOG[k] for k in sorted(_CATALOG.keys()))

    @classmethod
    def count(cls) -> int:
        return len(_CATALOG)


def get_sequence_catalog() -> SequenceCatalog:
    return SequenceCatalog
