# app/modules/modulos/application/helpers/menu_transformer.py
"""
Helper para transformar el resultado del stored procedure sp_obtener_menu_usuario
a la estructura JSON jerárquica esperada por el frontend.

El SP retorna un dataset plano que debe transformarse a:
{
  "modulos": [
    {
      "modulo_id": "...",
      "codigo": "...",
      "secciones": [
        {
          "seccion_id": "...",
          "menus": [
            {
              "menu_id": "...",
              "permisos": {...},
              "submenus": [...]
            }
          ]
        }
      ]
    }
  ]
}
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from app.modules.modulos.presentation.schemas import (
    MenuUsuarioResponse, ModuloMenuResponse, SeccionMenu, MenuItem, PermisosMenu
)

logger = logging.getLogger(__name__)


def transformar_sp_menu_usuario(sp_result: List[Dict[str, Any]]) -> MenuUsuarioResponse:
    """
    Transforma el resultado plano del SP sp_obtener_menu_usuario a estructura jerárquica.
    
    El SP debe retornar columnas como:
    - modulo_id, modulo_codigo, modulo_nombre, modulo_icono, modulo_color, modulo_categoria, modulo_orden
    - seccion_id, seccion_codigo, seccion_nombre, seccion_icono, seccion_orden
    - menu_id, menu_codigo, menu_nombre, menu_icono, menu_ruta, menu_nivel, menu_tipo, menu_orden
    - menu_padre_id
    - puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, puede_aprobar
    
    Args:
        sp_result: Lista de diccionarios con el resultado del SP
        
    Returns:
        MenuUsuarioResponse: Estructura jerárquica completa
    """
    if not sp_result:
        logger.info("SP sp_obtener_menu_usuario no retornó resultados")
        return MenuUsuarioResponse(modulos=[])
    
    # Estructura para agrupar: modulo -> seccion -> menu -> submenu
    modulos_dict: Dict[UUID, Dict[str, Any]] = {}
    
    for row in sp_result:
        # Extraer datos del módulo
        modulo_id = row.get('modulo_id')
        if not modulo_id:
            logger.warning(f"Fila sin modulo_id, saltando: {row}")
            continue
        
        # Inicializar módulo si no existe
        if modulo_id not in modulos_dict:
            modulos_dict[modulo_id] = {
                'modulo_id': modulo_id,
                'codigo': row.get('modulo_codigo', ''),
                'nombre': row.get('modulo_nombre', ''),
                'icono': row.get('modulo_icono'),
                'color': row.get('modulo_color', '#1976D2'),
                'categoria': row.get('modulo_categoria', 'operaciones'),
                'orden': row.get('modulo_orden', 0),
                'secciones': {}
            }
        
        modulo = modulos_dict[modulo_id]
        
        # Extraer datos de la sección (puede ser None)
        seccion_id = row.get('seccion_id')
        if seccion_id:
            if seccion_id not in modulo['secciones']:
                modulo['secciones'][seccion_id] = {
                    'seccion_id': seccion_id,
                    'codigo': row.get('seccion_codigo', ''),
                    'nombre': row.get('seccion_nombre', ''),
                    'icono': row.get('seccion_icono'),
                    'orden': row.get('seccion_orden', 0),
                    'menus': {}
                }
            seccion = modulo['secciones'][seccion_id]
        else:
            # Menú sin sección - crear sección virtual "SIN_SECCION"
            seccion_id_virtual = UUID('00000000-0000-0000-0000-000000000000')
            if seccion_id_virtual not in modulo['secciones']:
                modulo['secciones'][seccion_id_virtual] = {
                    'seccion_id': None,
                    'codigo': 'SIN_SECCION',
                    'nombre': 'Sin Sección',
                    'icono': None,
                    'orden': 9999,
                    'menus': {}
                }
            seccion = modulo['secciones'][seccion_id_virtual]
        
        # Extraer datos del menú
        menu_id = row.get('menu_id')
        if not menu_id:
            logger.warning(f"Fila sin menu_id, saltando: {row}")
            continue
        
        # Crear permisos
        permisos = PermisosMenu(
            ver=bool(row.get('puede_ver', False)),
            crear=bool(row.get('puede_crear', False)),
            editar=bool(row.get('puede_editar', False)),
            eliminar=bool(row.get('puede_eliminar', False)),
            exportar=bool(row.get('puede_exportar', False)),
            imprimir=bool(row.get('puede_imprimir', False)),
            aprobar=bool(row.get('puede_aprobar', False))
        )
        
        # Crear item de menú
        menu_item = {
            'menu_id': menu_id,
            'codigo': row.get('menu_codigo'),
            'nombre': row.get('menu_nombre', ''),
            'icono': row.get('menu_icono'),
            'ruta': row.get('ruta') or row.get('menu_ruta'),  # Compatibilidad con ambos nombres
            'nivel': row.get('menu_nivel', 1),
            'tipo_menu': row.get('menu_tipo', 'pantalla'),
            'orden': row.get('menu_orden', 0),
            'permisos': permisos,
            'menu_padre_id': row.get('menu_padre_id'),
            'submenus': []
        }
        
        # Agregar a la sección
        seccion['menus'][menu_id] = menu_item
    
    # Construir jerarquía de submenús
    for modulo_data in modulos_dict.values():
        for seccion_data in modulo_data['secciones'].values():
            menus = seccion_data['menus']
            
            # Separar menús raíz y submenús
            root_menus = []
            menus_by_id = {}
            
            for menu_id, menu_data in menus.items():
                menus_by_id[menu_id] = menu_data
                if not menu_data['menu_padre_id']:
                    root_menus.append(menu_data)
            
            # Asignar submenús a sus padres
            for menu_id, menu_data in menus.items():
                padre_id = menu_data['menu_padre_id']
                if padre_id and padre_id in menus_by_id:
                    padre = menus_by_id[padre_id]
                    if menu_data not in padre['submenus']:
                        padre['submenus'].append(menu_data)
            
            # Ordenar menús raíz y submenús
            root_menus.sort(key=lambda m: m['orden'])
            for menu in menus_by_id.values():
                menu['submenus'].sort(key=lambda m: m['orden'])
            
            # Actualizar lista de menús de la sección (solo raíz)
            seccion_data['menus'] = root_menus
    
    # Convertir a schemas Pydantic
    modulos_list = []
    for modulo_data in modulos_dict.values():
        secciones_list = []
        for seccion_data in modulo_data['secciones'].values():
            menus_list = []
            for menu_data in seccion_data['menus']:
                menus_list.append(MenuItem(**menu_data))
            
            secciones_list.append(SeccionMenu(
                seccion_id=seccion_data['seccion_id'],
                codigo=seccion_data['codigo'],
                nombre=seccion_data['nombre'],
                icono=seccion_data['icono'],
                orden=seccion_data['orden'],
                menus=menus_list
            ))
        
        # Ordenar secciones
        secciones_list.sort(key=lambda s: s.orden)
        
        modulos_list.append(ModuloMenuResponse(
            modulo_id=modulo_data['modulo_id'],
            codigo=modulo_data['codigo'],
            nombre=modulo_data['nombre'],
            icono=modulo_data['icono'],
            color=modulo_data['color'],
            categoria=modulo_data['categoria'],
            orden=modulo_data['orden'],
            secciones=secciones_list
        ))
    
    # Ordenar módulos
    modulos_list.sort(key=lambda m: m.orden)
    
    logger.info(f"Transformación completada: {len(modulos_list)} módulos, {sum(len(m.secciones) for m in modulos_list)} secciones")
    return MenuUsuarioResponse(modulos=modulos_list)

