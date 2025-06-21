# models/aft_transfer.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class AssetTransfer(models.Model):
    _name = 'aft.asset.transfer'
    
    asset_id = fields.Many2one('aft.asset', required=True)
    date = fields.Date(default=fields.Date.today)
    from_area_id = fields.Many2one('aft.area', string="Área Origen")
    to_area_id = fields.Many2one('aft.area', string="Área Destino", required=True)
    note = fields.Text("Observaciones")
    
    asset_id = fields.Many2one('aft.activos_fijos', string='Activo')
    area_origen_id = fields.Many2one('aft.areas', string='Área origen')
    area_destino_id = fields.Many2one('aft.areas', string='Área destino')
    fecha = fields.Date(default=fields.Date.today)
    usuario_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    
    def confirm_transfer(self):
        self.ensure_one()
        # Registrar en historial
        self.env['aft.asset.history'].create({
            'asset_id': self.asset_id.id,
            'date': self.date,
            'from_area': self.from_area_id.id,
            'to_area': self.to_area_id.id,
            'user_id': self.env.user.id
        })
        # Actualizar área actual
        self.asset_id.area_id = self.to_area_id.id