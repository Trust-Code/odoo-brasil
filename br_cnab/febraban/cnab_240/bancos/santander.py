# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import string
from ..cnab_240 import Cnab240


class Santander240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import santander
        self.bank = santander

    def _prepare_header(self):
        vals = super(Santander240, self)._prepare_header()
        vals['cedente_dv_ag_cc'] = int(vals['cedente_dv_ag_cc'])
        vals['cedente_agencia_dv'] = int(vals['cedente_agencia_dv'])
        vals['codigo_transmissao'] = \
            int(self.order.payment_mode_id.boleto_cnab_code)
        return vals

    def _prepare_segmento(self, line):
        vals = super(Santander240, self)._prepare_segmento(line)

        carteira, nosso_numero, digito = self.nosso_numero(line.nosso_numero)

        vals['cedente_dv_ag_cc'] = int(vals['cedente_dv_ag_cc'])
        vals['cedente_agencia_conta_dv'] = int(vals['cedente_dv_ag_cc'])
        vals['carteira_numero'] = int(carteira)
        vals['nosso_numero'] = int(line.nosso_numero)
        vals['nosso_numero_dv'] = int(digito)
        dig_ag = int(vals['cedente_agencia_dv'])
        vals['cedente_agencia_dv'] = dig_ag
        vals['conta_cobranca'] = vals['cedente_conta']
        vals['conta_cobranca_dv'] = int(vals['cedente_conta_dv'])
        vals['forma_cadastramento'] = 1
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
        vals['juros_mora_data'] = 0

        return vals

    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito
