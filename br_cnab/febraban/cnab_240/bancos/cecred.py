# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab_240 import Cnab240


class Cecred240(Cnab240):

    def __init__(self):
        super(Cecred240, self).__init__()
        from cnab240.bancos import cecred
        self.bank = cecred

    def _prepare_header(self):
        vals = super(Cecred240, self)._prepare_header()
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(Cecred240, self)._prepare_segmento(line)
        vals['carteira_numero'] = int(line.invoice_id.payment_mode_id.boleto_carteira)
        vals['nosso_numero'] = '00000'#line.move_line_id.transaction_ref
        vals['prazo_baixa'] = ''
        vals['especie_titulo'] = 2  # Duplicata Mercantil
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals
