# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab_240 import Cnab240
from decimal import Decimal


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
        vals['codigo_convenio_banco'] = self.format_codigo_convenio_banco(
            line.payment_mode_id)
        vals['carteira_numero'] = int(line.payment_mode_id.boleto_carteira[:2])
        vals['nosso_numero'] = self.format_nosso_numero(
            line.payment_mode_id.boleto_cnab_code, line.nosso_numero)
        vals['codigo_baixa'] = 0
        vals['prazo_baixa'] = ''
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        # Codigo juro mora:
        # 1 - Valor ao dia
        # 2 - Taxa Mensal
        # 3 - Isento (deve ser cadastrado no banco)
        vals['juros_cod_mora'] = int(
            line.payment_mode_id.late_payment_interest_type)

        if vals['juros_cod_mora'] in [3]:
            vals['juros_mora_taxa'] = Decimal(str(0.00)).quantize(
                Decimal('1.00'))
        else:
            vals['juros_mora_taxa'] = Decimal(
                str(self.order.payment_mode_id.late_payment_interest)
                ).quantize(Decimal('1.00'))

        # Banco do Brasil aceita apenas código de protesto 1, 2, ou
        # 3 (dias corridos, dias úteis ou não protestar, respectivamente)
        if vals['codigo_protesto'] not in [1, 2, 3]:
            vals['codigo_protesto'] = 3
        vals['cobranca_emissaoBloqueto'] = 2

        especie_titulo_banco = {
            '01': 2,
            '02': 12,
            '03': 16,
            '04': 21,
            '05': 17,
            '06': 99,
            '07': 99,
            '08': 4,
            '09': 7,
            '13': 19,
            '15': 24,
            '16': 30,
            '17': 99,
            '99': 99,
            }
        especie_titulo = especie_titulo_banco[
            line.payment_mode_id.boleto_especie]
        vals['especie_titulo'] = especie_titulo
        vals['multa_codigo'] = vals['codigo_multa']
        vals['multa_data'] = self.format_date(line.date_maturity)
        vals['multa_percentual'] = Decimal(
            str(self.order.payment_mode_id.late_payment_fee)).quantize(
                Decimal('1.00'))
        return vals

    def nosso_numero(self, format):
        digito = format[-1:]
        nosso_numero = format[2:-2]
        return nosso_numero, digito

    def format_nosso_numero(self, convenio, nosso_numero):
        return "%s%s" % (convenio.zfill(7), nosso_numero.zfill(10))

    def format_codigo_convenio_banco(self, payment_mode):
        num_convenio = payment_mode.boleto_cnab_code
        carteira = payment_mode.boleto_carteira[:2]
        boleto = payment_mode.boleto_variacao.zfill(3)
        return "00%s0014%s%s  " % (num_convenio, carteira, boleto)
