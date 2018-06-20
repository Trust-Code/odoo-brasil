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

    def _get_segmento_a(self, order_line):
        #cpf_cnpj = re.sub('[^0-9]', self._order.payment_mode_id.company_id.cnpj_cpf)
        segmentoA = {"controle_lote": 159, "sequencial_registro_lote": 00000 , "tipo_movimento":5 , "codigo_instrucao_movimento":14 , "codigo_camara_compensacao":157 , "favorecido_banco":212, "favorecido_agencia":00000 , "favorecido_agencia_dv":"R",
        "favorecido_conta":000000000000 , "favorecido_conta_dv":0 , "favorecido_agencia_conta_dv":" " , "favorecido_nome":" " , "numero_documento_cliente": "156341546546546" , "data_pagamento":19062018 , "valor_pagamento":Decimal('32.03') , "numero_documento_banco":"000" , "data_real_pagamento":20062018, "valor_real_pagamento":Decimal('33.00') ,  "mensagem2":"Warning",
        "finalidade_doc_ted":str(55) , "favorecido_emissao_aviso":" " , "ocorrencias_retorno":" "  }
        return segmentoA
# order_line.other_payment.mov_finality
    def _get_segmento_b(self, order_line):
        SegmentoB = {"controle_lote": 1001, "sequencial_registro_lote": 102, "favorecido_inscricao_tipo":1}
        return SegmentoB

    def _get_segmento_g(self, order_line):
        SegmentoG = {"controle_lote": 1002}
        return SegmentoG

    def _get_segmento_h(self, order_line):
        SegmentoH = {"controle_lote": 1003}
        return SegmentoH

    def _get_segmento_j(self, order_line):
        SegmentoJ = {"controle_lote": 1004}
        return SegmentoJ

    def _get_segmento_n(self, order_line):
        SegmentoN = {"controle_lote": 1005}
        return SegmentoN

    def _get_segmento_o(self, order_line):
        SegmentoO = {"controle_lote": 1006}
        return SegmentoO

    def _get_segmento_w(self, order_line):
        SegmentoW = {"controle_lote": 1006}
        return SegmentoW

    def _get_segmento_z(self):
        SegmentoZ = {"controle_lote": 1007}
        return SegmentoZ

    def _get_trailer_arq(self):
        trailerArq = {'bankCode': 0, 'loteServ': 0000, 'registerType': 9, 'filler': 000, 'numLotes': 0, 'numReg': 0, 'filler2': 0}
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

        #determinar depois se essa é a melhor forma
        #pois desse jeito toda vez que vai criar um detalhe testa todas as opcoes
        #quando a ordenação dos segmentos for realizada antes de rodar essa função
        #será possivel saber quando o lote é trocado.

    def create_cnab(self):
        self._cnab_file.add_header(self._get_header_arq())

    def __init__(self, payment_order):
        self._order = payment_order
        self._bank = santander
        self._cnab_file = File(santander)
        self.create_cnab()

    def _create_segment(self, segment, dict ):
        self._cnab_file.add_segment(segment, dict)

    def create_detail(self, operation, order_line): #descobrir quais dos tributos sao titulos de cobranca e quais usam barcode
        if(int(operation) <= 10 or operation == '20'):
            self._create_segment('SegmentoA', self._get_segmento_a(order_line))
            self._create_segment('SegmentoB', self._get_segmento_b(order_line))
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

        return listOfLines #deve ordenar as payment order lines de forma a juntar as mesmas operações em blocos.
