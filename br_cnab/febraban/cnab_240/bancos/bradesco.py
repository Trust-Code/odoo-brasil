# -*- coding: utf-8 -*-
# © 2015 Luis Felipe Mileo
#        Fernando Marcato Rodrigues
#        Daniel Sadamo Hirayama
#        KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from ..cnab_240 import Cnab240
import re
import string
from decimal import Decimal
from odoo.exceptions import UserError


class Bradesco240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import bradesco
        self.bank = bradesco

    def _prepare_header(self):
        vals = super(Bradesco240, self)._prepare_header()

        cod_convenio = self.order.src_bank_account_id.codigo_convenio

        vals['servico_servico'] = 1
        vals['cedente_convenio'] = '{:>020s}'.format(cod_convenio)
        vals['controlecob_numero'] = self.order.id
        vals['controlecob_data_gravacao'] = self.data_hoje()
        vals['nome_do_banco'] = 'BANCO BRADESCO S.A'
        return vals

    def _prepare_segmento(self, line):
        vals = super(Bradesco240, self)._prepare_segmento(line)
        if vals['prazo_protesto'] < 3:
            vals['prazo_protesto'] = 3
        vals['codigo_moeda'] = 9
        vals['prazo_baixa'] = str(vals['prazo_baixa'])
        vals['desconto1_percentual'] = Decimal('0.00')
        vals['valor_iof'] = Decimal('0.00')
        # vals['cobrancasimples_valor_titulos'] = Decimal('02.00')
        vals['identificacao_titulo_banco'] = self.get_identificacao_titulo(
            line)
        vals['cedente_conta_dv'] = str(vals['cedente_conta_dv'])
        vals['cedente_agencia_dv'] = str(vals['cedente_agencia_dv'])
        vals['cedente_dv_ag_cc'] = str(vals['cedente_dv_ag_cc'])
        vals['cobranca_carteira'] = 1
        vals['cobranca_cadastramento'] = 1
        vals['cobranca_documentoTipo'] = 1
        vals['cobranca_distribuicaoBloqueto'] = 2
        vals['juros_cod_mora'] = 2
        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos entre
    # CEF e Itau
    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito

    def get_identificacao_titulo(self, line):
        carteira = line.payment_mode_id.boleto_carteira
        return "%s%s%s%s" % (
            str(carteira).zfill(3),
            '0'.zfill(5),
            str(line.nosso_numero).zfill(11),
            self.dv_nosso_numero(carteira, line.nosso_numero)
        )

    def dv_nosso_numero(self, carteira, nosso_numero):
        resto2 = self.modulo11(carteira + nosso_numero.zfill(11), 7, 1)
        digito = 11 - resto2
        if digito == 10:
            dv = 'P'
        elif digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    def modulo11(self, num, base=9, r=0):
        if not isinstance(num, str):
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

    def _hook_validation(self):
        if not self.order.src_bank_account_id.codigo_convenio:
            raise UserError(
                'Código de convênio não pode estar vazio!')
