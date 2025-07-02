from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class AftAsset(models.Model):
    _name = 'aft.asset'
    _description = 'Activo Fijo Tangible'
    _inherit = ['mail.thread']

    name = fields.Char('Nombre', required=True, tracking=True)
    inventory_number = fields.Char(
        'Número de Inventario',
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('aft.asset.sequence')
    )
    category_id = fields.Many2one('aft.category', 'Categoría', required=True, tracking=True)
    area_id = fields.Many2one('aft.area', 'Área', required=True, tracking=True)
    purchase_date = fields.Date('Fecha de Compra', default=fields.Date.today, tracking=True)
    purchase_value = fields.Monetary('Valor de Compra', required=True, tracking=True)
    current_value = fields.Monetary('Valor Actual', compute='_compute_current_value', store=True)
    
    # ✅ TASA DE DEPRECIACIÓN CON LÓGICA CORRECTA
    custom_depreciation_rate = fields.Float(
        'Tasa de Depreciación Personalizada (%)',
        digits=(5, 2),
        help='Dejar en 0 para usar la tasa de la categoría'
    )
    effective_depreciation_rate = fields.Float(
        'Tasa de Depreciación Efectiva (%)',
        compute='_compute_effective_depreciation_rate',
        store=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('purchased', 'Comprado'),
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ], default='draft', tracking=True)
    
    depreciation_line_ids = fields.One2many(
        'aft.depreciation.line',
        'asset_id',
        string='Líneas de Depreciación',
        readonly=True  # ✅ SOLO LECTURA
    )
    
    # Agregar estos campos después de current_value:

    depreciation_percentage = fields.Float(
        'Porcentaje Depreciado (%)',
        compute='_compute_depreciation_info',
        store=False,
        help='Porcentaje del activo que ya se ha depreciado'
    )

    total_depreciated = fields.Monetary(
        'Total Depreciado',
        compute='_compute_depreciation_info',
        currency_field='currency_id',
        store=False
    )

    remaining_to_depreciate = fields.Monetary(
        'Pendiente por Depreciar',
        compute='_compute_depreciation_info',
        currency_field='currency_id',
        store=False
    )

    depreciation_warning = fields.Text(
        'Aviso de Depreciación',
        compute='_compute_depreciation_warning',
        store=False
    )

    depreciation_alert_level = fields.Selection([
        ('none', 'Sin Alerta'),
        ('warning', 'Advertencia'),
        ('critical', 'Crítico'),
        ('completed', 'Completado')
    ], compute='_compute_depreciation_warning', store=False)
    
    transfer_ids = fields.One2many(
        'aft.transfer',
        'asset_id',
        string='Historial de Traslados',
        readonly=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('category_id.depreciation_rate', 'custom_depreciation_rate')
    def _compute_effective_depreciation_rate(self):
        """Calcula la tasa efectiva: personalizada o de categoría"""
        for asset in self:
            if asset.custom_depreciation_rate > 0:
                asset.effective_depreciation_rate = asset.custom_depreciation_rate
            elif asset.category_id:
                asset.effective_depreciation_rate = asset.category_id.depreciation_rate
            else:
                asset.effective_depreciation_rate = 0.0

    @api.depends('purchase_value', 'depreciation_line_ids.amount', 'depreciation_line_ids.state')
    def _compute_current_value(self):
        """Calcula el valor actual restando depreciaciones publicadas"""
        for asset in self:
            # ✅ SOLO DEPRECIACIONES PUBLICADAS HASTA FECHA ACTUAL
            total_depreciation = sum(
                line.amount for line in asset.depreciation_line_ids
                if line.state == 'Publicado' and line.date <= fields.Date.today()
            )
        
            # ✅ ASEGURAR QUE EL VALOR ACTUAL NO SEA NEGATIVO
            current_value = asset.purchase_value - total_depreciation
            asset.current_value = max(current_value, 0.0)
            
    def action_purchase(self):
        self.state = 'purchased'

    def action_activate(self):
        self.state = 'active'
        # ✅ GENERAR DEPRECIACIONES SOLO HASTA FECHA ACTUAL
        self._generate_depreciation_lines()

    def action_deactivate(self):
        self.state = 'inactive'
    def _generate_depreciation_lines(self):
        """Genera líneas de depreciación SOLO hasta la fecha actual"""
        for asset in self.filtered(lambda a: a.state == 'active'):
            # ✅ VERIFICAR QUE NO EXISTAN YA LÍNEAS
            existing_lines = self.env['aft.depreciation.line'].search([
                ('asset_id', '=', asset.id)
            ])
            if existing_lines:
                continue  # Ya tiene líneas, no generar duplicados
        
            annual_rate = asset.effective_depreciation_rate / 100
            monthly_rate = annual_rate / 12
            monthly_depreciation = asset.purchase_value * monthly_rate
        
            start_date = asset.purchase_date or fields.Date.today()
            current_date = fields.Date.today()
        
            # ✅ CONTROL DE DEPRECIACIÓN ACUMULADA
            total_depreciated = 0.0
        
            # ✅ GENERAR SOLO HASTA LA FECHA ACTUAL CON VALIDACIÓN DE TOPES
            date = start_date
            while date <= current_date:
                # Ir al final del mes
                next_month = date + relativedelta(months=1)
                end_of_month = next_month.replace(day=1) - relativedelta(days=1)
            
                # Si el final del mes es futuro, usar fecha actual
                dep_date = min(end_of_month, current_date)
            
                # ✅ CALCULAR MONTO SIN PASARSE DEL TOPE
                remaining_value = asset.purchase_value - total_depreciated
            
                # Si ya no queda nada por depreciar, salir del bucle
                if remaining_value <= 0.01:
                    break
            
                # El monto a depreciar es el menor entre:
                # - La depreciación mensual normal
                # - Lo que queda por depreciar
                depreciation_amount = min(monthly_depreciation, remaining_value)
            
                # Solo crear la línea si el monto es significativo
                if depreciation_amount > 0.01:
                    self.env['aft.depreciation.line'].create({
                        'asset_id': asset.id,
                        'date': dep_date,
                        'amount': depreciation_amount,
                        'state': 'No Publicado'
                    })
                
                    total_depreciated += depreciation_amount
            
                date = next_month
                if date > current_date or total_depreciated >= asset.purchase_value:
                    break
        
    @api.depends('purchase_value', 'depreciation_line_ids.amount', 'depreciation_line_ids.state', 'effective_depreciation_rate')
    def _compute_depreciation_info(self):
        """Calcula información detallada de depreciación"""
        for asset in self:
            # Total depreciado (solo líneas publicadas)
            total_depreciated = sum(
                line.amount for line in asset.depreciation_line_ids
                if line.state == 'Publicado'
            )
        
            asset.total_depreciated = total_depreciated
            asset.remaining_to_depreciate = max(asset.purchase_value - total_depreciated, 0.0)
        
            # Porcentaje depreciado
            if asset.purchase_value > 0:
                asset.depreciation_percentage = (total_depreciated / asset.purchase_value) * 100
            else:
                asset.depreciation_percentage = 0.0
                
        
    @api.depends('current_value', 'effective_depreciation_rate', 'purchase_value', 'depreciation_percentage')
    def _compute_depreciation_warning(self):
        """Genera avisos sobre el estado de depreciación"""
        for asset in self:
            # Calcular depreciación mensual
            if asset.effective_depreciation_rate > 0:
                monthly_depreciation = (asset.purchase_value * asset.effective_depreciation_rate / 100) / 12
            else:
                monthly_depreciation = 0
        
            # Determinar nivel de alerta y mensaje
            if asset.depreciation_percentage >= 100:
                asset.depreciation_alert_level = 'completed'
                asset.depreciation_warning = (
                    f"🔴 ACTIVO TOTALMENTE DEPRECIADO\n"
                    f"Este activo ha alcanzado el 100% de su depreciación.\n"
                    f"Valor actual: ${asset.current_value:,.2f}"
                )
            elif asset.depreciation_percentage >= 90:
                asset.depreciation_alert_level = 'critical'
                remaining_months = int((asset.remaining_to_depreciate / monthly_depreciation)) if monthly_depreciation > 0 else 0
                asset.depreciation_warning = (
                    f"🟠 DEPRECIACIÓN CRÍTICA ({asset.depreciation_percentage:.1f}%)\n"
                    f"Solo quedan ${asset.remaining_to_depreciate:,.2f} por depreciar.\n"
                    f"Tiempo estimado restante: {remaining_months} meses"
                )
            elif asset.current_value < monthly_depreciation and asset.current_value > 0:
                asset.depreciation_alert_level = 'warning'
                asset.depreciation_warning = (
                    f"⚠️ PRÓXIMO A COMPLETAR DEPRECIACIÓN\n"
                    f"El valor actual (${asset.current_value:,.2f}) es menor que\n"
                    f"la próxima depreciación mensual (${monthly_depreciation:,.2f}).\n"
                    f"En el próximo mes se completará la depreciación."
                )
            elif asset.depreciation_percentage >= 75:
                asset.depreciation_alert_level = 'warning'
                remaining_months = int((asset.remaining_to_depreciate / monthly_depreciation)) if monthly_depreciation > 0 else 0
                asset.depreciation_warning = (
                    f"🟡 DEPRECIACIÓN AVANZADA ({asset.depreciation_percentage:.1f}%)\n"
                    f"Quedan ${asset.remaining_to_depreciate:,.2f} por depreciar.\n"
                    f"Tiempo estimado restante: {remaining_months} meses"
                )
            else:
                asset.depreciation_alert_level = 'none'
                asset.depreciation_warning = ""
            

class AftDepreciationLine(models.Model):
    _name = 'aft.depreciation.line'
    _description = 'Línea de Depreciación'
    _order = 'date desc'
    
    asset_id = fields.Many2one('aft.asset', 'Activo', required=True, ondelete='cascade')
    date = fields.Date('Fecha', required=True, readonly=True)  # ✅ READONLY
    amount = fields.Monetary('Monto', required=True, readonly=True)  # ✅ READONLY
    state = fields.Selection([
        ('No Publicado', 'No Publicado'),
        ('Publicado', 'Publicado'),
    ], default='No Publicado', readonly=True)  # ✅ READONLY
    
    move_id = fields.Many2one('account.move', 'Asiento Contable', readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        related='asset_id.currency_id',
        readonly=True
    )

    # ✅ PREVENIR MODIFICACIÓN DE LÍNEAS PUBLICADAS
    @api.constrains('state', 'amount', 'date')
    def _check_no_modification_if_posted(self):
        """Impedir modificación de líneas publicadas"""
        for line in self:
            if line.state == 'Publicado':
                raise ValidationError(
                    f"No se puede modificar la línea de depreciación del {line.date} "
                    f"porque ya está publicada. Las depreciaciones publicadas son inmutables."
                )

    # ✅ PREVENIR ELIMINACIÓN DE LÍNEAS PUBLICADAS
    def unlink(self):
        for line in self:
            if line.state == 'Publicado':
                raise ValidationError(
                    f"No se puede eliminar la línea de depreciación del {line.date} "
                    f"porque ya está publicada."
                )
        return super().unlink()

    def action_post(self):
        """Publicar la depreciación y crear asiento contable"""
        for line in self:
            if line.state == 'Publicado':
                continue
            
        # ✅ SOLO PERMITIR PUBLICAR HASTA FECHA ACTUAL
        if line.date > fields.Date.today():
            raise UserError(
                f"No se puede publicar la depreciación del {line.date} "
                f"porque es una fecha futura. Solo se pueden publicar "
                f"depreciaciones hasta la fecha actual."
            )
            
        # ✅ VALIDAR QUE NO SE PASE DEL TOPE DE DEPRECIACIÓN
        total_depreciated = sum(
            dep_line.amount for dep_line in line.asset_id.depreciation_line_ids
            if dep_line.state == 'Publicado' and dep_line.id != line.id
        )
        
        new_total = total_depreciated + line.amount
        
        if new_total > line.asset_id.purchase_value:
            remaining = line.asset_id.purchase_value - total_depreciated
            raise UserError(
                f"No se puede publicar esta depreciación porque excedería el valor del activo.\n\n"
                f"• Valor de compra: ${line.asset_id.purchase_value:,.2f}\n"
                f"• Ya depreciado: ${total_depreciated:,.2f}\n"
                f"• Disponible para depreciar: ${remaining:,.2f}\n"
                f"• Monto a publicar: ${line.amount:,.2f}\n\n"
                f"Ajuste el monto a máximo ${remaining:,.2f}"
            )
            
        # ✅ BUSCAR DIARIO CON VALIDACIÓN
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
        ], limit=1)
        
        if not journal:
            raise UserError(
                "No se encontró un diario contable general.\n\n"
                "Cree un diario de tipo 'Misceláneo' en Contabilidad → Configuración → Diarios"
            )
            
        # Crear asiento contable
        account_move = self.env['account.move'].create({
            'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'date': line.date,
            'ref': f'Depreciación {line.asset_id.name} - {line.date}',
            'line_ids': [
                (0, 0, {
                    'name': f'Depreciación {line.asset_id.name}',
                    'account_id': line.asset_id.area_id.expense_account_id.id,
                    'debit': line.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': f'Depreciación Acumulada {line.asset_id.name}',
                    'account_id': line.asset_id.category_id.accumulated_depreciation_account_id.id,
                    'debit': 0.0,
                    'credit': line.amount,
                }),
            ]
        })
        
        # Confirmar el asiento
        account_move.action_post()
            
        line.write({
            'state': 'Publicado',
            'move_id': account_move.id
        })
        
        # ✅ MOSTRAR AVISO DESPUÉS DE PUBLICAR
        line.asset_id._compute_depreciation_warning()
        if line.asset_id.depreciation_alert_level in ['warning', 'critical', 'completed']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aviso de Depreciación',
                    'message': line.asset_id.depreciation_warning,
                    'type': 'warning' if line.asset_id.depreciation_alert_level == 'warning' else 'info',
                    'sticky': True,
                }
            }