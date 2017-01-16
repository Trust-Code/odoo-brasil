# -*- coding: utf-8 -*-
# © 2015 Luis Felipe Mileo
#        Fernando Marcato Rodrigues
#        Daniel Sadamo Hirayama
#        KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from ..cnab_240 import Cnab240


class Itau240(Cnab240):

    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import itau
        self.bank = itau

    def _prepare_header(self):
        vals = super(Itau240, self)._prepare_header()
        vals['cedente_conta_dv'] = int(vals['cedente_conta_dv'])
        vals['cedente_agencia_dv'] = int(vals['cedente_agencia_dv'])
        vals['cedente_dv_ag_cc'] = int(vals['cedente_dv_ag_cc'])
        return vals

    def _prepare_segmento(self, line):
        vals = super(Itau240, self)._prepare_segmento(line)
        dv = self.dv_nosso_numero(
            line.payment_mode_id.bank_account_id.bra_number,
            line.payment_mode_id.bank_account_id.acc_number,
            line.payment_mode_id.boleto_carteira,
            line.nosso_numero
        )
        vals['nosso_numero'] = int(line.nosso_numero)
        vals['nosso_numero_dv'] = dv
        vals['carteira_numero'] = int(
            self.order.payment_mode_id.boleto_carteira)
        vals['cedente_conta_dv'] = int(vals['cedente_conta_dv'])
        vals['cedente_agencia_dv'] = int(vals['cedente_agencia_dv'])
        vals['cedente_dv_ag_cc'] = int(vals['cedente_dv_ag_cc'])
        return vals

    def dv_nosso_numero(self, agencia, conta, carteira, nosso_numero):
        composto = "%4s%5s%3s%8s" % (agencia.zfill(4), conta.zfill(5),
                                     carteira.zfill(3), nosso_numero.zfill(8))
        return self.modulo10(composto)

    @staticmethod
    def modulo10(num):
        if not isinstance(num, basestring):
            raise TypeError
        soma = 0
        peso = 2
        for c in reversed(num):
            parcial = int(c) * peso
            if parcial > 9:
                s = str(parcial)
                parcial = int(s[0]) + int(s[1])
            soma += parcial
            if peso == 2:
                peso = 1
            else:
                peso = 2

        resto10 = soma % 10
        if resto10 == 0:
            modulo10 = 0
        else:
            modulo10 = 10 - resto10

        return modulo10
