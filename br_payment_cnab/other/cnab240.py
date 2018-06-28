from decimal import Decimal
import time
import re
from io import StringIO
from pycnab240.file import File
from pycnab240.bancos import santander


class Cnab_240(object):

    segments_dict = {
        "01": ["SegmentoA", "SegmentoB"],
        "03": ["SegmentoA", "SegmentoB"],
        "05": ["SegmentoA", "SegmentoB"],
        "10": ["SegmentoA", "SegmentoB"],
        "20": ["SegmentoA", "SegmentoB"],
        "16": ["SegmentoJ", "SegmentoB"],
        "17": ["SegmentoJ", "SegmentoB"],
        "18": ["SegmentoJ", "SegmentoB"],
        "22": ["SegmentoO", "SegmentoB"],
        "23": ["SegmentoO", "SegmentoB"],
        "24": ["SegmentoO", "SegmentoB"],
        "25": ["SegmentoO", "SegmentoB"],
        "26": ["SegmentoO", "SegmentoB"],
        "27": ["SegmentoO", "SegmentoB"],
        "11": ["SegmentoO", "SegmentoB"]
    }

    def _date_today(self):
        return (int(time.strftime("%d%m%Y")))

    def _hour_now(self):
        return (int(time.strftime("%H%M%S")[0:4]))

    def _get_inscription(self, inscription):
        if inscription:
            return 2
        else:
            return 1

    def _get_E_field(self, date, value):
        date = str(self._string_to_num(date))
        value = str(self._string_to_num(value))
        e_field = (date + value)
        return '0'*(14-(len(e_field))) + e_field

    def _format_barcode(self, currency_code, date_due, value): #Descobrir o que diabos é o campo livre
        bank_code = '033'
        # currency_code =  str(line.other_payment.currency_code)
        e_field = self._get_E_field(date_due, value)#line.date_maturity, line.value_final)
        c_field = '0'*25
        return int(bank_code+currency_code+'1'+e_field+c_field)

    def _int_to_monetary(self, numero, precision=2):
        frmt = '{:.%df}' % precision
        return Decimal(frmt.format(numero))

    def _string_to_num(self, toTransform, default=None):
        value = re.sub('[^0-9]', '', str(toTransform))
        try:
            return int(value)
        except ValueError:
            if default:
                return default
            else:
                raise

    def _get_header_arq(self):
        payment = self._order.payment_mode_id
        bank = payment.bank_account_id
        headerArq = {
            'cedente_inscricao_tipo': 2,  # 0 = Isento, 1 = CPF, 2 = CNPJ
            'cedente_inscricao_numero': self._string_to_num(
                self._order.company_id.cnpj_cpf),  # número do registro da empresa
            'codigo_convenio': str(payment.boleto_cnab_code),  # Código adotado pelo Banco para identificar o contrato -númerodo banco(4), códigode agência(4 "sem DV"), número do convênio(12).
            'cedente_agencia': int(bank.bra_number),   #Conta com letra substituir-se por zero. Para ordem de pagamento -saque em uma agência -número da agência, caso contrário preencher com zeros.
            'cedente_agencia_dv': str(bank.acc_number_dig),
            'cedente_conta': int(bank.acc_number),
            'cedente_conta_dv': str(int(bank.bra_number_dig)),
            'cedente_nome': str(self._order.company_id.name),
            'data_geracao_arquivo': self._date_today(),
            'hora_geracao_arquivo': self._hour_now(),
            'numero_sequencial_arquivo': self._order.file_number,  # Número sequêncial onde cada novo arquivo adicionado 1.
        }
        return headerArq

    def _get_segmento(self, line):
        other = line.other_payment
        segmento = {
            "tipo_movimento": int(other.mov_type),
            "codigo_instrucao_movimento": int(other.mov_instruc),
            "codigo_camara_compensacao": int(other.operation_code),
            "favorecido_banco": line.bank_account_id.bank_id.name,  #adicionar campo para o banco do clinte com um valor default
            "favorecido_agencia": line.bank_account_id.bra_number,
            "favorecido_agencia_dv": line.bank_account_id.bra_number_dig,
            "favorecido_conta": line.bank_account_id.acc_number,
            "favorecido_conta_dv": line.bank_account_id.acc_number_dig,
            "favorecido_agencia_conta_dv": " ",
            "favorecido_nome": line.partner_id.name,
            "numero_documento_cliente": 150,  # TODO Esse campo é um identificador único da linha, utilizamos geralmente o campo nosso número
            "data_pagamento": self._string_to_num(line.date_maturity),
            "valor_pagamento": self._int_to_monetary(line.value),
            "numero_documento_banco": "000",
            "data_real_pagamento": self._string_to_num(
                self._order.data_emissao_cnab[0:10]),  # verificar se essa data é a data de emissao do cnab
            "valor_real_pagamento": Decimal('33.00'),
            "mensagem2": str(other.message2),
            "finalidade_doc_ted": str(other.mov_finality),
            #"favorecido_emissao_aviso": int(other.warning_code),
            "favorecido_inscricao_tipo":
            2 if line.partner_id.is_company else 1,
            "favorecido_inscricao_numero":self._string_to_num(
                line.partner_id.cnpj_cpf), # Rever este campo
            "favorecido_endereco_rua": str(line.partner_id.street),
            "favorecido_endereco_numero": self._string_to_num(
                line.partner_id.number, default='0'),
            "favorecido_endereco_complemento": str(
                line.partner_id.street2)[0:15],
            "favorecido_bairro": str(line.partner_id.district),
            "favorecido_cidade": str(line.partner_id.city),
            "favorecido_cep": self._string_to_num(str(line.partner_id.zip)),
            "favorecido_uf": str(line.partner_id.state_id.code),
            "valor_documento": self._int_to_monetary(line.value_final),
            "valor_abatimento": self._int_to_monetary(other.rebate_value),
            "valor_desconto": self._int_to_monetary(other.discount_value),
            "valor_mora": self._int_to_monetary(other.mora_value),
            "valor_multa": self._int_to_monetary(other.duty_value),
            "hora_envio_ted": self._hour_now(),
            "codigo_historico_credito": int(other.credit_hist_code),
            "cedente_nome": self._order.company_id.name,
            "valor_nominal_titulo": self._int_to_monetary(line.value),
            "valor_desconto_abatimento": self._int_to_monetary(
                other.rebate_value + other.discount_value),
            "valor_multa_juros": self._int_to_monetary(
                other.mora_value + other.duty_value),
            "codigo_moeda": int(other.currency_code),
            "codigo_de_barras": self._composition_barcode(line),  ## tá errado, esse campo deve ser obtido a partir do payment_mode_id
            "nome_concessionaria": other.agency_name,
            "data_vencimento": self._string_to_num(line.date_maturity)
        }
        return segmento

    def _get_trailer_arq(self):
        trailerArq = { }
        return trailerArq

    def _get_trailer_lot(self):
        trailer_lot = {
            "somatorio_valores": self._int_to_monetary(123456)   # Fazer funcao que calcula o somatorio dos valores de cada detalhe
        }
        return trailer_lot

    def _get_header_lot(self, line):
        other = line.other_payment
        payment = self._order.payment_mode_id
        bank = payment.bank_account_id
        header_lot = {
            "tipo_servico": int(other.serv_type),
            # "forma_lancamento": int(other.entry_mode),
            "numero_versao_lote": 31,
            "cedente_inscricao_tipo": 2,
            "cedente_inscricao_numero": self._string_to_num(
                payment.company_id.cnpj_cpf),
            "codigo_convenio": bank.codigo_convenio,
            "cedente_agencia": int(bank.bra_number),
            "cedente_agencia_dv": bank.acc_number_dig,
            "cedente_conta": int(bank.acc_number),
            "cedente_conta_dv": bank.acc_number_dig,
            "cedente_nome": payment.company_id.name,
            "mensagem1": str(other.message1),
            "cedente_endereco_rua": str(self._order.company_id.street),
            "cedente_endereco_numero": self._string_to_num(
                payment.company_id.number),
            "cedente_endereco_complemento": str(
                self._order.company_id.street2)[0:15],
            "cedente_cidade": str(self._order.company_id.city_id.name)[:20],
            "cedente_cep": int(self._order.company_id.zip[0:5]),
            "cedente_cep_complemento": int(self._order.company_id.zip[5:8]),
            "cedente_uf": str(self._order.company_id.state_id.code),
        }
        return header_lot

    def _ordenate_lines(self, listOfLines):
        operacoes = {}
        for line in listOfLines:
            if line.other_payment.entry_mode in operacoes:
                operacoes[line.other_payment.entry_mode].append(line)
            else:
                operacoes[line.other_payment.entry_mode] = [line]
        return operacoes

    def __init__(self, payment_order):
        self._order = payment_order
        self._bank = santander
        self._cnab_file = File(santander)

    def create_cnab(self, listOfLines):
        self._cnab_file.add_header(self._get_header_arq())
        self.create_details(self._ordenate_lines(listOfLines))

    def create_detail(self, operation, event):
        for segment in self.segments_dict[operation]:
            self._cnab_file.add_segment(segment, self._get_segmento(event))
        self._cnab_file.get_active_lot().get_active_event().close_event()

    def _create_trailer_lote(self):
        self._cnab_file.add_segment('TrailerLote', self._get_trailer_lot())
        self._cnab_file.get_active_lot().close_lot()

    def _create_header_lote(self, line):
        self._cnab_file.add_segment('HeaderLote', self._get_header_lot(line))

    def create_details(self, operacoes):
        for lote in operacoes:
            self._create_header_lote(operacoes[lote][0])
            for event in operacoes[lote]:
                self.create_detail(lote, event)
            self._create_trailer_lote()

    def _generate_file(self):
        arquivo = StringIO()
        self._cnab_file.write_to_file(arquivo)
        return arquivo.getvalue()

    def write_cnab(self):
        self._cnab_file.add_trailer(self._get_trailer_arq())
        self._cnab_file.close_file()
        return self._generate_file().encode()
