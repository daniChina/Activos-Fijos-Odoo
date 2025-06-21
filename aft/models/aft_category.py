# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class AftCategory(models.Model):
    _name = 'aft.category'
    _description = 'Categoría de Activo Fijo Tangible'
    _order = 'name asc'

    name = fields.Char(
        string='Nombre', 
        required=True,
        help="Nombre de la categoría (Ej: Maquinaria, Equipos de Computación)"
    )
    
    code = fields.Char(
        string='Código',
        size=10,
        help="Código corto para identificación"
    )
    
    default_depreciation_rate = fields.Float(
        string='Tasa de Depreciación (%)',
        required=True,
        default=10.0,
        help="Tasa de depreciación anual según legislación cubana"
    )
    
    asset_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Activo',
        required=True,
        domain=[('deprecated', '=', False)],
        help="Cuenta contable donde se registrará el activo al dar de alta"
    )
    
    note = fields.Text(string='Notas Adicionales')
    
    # Restricción para validar la tasa de depreciación
    @api.constrains('default_depreciation_rate')
    def _check_depreciation_rate(self):
        for record in self:
            if record.default_depreciation_rate <= 0 or record.default_depreciation_rate > 100:
                raise ValidationError(
                    _("La tasa de depreciación debe estar entre 0.01% y 100%")
                )
    
    # Restricción para nombres únicos
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'El nombre de la categoría debe ser único'),
        ('code_unique', 'UNIQUE(code)', 'El código de categoría debe ser único')
    ]