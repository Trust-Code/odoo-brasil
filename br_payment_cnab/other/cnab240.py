from decimal import Decimal
import re
import string
import time
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
        return (int(time.strftime("%H%M%S")))

    def _get_header_arq(self):
        payment = self._order.payment_mode_id
        headerArq = {
                    'bankCode': 33,
                    'loteServ': 0000,
                    'registerType': 0,  # Tipo de registro da empresa
                    'filler': 000,
                    'idRegisterCompany': self._get_inscription(payment.company_id.partner_id.is_company),  # 0 = Isento, 1 = CPF, 2 = CNPJ
                    'nunRegisterCompany': 000000000000000,  # número do registro da empresa
                    'contractId': 000000000000000000000,  # Código adotado pelo Banco para identificar o contrato -númerodo banco(4), códigode agência(4 "sem DV"), número do convênio(12).
                    'agency': int(payment.bank_account_id.bra_number),   #Conta com letra substituir-se por zero. Para ordem de pagamento -saque em uma agência -número da agência, caso contrário preencher com zeros.
                    'agencyDv': 0,
                    'accountNumber': 0000000000000,
                    'accountDv': 0,
                    'agencyAccountDv': 0,
                    'companyName': 0000000000000000000000000000000,
                    'bankName': santander,  # Banco Santander
                    'filler2': 0000000000,
                    'remittanceId': 1,
                    'dateFileGeneration': self._date_today(),
                    'hourFileGeneration': self._hour_now(),
                    'fileNumber': 1,  # Número sequêncial onde cada novo arquivo adicionado 1.
                    'layoutVersion': 0,
                    'fileDensity': 00000,
                    'bankspace': " "*20,  # Uso Resenvado do banco.
                    'companyspace': " "*20,  # Uso opcional.
                    'filler3': 0000000000000000000,
                    'codeRecurrence': 00000000000}  # Ocorrências para ocorrencias_retorno.
        return headerArq

    def _get_segmento(self, order_line):
        other = order_line.other_payment
        # cpf_cnpj = re.sub('[^0-9]', self._order.payment_mode_id.company_id.cnpj_cpf)
        segmento = {"controle_lote": 159,
                    "sequencial_registro_lote": 00000,
                    "tipo_movimento": int(other.mov_type),
                    "codigo_instrucao_movimento": int(other.mov_instruc),
                    "codigo_camara_compensacao": 157,
                    "favorecido_banco": 212,
                    "favorecido_agencia": 00000,
                    "favorecido_agencia_dv": "R",
                    "favorecido_conta": 000000000000,
                    "favorecido_conta_dv": 0,
                    "favorecido_agencia_conta_dv": " ",
                    "favorecido_nome": " ",
                    "numero_documento_cliente": "156341546546546",
                    "data_pagamento": 19062018,
                    "valor_pagamento": Decimal('32.03'),
                    "numero_documento_banco": "000",
                    "data_real_pagamento": 20062018,
                    "valor_real_pagamento": Decimal('33.00'),
                    "mensagem2": "Warning",
                    "finalidade_doc_ted": str(other.mov_finality),
                    # "favorecido_emissao_aviso":str(order_line.other_payment.warning_code),
                    # "ocorrencias_retorno":"",
                    # "favorecido_inscricao_tipo":" ",
                    # "favorecido_inscricao_numero": 000,
                    # "favorecido_endereco_rua":"",
                    # "favorecido_endereco_numero":"",
                    # "favorecido_endereco_complemento":"",
                    # "favorecido_bairro":"",
                    # "favorecido_cidade":"",
                    # "favorecido_cep":0,
                    # "favorecido_uf":"",
                    "valor_documento": round(Decimal(self._order.amount_total), 2),
                    # "valor_abatimento":"",
                    # "valor_desconto":"",
                    # "valor_mora":"",
                    # "valor_multa":"",
                    # "hora_envio_ted":self._hour_now(),
                    # "codigo_historico_credito":"",
                    # "cedente_nome":self._order.user_id.name,
                    # "valor_nominal_titulo":"",
                    # "valor_desconto_abatimento":"",
                    # "valor_multa_juros":"",
                    # "quantidade_moeda":"",
                    # "codigo_moeda":"",
                    # "codigo_de_barras":"",
                    # "nome_concessionaria":"",
                    # "data_vencimento":order_line.date_maturity
                    }
        return segmento

    def _get_trailer_arq(self):
        trailerArq = {'bankCode': 7, 'loteServ': 12345, 'registerType': 9,
                      'filler': 000, 'numLotes': 0, 'numReg': 0, 'filler2': 0}
        return trailerArq

    def _get_trailer_lot(self):
        trailer_lot = {"bankCode": 0, "quantidade_registros": 2}
        return trailer_lot

    def _get_header_lot(self, line):
        other = line.other_payment
        payment = self._order.payment_mode_id
        header_lot = {"controle_lote": 0, "tipo_servico": int(other.serv_type),
                      "forma_lancamento": int(other.entry_mode), 
                      "numero_versao_lote": 31,
                      "cedente_inscricao_tipo": self._get_inscription(payment.company_id.partner_id.is_company),
                      "cedente_inscricao_numero": payment.company_id.cnpj_cpf,
                      "codigo_convenio": "naosabemos",
                      "cedente_agencia": ,
                      "cedente_agencia_dv": ,
                      "cedente_conta": ,
                      "cedente_conta_dv": ,
                      "cedente_nome": , 
                      "mensagem1": ,
                      "cedente_endereco_rua": ,
                      "cedente_endereco_numero": ,
                      "cedente_endereco_complemento":,
                      "cedente_cidade":,
                      "cedente_cep":,
                      "cedente_cep_complemento":,
                      "cedente_uf":,
                      "ocorrencias_retorno": }
        return header_lot

    def _get_inscription(self, inscription):
        if inscription:
            return 2
        else:
            return 1

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

    def _create_header_lote(self):
        self._cnab_file.add_segment('HeaderLote', self._get_header_lot())

    def create_details(self, operacoes):
        for lote in operacoes:
            self._create_header_lote(operacoes[lote])
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
