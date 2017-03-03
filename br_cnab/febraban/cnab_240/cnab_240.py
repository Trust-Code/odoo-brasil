# -*- coding: utf-8 -*-
# © 2015 Luis Felipe Mileo
#        Fernando Marcato Rodrigues
#        Daniel Sadamo Hirayama
#        KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..cnab import Cnab
from decimal import Decimal
import datetime
import re
import string
import unicodedata
import time
import logging

_logger = logging.getLogger(__name__)

try:
    from cnab240.tipos import Arquivo
except ImportError:
    _logger.debug('Cannot import cnab240')


class Cnab240(Cnab):
    """

    """

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        if bank == '237':
            from .bancos.bradesco import Bradesco240
            return Bradesco240
        elif bank == '756':
            from .bancos.sicoob import Sicoob240
            return Sicoob240
        elif bank == '001':
            from .bancos.banco_brasil import BancoBrasil240
            return BancoBrasil240
        elif bank == '0851':
            from .bancos.cecred import Cecred240
            return Cecred240
        elif bank == '341':
            from .bancos.itau import Itau240
            return Itau240
        elif bank == '033':
            from .bancos.santander import Santander240
            return Santander240
        else:
            return Cnab240

    @property
    def inscricao_tipo(self):
        if self.order.payment_mode_id.bank_account_id.partner_id.is_company:
            return 2
        else:
            return 1

    def _prepare_header(self):
        """

        :param:
        :return:
        """
        cnpj_cpf = re.sub('[^0-9]', '',
                          self.order.payment_mode_id.company_id.cnpj_cpf)
        cedente_conta_dv = self.order.payment_mode_id.bank_account_id.\
            acc_number_dig
        cedente_conta_dv = str(cedente_conta_dv)
        return {
            'controle_banco': int(self.order.payment_mode_id.
                                  bank_account_id.bank_bic),
            'arquivo_data_de_geracao': self.data_hoje(),
            'arquivo_hora_de_geracao': self.hora_agora(),
            'arquivo_sequencia': self.order.file_number,
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cedente_inscricao_numero': int(cnpj_cpf),
            'cedente_agencia': int(
                self.order.payment_mode_id.bank_account_id.bra_number),
            'cedente_conta': int(self.order.payment_mode_id.bank_account_id.
                                 acc_number),
            'cedente_conta_dv': cedente_conta_dv,
            'cedente_convenio': self.order.payment_mode_id.bank_account_id.
            codigo_convenio,
            'cedente_agencia_dv': self.order.payment_mode_id.
            bank_account_id.bra_number_dig,
            'cedente_nome': self.order.user_id.company_id.legal_name,
            # DV ag e conta
            'cedente_dv_ag_cc': (self.order.payment_mode_id.
                                 bank_account_id.bra_number_dig),
            'arquivo_codigo': 1,  # Remessa/Retorno
            'servico_operacao': u'R',
            'nome_banco': unicode(self.order.payment_mode_id.bank_account_id.
                                  bank_name)
        }

    def get_file_numeration(self):
        numero = False  # self.order.get_next_number()
        if not numero:
            numero = 1
        return numero

    def format_date(self, srt_date):
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%d%m%Y'))

    def nosso_numero(self, format):
        pass

    def cep(self, format):
        sulfixo = format[-3:]
        prefixo = format[:5]
        return prefixo, sulfixo

    def sacado_inscricao_tipo(self, partner_id):
        # TODO: Implementar codigo para PIS/PASEP
        if partner_id.is_company:
            return 2
        else:
            return 1

    def rmchar(self, format):
        return re.sub('[%s]' % re.escape(string.punctuation), '',
                      format or '')

    def _prepare_segmento(self, line):
        """
        :param line:
        :return:
        """
        prefixo, sulfixo = self.cep(line.partner_id.zip)

        # if not self.order.payment_mode_id.boleto_aceite == 'S':
        #    aceite = u'A'

        # Código agencia do cedente
        # cedente_agencia = cedente_agencia

        # Dígito verificador da agência do cedente
        # cedente_agencia_conta_dv = cedente_agencia_dv

        # Código da conta corrente do cedente
        # cedente_conta = cedente_conta

        # Dígito verificador da conta corrente do cedente
        # cedente_conta_dv = cedente_conta_dv

        # Dígito verificador de agencia e conta
        # Era cedente_agencia_conta_dv agora é cedente_dv_ag_cc

        return {
            'controle_banco': int(self.order.payment_mode_id.bank_account_id.
                                  bank_bic),
            'cedente_agencia': int(self.order.payment_mode_id.bank_account_id.
                                   bra_number),
            'cedente_conta': int(self.order.payment_mode_id.bank_account_id.
                                 acc_number),
            'cedente_conta_dv': self.order.payment_mode_id.bank_account_id.
            acc_number_dig,
            'cedente_agencia_dv': self.order.payment_mode_id.bank_account_id.
            bra_number_dig,
            'cedente_nome':
            self.order.payment_mode_id.bank_account_id.partner_id.legal_name,
            # DV ag e cc
            'cedente_dv_ag_cc': (self.order.payment_mode_id.bank_account_id.
                                 bra_number_dig),
            'identificacao_titulo': u'0000000',  # TODO
            'identificacao_titulo_banco': u'0000000',  # TODO
            'identificacao_titulo_empresa': (' ' * 25),
            'numero_documento': "%s/%s" % (line.move_id.name, line.name),
            'vencimento_titulo': self.format_date(
                line.date_maturity),
            'valor_titulo': Decimal(str(line.debit)).quantize(
                Decimal('1.00')),
            # TODO: Código adotado para identificar o título de cobrança.
            # 8 é Nota de cŕedito comercial
            'especie_titulo': int(self.order.payment_mode_id.boleto_especie),
            'aceite_titulo': self.order.payment_mode_id.boleto_aceite,
            'data_emissao_titulo': self.format_date(
                line.date),
            # Taxa de juros do Odoo padrão mensal: 2. Campo 27.3P
            # CEF/FEBRABAN e Itaú não tem.
            'codigo_juros': 2,
            'juros_mora_data': self.format_date(
                line.date_maturity),
            'juros_mora_taxa':  Decimal(
                str(self.order.payment_mode_id.late_payment_interest)
                ).quantize(Decimal('1.00')),
            # Multa padrão em percentual no Odoo, valor '2'
            'codigo_multa': '2',
            'data_multa': self.format_date(
                line.date_maturity),
            'juros_multa':  Decimal(
                str(self.order.payment_mode_id.late_payment_fee)).quantize(
                    Decimal('1.00')),
            # TODO Remover taxa dia - deixar apenas taxa normal
            'juros_mora_taxa_dia': Decimal('0.00'),
            'valor_abatimento': Decimal('0.00'),
            'sacado_inscricao_tipo': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': int(
                self.rmchar(line.partner_id.cnpj_cpf)),
            'sacado_nome': line.partner_id.legal_name or line.partner_id.name,
            'sacado_endereco': (
                line.partner_id.street + ' ' + line.partner_id.number),
            'sacado_bairro': line.partner_id.district,
            'sacado_cep': int(prefixo),
            'sacado_cep_sufixo': int(sulfixo),
            'sacado_cidade': line.partner_id.city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'codigo_protesto': int(self.order.payment_mode_id.boleto_protesto),
            'prazo_protesto': int(
                self.order.payment_mode_id.boleto_protesto_prazo),
            'codigo_baixa': 2,
            'prazo_baixa': 0,  # De 5 a 120 dias.
            'controlecob_data_gravacao': self.data_hoje(),
            'cobranca_carteira': int(
                self.order.payment_mode_id.boleto_carteira[:2]),
        }

    def remessa(self, order):
        """

        :param order:
        :return:
        """
        cobrancasimples_valor_titulos = 0

        self.order = order
        header = self._prepare_header()
        self.arquivo = Arquivo(self.bank, **header)
        for line in order.line_ids:
            seg = self._prepare_segmento(line.move_line_id)
            self.arquivo.incluir_cobranca(header, **seg)
            self.arquivo.lotes[0].header.servico_servico = 1
            # TODO: tratar soma de tipos de cobranca
            cobrancasimples_valor_titulos += line.move_line_id.amount_currency
            self.arquivo.lotes[0].trailer.cobrancasimples_valor_titulos = \
                Decimal(cobrancasimples_valor_titulos).quantize(
                    Decimal('1.00'))

        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')

    def data_hoje(self):
        return (int(time.strftime("%d%m%Y")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))
