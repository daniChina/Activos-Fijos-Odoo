# models/aft_asset.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class AftAsset(models.Model):
    _name = 'aft.asset'
    
    category_id = fields.Many2one('aft.category', required=True)
    custom_depreciation_rate = fields.Float(
        string="Tasa de Depreciación Personalizada",
        help="Sobreescribe la tasa de depreciación de la categoría"
    )
    
    @api.depends('category_id', 'custom_depreciation_rate')
    def _compute_effective_rate(self):
        for asset in self:
            asset.effective_depreciation_rate = (
                asset.custom_depreciation_rate or 
                asset.category_id.default_depreciation_rate
     
            )
            
    depreciation_line_ids = fields.One2many(
        'aft.depreciation.line', 
        'asset_id', 
        string="Líneas de Depreciación"
    )            
            
            