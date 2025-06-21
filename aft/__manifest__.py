# -*- coding: utf-8 -*-
{
    'name': "Activos Fijos ",

    'summary': """
     Modulo para la gestion de los activos fijos tangibles de una empresa
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "DGA & RPV",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Contabilidad',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    
    'installable':True,
    'application': True,

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/aft_area_view.xml',
        'views/aft_assets_view.xml',
        'views/aft_category_view.xml',
        'views/aft_report_view.xml',
        'views/aft_transfer_view.xml'
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
