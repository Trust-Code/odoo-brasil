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
        vals['carteira_numero'] = int(
            line.payment_mode_id.boleto_carteira)
        vals['nosso_numero'] = "%s%s%s   " % (
            line.payment_mode_id.bank_account_id.acc_number.zfill(7),
            line.payment_mode_id.bank_account_id.acc_number_dig,
            line.nosso_numero.zfill(9))
        vals['prazo_baixa'] = ''
        vals['especie_titulo'] = 2  # Duplicata Mercantil
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals
