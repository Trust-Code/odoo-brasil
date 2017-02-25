# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
import logging
from datetime import datetime, date

_logger = logging.getLogger(__name__)

try:
    from pyboleto import bank
except ImportError:
    _logger.debug('Cannot import pyboleto')

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
BoletoException = bank.BoletoException

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
    def getBoleto(move_line, nosso_numero):
        boleto_type = move_line.payment_mode_id.boleto_type
        if boleto_type:
            return dict_boleto[boleto_type][0](move_line, nosso_numero)
        raise BoletoException(u'Configure o tipo de boleto no modo de '
                              u'pagamento')

    @staticmethod
    def getBoletoClass(move_line):
        bank_code = move_line.payment_mode_id.bank_account_id.bank_id.bic
        return bank.get_class_for_codigo(bank_code)

    def __init__(self, move_line, nosso_numero):
        self._cedente(move_line.company_id)
        self._sacado(move_line.partner_id)
        self._move_line(move_line)
        self.nosso_numero = nosso_numero

    def getAccountNumber(self):
        if self.account_digit:
            return str(self.account_number + '-' +
                       self.account_digit).encode('utf-8')
        return self.account_number.encode('utf-8')

    def getBranchNumber(self):
        if self.branch_digit:
            return str(self.branch_number + '-' +
                       self.branch_digit).encode('utf-8').strip()
        return self.branch_number.encode('utf-8').strip()

    def _move_line(self, move_line):
        self._payment_mode(move_line.payment_mode_id)
        self.boleto.data_vencimento = datetime.date(datetime.strptime(
            move_line.date_maturity, '%Y-%m-%d'))
        self.boleto.data_documento = datetime.date(datetime.strptime(
            move_line.invoice_id.date_invoice, '%Y-%m-%d'))
        self.boleto.data_processamento = date.today()
        self.boleto.valor = str("%.2f" % (move_line.debit or move_line.credit))
        self.boleto.valor_documento = str("%.2f" % (move_line.debit or
                                          move_line.credit))
        self.boleto.especie = \
            move_line.currency_id and move_line.currency_id.symbol or 'R$'
        self.boleto.quantidade = '1'
        self.boleto.numero_documento = u"%s/%s" % (
            move_line.move_id.name, move_line.name)

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
        self.boleto.cedente = company.partner_id.legal_name
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
        fbuffer = StringIO()

        fbuffer.reset()
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
    def __init__(self, move_line, nosso_numero):
        # TODO: size o convenio and nosso numero, replace (7,2)
        # Size of convenio 4, 6, 7 or 8
        # Nosso Numero format. 1 or 2
        # Used only for convenio=6
        # 1: Nosso Numero with 5 positions
        # 2: Nosso Numero with 17 positions
        self.boleto = Boleto.getBoletoClass(move_line)(7, 2)
        self.account_number = move_line.payment_mode_id.\
            bank_account_id.acc_number
        self.branch_number = move_line.payment_mode_id.\
            bank_account_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoBanrisul(Boleto):
    pass


class BoletoBradesco(Boleto):
    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.\
            bank_account_id.acc_number
        self.branch_number = move_line.payment_mode_id.\
            bank_account_id.bra_number
        # bank specific
        self.account_digit = move_line.payment_mode_id.\
            bank_account_id.acc_number_dig
        self.branch_digit = move_line.payment_mode_id.\
            bank_account_id.bra_number_dig
        # end bank specific
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero
        self.boleto.valor = 0.0  # Não preencher


class BoletoCaixa(Boleto):
    pass


class BoletoCecred(Boleto):
    def __init__(self, move_line, nosso_numero):
        conta = move_line.payment_mode_id.bank_account_id
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = conta.acc_number
        self.account_digit = conta.acc_number_dig
        self.branch_number = conta.bra_number
        self.branch_digit = conta.bra_number_dig
        Boleto.__init__(self, move_line, nosso_numero)
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
    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.\
            bank_account_id.acc_number
        self.branch_number = move_line.payment_mode_id.\
            bank_account_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoSantander(Boleto):
    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = \
            move_line.payment_mode_id.bank_account_id.acc_number[:7]
        self.branch_number = \
            move_line.payment_mode_id.bank_account_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero
        self.boleto.conta_cedente = \
            move_line.payment_mode_id.bank_account_id.codigo_convenio


class BoletoSicredi(Boleto):
    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.\
            bank_account_id.acc_number
        self.branch_number = move_line.payment_mode_id.\
            bank_account_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoSicoob(Boleto):
    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.\
            bank_account_id.acc_number
        self.account_digit = move_line.payment_mode_id.\
            bank_account_id.acc_number_dig
        self.branch_number = move_line.payment_mode_id.\
            bank_account_id.bra_number
        self.branch_digit = move_line.payment_mode_id.\
            bank_account_id.bra_number_dig
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.codigo_beneficiario = \
            re.sub('[^0-9]', '',
                   move_line.payment_mode_id.bank_account_id.codigo_convenio)
        self.boleto.nosso_numero = self.nosso_numero

    def getAccountNumber(self):
        return self.account_number.encode('utf-8')

    def getBranchNumber(self):
        return self.branch_number.encode('utf-8')


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
