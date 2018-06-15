

import base64
from odoo import api, fields, models
from odoo.addons.br_payment_cnab.other.cnab240 import Cnab_240

class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    @api.multi
    def gerar_cnab(self):

        cnab = Cnab_240()

        # # Inicializa o cabecalho
        create_other = cnab.createCnab(self)

        for linha in self.line_ids:
            cnab.add_order_line(linha)

        #texto = cnab.generate_cnab_text()
            linha.other_payment.operation_code

        self.cnab_file = base64.b64encode(create_other.encode())
        self.name = 'cnab_pagamento.rem'
