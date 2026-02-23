# app/infrastructure/database/tables_erp/__init__.py
"""
Tablas SQLAlchemy Core para módulos ERP.

✅ Diseño multi-tenant: Todas las tablas tienen cliente_id.
✅ Sin FK a cliente: Permite usar en BD dedicada donde no existe tabla cliente.
✅ Metadata propia: metadata_erp para no depender de tabla cliente en definición.

USO:
    from app.infrastructure.database.tables_erp import (
        OrgEmpresaTable,
        OrgCentroCostoTable,
        OrgSucursalTable,
    )
"""

from app.infrastructure.database.tables_erp.tables_org import (
    OrgEmpresaTable,
    OrgCentroCostoTable,
    OrgSucursalTable,
    OrgDepartamentoTable,
    OrgCargoTable,
    OrgParametroSistemaTable,
)
from app.infrastructure.database.tables_erp.tables_inv import (
    InvCategoriaProductoTable,
    InvUnidadMedidaTable,
    InvProductoTable,
    InvAlmacenTable,
    InvStockTable,
    InvTipoMovimientoTable,
    InvMovimientoTable,
    InvMovimientoDetalleTable,
    InvInventarioFisicoTable,
    InvInventarioFisicoDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_pur import (
    PurProveedorTable,
    PurProveedorContactoTable,
    PurProductoProveedorTable,
    PurSolicitudCompraTable,
    PurSolicitudCompraDetalleTable,
    PurCotizacionTable,
    PurCotizacionDetalleTable,
    PurOrdenCompraTable,
    PurOrdenCompraDetalleTable,
    PurRecepcionTable,
    PurRecepcionDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_sls import (
    SlsClienteTable,
    SlsClienteContactoTable,
    SlsClienteDireccionTable,
    SlsCotizacionTable,
    SlsCotizacionDetalleTable,
    SlsPedidoTable,
    SlsPedidoDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_invbill import (
    InvbillSerieComprobanteTable,
    InvbillComprobanteTable,
    InvbillComprobanteDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_prc import (
    PrcListaPrecioTable,
    PrcListaPrecioDetalleTable,
    PrcPromocionTable,
)
from app.infrastructure.database.tables_erp.tables_log import (
    LogTransportistaTable,
    LogVehiculoTable,
    LogRutaTable,
    LogGuiaRemisionTable,
    LogGuiaRemisionDetalleTable,
    LogDespachoTable,
    LogDespachoGuiaTable,
)
from app.infrastructure.database.tables_erp.tables_fin import (
    FinPlanCuentasTable,
    FinPeriodoContableTable,
    FinAsientoContableTable,
    FinAsientoDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_wms import (
    WmsZonaAlmacenTable,
    WmsUbicacionTable,
    WmsStockUbicacionTable,
    WmsTareaTable,
)
from app.infrastructure.database.tables_erp.tables_qms import (
    QmsParametroCalidadTable,
    QmsPlanInspeccionTable,
    QmsPlanInspeccionDetalleTable,
    QmsInspeccionTable,
    QmsInspeccionDetalleTable,
    QmsNoConformidadTable,
)
from app.infrastructure.database.tables_erp.tables_crm import (
    CrmCampanaTable,
    CrmLeadTable,
    CrmOportunidadTable,
    CrmActividadTable,
)
from app.infrastructure.database.tables_erp.tables_pos import (
    PosPuntoVentaTable,
    PosTurnoCajaTable,
    PosVentaTable,
    PosVentaDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_hcm import (
    HcmEmpleadoTable,
    HcmContratoTable,
    HcmConceptoPlanillaTable,
    HcmPlanillaTable,
    HcmPlanillaEmpleadoTable,
    HcmPlanillaDetalleTable,
    HcmAsistenciaTable,
    HcmVacacionesTable,
    HcmPrestamoTable,
)
from app.infrastructure.database.tables_erp.tables_mfg import (
    MfgCentroTrabajoTable,
    MfgOperacionTable,
    MfgListaMaterialesTable,
    MfgListaMaterialesDetalleTable,
    MfgRutaFabricacionTable,
    MfgRutaFabricacionDetalleTable,
    MfgOrdenProduccionTable,
    MfgOrdenProduccionOperacionTable,
    MfgConsumoMaterialesTable,
)
from app.infrastructure.database.tables_erp.tables_mrp import (
    MrpPlanMaestroTable,
    MrpNecesidadBrutaTable,
    MrpExplosionMaterialesTable,
    MrpOrdenSugeridaTable,
)
from app.infrastructure.database.tables_erp.tables_mps import (
    MpsPronosticoDemandaTable,
    MpsPlanProduccionTable,
    MpsPlanProduccionDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_mnt import (
    MntActivoTable,
    MntPlanMantenimientoTable,
    MntOrdenTrabajoTable,
    MntHistorialMantenimientoTable,
)
from app.infrastructure.database.tables_erp.tables_cst import (
    CstCentroCostoTipoTable,
    CstProductoCostoTable,
)
from app.infrastructure.database.tables_erp.tables_tax import (
    TaxLibroElectronicoTable,
)
from app.infrastructure.database.tables_erp.tables_bdg import (
    BdgPresupuestoTable,
    BdgPresupuestoDetalleTable,
)
from app.infrastructure.database.tables_erp.tables_pm import (
    PmProyectoTable,
)
from app.infrastructure.database.tables_erp.tables_svc import (
    SvcOrdenServicioTable,
)
from app.infrastructure.database.tables_erp.tables_tkt import (
    TktTicketTable,
)
from app.infrastructure.database.tables_erp.tables_dms import (
    DmsDocumentoTable,
)
from app.infrastructure.database.tables_erp.tables_wfl import (
    WflFlujoTrabajoTable,
)
from app.infrastructure.database.tables_erp.tables_bi import (
    BiReporteTable,
)
from app.infrastructure.database.tables_erp.tables_aud import (
    AudLogAuditoriaTable,
)

__all__ = [
    # ORG
    "OrgEmpresaTable",
    "OrgCentroCostoTable",
    "OrgSucursalTable",
    "OrgDepartamentoTable",
    "OrgCargoTable",
    "OrgParametroSistemaTable",
    # INV
    "InvCategoriaProductoTable",
    "InvUnidadMedidaTable",
    "InvProductoTable",
    "InvAlmacenTable",
    "InvStockTable",
    "InvTipoMovimientoTable",
    "InvMovimientoTable",
    "InvMovimientoDetalleTable",
    "InvInventarioFisicoTable",
    "InvInventarioFisicoDetalleTable",
    # PUR
    "PurProveedorTable",
    "PurProveedorContactoTable",
    "PurProductoProveedorTable",
    "PurSolicitudCompraTable",
    "PurSolicitudCompraDetalleTable",
    "PurCotizacionTable",
    "PurCotizacionDetalleTable",
    "PurOrdenCompraTable",
    "PurOrdenCompraDetalleTable",
    "PurRecepcionTable",
    "PurRecepcionDetalleTable",
    # SLS
    "SlsClienteTable",
    "SlsClienteContactoTable",
    "SlsClienteDireccionTable",
    "SlsCotizacionTable",
    "SlsCotizacionDetalleTable",
    "SlsPedidoTable",
    "SlsPedidoDetalleTable",
    # INV_BILL
    "InvbillSerieComprobanteTable",
    "InvbillComprobanteTable",
    "InvbillComprobanteDetalleTable",
    # PRC
    "PrcListaPrecioTable",
    "PrcListaPrecioDetalleTable",
    "PrcPromocionTable",
    # LOG
    "LogTransportistaTable",
    "LogVehiculoTable",
    "LogRutaTable",
    "LogGuiaRemisionTable",
    "LogGuiaRemisionDetalleTable",
    "LogDespachoTable",
    "LogDespachoGuiaTable",
    # FIN
    "FinPlanCuentasTable",
    "FinPeriodoContableTable",
    "FinAsientoContableTable",
    "FinAsientoDetalleTable",
    # WMS
    "WmsZonaAlmacenTable",
    "WmsUbicacionTable",
    "WmsStockUbicacionTable",
    "WmsTareaTable",
    # QMS
    "QmsParametroCalidadTable",
    "QmsPlanInspeccionTable",
    "QmsPlanInspeccionDetalleTable",
    "QmsInspeccionTable",
    "QmsInspeccionDetalleTable",
    "QmsNoConformidadTable",
    # CRM
    "CrmCampanaTable",
    "CrmLeadTable",
    "CrmOportunidadTable",
    "CrmActividadTable",
    # POS
    "PosPuntoVentaTable",
    "PosTurnoCajaTable",
    "PosVentaTable",
    "PosVentaDetalleTable",
    # HCM
    "HcmEmpleadoTable",
    "HcmContratoTable",
    "HcmConceptoPlanillaTable",
    "HcmPlanillaTable",
    "HcmPlanillaEmpleadoTable",
    "HcmPlanillaDetalleTable",
    "HcmAsistenciaTable",
    "HcmVacacionesTable",
    "HcmPrestamoTable",
    # MFG
    "MfgCentroTrabajoTable",
    "MfgOperacionTable",
    "MfgListaMaterialesTable",
    "MfgListaMaterialesDetalleTable",
    "MfgRutaFabricacionTable",
    "MfgRutaFabricacionDetalleTable",
    "MfgOrdenProduccionTable",
    "MfgOrdenProduccionOperacionTable",
    "MfgConsumoMaterialesTable",
    # MRP
    "MrpPlanMaestroTable",
    "MrpNecesidadBrutaTable",
    "MrpExplosionMaterialesTable",
    "MrpOrdenSugeridaTable",
    # MPS
    "MpsPronosticoDemandaTable",
    "MpsPlanProduccionTable",
    "MpsPlanProduccionDetalleTable",
    # MNT
    "MntActivoTable",
    "MntPlanMantenimientoTable",
    "MntOrdenTrabajoTable",
    "MntHistorialMantenimientoTable",
    # CST
    "CstCentroCostoTipoTable",
    "CstProductoCostoTable",
    # TAX
    "TaxLibroElectronicoTable",
    # BDG
    "BdgPresupuestoTable",
    "BdgPresupuestoDetalleTable",
    # PM
    "PmProyectoTable",
    # SVC
    "SvcOrdenServicioTable",
    # TKT
    "TktTicketTable",
    # DMS
    "DmsDocumentoTable",
    # WFL
    "WflFlujoTrabajoTable",
    # BI
    "BiReporteTable",
    # AUD
    "AudLogAuditoriaTable",
]
