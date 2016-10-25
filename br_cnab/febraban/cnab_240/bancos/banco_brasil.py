# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab_240 import Cnab240


class BancoBrasil240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import banco_brasil
        self.bank = banco_brasil

    def _prepare_header(self):
        vals = super(BancoBrasil240, self)._prepare_header()
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(BancoBrasil240, self)._prepare_segmento(line)

        nossonumero, digito = self.nosso_numero(
            line.nosso_numero)
        try:
            parcela = line.name.split('/')[1]
        except:
            parcela = line.name
        vals['codigo_convenio_banco'] = self.format_codigo_convenio_banco(line)
        vals['carteira_numero'] = int(line.payment_mode_id.boleto_carteira[:2])
        vals['nosso_numero'] = self.format_nosso_numero(
            nossonumero, digito, parcela,
            line.payment_mode_id.boleto_modalidade)
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

    def format_codigo_convenio_banco(self, line):
        num_convenio = line.payment_mode_id.bank_account_id.codigo_convenio
        carteira = line.payment_mode_id.boleto_carteira[:2]
        boleto = line.payment_mode_id.boleto_variacao.zfill(3)
        return "%s0014%s%s  " % (num_convenio, carteira, boleto)
