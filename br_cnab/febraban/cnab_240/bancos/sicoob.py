# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
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
        digito = self.dv_nosso_numero(
            line.src_bank_account_id.bra_number,
            re.sub('[^0-9]', '', line.src_bank_account_id.codigo_convenio),
            line.nosso_numero)
        vals['carteira_numero'] = int(line.payment_mode_id.boleto_carteira)
        vals['nosso_numero'] = self.format_nosso_numero(
            line.nosso_numero, digito, '01', line.payment_mode_id.
            boleto_modalidade)
        vals['nosso_numero_dv'] = int(digito)
        vals['prazo_baixa'] = ''
        vals['codigo_baixa'] = 0
        vals['codigo_multa'] = int(vals['codigo_multa'])
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def dv_nosso_numero(self, agencia, codigo_beneficiario, nosso_numero):
        composto = "%4s%10s%7s" % (agencia.zfill(4),
                                   codigo_beneficiario.zfill(10),
                                   nosso_numero.zfill(7))
        constante = '319731973197319731973'
        soma = 0
        for i in range(21):
            soma += int(composto[i]) * int(constante[i])
        resto = soma % 11
        return '0' if (resto == 1 or resto == 0) else 11 - resto

    def format_nosso_numero(self, nosso_numero, digito, parcela, modalidade):
        return "%s%s%s%s4     " % (nosso_numero.zfill(9), digito,
                                   parcela.zfill(2), modalidade)
