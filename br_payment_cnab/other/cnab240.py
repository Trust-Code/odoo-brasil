from decimal import Decimal
import datetime
import re
import string
import time
from ../../../PyTrustCnab240 import Cnab


class Cnab_240(object):

    def setArquivo(self, OP):
        header = setHeaderArq()
        trailer = setTrailerArq()


    def setHeaderArq(self):
        bankCode = 33
        loteServ = 0000
        registerType = 0 # Tipo de registro da empresa
        filler = 000
        idRegisterCompany = 0 #0 = Isento, 1 = CPF, 2 = CNPJ
        nunRegisterCompany = 000000000000000 #número do registro da empresa
        contractId = 000000000000000000000 #Código adotado pelo Banco para identificar o contrato -númerodo banco(4), códigode agência(4 "sem DV"), número do convênio(12).
        agency = 00000   #Conta com letra substituir-se por zero. Para ordem de pagamento -saque em uma agência -número da agência, caso contrário preencher com zeros.
        agencyDv = 0
        accountNunber = 0000000000000
        accountDv = 0
        agencyAccountDv = 0
        companyName = 0000000000000000000000000000000
        bankName =  0000000000000000000000000000000 #Banco Santander
        filler2 = 0000000000
        remittanceId = 1
        writeFileDate = Date
        writeFileTime = datetime
        fileNumber = 1 #Número sequêncial onde cada novo arquivo adicionado 1.
        layoutVersion = 060
        fileDensity = 00000
        bankspace = " "*20 # Uso Resenvado do banco.
        companyspace = " "*20 # Uso opcional.
        filler = 0000000000000000000
        codeRecurrence = 00000000000 #Ocorrências para ocorrencias_retorno.

    def setTrailerArq(self):
        bankCode = 033
        loteServ = 0000
        registerType = 9
        filler = 000
        numLotes = 0
        numReg = 0
        filler2 = 0

    def defHeaderLote(self): # Conta corrente

    def defTrailerLote(self):

    def defDetalhe(self):
        #define qual registro de detalhe necessário

    def defSegmentoA(self):

        dictionaryA = {"controle_banco": 33 , "controle_lote": , "controle_registro": 3, "sequencial_registro_lote": A , "servico_segmento": , "tipo_movimento": , "codigo_instrucao_movimento": , "codigo_camara_compensacao": , "favorecido_banco": , "favorecido_agencia": , "favorecido_agencia_dv":,
        "favorecido_conta": , "favorecido_conta_dv": , "favorecido_agencia_conta_dv": , "favorecido_nome": , "numero_documento_cliente": , "data_pagamento": , "tipo_moeda": "BRL", "vazio1": , "valor_pagamento": , "numero_documento_banco": , "data_real_pagamento": , "valor_real_pagamento": ,  "mensagem2":,
        "finalidade_doc_ted": ,"vazio2": , "favorecido_emissao_aviso": , "ocorrencias_retorno":  }


    def defSegmentoB(self):
