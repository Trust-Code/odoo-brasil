# -*- coding: utf-8 -*-
# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp


class InvoicePaymentLines(models.Model):
    _name = 'invoice.payment.lines'
    _description = 'Invoice Payment Note Lines'

    name = fields.Char(string="Name")
    invoice_id = fields.Many2one(
        string="Invoice",
        comodel_name="account.invoice")
    days = fields.Integer(string="Days", required="1")
    date_previews = fields.Date(
        string="Previews Date",
        compute="_compute_date_previews")
    amount = fields.Float(
        string="Value",
        digits=dp.get_precision('Product Price'))
    payment_term_line_id = fields.Many2one(
        string="Payment Term Line",
        comodel_name="account.payment.term.line")
    payment_mode_id = fields.Many2one(
        string="Payment Mode",
        required="1",
        comodel_name="l10n_br.payment.mode",
        ondelete="set null",
        help="Payment mode related with this quote")

    @api.depends('days')
    def _compute_date_previews(self):
        for s in self:
            s.date_previews = self.get_date_previews(s.days)

    def get_date_previews(self, days=0):
        date_previews = datetime.today() + relativedelta(days=days)
        return date_previews.strftime('%Y-%m-%d')
