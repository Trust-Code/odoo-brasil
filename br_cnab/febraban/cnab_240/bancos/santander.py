# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab_240 import Cnab240
from decimal import Decimal


class Santander240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import santander
        self.bank = santander

    def _prepare_header(self):
        vals = super(Santander240, self)._prepare_header()
        vals['cedente_agencia_dv'] = 0  # Não obrigatório
        vals['codigo_transmissao'] = self.codigo_transmissao()
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(Santander240, self)._prepare_segmento(line)

        nosso_numero = self.nosso_numero(line.nosso_numero)
        vals['nosso_numero'] = nosso_numero
        vals['cedente_agencia_dv'] = 0  # Não obrigatório
        vals['cedente_conta_dv'] = int(vals['cedente_conta_dv'])
        vals['conta_cobranca'] = vals['cedente_conta']
        vals['conta_cobranca_dv'] = int(vals['cedente_conta_dv'])
        vals['forma_cadastramento'] = 1
        vals['codigo_multa'] = int(vals['codigo_multa'])
        vals['codigo_juros'] = int(vals['codigo_juros'])
        vals['juros_mora_taxa'] = vals['juros_mora_taxa'] * Decimal('1000')
        # Data da multa fica zerado, dai ele considera data de vencimento
        vals['data_multa'] = 0
        # tipo documento : 1- Tradicional , 2- Escritural
        vals['tipo_documento'] = 1
        especie = 2
        if vals['especie_titulo'] == '01':
            especie = 2
        elif vals['especie_titulo'] == '02':
            especie = 12
        elif vals['especie_titulo'] == '08':
            especie = 4
        vals['especie_titulo'] = especie

        return vals

    def codigo_transmissao(self):
        return int("%s%s" % (
            self.order.payment_mode_id.bank_account_id.bra_number,
            self.order.payment_mode_id.boleto_cnab_code.zfill(11)))

    def nosso_numero(self, nosso_numero_sem_dv):
        digito = self.modulo11(nosso_numero_sem_dv)
        return int("%s%s" % (nosso_numero_sem_dv, digito))

    @staticmethod
    def modulo11(num, base=9, r=0):
        if not isinstance(num, basestring):
            raise TypeError
        soma = 0
        fator = 2
        for c in reversed(num):
            soma += int(c) * fator
            if fator == base:
                fator = 1
            fator += 1
        if r == 0:
            soma = soma * 10
            digito = soma % 11
            if digito == 10:
                digito = 0
            return digito
        if r == 1:
            resto = soma % 11
            return resto
