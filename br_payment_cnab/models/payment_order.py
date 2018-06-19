

import base64
from odoo import api, fields, models
from odoo.addons.br_payment_cnab.other.cnab240 import Cnab_240

class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    @api.multi
    def gerar_cnab(self):

        cnab = Cnab_240(self)
        cnab.create_cnab()

        for line in cnab.ordenate_lines(self.line_ids):
            cnab.create_detail(line.other_payment.entry_mode, line)

        self.cnab_file = base64.b64encode(cnab.write_cnab())
        self.name = 'cnab_pagamento.rem'
