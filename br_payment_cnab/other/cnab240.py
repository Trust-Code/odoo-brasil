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

    def setTrailerArq(self):
        BankCode = 033
        LoteServ = 000
        filler =000
        numLotes = 0
        numReg = 0
        filler2=0


    def defHeaderLote(self):

    def defTrailerLote(self):

    def defDetalhe(self):
        #define qual registro de detalhe necessário

    def defSegmentoA(self):
        # dictionaryA = {"controle_banco": 33 , "controle_lote": , "controle_registro": 3, "sequencial_registro_lote": A , "servico_segmento": , "tipo_movimento": , "codigo_instrucao_movimento": , "codigo_camara_compensacao": , "favorecido_banco": , "favorecido_agencia": , "favorecido_agencia_dv":,
        #     "favorecido_conta": , "favorecido_conta_dv": , "favorecido_agencia_conta_dv": , "favorecido_nome": , "numero_documento_cliente": , "data_pagamento": , "tipo_moeda": "BRL", "vazio1": , "valor_pagamento": , "numero_documento_banco": , "data_real_pagamento": , "valor_real_pagamento": ,  "mensagem2":,
        #     "finalidade_doc_ted": ,"vazio2": , "favorecido_emissao_aviso": , "ocorrencias_retorno":  }


    def defSegmentoB(self):
