

import base64
from odoo import api, fields, models
from odoo.addons.br_payment_cnab.other.cnab240 import Cnab_240


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    @api.multi
    def gerar_cnab(self):

        cnab = Cnab_240(self)
        cnab.create_cnab(self.line_ids)
        self.cnab_file = base64.b64encode(cnab.write_cnab())
        self.name = 'cnab_pagamento.rem'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.payment.mode'))