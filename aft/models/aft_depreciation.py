# models/aft_depreciation.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class AssetDepreciation(models.Model):
    _name = 'aft.depreciation.line'
    
    date = fields.Date(required=True)
    amount = fields.Monetary()
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Registrado'),
        ('future', 'Futuro')], default='draft')
    
    def write(self, vals):
        # Bloquear modificación de depreciaciones registradas
        if 'state' not in vals and any(line.state == 'posted' for line in self):
            raise UserError("No puede modificar depreciaciones ya registradas")
        return super().write(vals)

    def unlink(self):
        raise UserError('No se puede eliminar la depreciación registrada.')