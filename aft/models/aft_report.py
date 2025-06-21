# models/aft_area.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class AftReport(models.Model):
    _name = 'aft.report'
    _description = 'AFT Report'

    name = fields.Char(string='Report Name', required=True)
    report_date = fields.Date(string='Report Date', default=fields.Date.today)
    area_id = fields.Many2one('aft.area', string='Area', required=True)
    asset_ids = fields.Many2many('aft.asset', string='Assets')
    total_value = fields.Float(string='Total Value', compute='_compute_total_value')

    @api.depends('asset_ids.value')
    def _compute_total_value(self):
        for record in self:
            record.total_value = sum(asset.value for asset in record.asset_ids)