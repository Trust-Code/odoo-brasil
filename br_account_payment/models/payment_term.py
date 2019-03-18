# -*- coding: utf-8 -*-
# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountPaymentline(models.Model):
    _inherit = 'account.payment.term.line'

    default_payment_mode_id = fields.Many2one(
        string="Default Payment Mode",
        comodel_name="l10n_br.payment.mode",
        ondelete="set null",
        help="Default payment mode for invoices")
