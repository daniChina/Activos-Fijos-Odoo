from odoo import models, fields, api

class AftArea(models.Model):
    _name = 'aft.area'
    _description = 'Área de ubicación de activos'
    
    name = fields.Char('Nombre del Área', required=True)
    area_type = fields.Selection(
        selection=[
            ('productive', 'Productiva'),
            ('associated', 'Asociada a producción, distribución y venta'),
            ('administrative', 'Administrativa'),
        ],
        string='Tipo de Área',
        required=True,
        default='productive'
    )
    expense_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Gasto (Depreciación)',
        domain=[('deprecated', '=', False)],
        required=True
    )
    description = fields.Text('Descripción')
    active = fields.Boolean('Activo', default=True)