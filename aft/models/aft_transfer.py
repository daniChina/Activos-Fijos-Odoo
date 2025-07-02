from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AftTransfer(models.Model):
    _name = 'aft.transfer'
    _description = 'Traslado de Activos entre Áreas'
    _order = 'date desc'
    
    # ✅ ELIMINAR CAMPO DUPLICADO transfer_ids
    
    asset_id = fields.Many2one(
        'aft.asset',
        string='Activo',
        required=True,
        domain=[('state', 'in', ['purchased', 'active'])]
    )
    from_area_id = fields.Many2one(
        'aft.area',
        string='Área de Origen',
        readonly=True
    )
    to_area_id = fields.Many2one(
        'aft.area',
        string='Área de Destino',
        required=True
    )
    date = fields.Datetime(
        string='Fecha de Traslado',
        default=fields.Datetime.now,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        required=True
    )
    notes = fields.Text('Observaciones')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
    ], default='draft', string='Estado')

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        """Actualiza automáticamente el área de origen"""
        if self.asset_id:
            if self.asset_id.area_id:
                self.from_area_id = self.asset_id.area_id
                return {
                    'domain': {
                        'to_area_id': [('id', '!=', self.asset_id.area_id.id)]
                    }
                }
            else:
                self.from_area_id = False
                return {
                    'warning': {
                        'title': 'Advertencia',
                        'message': f'El activo "{self.asset_id.name}" no tiene un área asignada. Debe asignarlo a un área antes de trasladarlo.'
                    }
                }
        else:
            self.from_area_id = False

    @api.constrains('from_area_id', 'to_area_id')
    def _check_different_areas(self):
        """Validar que las áreas sean diferentes"""
        for record in self:
            if record.from_area_id and record.to_area_id and record.from_area_id == record.to_area_id:
                raise ValidationError(
                    "El área de destino debe ser diferente al área de origen."
                )

    def action_confirm(self):
        """Confirmar el traslado del activo"""
        self.ensure_one()
        
        # ✅ ASEGURAR que from_area_id esté actualizado
        if self.asset_id and self.asset_id.area_id and not self.from_area_id:
            self.from_area_id = self.asset_id.area_id
        
        # ✅ DEBUG MEJORADO
        print(f"\n=== DEBUG TRASLADO ===")
        print(f"Activo ID: {self.asset_id.id}")
        print(f"Activo Nombre: {self.asset_id.name}")
        print(f"Activo Área ID: {self.asset_id.area_id.id if self.asset_id.area_id else 'None'}")
        print(f"Activo Área Nombre: {self.asset_id.area_id.name if self.asset_id.area_id else 'None'}")
        print(f"from_area_id: {self.from_area_id.id if self.from_area_id else 'None'}")
        print(f"to_area_id: {self.to_area_id.id if self.to_area_id else 'None'}")
        print(f"======================\n")
        
        # Validar que el activo tenga área
        if not self.asset_id.area_id:
            raise UserError(
                f"El activo '{self.asset_id.name}' no tiene un área asignada.\n\n"
                f"SOLUCIÓN:\n"
                f"1. Vaya a AFT → Activos\n"
                f"2. Edite el activo '{self.asset_id.name}'\n"
                f"3. Asigne un área en el campo 'Área'\n"
                f"4. Guarde el activo\n"
                f"5. Vuelva a intentar el traslado"
            )
        
        # Validar área de origen
        if not self.from_area_id:
            raise UserError(
                f"Error interno: No se pudo determinar el área de origen.\n\n"
                f"DETALLES:\n"
                f"• Activo: {self.asset_id.name}\n"
                f"• Área del activo: {self.asset_id.area_id.name if self.asset_id.area_id else 'NINGUNA'}\n"
                f"• from_area_id: {self.from_area_id.name if self.from_area_id else 'VACÍO'}\n\n"
                f"Contacte al administrador del sistema."
            )
        
        # Validar área de destino
        if not self.to_area_id:
            raise UserError("Debe seleccionar un área de destino.")
        
        # Realizar el traslado
        old_area_name = self.from_area_id.name
        self.asset_id.area_id = self.to_area_id
        self.state = 'confirmed'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Traslado Confirmado!',
                'message': f"Activo '{self.asset_id.name}' trasladado de '{old_area_name}' a '{self.to_area_id.name}'",
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def create(self, vals):
        """Asegurar área de origen al crear"""
        if 'asset_id' in vals and vals['asset_id']:
            asset = self.env['aft.asset'].browse(vals['asset_id'])
            if asset.area_id:
                vals['from_area_id'] = asset.area_id.id
        return super().create(vals)