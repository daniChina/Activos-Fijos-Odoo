# aft/__manifest__.py
{
    'name': 'Gestión de Activos Fijos Tangibles (AFT)',
    'version': '1.0',
    'category': 'Contabilidad',
    'summary': 'Gestión de activos fijos con depreciación y movimientos',
    'license': 'LGPL-3',
    
    'images': ['static/description/banner.jpeg'],
    'icon': 'static/description/icon.png',   
    
    'price': 0.0,
    'currency': 'CUP',
    'description': """
        Módulo para gestión de activos fijos tangibles
        - Depreciación automática según categorías
        - Movimientos: Compra, Alta, Baja y Traslado
        - Control por áreas con cuentas contables
    """,
    'author': "DGA & RPV",
    'website': 'https://www.pdl999.com',
    'depends': ['account', 'base'],
    'data': [
        # Archivos de seguridad
        'security/ir.model.access.csv',
        # Archivos de datos
        'data/depreciation_cron.xml',
        'data/sequence_data.xml', 
        'data/account_data.xml', 
        # Archivos de vistas
        'views/aft_area_views.xml',
        'views/aft_assets_views.xml',
        'views/aft_category_views.xml',
        'views/aft_transfer_views.xml',
        'views/menu_views.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}