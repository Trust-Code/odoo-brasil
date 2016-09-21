# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    payment_type_id = fields.Many2one('payment.type',
                                      string='Tipo de Pagamento')
