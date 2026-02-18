"""
Job para limpiar tokens expirados en todos los tenants.
Funciona tanto para Single-DB como Multi-DB.

✅ FASE 4: Job centralizado para cleanup de tokens por tenant.
"""
import logging
from uuid import UUID
from typing import Dict, List, Any
from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
from app.infrastructure.database.tables import ClienteTable
from sqlalchemy import select
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context
from app.core.tenant.routing import get_connection_metadata_async

logger = logging.getLogger(__name__)


class RefreshTokenCleanupJob:
    """Job para limpiar tokens expirados por tenant."""
    
    @staticmethod
    async def cleanup_all_tenants() -> Dict[str, Any]:
        """
        Limpia tokens expirados en todos los tenants activos.
        
        ✅ FASE 4: Itera todos los tenants activos, establece contexto para cada uno,
        y ejecuta cleanup_expired_tokens() que requiere contexto de tenant.
        
        Funciona tanto para Single-DB como Multi-DB:
        - Single-DB: Todos los tenants en bd_sistema, cleanup por cliente_id
        - Multi-DB: Cada tenant en su BD dedicada, cleanup en su BD específica
        
        Returns:
            Dict con estadísticas de cleanup:
            {
                'tenants_processed': int,
                'tokens_deleted': int,
                'tenants_detail': List[Dict],  # Detalle por tenant
                'errors': List[str]  # Errores por tenant
            }
        """
        stats = {
            'tenants_processed': 0,
            'tokens_deleted': 0,
            'tenants_detail': [],
            'errors': []
        }
        
        logger.info("[CLEANUP_JOB] Iniciando cleanup de tokens expirados para todos los tenants")
        
        try:
            # Obtener todos los tenants activos desde BD central
            query = select(
                ClienteTable.c.cliente_id,
                ClienteTable.c.codigo_cliente,
                ClienteTable.c.subdominio,
                ClienteTable.c.tipo_instalacion
            ).where(
                ClienteTable.c.es_activo == True
            )
            
            async with get_db_connection(
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            ) as session:
                result = await session.execute(query)
                tenants = result.fetchall()
            
            logger.info(f"[CLEANUP_JOB] Encontrados {len(tenants)} tenants activos para procesar")
            
            # Procesar cada tenant
            for tenant in tenants:
                cliente_id = tenant['cliente_id']
                codigo_cliente = tenant.get('codigo_cliente', 'N/A')
                subdominio = tenant.get('subdominio', 'N/A')
                tipo_instalacion = tenant.get('tipo_instalacion', 'shared')
                
                tenant_stats = {
                    'cliente_id': str(cliente_id),
                    'codigo_cliente': codigo_cliente,
                    'tokens_deleted': 0,
                    'success': False,
                    'error': None
                }
                
                try:
                    # ✅ FASE 4: Obtener metadata de conexión para este tenant
                    connection_metadata = await get_connection_metadata_async(cliente_id)
                    database_type = connection_metadata.get('database_type', 'single')
                    nombre_bd = connection_metadata.get('nombre_bd', 'bd_sistema')
                    
                    logger.debug(
                        f"[CLEANUP_JOB] Procesando tenant {codigo_cliente} ({cliente_id}): "
                        f"{database_type.upper()}-DB ({nombre_bd})"
                    )
                    
                    # ✅ FASE 4: Establecer contexto del tenant con metadata completa
                    tenant_context = TenantContext(
                        client_id=cliente_id,
                        codigo_cliente=codigo_cliente,
                        subdominio=subdominio,
                        database_type=database_type,
                        nombre_bd=nombre_bd,
                        tipo_instalacion=tipo_instalacion,
                        connection_metadata=connection_metadata
                    )
                    
                    # Establecer contexto (retorna tokens para reset)
                    tokens = set_tenant_context(tenant_context)
                    
                    try:
                        # ✅ FASE 4: Ejecutar cleanup para este tenant
                        # cleanup_expired_tokens() requiere contexto (modificado en Fase 2)
                        deleted_count = await RefreshTokenService.cleanup_expired_tokens()
                        
                        # Actualizar estadísticas
                        stats['tenants_processed'] += 1
                        stats['tokens_deleted'] += deleted_count
                        tenant_stats['tokens_deleted'] = deleted_count
                        tenant_stats['success'] = True
                        
                        logger.info(
                            f"[CLEANUP_JOB] ✅ Tenant {codigo_cliente} ({cliente_id}): "
                            f"{deleted_count} tokens eliminados"
                        )
                        
                    except Exception as cleanup_error:
                        # Error durante cleanup (no crítico, continuar con siguiente tenant)
                        error_msg = (
                            f"Error en cleanup para tenant {codigo_cliente} ({cliente_id}): "
                            f"{str(cleanup_error)}"
                        )
                        logger.error(f"[CLEANUP_JOB] ❌ {error_msg}", exc_info=True)
                        stats['errors'].append(error_msg)
                        tenant_stats['error'] = str(cleanup_error)
                        
                    finally:
                        # ✅ FASE 4: Limpiar contexto siempre
                        reset_tenant_context(tokens)
                        
                except Exception as tenant_error:
                    # Error al obtener metadata o establecer contexto
                    error_msg = (
                        f"Error procesando tenant {codigo_cliente} ({cliente_id}): "
                        f"{str(tenant_error)}"
                    )
                    logger.error(f"[CLEANUP_JOB] ❌ {error_msg}", exc_info=True)
                    stats['errors'].append(error_msg)
                    tenant_stats['error'] = str(tenant_error)
                
                # Agregar detalle del tenant a estadísticas
                stats['tenants_detail'].append(tenant_stats)
            
            logger.info(
                f"[CLEANUP_JOB] ✅ Completado: {stats['tenants_processed']} tenants procesados, "
                f"{stats['tokens_deleted']} tokens eliminados, "
                f"{len(stats['errors'])} errores"
            )
            
            return stats
            
        except Exception as e:
            logger.exception(f"[CLEANUP_JOB] ❌ Error crítico en cleanup job: {str(e)}")
            stats['errors'].append(f"Error crítico: {str(e)}")
            return stats
    
    @staticmethod
    async def cleanup_single_tenant(cliente_id: UUID) -> Dict[str, Any]:
        """
        Limpia tokens expirados para un tenant específico.
        
        ✅ FASE 4: Versión simplificada para cleanup de un solo tenant.
        Útil para ejecución manual o desde endpoints específicos.
        
        Args:
            cliente_id: ID del tenant a limpiar
        
        Returns:
            Dict con estadísticas del cleanup:
            {
                'cliente_id': str,
                'tokens_deleted': int,
                'success': bool,
                'error': Optional[str]
            }
        """
        logger.info(f"[CLEANUP_JOB] Iniciando cleanup para tenant {cliente_id}")
        
        result = {
            'cliente_id': str(cliente_id),
            'tokens_deleted': 0,
            'success': False,
            'error': None
        }
        
        try:
            # Obtener metadata de conexión
            connection_metadata = await get_connection_metadata_async(cliente_id)
            database_type = connection_metadata.get('database_type', 'single')
            nombre_bd = connection_metadata.get('nombre_bd', 'bd_sistema')
            
            # Obtener información del cliente desde BD central
            query = select(
                ClienteTable.c.codigo_cliente,
                ClienteTable.c.subdominio,
                ClienteTable.c.tipo_instalacion
            ).where(
                ClienteTable.c.cliente_id == cliente_id,
                ClienteTable.c.es_activo == True
            )
            
            async with get_db_connection(
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            ) as session:
                tenant_result = await session.execute(query)
                tenant_info = tenant_result.fetchone()
                
                if not tenant_info:
                    raise ValueError(f"Tenant {cliente_id} no encontrado o inactivo")
                
                codigo_cliente = tenant_info['codigo_cliente']
                subdominio = tenant_info.get('subdominio', 'N/A')
                tipo_instalacion = tenant_info.get('tipo_instalacion', 'shared')
            
            # Establecer contexto
            tenant_context = TenantContext(
                client_id=cliente_id,
                codigo_cliente=codigo_cliente,
                subdominio=subdominio,
                database_type=database_type,
                nombre_bd=nombre_bd,
                tipo_instalacion=tipo_instalacion,
                connection_metadata=connection_metadata
            )
            
            tokens = set_tenant_context(tenant_context)
            
            try:
                # Ejecutar cleanup
                deleted_count = await RefreshTokenService.cleanup_expired_tokens()
                result['tokens_deleted'] = deleted_count
                result['success'] = True
                
                logger.info(
                    f"[CLEANUP_JOB] ✅ Tenant {codigo_cliente} ({cliente_id}): "
                    f"{deleted_count} tokens eliminados"
                )
                
            finally:
                reset_tenant_context(tokens)
                
        except Exception as e:
            error_msg = f"Error en cleanup para tenant {cliente_id}: {str(e)}"
            logger.error(f"[CLEANUP_JOB] ❌ {error_msg}", exc_info=True)
            result['error'] = str(e)
        
        return result
