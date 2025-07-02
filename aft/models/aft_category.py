from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AftCategory(models.Model):
    _name = 'aft.category'
    _description = 'Categoría de Activos Fijos'
    
    name = fields.Char('Nombre de la Categoría', required=True)
    depreciation_rate = fields.Float(
        'Tasa de Depreciación Anual (%)',
        digits=(5, 2),
        required=True,
        help='Porcentaje de depreciación anual (ej: 33.33 para 3 años)'
    )
    
    # ✅ CUENTA DE DEPRECIACIÓN ACUMULADA (HABER - cuando se deprecia)
    accumulated_depreciation_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Depreciación Acumulada',
        domain=[
            ('deprecated', '=', False),
            ('user_type_id.name', 'in', ['Fixed Assets', 'Non-current Assets']),  # Solo cuentas de activo
            ('code', 'like', '15%'),  # Filtrar por código que empiece con 15 (activos fijos)
        ],
        required=True,
        help='Cuenta contable donde se acumula la depreciación (HABER)\nEjemplo: 1519 - Depreciación Acumulada Equipos'
    )
    # ✅ CUENTA DE ACTIVO FIJO (DEBE - cuando se compra el activo)
    fixed_asset_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Activo Fijo',
        domain=[
            ('deprecated', '=', False),
            ('user_type_id.name', 'in', ['Fixed Assets', 'Non-current Assets']),  # Solo cuentas de activo fijo
        ],
        required=True,
        help='Cuenta contable donde se registra el valor del activo al comprarlo (DEBE)\nEjemplo: 1511 - Equipos de Cómputo'
    )
    
    description = fields.Text('Descripción')
    active = fields.Boolean('Activo', default=True)

    @api.constrains('depreciation_rate')
    def _check_depreciation_rate(self):
        """Validar que la tasa de depreciación sea válida"""
        for record in self:
            if record.depreciation_rate <= 0 or record.depreciation_rate > 100:
                raise ValidationError(
                    f"La tasa de depreciación debe estar entre 0.01% y 100%. "
                    f"Valor actual: {record.depreciation_rate}%"
                )
                
    
    @api.constrains('fixed_asset_account_id', 'accumulated_depreciation_account_id')
    def _check_different_accounts(self):
        """Validar que las cuentas sean diferentes"""
        for record in self:
            if record.fixed_asset_account_id and record.accumulated_depreciation_account_id:
                if record.fixed_asset_account_id == record.accumulated_depreciation_account_id:
                    raise ValidationError(
                        "La cuenta de activo fijo debe ser diferente a la cuenta de depreciación acumulada."
                    )

    @api.constrains('fixed_asset_account_id')
    def _check_fixed_asset_account_type(self):
        """Validar que la cuenta de activo fijo sea del tipo correcto"""
        for record in self:
             if record.fixed_asset_account_id:
                account_type = record.fixed_asset_account_id.user_type_id.name
                if 'Asset' not in account_type:
                    raise ValidationError(
                        f"La cuenta '{record.fixed_asset_account_id.name}' no es una cuenta de activo.\n"
                        f"Seleccione una cuenta de tipo 'Activo Fijo' o 'Activo No Corriente'."
                    )