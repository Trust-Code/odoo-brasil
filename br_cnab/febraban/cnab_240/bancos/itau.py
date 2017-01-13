# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from ..cnab_240 import Cnab240


class Itau240(Cnab240):
    """

    """

    def __init__(self):
        """

        :return:
        """
        super(Cnab240, self).__init__()
        from cnab240.bancos import itau
        self.bank = itau

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        vals = super(Itau240, self)._prepare_header()
        return vals

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Itau240, self)._prepare_segmento(line)
        dv = self.dv_nosso_numero(
            line.payment_mode_id.bank_account_id.bra_number,
            line.payment_mode_id.bank_account_id.acc_number,
            line.payment_mode_id.boleto_carteira,
            line.nosso_numero
        )
        vals['nosso_numero_dv'] = dv
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
