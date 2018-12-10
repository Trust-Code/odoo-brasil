# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
import io
import logging
from datetime import datetime, date

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

    @staticmethod
    def getBoleto(order_line, nosso_numero):
        boleto_type = order_line.payment_mode_id.boleto_type
        if boleto_type:
            return dict_boleto[boleto_type][0](order_line, nosso_numero)
        raise BoletoException(u'Configure o tipo de boleto no modo de '
                              u'pagamento')

    @staticmethod
    def getBoletoClass(order_line):
        bank_code = order_line.src_bank_account_id.bank_id.bic
        return bank.get_class_for_codigo(bank_code)

    def __init__(self, order_line, nosso_numero):
        self._cedente(order_line.company_id)
        self._sacado(order_line.partner_id)
        self._order_line(order_line)
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

    def _order_line(self, order_line):
        self._payment_mode(order_line.payment_mode_id)
        self.boleto.data_vencimento = datetime.date(datetime.strptime(
            order_line.date_maturity, '%Y-%m-%d'))
        self.boleto.data_documento = datetime.date(datetime.strptime(
            order_line.emission_date, '%Y-%m-%d'))
        self.boleto.data_processamento = date.today()
        self.boleto.valor = "%.2f" % order_line.amount_total
        self.boleto.valor_documento = "%.2f" % order_line.amount_total
        self.boleto.especie = \
            order_line.currency_id and order_line.currency_id.symbol or 'R$'
        self.boleto.quantidade = '1'
        # Importante - Número documento deve ser o identificador único da linha
        self.boleto.numero_documento = order_line.identifier

    def _payment_mode(self, payment_mode_id):
        """
        :param payment_mode:
        :return:
        """
        self.boleto.convenio = payment_mode_id.boleto_cnab_code
        self.boleto.especie_documento = especie[payment_mode_id.boleto_especie]
        self.boleto.aceite = payment_mode_id.boleto_aceite
        self.boleto.carteira = payment_mode_id.boleto_carteira
        self.boleto.instrucoes = payment_mode_id.instrucoes or ''

    def _cedente(self, company):
        """
        :param company:
        :return:
        """
        company_legal_name = company.partner_id.legal_name

        if len(company_legal_name) > 45:
            company_legal_name = company_legal_name[0:42] + '...'

        self.boleto.cedente = company_legal_name
        self.boleto.cedente_documento = company.cnpj_cpf
        self.boleto.cedente_bairro = company.district
        self.boleto.cedente_cep = company.zip
        self.boleto.cedente_cidade = company.city_id.name
        self.boleto.cedente_logradouro = company.street + ', ' + company.number
        self.boleto.cedente_uf = company.state_id.code
        self.boleto.agencia_cedente = self.getBranchNumber()
        self.boleto.conta_cedente = self.getAccountNumber()

    def _sacado(self, partner):
        """

        :param partner:
        :return:
        """
        self.boleto.sacado_endereco = partner.street + ', ' + partner.number
        self.boleto.sacado_cidade = partner.city_id.name
        self.boleto.sacado_bairro = partner.district
        self.boleto.sacado_uf = partner.state_id.code
        self.boleto.sacado_cep = partner.zip
        self.boleto.sacado_nome = partner.legal_name\
            if partner.company_type == 'company' else partner.name
        self.boleto.sacado_documento = partner.cnpj_cpf

    @classmethod
    def get_pdfs(cls, boleto_list):
        """

        :param boletoList:
        :return:
        """
        fbuffer = io.BytesIO()

        # fbuffer.reset()
        from pyboleto.pdf import BoletoPDF
        boleto = BoletoPDF(fbuffer)
        for i in range(len(boleto_list)):
            boleto.drawBoleto(boleto_list[i])
            boleto.nextPage()
        boleto.save()
        boleto_file = fbuffer.getvalue()

        fbuffer.close()
        return boleto_file


class BoletoBB(Boleto):
    def __init__(self, order_line, nosso_numero):
        # TODO: size o convenio and nosso numero, replace (7,2)
        # Size of convenio 4, 6, 7 or 8
        # Nosso Numero format. 1 or 2
        # Used only for convenio=6
        # 1: Nosso Numero with 5 positions
        # 2: Nosso Numero with 17 positions
        self.boleto = Boleto.getBoletoClass(order_line)(7, 2)
        self.account_number = order_line.src_bank_account_id.acc_number
        self.branch_number = order_line.src_bank_account_id.bra_number
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoBanrisul(Boleto):
    pass


class BoletoBradesco(Boleto):
    def __init__(self, order_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(order_line)()
        self.account_number = order_line.src_bank_account_id.acc_number
        self.branch_number = order_line.src_bank_account_id.bra_number
        # bank specific
        self.account_digit = order_line.src_bank_account_id.acc_number_dig
        self.branch_digit = order_line.src_bank_account_id.bra_number_dig
        # end bank specific
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero
        self.boleto.valor = 0.0  # Não preencher
        self.boleto.quantidade = ''


class BoletoCaixa(Boleto):
    def __init__(self, order_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(order_line)()
        conta = order_line.src_bank_account_id
        self.account_number = conta.acc_number
        self.branch_number = conta.bra_number
        # bank specific
        self.account_digit = conta.acc_number_dig
        self.branch_digit = conta.bra_number_dig
        # end bank specific
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero
        self.boleto.codigo_beneficiario = conta.codigo_convenio

    def getBranchNumber(self):
        return self.branch_number


class BoletoCecred(Boleto):
    def __init__(self, order_line, nosso_numero):
        conta = order_line.src_bank_account_id
        self.boleto = Boleto.getBoletoClass(order_line)()
        self.account_number = conta.acc_number
        self.account_digit = conta.acc_number_dig
        self.branch_number = conta.bra_number
        self.branch_digit = conta.bra_number_dig
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.codigo_beneficiario = re.sub(
            r'\D', '', conta.codigo_convenio)
        self.boleto.nosso_numero = self.nosso_numero

    def getAccountNumber(self):
        return u"%s-%s" % (self.account_number, self.account_digit)

    def getBranchNNumber(self):
        return u"%s-%s" % (self.branch_number, self.branch_digit)


class BoletoHsbc(Boleto):
    pass


class BoletoItau157(Boleto):
    pass


class BoletoItau(Boleto):
    def __init__(self, order_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(order_line)()
        conta = order_line.src_bank_account_id
        self.account_number = conta.acc_number
        self.branch_number = conta.bra_number
        self.account_digit = conta.acc_number_dig
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero
        if '-' in self.boleto.conta_cedente:
            self.boleto.conta_cedente = self.boleto.conta_cedente.split('-')[0]
        self.boleto.conta_cedente_dv = self.account_digit


class BoletoSantander(Boleto):
    def __init__(self, order_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(order_line)()
        self.account_number = order_line.src_bank_account_id.acc_number[:7]
        self.branch_number = order_line.src_bank_account_id.bra_number
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero

        self.boleto.conta_cedente = \
            order_line.payment_mode_id.boleto_cnab_code


class BoletoSicredi(Boleto):
    def __init__(self, order_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(order_line)()
        self.account_number = order_line.src_bank_account_id.acc_number
        self.branch_number = order_line.src_bank_account_id.bra_number
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoSicoob(Boleto):
    def __init__(self, order_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(order_line)()
        self.account_number = order_line.src_bank_account_id.acc_number
        self.account_digit = order_line.src_bank_account_id.acc_number_dig
        self.branch_number = order_line.src_bank_account_id.bra_number
        self.branch_digit = order_line.src_bank_account_id.bra_number_dig
        Boleto.__init__(self, order_line, nosso_numero)
        self.boleto.codigo_beneficiario = \
            re.sub('[^0-9]', '',
                   order_line.src_bank_account_id.codigo_convenio)
        self.boleto.nosso_numero = self.nosso_numero

    def getAccountNumber(self):
        return self.account_number

    def getBranchNumber(self):
        return self.branch_number


dict_boleto = {
    u'1': (BoletoBB, 'Banco do Brasil'),
    u'2': (BoletoBanrisul, 'Banrisul'),
    u'3': (BoletoBradesco, 'Bradesco'),
    u'4': (BoletoCaixa, u'Caixa Econômica'),
    u'5': (BoletoHsbc, 'HSBC'),
    u'6': (BoletoItau, 'Itaú'),
    u'7': (BoletoSantander, 'Santander'),
    u'8': (BoletoSicredi, 'Sicredi'),
    u'9': (BoletoSicoob, 'Sicoob'),
    u'10': (BoletoCecred, 'Cecred'),
}


def getBoletoSelection():
    list = []
    for i in dict_boleto:
        list.append((i, dict_boleto[i][1]))
    return list
