# models/aft_area.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class AftArea(models.Model):
    _name = 'aft.area'
    _description = 'Área de Activos Fijos'
    
    
    name = fields.Char(required=True)
    depreciation_expense_account_id = fields.Many2one(
        'account.account',
        string="Cuenta de Gasto de Depreciación",
        required=True,
        domain=[('deprecated', '=', False)]
    )