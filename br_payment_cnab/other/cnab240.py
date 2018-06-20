from decimal import Decimal
import datetime
import re
import string
import time
from random import choice
from io import StringIO
from pycnab240.file import File
from pycnab240.file import Lot
from pycnab240.bancos import santander


class Cnab_240(object):
    # _cnab_file = None
    # _order = None
    # _bank = None

    def _get_header_arq(self):
        headerArq = {'bankCode': 33, 'loteServ': 0000, 'registerType': 0, # Tipo de registro da empresa
                    'filler': 000, 'idRegisterCompany': self._get_type_inscription(), #0 = Isento, 1 = CPF, 2 = CNPJ
                    'nunRegisterCompany': 000000000000000, #número do registro da empresa
                    'contractId':000000000000000000000, #Código adotado pelo Banco para identificar o contrato -númerodo banco(4), códigode agência(4 "sem DV"), número do convênio(12).
                    'agency': int(self._order.payment_mode_id.bank_account_id.bra_number),   #Conta com letra substituir-se por zero. Para ordem de pagamento -saque em uma agência -número da agência, caso contrário preencher com zeros.
                    'agencyDv': 0, 'accountNumber': 0000000000000, 'accountDv': 0,
                    'agencyAccountDv': 0,'companyName': 0000000000000000000000000000000,
                    'bankName':  0000000000000000000000000000000, #Banco Santander
                    'filler2': 0000000000, 'remittanceId': 1, 'dateFileGeneration': self._date_today(),
                    'hourFileGeneration': self._hour_now(), 'fileNumber': 1, #Número sequêncial onde cada novo arquivo adicionado 1.
                    'layoutVersion':0, 'fileDensity': 00000, 'bankspace': " "*20, # Uso Resenvado do banco.
                    'companyspace': " "*20, # Uso opcional.
                    'filler3': 0000000000000000000, 'codeRecurrence': 00000000000} #Ocorrências para ocorrencias_retorno.
        return headerArq

    def _get_segmento(self, order_line):
        #cpf_cnpj = re.sub('[^0-9]', self._order.payment_mode_id.company_id.cnpj_cpf)
        segmento = {"controle_lote": 159,
                    "sequencial_registro_lote": 00000,
                    "tipo_movimento":int(order_line.other_payment.mov_type),
                    "codigo_instrucao_movimento":int(order_line.other_payment.mov_instruc),
                    "codigo_camara_compensacao":157,
                    "favorecido_banco":212,
                    "favorecido_agencia":00000,
                    "favorecido_agencia_dv":"R",
                    "favorecido_conta":000000000000,
                    "favorecido_conta_dv":0,
                    "favorecido_agencia_conta_dv":" ",
                    "favorecido_nome":" ",
                    "numero_documento_cliente": "156341546546546",
                    "data_pagamento":19062018,
                    "valor_pagamento":Decimal('32.03'),
                    "numero_documento_banco":"000",
                    "data_real_pagamento":20062018,
                    "valor_real_pagamento":Decimal('33.00'),
                    "mensagem2":"Warning",
                    "finalidade_doc_ted":str(order_line.other_payment.mov_finality),
                    #"favorecido_emissao_aviso":str(order_line.other_payment.warning_code),
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
                    "valor_documento":round(Decimal(self._order.amount_total),2),
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
# order_line.other_payment.mov_finality


    def _get_trailer_arq(self):
        trailerArq = {'bankCode': 7, 'loteServ': 12345, 'registerType': 9, 'filler': 000, 'numLotes': 0, 'numReg': 0, 'filler2': 0}
        return trailerArq

    def _get_trailer_lot(self, order_line):
        trailerLot = {'bankCode': 0}
        return trailerLot

    def _date_today(self):
        return (int(time.strftime("%d%m%Y")))

    def _hour_now(self):
        return (int(time.strftime("%H%M%S")))

    def _get_type_inscription(self):
        if self._order.payment_mode_id.company_id.partner_id.is_company:
            return 2
        else:
            return 1

    def create_cnab(self):
        self._cnab_file.add_header(self._get_header_arq())

    def __init__(self, payment_order):
        self._order = payment_order
        self._bank = santander
        self._cnab_file = File(santander)
        self.create_cnab()

    def _create_segment(self, segment, dict ):
        self._cnab_file.add_segment(segment, dict)


    detail = { "01":["SegmentoA","SegmentoB"],
              "03":["SegmentoA","SegmentoB"],
              "05":["SegmentoA","SegmentoB"],
              "10":["SegmentoA","SegmentoB"],
              "20":["SegmentoA","SegmentoB"],
              "16":["SegmentoJ","SegmentoB"],
              "17":["SegmentoJ","SegmentoB"],
              "18":["SegmentoJ","SegmentoB"],
              "22":["SegmentoO","SegmentoB"],
              "23":["SegmentoO","SegmentoB"],
              "24":["SegmentoO","SegmentoB"],
              "25":["SegmentoO","SegmentoB"],
              "26":["SegmentoO","SegmentoB"],
              "27":["SegmentoO","SegmentoB"],
              "11":["SegmentoO","SegmentoB"]}



    def create_detail(self, operation, order_line): #descobrir quais dos tributos sao titulos de cobranca e quais usam barcode

        if(int(operation) <= 10 or operation == '20'):
            self._create_segment('SegmentoA', self._get_segmento(order_line))
            self._create_segment('SegmentoB', self._get_segmento(order_line))
            pass
        elif (operation == '11'): #com barcode
            self._create_segment('SegmentoO', self._get_segmento_o(order_line))
        else: #titulos de cobranca
            self._create_segment('SegmentoJ', self._get_segmento_j(order_line))
            self._create_segment('SegmentoB', self._get_segmento_b(order_line)) #opcional
        self._cnab_file.get_active_lot().get_active_event().close_event()

    def _create_trailer_lote(self):
        self._cnabFile.add_segment('TrailerLote', self._get_trailer_lot())

    def _generate_file(self):
        arquivo = StringIO()
        self._cnab_file.write_to_file(arquivo)
        return arquivo.getvalue()

    def write_cnab(self):
        self._cnab_file.add_trailer(self._get_trailer_arq())
        self._cnab_file.close_file()
        return self._generate_file().encode()


    def ordenate_lines(self, listOfLines):
        operacoes = {}
        for line in listOfLines:
            if line.other_payment.entry_mode in operacoes:
                operacoes[line.other_payment.entry_mode].append(line)
            else:
                operacoes[line.other_payment.entry_mode] = [line]
        return operacoes
         #deve ordenar as payment order lines de forma a juntar as mesmas operações em blocos.
