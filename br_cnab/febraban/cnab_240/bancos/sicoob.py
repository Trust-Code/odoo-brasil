# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab_240 import Cnab240


class Sicoob240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import sicoob
        self.bank = sicoob

    def _prepare_header(self):
        vals = super(Sicoob240, self)._prepare_header()
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(Sicoob240, self)._prepare_segmento(line)

        nossonumero, digito = self.nosso_numero(
            line.move_line_id.transaction_ref)

        parcela = line.move_line_id.name.split('/')[1]
        vals['carteira_numero'] = int(line.order_id.mode.boleto_carteira)
        vals['nosso_numero'] = self.format_nosso_numero(
            nossonumero, digito, parcela, line.order_id.mode.boleto_modalidade)
        vals['nosso_numero_dv'] = int(digito)
        vals['prazo_baixa'] = '0'
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def nosso_numero(self, format):
        digito = format[-1:]
        nosso_numero = format[2:-2]
        return nosso_numero, digito

    def format_nosso_numero(self, nosso_numero, digito, parcela, modalidade):
        return "%s%s%s%s4     " % (nosso_numero.zfill(9), digito,
                                   parcela.zfill(2), modalidade)
