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
        vals['codigo_convenio_banco'] = self.format_codigo_convenio_banco(
            self.order.payment_mode_id)
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(BancoBrasil240, self)._prepare_segmento(line)
        vals['numero_documento'] = (u"%s/%s" % (
            line.move_id.name, line.name))[-15:]
        vals['codigo_convenio_banco'] = self.format_codigo_convenio_banco(
            line.payment_mode_id)
        vals['carteira_numero'] = int(line.payment_mode_id.boleto_carteira[:2])
        vals['nosso_numero'] = self.format_nosso_numero(
            line.payment_mode_id.boleto_cnab_code, line.nosso_numero)
        vals['prazo_baixa'] = '0'
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def nosso_numero(self, format):
        digito = format[-1:]
        nosso_numero = format[2:-2]
        return nosso_numero, digito

    def format_nosso_numero(self, convenio, nosso_numero):
        return "%s%s" % (convenio.zfill(7), nosso_numero.ljust(10))

    def format_codigo_convenio_banco(self, payment_mode):
        num_convenio = payment_mode.boleto_cnab_code
        carteira = payment_mode.boleto_carteira[:2]
        boleto = payment_mode.boleto_variacao.zfill(3)
        return "%s0014%s%s  " % (num_convenio, carteira, boleto)
