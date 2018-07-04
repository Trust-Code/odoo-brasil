# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from ..cnab_240 import Cnab240
from decimal import Decimal
from odoo.exceptions import UserError
from odoo import fields


class Sicredi240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import sicredi
        self.bank = sicredi

    def _prepare_header(self):
        vals = super(Sicredi240, self)._prepare_header()
        vals['cedente_agencia_dv'] = ''
        conta_dv = vals['cedente_conta_dv']
        vals['cedente_conta_dv'] = str(conta_dv)
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(Sicredi240, self)._prepare_segmento(line)
        if not line.payment_mode_id.bank_account_id.codigo_convenio or \
           not line.payment_mode_id.bank_account_id.bra_number:
            raise UserError(
                u'Código do beneficiario ou número da agência em branco')
        digito = self.dv_nosso_numero(
            line.payment_mode_id.bank_account_id.bra_number,
            re.sub('[^0-9]', '',
                   line.payment_mode_id.bank_account_id.codigo_convenio),
            line.nosso_numero)
        vals['nosso_numero'] = self.format_nosso_numero(
            line.nosso_numero, digito)
        vals['nosso_numero_dv'] = int(digito)
        vals['prazo_baixa'] = '0'
        vals['codigo_multa'] = int(vals['codigo_multa'])
        vals['cedente_conta_dv'] = str(vals['cedente_conta_dv'])
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        if line.payment_mode_id.boleto_especie == '01':
            especie = '03'
        elif line.payment_mode_id.boleto_especie == '02':
            especie = '12'
        elif line.payment_mode_id.boleto_especie == '03':
            especie = '16'
        elif line.payment_mode_id.boleto_especie == '04':
            especie = '99'
        elif line.payment_mode_id.boleto_especie == '05':
            especie = '17'
        elif line.payment_mode_id.boleto_especie == '06':
            especie = '99'
        elif line.payment_mode_id.boleto_especie == '07':
            especie = '99'
        elif line.payment_mode_id.boleto_especie == '08':
            especie = '05'
        elif line.payment_mode_id.boleto_especie == '09':
            especie = '07'
        elif line.payment_mode_id.boleto_especie == '13':
            especie = '19'
        elif line.payment_mode_id.boleto_especie == '15':
            especie = '99'
        elif line.payment_mode_id.boleto_especie == '16':
            especie = '99'
        elif line.payment_mode_id.boleto_especie == '17':
            especie = '99'
        else:
            especie = '99'
        vals['especie_titulo'] = especie
        vals['codigo_multa'] = '1'  # 1 - Valor por dia
        vlr_doc = line.debit
        juros_dia = vlr_doc * (
            self.order.payment_mode_id.late_payment_interest / 100 / 30)
        vals['juros_mora_taxa'] = Decimal(str(juros_dia)).quantize(
            Decimal('1.00'))
        vals['codigo_baixa'] = 1
        vals['prazo_baixa'] = '060'  # Usar sempre "060" - Para baixa/devolução
        return vals

    def dv_nosso_numero(self, agencia, codigo_beneficiario, nosso_numero):
        n_num = "%s2%s" % (self.format_ano(), nosso_numero.zfill(5))
        composto = "%s05%s%s" % (
            agencia.zfill(4), codigo_beneficiario.zfill(5), n_num.zfill(8))
        constante = '4329876543298765432'
        soma = 0
        for i in range(19):
            soma += int(composto[i]) * int(constante[i])
        resto = soma % 11
        return '0' if (resto == 1 or resto == 0) else 11 - resto

    def format_nosso_numero(self, nosso_numero, dv):
        return "%s2%s%s    " % (self.format_ano(), nosso_numero.zfill(5), dv)

    def format_ano(self):
        data = fields.Datetime.now()
        data = data.split('-')
        ano = data[0]
        return ano[2:4]
