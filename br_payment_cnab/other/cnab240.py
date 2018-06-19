from decimal import Decimal
import datetime
import re
import string
import time
from random import choice
from io import StringIO
from pycnab240.file import File
from pycnab240.bancos import santander


class Cnab_240(object):

    def __init__(self):
        pass



    def add_order_line(self, order_line):
        pass
        #self._initialize_header(order_line)
        #self._generate_detail(order_line)
        #self._generate_trailer(order_line)

    def generate_file(self):
        return ""

    #def createArq(self, order_line, order):
        #File.add_header(Cnab_240.getHeaderArq(order))
        #File.add_trailer(Cnab_240.getTrailerArq())


    def getHeaderArq(self, payment_order):
        headerArq = {'bankCode': 33, 'loteServ': 0000, 'registerType': 0, # Tipo de registro da empresa
                    'filler': 000, 'idRegisterCompany': self.getTypeInscription(), #0 = Isento, 1 = CPF, 2 = CNPJ
                    'nunRegisterCompany': 000000000000000, #número do registro da empresa
                    'contractId':000000000000000000000, #Código adotado pelo Banco para identificar o contrato -númerodo banco(4), códigode agência(4 "sem DV"), número do convênio(12).
                    'agency': int(self.order.payment_mode_id.bank_account_id.bra_number),   #Conta com letra substituir-se por zero. Para ordem de pagamento -saque em uma agência -número da agência, caso contrário preencher com zeros.
                    'agencyDv': 0, 'accountNumber': 0000000000000, 'accountDv': 0,
                    'agencyAccountDv': 0,'companyName': 0000000000000000000000000000000,
                    'bankName':  0000000000000000000000000000000, #Banco Santander
                    'filler2': 0000000000, 'remittanceId': 1, 'dateFileGeneration': self.dateToday(),
                    'hourFileGeneration': self.hourNow(), 'fileNumber': 1, #Número sequêncial onde cada novo arquivo adicionado 1.
                    'layoutVersion':0, 'fileDensity': 00000, 'bankspace': " "*20, # Uso Resenvado do banco.
                    'companyspace': " "*20, # Uso opcional.
                    'filler3': 0000000000000000000, 'codeRecurrence': 00000000000} #Ocorrências para ocorrencias_retorno.
        return headerArq

    def setTrailerArq(self):
        trailerArq = {'bankCode': 0, 'loteServ': 0000, 'registerType': 9, 'filler': 000, 'numLotes': 0, 'numReg': 0, 'filler2': 0}
        return trailerArq

    def setHeaderLot(self): # Conta corrente
        pass

    def setTrailerLot(self):
        pass

    def defDetalhe(self):
        #define qual registro de detalhe necessário
        pass

    def setSegmentoA(self):
        segmentoA = {"controle_banco": 33, "controle_lote": 159, "controle_registro": 3, "sequencial_registro_lote": 'A' , "servico_segmento":" ", "tipo_movimento":" " , "codigo_instrucao_movimento":" " , "codigo_camara_compensacao":" " , "favorecido_banco": " ", "favorecido_agencia":" " , "favorecido_agencia_dv":" ",
        "favorecido_conta":" " , "favorecido_conta_dv":" " , "favorecido_agencia_conta_dv":" " , "favorecido_nome":" " , "numero_documento_cliente": int(re.sub('[^0-9]', self.order.payment_mode_id.company_id.cnpj_cpf)) , "data_pagamento":" " , "tipo_moeda": "BRL", "vazio1":" " , "valor_pagamento":" " , "numero_documento_banco":" " , "data_real_pagamento":" " , "valor_real_pagamento":" " ,  "mensagem2":" ",
        "finalidade_doc_ted":" " ,"vazio2":" " , "favorecido_emissao_aviso":" " , "ocorrencias_retorno":" "  }
        return segmentoA

    def setSegmentoB(self):
        SegmentoB = {"controle_lote": 1001, "sequencial_registro_lote": 102, "favorecido_inscricao_tipo": 103}
        return SegmentoB
    def dateToday(self):
        return (int(time.strftime("%d%m%Y")))

    def hourNow(self):
        return (int(time.strftime("%H%M%S")))

    def getTypeInscription(self):
        if self.order.payment_mode_id.company_id.partner_id.is_company:
            return 2
        else:
            return 1

    def _initialize_header(self, ):
        vals = self.getHeaderArq(order_line)
        cnabFile.add_header(vals)

    def createHeaderLot(self, ):
        vals = self.getHeaderLot(order_line)
        cnabFile.add_segment('HeaderLote', vals)

    def createSegment(self, ):
        lista = [1,2]
        sortear = choice(lista)
            if sortear == 1:
                vals = self.getSegmentoA(order_line)
                cnabFile.add_segment('SegmentoA', vals)
            else:
                vals = self.getSegmentoB(order_line)
                cnabFile.add_segment('SegmentoB', vals)

    def createTrailerLote(self, ):
        vals = self.getTrailerLot(order_line)
        cnabFile.add_segment('TrailerLote' vals)

    def _inicialize_trailer(self, ):
        vals = self.setTrailerArq(order_line)
        cnabFile.add_trailer(vals)

    def _inicialize_service(self, ):
        self.createHeaderLot()
        self.createSegment()
        self.createTrailerLote()

    def create_arq(self, ):
        self._inicialize_header()
        self._inicialize_service()
        self._inicialize_trailer()


    def createCnab(self, payment_order):
        arquivo = StringIO()
        cnabFile = File(santander)
        self.create_arq()
        #self.order = payment_order
        cnabFile.close_file()
        cnabFile.write_to_file(arquivo)
        return arquivo.getvalue()
