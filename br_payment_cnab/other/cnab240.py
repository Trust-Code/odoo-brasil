from decimal import Decimal
import datetime
import re
import string
import time
from pycnab240.file import File
from pycnab240.bancos import santander

class Cnab_240(object):

    def createCnab(self):
        cnabFile = File(santander)
        cnabLot = cnabFile.create_new_lot()
        createArq(cnabFile. cnabLot)


    def createArq(self, File, Lot):
        cnabFile.add_header(setHeaderArq)
        cnabFile.add_trailer(setTrailerArq)


    def setHeaderArq(self):
        headerArq = {'bankCode': 33, 'loteServ': 0000, 'registerType': 0, # Tipo de registro da empresa
                    'filler': 000, 'idRegisterCompany': self.getTypeInscription(), #0 = Isento, 1 = CPF, 2 = CNPJ
                    'nunRegisterCompany': 000000000000000, #número do registro da empresa
                    'contractId':000000000000000000000, #Código adotado pelo Banco para identificar o contrato -númerodo banco(4), códigode agência(4 "sem DV"), número do convênio(12).
                    'agency': int(self.order.payment_mode_id.bank_account_id.bra_number),   #Conta com letra substituir-se por zero. Para ordem de pagamento -saque em uma agência -número da agência, caso contrário preencher com zeros.
                    'agencyDv': 0, 'accountNumber': 0000000000000, 'accountDv': 0,'agencyAccountDv': 0,'companyName': 0000000000000000000000000000000, 'bankName':  0000000000000000000000000000000, #Banco Santander
                    'filler2': 0000000000, 'remittanceId': 1, 'dateFileGeneration': self.dateToday(), 'hourFileGeneration': self.hourNow(), 'fileNumber': 1 #Número sequêncial onde cada novo arquivo adicionado 1.
                    'layoutVersion': 060, 'fileDensity': 00000, 'bankspace': " "*20, # Uso Resenvado do banco.
                    'companyspace': " "*20, # Uso opcional.
                    'filler': 0000000000000000000, 'codeRecurrence': 00000000000} #Ocorrências para ocorrencias_retorno.
        return headerArq

    def setTrailerArq(self):
        trailerArq = {'bankCode': 033, 'loteServ': 0000, 'registerType': 9, 'filler': 000, 'numLotes': 0, 'numReg': 0, 'filler2': 0}
        return trailerArq

    def setHeaderLot(self): # Conta corrente

    def setTrailerLot(self):

    def defDetalhe(self):
        #define qual registro de detalhe necessário

    def setSegmentoA(self):
        segmentoA = {"controle_banco": 33 , "controle_lote": , "controle_registro": 3, "sequencial_registro_lote": A , "servico_segmento": , "tipo_movimento": , "codigo_instrucao_movimento": , "codigo_camara_compensacao": , "favorecido_banco": , "favorecido_agencia": , "favorecido_agencia_dv":,
        "favorecido_conta": , "favorecido_conta_dv": , "favorecido_agencia_conta_dv": , "favorecido_nome": , "numero_documento_cliente": int(re.sub('[^0-9]', self.order.payment_mode_id.company_id.cnpj_cpf)) , "data_pagamento": , "tipo_moeda": "BRL", "vazio1": , "valor_pagamento": , "numero_documento_banco": , "data_real_pagamento": , "valor_real_pagamento": ,  "mensagem2":,
        "finalidade_doc_ted": ,"vazio2": , "favorecido_emissao_aviso": , "ocorrencias_retorno":  }
        return segmentoA

    def setSegmentoB(self):

    def dateToday(self):
        return (int(time.strftime("%d%m%Y")))

    def hourNow(self):
        return (int(time.strftime("%H%M%S")))


        @property
    def getTypeInscription(self):
        if self.order.payment_mode_id.company_id.partner_id.is_company:
            return 2
        else:
            return 1
