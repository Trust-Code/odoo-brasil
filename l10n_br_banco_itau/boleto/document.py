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
    _logger.error("Cannot import pyboleto", exc_info=True)


especie = {
    "01": "DM",
    "02": "NP",
    "03": "NS",
    "04": "ME",
    "05": "REC",
    "08": "DS",
    "13": "ND",
}


def format_cnpj_cpf(cnpj_cpf):
    cnpj_cpf = re.sub('[^0-9]', '', cnpj_cpf or '')
    if len(cnpj_cpf) == 14:
        cnpj_cpf = (cnpj_cpf[0:2] + '.' + cnpj_cpf[2:5] +
                    '.' + cnpj_cpf[5:8] +
                    '/' + cnpj_cpf[8:12] +
                    '-' + cnpj_cpf[12:14])
    else:
        cnpj_cpf = (cnpj_cpf[0:3] + '.' + cnpj_cpf[3:6] +
                    '.' + cnpj_cpf[6:9] + '-' + cnpj_cpf[9:11])
    return cnpj_cpf


class Boleto:
    boleto = object
    account_number = ""
    account_digit = ""

    branch_number = ""
    branch_digit = ""

    nosso_numero = ""

    @staticmethod
    def getBoletoClass(payment):
        bank_code = payment.payment_journal_id.bank_account_id.bank_id.bic
        return bank.get_class_for_codigo(bank_code)

    def __init__(self, payment, nosso_numero):
        self._cedente(payment.company_id)
        self._sacado(payment.partner_id)
        self._payment_transfer(payment)
        self.nosso_numero = nosso_numero

    def getAccountNumber(self):
        if self.account_digit:
            return str(self.account_number + "-" + self.account_digit)
        return self.account_number

    def getBranchNumber(self):
        if self.branch_digit:
            return str(self.branch_number + "-" + self.branch_digit)
        return self.branch_number

    def _payment_transfer(self, payment):
        self._payment_mode(payment.payment_journal_id)
        self.boleto.numero_documento = "%08d" % payment.id
        self.boleto.data_vencimento = payment.date_maturity
        self.boleto.data_documento = payment.create_date
        self.boleto.data_processamento = date.today()
        self.boleto.valor = "%.2f" % payment.amount
        self.boleto.valor_documento = "%.2f" % payment.amount
        self.boleto.especie = (
            payment.currency_id and payment.currency_id.symbol or "R$"
        )
        self.boleto.quantidade = "1"

    def _payment_mode(self, journal_id):
        """
        :param payment_mode:
        :return:
        """
        self.boleto.convenio = journal_id.l10n_br_cnab_code
        self.boleto.especie_documento = especie.get(journal_id.l10n_br_boleto_especie, "DM")
        self.boleto.aceite = journal_id.l10n_br_boleto_aceite
        self.boleto.carteira = journal_id.l10n_br_boleto_carteira
        self.boleto.instrucoes = journal_id.l10n_br_boleto_instr or ""

    def _cedente(self, company):
        """
        :param company:
        :return:
        """
        company_legal_name = company.partner_id.l10n_br_legal_name

        if len(company_legal_name) > 45:
            company_legal_name = company_legal_name[0:42] + "..."

        self.boleto.cedente = company_legal_name
        self.boleto.cedente_documento = company.l10n_br_cnpj_cpf
        self.boleto.cedente_bairro = company.l10n_br_district
        self.boleto.cedente_cep = company.zip
        self.boleto.cedente_cidade = company.city_id.name
        self.boleto.cedente_logradouro = (
            company.street + ", " + company.l10n_br_number
        )
        self.boleto.cedente_uf = company.state_id.code
        self.boleto.agencia_cedente = self.branch_number
        self.boleto.agencia_cedente_dv = self.branch_digit
        self.boleto.conta_cedente = self.account_number
        self.boleto.conta_cedente_dv = self.account_digit

    def _sacado(self, partner):
        """

        :param partner:
        :return:
        """
        self.boleto.sacado_endereco = (
            partner.street + ", " + partner.l10n_br_number
        )
        self.boleto.sacado_cidade = partner.city_id.name
        self.boleto.sacado_bairro = partner.l10n_br_district
        self.boleto.sacado_uf = partner.state_id.code
        self.boleto.sacado_cep = partner.zip
        self.boleto.sacado_nome = (
            partner.l10n_br_legal_name
            if partner.company_type == "company"
            else partner.name
        )
        self.boleto.sacado_documento = partner.l10n_br_cnpj_cpf
        self.boleto.sacado = [
            "{} - CPF/CNPJ: {}".format(
                partner.l10n_br_legal_name or partner.name,
                format_cnpj_cpf(partner.l10n_br_cnpj_cpf),
            ),
            partner.street + ", " + partner.l10n_br_number,
            "{} - {} - {} - {}".format(
                partner.l10n_br_district,
                partner.city_id.name,
                partner.state_id.code,
                partner.zip,
            ),
        ]

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
            boleto.drawBoleto(boleto_list[i])
            boleto.nextPage()
        boleto.save()
        boleto_file = fbuffer.getvalue()

        fbuffer.close()
        return boleto_file


class BoletoItau(Boleto):
    def __init__(self, payment, nosso_numero):
        self.boleto = Boleto.getBoletoClass(payment)()
        conta = payment.payment_journal_id.bank_account_id
        self.account_number = conta.acc_number
        self.account_digit = conta.acc_number_dig
        self.branch_number = conta.bra_number
        self.branch_digit = conta.bra_number_dig
        Boleto.__init__(self, payment, nosso_numero)

    def _payment_transfer(self, payment):
        self.boleto.nosso_numero = payment.l10n_br_itau_nosso_numero
        Boleto._payment_transfer(self, payment)
