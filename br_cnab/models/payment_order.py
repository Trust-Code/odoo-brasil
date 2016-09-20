# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    @api.multi
    def gerar_cnab(self):
        raise UserError('Oi')
