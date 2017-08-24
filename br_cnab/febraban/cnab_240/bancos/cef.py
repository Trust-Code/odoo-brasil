# -*- coding: utf-8 -*-
# © 2015 Luis Felipe Mileo
#        Fernando Marcato Rodrigues
#        Daniel Sadamo Hirayama
#        KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from decimal import Decimal
from ..cnab_240 import Cnab240


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
        # Não pode pegar comentário da payment_line.
        vals['reservado_cedente_campo23'] = u'REMESSA TESTE'
        # reservado_banco_campo22 não é required. Código atualizado na
        # biblioteca cnab240
        vals['data_credito_hd_lote'] = 15052015

        return vals

    def _prepare_segmento(self, line):
        vals = super(Cef240, self)._prepare_segmento(line)

        vals['cedente_convenio'] = int(vals['cedente_convenio'])
        vals['cedente_beneficiario'] = vals['cedente_convenio']
        vals['carteira_numero'] = int(line.payment_mode_id.boleto_modalidade)

        # Informar o Número do Documento - Seu Número (mesmo das posições
        # 63-73 do Segmento P)
        vals['nosso_numero'] = "%s%s" % (
            line.payment_mode_id.boleto_modalidade.zfill(2),
            line.nosso_numero.zfill(10))

        vals['identificacao_titulo'] = str(vals['numero_documento'])
        # TODO: campo 27.3P CEF. Código do juros de mora
        vals['juros_cod_mora'] = 3
        vals['prazo_baixa'] = str(vals['prazo_baixa'])

        # Precisam estar preenchidos
        # Header lote
        # vals['servico_operacao'] = u'R'
        # vals['servico_servico'] = 1
        vals['cedente_conta_dv'] = str(vals['cedente_conta_dv'])
        vals['cedente_codigo_codCedente'] = 6088
        vals['data_credito_hd_lote'] = 15052015

        vals['desconto1_cod'] = 3
        vals['desconto1_data'] = 0
        vals['desconto1_percentual'] = Decimal('0.00')
        vals['valor_iof'] = Decimal('0.00')

        return vals
