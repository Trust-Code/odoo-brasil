# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
import io
import logging
from datetime import date

_logger = logging.getLogger(__name__)

try:
    from pyboleto import bank
    BoletoException = bank.BoletoException
except ImportError:
    _logger.error('Cannot import pyboleto', exc_info=True)


especie = {
    '01': 'DM',
    '02': 'NP',
    '03': 'NS',
    '04': 'ME',
    '05': 'REC',
    '08': 'DS',
    '13': 'ND',
}


class Boleto:
    boleto = object
    account_number = ''
    account_digit = ''

    branch_number = ''
    branch_digit = ''

    nosso_numero = ''

    def __init__(self, payment, nosso_numero):
        self._cedente(payment.company_id)
        self._sacado(payment.partner_id)
        self._payment_transfer(payment)
        self.nosso_numero = nosso_numero

    def getAccountNumber(self):
        if self.account_digit:
            return str(self.account_number + '-' +
                       self.account_digit)
        return self.account_number

    def getBranchNumber(self):
        if self.branch_digit:
            return str(self.branch_number + '-' +
                       self.branch_digit)
        return self.branch_number

    def _payment_transfer(self, payment):
        self._payment_mode(payment.acquirer_id.journal_id)
        self.boleto.data_vencimento = payment.date_maturity
        self.boleto.data_documento = payment.create_date
        self.boleto.data_processamento = date.today()
        self.boleto.valor = "%.2f" % payment.amount
        self.boleto.valor_documento = "%.2f" % payment.amount
        self.boleto.especie = \
            payment.currency_id and payment.currency_id.symbol or 'R$'
        self.boleto.quantidade = '1'

    def _payment_mode(self, journal_id):
        """
        :param payment_mode:
        :return:
        """
        self.boleto.convenio = journal_id.boleto_cnab_code
        self.boleto.especie_documento = especie[journal_id.boleto_especie]
        self.boleto.aceite = journal_id.boleto_aceite
        self.boleto.carteira = journal_id.boleto_carteira
        self.boleto.instrucoes = journal_id.instrucoes or ''

    def _cedente(self, company):
        """
        :param company:
        :return:
        """
        company_legal_name = company.partner_id.l10n_br_legal_name

        if len(company_legal_name) > 45:
            company_legal_name = company_legal_name[0:42] + '...'

        self.boleto.cedente = company_legal_name
        self.boleto.cedente_documento = company.l10n_br_cnpj_cpf
        self.boleto.cedente_bairro = company.l10n_br_district
        self.boleto.cedente_cep = company.zip
        self.boleto.cedente_cidade = company.city_id.name
        self.boleto.cedente_logradouro = company.street + ', ' + company.l10n_br_number
        self.boleto.cedente_uf = company.state_id.code
        self.boleto.agencia_cedente = self.getBranchNumber()
        self.boleto.conta_cedente = self.getAccountNumber()

    def _sacado(self, partner):
        """

        :param partner:
        :return:
        """
        self.boleto.sacado_endereco = partner.street + ', ' + partner.l10n_br_number
        self.boleto.sacado_cidade = partner.city_id.name
        self.boleto.sacado_bairro = partner.l10n_br_district
        self.boleto.sacado_uf = partner.state_id.code
        self.boleto.sacado_cep = partner.zip
        self.boleto.sacado_nome = partner.l10n_br_legal_name\
            if partner.company_type == 'company' else partner.name
        self.boleto.sacado_documento = partner.l10n_br_cnpj_cpf

    @classmethod
    def get_pdfs(cls, boleto_list):
        """

        :param boletoList:
        :return:
        """
        fbuffer = io.BytesIO()

        from pyboleto.pdf import BoletoPDF
        boleto = BoletoPDF(fbuffer)
        for i in range(len(boleto_list)):
            boleto.drawBoleto(boleto_list[i].boleto)
            boleto.nextPage()
        boleto.save()
        boleto_file = fbuffer.getvalue()

        fbuffer.close()
        return boleto_file


class BoletoItau(Boleto):
    def __init__(self, payment, nosso_numero):
        self.boleto = bank.get_class_for_codigo('341')
        conta = payment.acquirer_id.journal_id.bank_account_id
        self.account_number = conta.acc_number
        # self.branch_number = conta.bra_number
        # self.account_digit = conta.acc_number_dig
        Boleto.__init__(self, payment, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero
        # if '-' in self.boleto.conta_cedente:
        #     self.boleto.conta_cedente = self.boleto.conta_cedente.split('-')[0]
        # self.boleto.conta_cedente_dv = self.account_digit

    def _payment_transfer(self, payment):
        self.boleto.nosso_numero = payment.l10n_br_itau_nosso_numero
        Boleto._payment_transfer(self, payment)

    def _payment_mode(self, journal_id):
        self.boleto.carteira = journal_id.l10n_br_itau_carteira
        self.boleto.instrucoes = ''


dict_boleto = {
    '6': (BoletoItau, 'Itaú'),
}


def getBoletoSelection():
    list = []
    for i in dict_boleto:
        list.append((i, dict_boleto[i][1]))
    return list
