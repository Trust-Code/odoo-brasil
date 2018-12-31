# -*- coding: utf-8 -*-
# © 2015 Luis Felipe Mileo
#        Fernando Marcato Rodrigues
#        Daniel Sadamo Hirayama
#        KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from decimal import Decimal
from ..cnab_240 import Cnab240

_logger = logging.getLogger(__name__)

try:
    from pyboleto.data import BoletoData
except ImportError:
    _logger.error('Cannot import pyboleto', exc_info=True)


class Cef240(Cnab240):
    def __init__(self):
        super(Cnab240, self).__init__()
        from cnab240.bancos import cef
        self.bank = cef

    def _prepare_header(self):
        vals = super(Cef240, self)._prepare_header()

        vals['cedente_convenio'] = int(vals['cedente_convenio'])
        vals['cedente_beneficiario'] = vals['cedente_convenio']

        vals['cedente_codigo_codCedente'] = 6088
        vals['nome_do_banco'] = u'CAIXA ECONOMICA FEDERAL'
        if self.order.payment_mode_id.l10n_br_environment == 'test':
            vals['reservado_cedente_campo23'] = 'REMESSA TESTE'
        else:
            vals['reservado_cedente_campo23'] = 'REMESSA-PRODUCAO'

        vals['controlecob_numero'] = self.order.file_number
        vals['controlecob_data_gravacao'] = self.data_hoje()
        return vals

    def _prepare_segmento(self, line):
        vals = super(Cef240, self)._prepare_segmento(line)

        vals['cedente_convenio'] = int(vals['cedente_convenio'])
        vals['cedente_beneficiario'] = vals['cedente_convenio']
        vals['carteira_numero'] = int(line.payment_mode_id.boleto_modalidade)

        # Segue a mesma regra de geração do dv do boleto
        # Carteira 1 + fixo 4 + 15 posições nosso número - aplica modulo 11
        numero = "%1s4%15s" % (int(line.payment_mode_id.boleto_carteira),
                               line.nosso_numero.zfill(15))
        nosso_numero = "%s%s" % (line.nosso_numero,
                                 BoletoData.modulo11(numero))
        vals['nosso_numero'] = int(nosso_numero)

        vals['identificacao_titulo'] = vals['numero_documento']

        vals['cedente_conta_dv'] = str(vals['cedente_conta_dv'])
        vals['cedente_codigo_codCedente'] = 6088
        vals['data_credito_hd_lote'] = 15052015

        vals['desconto1_cod'] = 3
        vals['desconto1_data'] = 0
        vals['desconto1_percentual'] = Decimal('0.00')
        vals['valor_iof'] = Decimal('0.00')

        return vals
