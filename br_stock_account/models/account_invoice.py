# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids
        self.amount_freight = sum(l.freight_value for l in lines)

    amount_freight = fields.Float(
        string='Valor do Frete', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    carrier_name = fields.Char('Transportadora', size=32)
    vehicle_plate = fields.Char('Placa do Veiculo', size=7)
    vehicle_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    vehicle_city_id = fields.Many2one(
        'res.state.city',
        'Municipio',
        domain="[('state_id', '=', vehicle_state_id)]")

    weight = fields.Float(
        string='Gross weight', states={'draft': [('readonly', False)]},
        help="The gross weight in Kg.", readonly=True)
    weight_net = fields.Float(
        'Net weight', help="The net weight in Kg.",
        readonly=True, states={'draft': [('readonly', False)]})
    number_of_packages = fields.Integer(
        'Volume', readonly=True, states={'draft': [('readonly', False)]})
    kind_of_packages = fields.Char(
        'Espécie', size=60, readonly=True, states={
            'draft': [
                ('readonly', False)]})
    brand_of_packages = fields.Char(
        'Brand', size=60, readonly=True, states={
            'draft': [
                ('readonly', False)]})
    notation_of_packages = fields.Char(
        'Numeração', size=60, readonly=True, states={
            'draft': [
                ('readonly', False)]})

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    freight_value = fields.Float(
        'Frete', digits=dp.get_precision('Account'), default=0.00)
