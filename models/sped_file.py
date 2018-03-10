# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import base64
from sped.efd.icms_ipi.arquivos import ArquivoDigital
from sped.efd.icms_ipi import registros
from sped.efd.icms_ipi.registros import Registro0100
from sped.efd.icms_ipi.registros import Registro0001
from sped.efd.icms_ipi.registros import Registro0005
from sped.efd.icms_ipi.registros import RegistroC001
from sped.efd.icms_ipi.registros import RegistroC100
from sped.efd.icms_ipi.registros import RegistroC101
from sped.efd.icms_ipi.registros import RegistroC170
from sped.efd.icms_ipi.registros import RegistroC190
from sped.efd.icms_ipi.registros import Registro9001
from sped.efd.icms_ipi.registros import RegistroE100
from sped.efd.icms_ipi.registros import RegistroE110
from sped.efd.icms_ipi.registros import RegistroE500
from sped.efd.icms_ipi.registros import RegistroE510
from sped.efd.icms_ipi.registros import RegistroE520
from sped.efd.icms_ipi.registros import Registro1001
from sped.efd.icms_ipi.registros import Registro1010

#from sped.efd.icms_ipi.registros import Registro9900

class SpedFile(models.Model):
    _name = "sped.file"
    _description = "Cria o arquivo para o Sped ICMS / IPI"

    date_start= fields.Date(string='Faturar de')
    date_end = fields.Date(string='Até')
    tipo_arquivo = fields.Selection([
        ('0', 'Remessa do arquivo original'),
        ('1', 'Remessa do arquivo substituto'),
        ], string='Finalidade do Arquivo', default='original')
    log_faturamento = fields.Html('Log de Faturamento')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    sped_file = fields.Binary(string=u"Sped")
    sped_file_name = fields.Char(
        string=u"Arquivo Sped")
    vl_sld_cred_ant_difal = fields.Float('Saldo Credor per. ant. Difal', default=0.0)
    vl_sld_cred_transp_difal = fields.Float('Saldo Credor per. seguinte Difal', default=0.0)
    vl_sld_cred_ant_fcp = fields.Float('Saldo Credor per. ant. FCP', default=0.0)
    vl_sld_cred_transp_fcp = fields.Float('Saldo Credor per. seguinte FCP', default=0.0)

    #arq = ArquivoDigital()
    fatura = 0

    @api.multi
    def create_file(self):
        #global arq
        
        if self.date_start > self.date_end:
            raise UserError('Erro, a data de início é maior que a data de encerramento!')
        num_mes = 1
        self.log_faturamento = 'Gerando arquivo .. <br />'
        if self.date_start and self.date_end:
            d1 = datetime.datetime.strptime(self.date_start, "%Y-%m-%d")
            d2 = datetime.datetime.strptime(self.date_end, "%Y-%m-%d")
            # TODO estou pegando somente NFe emissao propria aqui, 
            # o correto e pegar Emissao Terceiros tbem
            inv = self.env['account.invoice'].search([
                ('date_invoice','>=',self.date_start),
                ('date_invoice','<=',self.date_end),
                ('state','in',['open','paid', 'cancel']),
                ('product_document_id.code', '=', '55'),
                ])
            self.registro0000(inv)
            self.log_faturamento = 'Arquivo gerado com sucesso. <br />'
        return {
            "type": "ir.actions.do_nothing",
        }

    def versao(self):
        #if fields.Datetime.from_string(self.dt_ini) >= datetime.datetime(2018, 1, 1):
        #    return '012'
        return '012'

    def transforma_data(self, data):  # aaaammdd
        data = self.limpa_formatacao(data)
        return data[6:8] + data[4:6] + data[:4]

    def limpa_formatacao(self, data):
        if data:
            replace = ['-', ' ', '(', ')', '/', '.', ':','º']
            for i in replace:
                data = data.replace(i, '')

        return data

    def formata_cod_municipio(self, data):
        return data[:7]

    def junta_pipe(self, registro):
        junta = ''
        for i in range(1, len(registro._valores)):
            junta = junta + '|' + registro._valores[i]
        return junta

    def registro0000(self, inv):
        arq = ArquivoDigital()
        cod_mun = '%s%s' %(self.company_id.state_id.ibge_code, self.company_id.city_id.ibge_code)
        dta_s = '%s%s%s' %(self.date_start[8:10],self.date_start[5:7],self.date_start[:4])
        dta_e = '%s%s%s' %(self.date_end[8:10],self.date_end[5:7],self.date_end[:4])
        arq._registro_abertura.COD_VER = self.versao()
        arq._registro_abertura.COD_FIN = self.tipo_arquivo
        arq._registro_abertura.DT_INI = self.transforma_data(self.date_start)
        arq._registro_abertura.DT_FIN = self.transforma_data(self.date_end)
        arq._registro_abertura.NOME = self.company_id.legal_name
        arq._registro_abertura.CNPJ = self.limpa_formatacao(self.company_id.cnpj_cpf)
        arq._registro_abertura.UF = self.company_id.state_id.code
        arq._registro_abertura.IE = self.limpa_formatacao(self.company_id.inscr_est)
        arq._registro_abertura.COD_MUN = self.formata_cod_municipio(cod_mun)
        arq._registro_abertura.IM = ''
        arq._registro_abertura.SUFRAMA = ''
        arq._registro_abertura.IND_PERFIL = 'A'
        arq._registro_abertura.IND_ATIV = '0'
        reg0001 = Registro0001()
        if inv:
            reg0001.IND_MOV = '0'
        else:
            reg0001.IND_MOV = '1'
        arq._blocos['0'].add(reg0001)
            
        reg0005 = Registro0005()
        reg0005.FANTASIA = self.company_id.name
        reg0005.CEP = self.limpa_formatacao(self.company_id.zip)
        reg0005.END = self.company_id.street
        reg0005.NUM = self.limpa_formatacao(self.company_id.number)
        reg0005.COMPL = self.company_id.street2
        reg0005.BAIRRO = self.company_id.district
        reg0005.FONE = self.limpa_formatacao(self.company_id.phone)
        reg0005.EMAIL = self.company_id.email
        arq._blocos['0'].add(reg0005)            

        contabilista = Registro0100()
        cod_mun = '%s%s' %(self.company_id.accountant_id.state_id.ibge_code, self.company_id.accountant_id.city_id.ibge_code)
        contabilista.NOME = self.company_id.accountant_id.legal_name
        contabilista.CPF = self.limpa_formatacao(self.company_id.accountant_id.cnpj_cpf)
        contabilista.CRC = self.limpa_formatacao(self.company_id.accountant_id.rg_fisica)
        contabilista.END = self.company_id.accountant_id.street
        contabilista.CEP = self.limpa_formatacao(self.company_id.accountant_id.zip)
        contabilista.NUM = self.company_id.accountant_id.number
        contabilista.COMPL = self.company_id.accountant_id.street2
        contabilista.BAIRRO = self.company_id.accountant_id.district
        contabilista.FONE = self.limpa_formatacao(self.company_id.accountant_id.phone)
        #contabilista.FAX = self.company_id.accountant_id.fax
        contabilista.EMAIL = self.company_id.accountant_id.email
        contabilista.COD_MUN = cod_mun

        arq._blocos['0'].add(contabilista)
        
        for item_lista in self.query_registro0150():
            arq.read_registro(self.junta_pipe(item_lista))
            
        for item_lista in self.query_registro0190():
            arq.read_registro(self.junta_pipe(item_lista))

        for item_lista in self.query_registro0200():
            arq.read_registro(self.junta_pipe(item_lista))
            
        for item_lista in self.query_registro0400():
            arq.read_registro(self.junta_pipe(item_lista))

        regC001 = RegistroC001()
        if inv:
            regC001.IND_MOV = '0'
        else:
            regC001.IND_MOV = '1'
        arq._blocos['C'].add(regC001)

        query = """
                    select distinct
                        d.id, d.state, trim(d.nfe_modelo), d.product_document_id 
                    from
                        account_invoice as d
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    where
                        d.date_invoice between '%s' and '%s'
                        and ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid', 'cancel')
                        and d.fiscal_position_id is not null                        
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            if id[2] == '55' and id[1] == 'cancel':
                continue
            #import pudb;pu.db
            self.fatura = id[0]
            #if self.fatura == 222:
            #    import pudb;pu.db
            # TODO C100 - Notas Fiscais - Feito        
            for item_lista in self.query_registroC100(self.fatura):
                arq.read_registro(self.junta_pipe(item_lista))
                # TODO C101 - DIFAL - Feito 
                for item_lista in self.query_registroC101(self.fatura):
                    arq.read_registro(self.junta_pipe(item_lista))

            # TODO C110 - Inf. Adiciontal
               
            # TODO C170 - Itens Nota Fiscal de Compras = Fazendo
            for item_lista in self.query_registroC170(self.fatura):
                arq.read_registro(self.junta_pipe(item_lista))
                        
            # TODO C190 - Totalizacao por CST
            for item_lista in self.query_registroC190(self.fatura):
                arq.read_registro(self.junta_pipe(item_lista))
                
        # TODO BLOCO E - Apuracao ICMS
        # TODO E100 - Periodo Apuracao
        registro_E100 = RegistroE100()
        registro_E100.DT_INI = self.transforma_data(self.date_start)
        registro_E100.DT_FIN = self.transforma_data(self.date_end)
        arq._blocos['E'].add(registro_E100)

        # TODO E110 - Apuracao do ICMS
        for item_lista in self.query_registroE110():
            arq.read_registro(self.junta_pipe(item_lista))
        
        # TODO E300 - DIFAL
        for item_lista in self.query_registroE300():
            arq.read_registro(self.junta_pipe(item_lista))      
            # TODO E310 - DIFAL - Detalhe
            for uf_lista in self.query_registroE310(self.company_id.state_id.code, item_lista.UF):
                arq.read_registro(self.junta_pipe(uf_lista))
        
        # TODO E500 - Apuracao IPI
        registro_E500 = RegistroE500()
        registro_E500.IND_APUR = '0' # 0 - MENSAL 1 - DECENDIAL
        registro_E500.DT_INI = self.transforma_data(self.date_start)
        registro_E500.DT_FIN = self.transforma_data(self.date_end)
        arq._blocos['E'].add(registro_E500)
        

        # TODO E510 - Consolidação IPI
        for item_lista in self.query_registroE510():
            arq.read_registro(self.junta_pipe(item_lista))
        
        # TODO E520 - Apuracao   IPI
        for item_lista in self.query_registroE520():
            arq.read_registro(self.junta_pipe(item_lista))
        
        registro_1001 = Registro1001()
        registro_1001.IND_MOV = '0'
        arq._blocos['1'].add(registro_1001)

        # TODO Colocar no cadastro da Empresa 
        registro_1010 = Registro1010()
        registro_1010.IND_EXP = 'N'
        registro_1010.IND_CCRF = 'N'
        registro_1010.IND_COMB  = 'N'
        registro_1010.IND_USINA = 'N'
        registro_1010.IND_VA = 'N'
        registro_1010.IND_EE = 'N'
        registro_1010.IND_CART = 'N'
        registro_1010.IND_FORM = 'N'
        registro_1010.IND_AER = 'N'
        
        arq._blocos['1'].add(registro_1010)        
        
        #reg9001 = Registro9001()
        #import pudb;pu.db
        #if inv:
        #    reg9001.IND_MOV = '0'
        #else:
        #    reg9001.IND_MOV = '1'
        #arq._blocos['9'].add(reg9001)
        #import pudb;pu.db
        arq.prepare()
        #self.assertEqual(txt, )
        #sped_f = codecs.open(os.path.abspath(), mode='r', encoding='utf-8')
        self.sped_file_name =  "Sped-%s_%s.txt" % (self.date_end[5:7],self.date_end[:4])
        self.sped_file = base64.encodestring(bytes(arq.getstring(), 'utf-8'))
        #self.sped_file = arq.getstring()

    def query_registro0150(self):
        query = """
                    select distinct
                        d.partner_id
                    from
                        account_invoice as d
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    left join
                        invoice_eletronic nf
                            on nf.invoice_id = d.id        
                    where
                        d.date_invoice between '%s' and '%s'                        
                        and ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid', 'cancel')
                        and ((nf.state = 'done') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.fiscal_position_id is not null 
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for id in query_resposta:
            resposta_participante = self.env['res.partner'].browse(id[0])
            registro_0150 = registros.Registro0150()
            registro_0150.COD_PART = str(resposta_participante.id)
            registro_0150.NOME = resposta_participante.legal_name or resposta_participante.name
            registro_0150.COD_PAIS = resposta_participante.country_id.bc_code
            cpnj_cpf = self.limpa_formatacao(resposta_participante.cnpj_cpf)
            if len(cpnj_cpf) == 11:
                registro_0150.CPF = cpnj_cpf
            else:
                registro_0150.CNPJ = cpnj_cpf
            registro_0150.IE = self.limpa_formatacao(resposta_participante.inscr_est)
            cod_mun = '%s%s' %(resposta_participante.state_id.ibge_code, resposta_participante.city_id.ibge_code)
            registro_0150.COD_MUN = self.formata_cod_municipio(cod_mun)
            registro_0150.SUFRAMA = self.limpa_formatacao(resposta_participante.suframa)
            registro_0150.END = resposta_participante.street
            registro_0150.NUM = resposta_participante.number
            registro_0150.COMPL = resposta_participante.street2
            registro_0150.BAIRRO = resposta_participante.district
            lista.append(registro_0150)

        return lista

    def query_registro0190(self):
        query = """
                    select distinct
                        pu.name ,
                        substr(pu.name, 1,6)
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line as det
                            on d.id = det.invoice_id 
                    inner join
                        product_uom pu
                            on pu.id = det.uom_id
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        d.date_invoice between '%s' and '%s' 
                        and ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid', 'cancel')
                        and det.uom_id is not null
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for id in query_resposta:
            resposta = self.env['product.uom'].search([('name','=',id[0])],limit=1)
            if resposta:
                registro_0190 = registros.Registro0190()
                if resposta.name.find('-') != -1:
                    unidade = resposta.name[:resposta.name.find('-')]
                else:
                    unidade = resposta.name
                registro_0190.UNID = unidade[:6]
                registro_0190.DESCR = resposta.description
                lista.append(registro_0190)
        return lista

    def query_registro0200(self):
        query = """
                    select distinct
                        det.product_id
                    from
                        account_invoice as d
                    left join
                        account_invoice_line as det 
                            on d.id = det.invoice_id 
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        d.date_invoice between '%s' and '%s' 
                        and ((d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                """ % (self.date_start, self.date_end)

        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        #hash = {}
        lista = []
        cont = 1
        for resposta in query_resposta:
            resposta_produto = self.env['product.product'].browse(resposta[0])
            if not resposta_produto:
                continue
            #if not (resposta_produto.codigo_unico in hash):
            registro_0200 = registros.Registro0200()
            registro_0200.COD_ITEM = resposta_produto.default_code
            registro_0200.DESCR_ITEM = resposta_produto.name
            registro_0200.COD_BARRA = resposta_produto.barcode
            if resposta_produto.uom_id.name.find('-') != -1:
                unidade = resposta_produto.uom_id.name[:resposta_produto.uom_id.name.find('-')]
            else:
                unidade = resposta_produto.uom_id.name
            registro_0200.UNID_INV = unidade[:6]
            registro_0200.TIPO_ITEM = resposta_produto.type_product
            registro_0200.COD_NCM = self.limpa_formatacao(resposta_produto.fiscal_classification_id.code)
            
            lista.append(registro_0200)

        return lista
        
    def query_registro0400(self):
        query = """
                    select distinct
                        d.fiscal_position_id
                    from
                        account_invoice as d
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        d.date_invoice between '%s' and '%s'                        
                        and ((d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for resposta in query_resposta:
            resposta_nat = self.env['account.fiscal.position'].browse(resposta[0])
            registro_0400 = registros.Registro0400()
            registro_0400.COD_NAT = str(resposta_nat.id)
            registro_0400.DESCR_NAT = resposta_nat.natureza_operacao
            lista.append(registro_0400)
        return lista        

    def transforma_valor(self, valor):
        valor = ("%.2f" % (float(valor)))
        return str(valor).replace('.', ',')

    def query_registroC100(self, fatura):
        lista = []
        resposta = self.env['account.invoice'].browse(self.fatura)
        resposta_nfe = self.env['invoice.eletronic'].search([('invoice_id','=',self.fatura)])
        if (resposta.product_document_id or resposta.state in ['open','paid']) and \
            (resposta.nfe_modelo or resposta.product_document_id.code == '55'):
            # removendo Emissao de Terceiros canceladas
            #if not resposta.product_document_id and resposta.state == 'cancel':
            #    continue
            #if not resposta.nfe_modelo and resposta.product_document_id.code == '55':
            #    if not resposta_nfe:
            #        continue
            if resposta:
                cancel = False 
                registro_c100 = registros.RegistroC100()
                if resposta.fiscal_position_id.fiscal_type == 'entrada':
                    registro_c100.IND_OPER = '0'
                else:
                    registro_c100.IND_OPER = '1'
                if resposta.product_document_id:    
                    registro_c100.IND_EMIT = '0'
                else:
                    registro_c100.IND_EMIT = '1'
                #import pudb;pu.db
                registro_c100.COD_MOD = (resposta.nfe_modelo or resposta.product_document_id.code).zfill(2)
                if not resposta_nfe:
                    registro_c100.COD_SIT = '00'
                elif resposta_nfe.state == 'done':
                    registro_c100.COD_SIT = '00'
                elif resposta_nfe.state == 'cancel':
                    registro_c100.COD_SIT = '02'
                    cancel = True
                if resposta.nfe_serie:
                    registro_c100.SER = resposta.nfe_serie[:3]
                else:
                    registro_c100.SER = resposta.product_serie_id.code
                if resposta.nfe_chave:
                    if len(resposta.nfe_chave) != 44:
                        msg_err = 'Tamanho da Chave NFe invalida - Fatura %s.' %(str(resposta.number or resposta.id))
                        #raise UserError(msg_err)
                        self.log_faturamento += msg_err
                if resposta_nfe.chave_nfe:
                    if len(resposta_nfe.chave_nfe) != 44:
                        msg_err = 'Tamanho da Chave NFe invalida - Fatura %s. <br />' %(str(resposta.number or resposta.id))
                        #raise UserError(msg_err)
                        self.log_faturamento += msg_err
                registro_c100.CHV_NFE = resposta.nfe_chave or resposta_nfe.chave_nfe
                registro_c100.NUM_DOC = self.limpa_formatacao(str(resposta.nfe_num or resposta_nfe.numero))
                if not cancel:
                    try:
                        registro_c100.DT_DOC  = self.transforma_data(resposta.nfe_emissao or 
                            resposta_nfe.data_emissao or resposta.date_invoice)
                        registro_c100.DT_E_S  = self.transforma_data(resposta.nfe_emissao or 
                            resposta_nfe.data_fatura  or resposta.date_invoice)
                    except:
                        msg_err = 'Data Emissao Fatura %s , invalida. <br />' %(str(resposta.number or resposta.id))
                        #raise UserError(msg_err)
                        self.log_faturamento += msg_err
                       
                    if resposta.receivable_move_line_ids:
                        if len(resposta.receivable_move_line_ids) == 1:
                            if resposta.receivable_move_line_ids.date_maturity == resposta.date_invoice:
                                registro_c100.IND_PGTO = '0'
                            else:
                                registro_c100.IND_PGTO = '1'
                        else:
                            registro_c100.IND_PGTO = '1'
                    else:
                        registro_c100.IND_PGTO = '2'

                    registro_c100.VL_MERC = self.transforma_valor(resposta.amount_total)
                    registro_c100.IND_FRT = str(int(resposta.freight_responsibility))
                    registro_c100.VL_FRT = self.transforma_valor(resposta.total_frete)
                    registro_c100.VL_SEG = self.transforma_valor(resposta.total_seguro)
                    desp = 0.0
                    if resposta.total_despesas > 0.0:
                        desp = resposta.total_despesas
                        registro_c100.VL_OUT_DA = self.transforma_valor(resposta.total_despesas)
                    elif resposta.total_despesas < -0.01:
                        desp = resposta.total_despesas
                        registro_c100.VL_DESC = self.transforma_valor(resposta.total_despesas*(-1))
                    registro_c100.VL_DOC  = self.transforma_valor(resposta.total_bruto+desp)
                    registro_c100.VL_BC_ICMS = self.transforma_valor(resposta.icms_base)
                    registro_c100.VL_ICMS = self.transforma_valor(resposta.icms_value)
                    registro_c100.VL_BC_ICMS_ST = self.transforma_valor(resposta.icms_st_base)
                    registro_c100.VL_ICMS_ST = self.transforma_valor(resposta.icms_st_value)
                    registro_c100.VL_IPI = self.transforma_valor(resposta.ipi_value)
                    registro_c100.VL_PIS = self.transforma_valor(resposta.pis_value)
                    registro_c100.VL_COFINS = self.transforma_valor(resposta.cofins_value)
                    registro_c100.COD_PART = str(resposta.partner_id.id)
                    #registro_c100.VL_PIS_ST = 0,0
                    #registro_c100.VL_COFINS_ST = 0.0
                #else:
                #    x = resposta.id
                #    print (x)
                #    print ('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')        
    
                lista.append(registro_c100)

        return lista
                
    def query_registroC101(self, fatura):
        query = """
                    select 
                        sum(d.valor_icms_uf_remet) as icms_uf_remet, 
                        sum(d.valor_icms_uf_dest) as icms_uf_dest,
                        sum(d.valor_icms_fcp_uf_dest) as fcp_uf_dest,
                        fp.fiscal_type 
                    from
                        account_invoice as d
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    where
                        d.id = '%s'
                        and ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                    group by fp.fiscal_type
                """ % (fatura)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            #resposta = self.env['account.invoice'].browse(id[0])
            registro_c101 = registros.RegistroC101()
            registro_c101.VL_FCP_UF_DEST = self.transforma_valor(id[2])
            if id[3] == 'entrada':                
                registro_c101.VL_ICMS_UF_DEST = self.transforma_valor(id[0])
                registro_c101.VL_ICMS_UF_REM = self.transforma_valor(id[1])
            else:
                registro_c101.VL_ICMS_UF_DEST = self.transforma_valor(id[1])
                registro_c101.VL_ICMS_UF_REM = self.transforma_valor(id[0])
                
            lista.append(registro_c101)

        return lista

    def query_registroC170(self, fatura):
        #query = """
        """
                    select distinct
                        d.id
                    from
                        account_invoice as d
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    where
                        d.id = '%s'                        
                        and ((fd.code='55') or (d.nfe_modelo = '55'))
                        and d.state in ('open','paid', 'cancel')
                        and d.fiscal_position_id is not null                        
        #
        #        """ % (fatura)
        #self._cr.execute(query)
        #query_resposta = self._cr.fetchall()
        lista = []
        #cont = 1
        #for id in query_resposta:
        resposta = self.env['account.invoice'].browse(self.fatura)
        r_nfe = self.env['invoice.eletronic'].search([('invoice_id','=',self.fatura)])
        if resposta.fiscal_position_id.fiscal_type == 'entrada' and not r_nfe:
            n_item = 1
            for item in resposta.invoice_line_ids:
                registro_c170 = registros.RegistroC170()
                registro_c170.NUM_ITEM = str(n_item)
                #if item.product_id.default_code == '02805':
                #    import pudb;pu.db
                registro_c170.COD_ITEM = item.product_id.default_code
                registro_c170.DESCR_COMPL = item.name.strip()
                registro_c170.QTD = self.transforma_valor(item.quantity)
                if item.uom_id.name.find('-') != -1:
                    unidade = item.uom_id.name[:item.uom_id.name.find('-')]
                else:
                    unidade = item.uom_id.name
                registro_c170.UNID = unidade[:6]
                #registro_c170.VL_ITEM = self.transforma_valor(item.price_subtotal+item.outras_despesas)
                
                desc = 0.0
                if item.outras_despesas < -0.01:
                    desc = item.outras_despesas*(-1)
                if item.valor_desconto:
                    desc = desc + item.valor_desconto
                registro_c170.VL_DESC = self.transforma_valor(float(desc))
                registro_c170.VL_ITEM = self.transforma_valor(item.valor_bruto-desc)
                if item.cfop_id.code in ['5922', '6922']:
                    registro_c170.IND_MOV = '1'
                else:
                    registro_c170.IND_MOV = '0'
                try:
                    registro_c170.CST_ICMS = item.product_id.origin + item.icms_cst_normal
                except:
                    msg_err = 'Sem CST na Fatura %s. <br />' %(str(resposta.number or resposta.id))
                    #raise UserError(msg_err)
                    self.log_faturamento += msg_err

                registro_c170.CFOP = item.cfop_id.code
                registro_c170.COD_NAT = str(resposta.fiscal_position_id.id)
                registro_c170.VL_BC_ICMS = self.transforma_valor(item.icms_base_calculo)
                if item.tax_icms_id:
                    registro_c170.ALIQ_ICMS = self.transforma_valor(item.tax_icms_id.amount)
                else:
                    registro_c170.ALIQ_ICMS = '0'
                registro_c170.VL_ICMS = self.transforma_valor(item.icms_valor)
                registro_c170.VL_BC_ICMS_ST = self.transforma_valor(item.icms_st_base_calculo)
                if item.tax_icms_st_id:
                    registro_c170.ALIQ_ST = self.transforma_valor(item.tax_icms_st_id.amount)
                registro_c170.VL_ICMS_ST = self.transforma_valor(item.icms_st_valor)
                # TODO incluir na empresa o IND_APUR
                registro_c170.IND_APUR = '0'
                registro_c170.CST_IPI = item.ipi_cst
                #
                # TODO adicionar na Fatura de entrada a opcao de informar o Cod. Enquadramento
                # 
                #if item.fiscal_classification_id.codigo_enquadramento != '999':
                #    registro_c170.COD_ENQ = item.fiscal_classification_id.codigo_enquadramento
                #item_eletronic = self.env['invoice.eletronic.item'].search([('account_invoice_line_id','=', item.id)])
                #if item_eletronic:
                #    import pudb;pu.db
                #registro_c170.COD_ENQ = item_eletronic.codigo_enquadramento_ipi
                registro_c170.VL_BC_IPI = self.transforma_valor(item.ipi_base_calculo)
                if item.tax_ipi_id:
                    registro_c170.ALIQ_IPI = self.transforma_valor(item.tax_ipi_id.amount)
                registro_c170.VL_IPI = self.transforma_valor(item.ipi_valor)
                registro_c170.CST_PIS = item.pis_cst
                registro_c170.VL_BC_PIS = self.transforma_valor(item.pis_base_calculo)
                if item.tax_pis_id:
                    registro_c170.ALIQ_PIS = self.transforma_valor(item.tax_pis_id.amount)
                #registro_c170.QUANT_BC_PIS = self.transforma_valor(
                registro_c170.VL_PIS = self.transforma_valor(item.pis_valor)
                registro_c170.CST_COFINS = item.cofins_cst
                registro_c170.VL_BC_COFINS = self.transforma_valor(item.cofins_base_calculo)
                if item.tax_cofins_id:
                    registro_c170.ALIQ_COFINS = self.transforma_valor(item.tax_pis_id.amount)
                #registro_c170.QUANT_BC_COFINS = self.transforma_valor(
                registro_c170.VL_COFINS = self.transforma_valor(item.cofins_valor)
                #registro_c170.COD_CTA = 
                n_item += 1
           
                lista.append(registro_c170)

        return lista
        
    def query_registroC190(self, fatura):
        query = """
                select distinct
                        pt.origin || dl.icms_cst_normal,
                        cfop.code,
                        COALESCE(at.amount, 0.0) as ALIQUOTA ,
                        sum(dl.price_subtotal+dl.outras_despesas) as VL_OPR,
                        sum(dl.icms_base_calculo) as VL_BC_ICMS,
                        sum(dl.icms_valor) as VL_ICMS,
                        sum(dl.icms_st_base_calculo) as VL_BC_ICMS_ST,
                        sum(dl.icms_st_valor) as VL_ICMS_ST,
                        case when (dl.icms_aliquota_reducao_base > 0) then
                          sum((dl.price_subtotal+dl.outras_despesas)-dl.icms_base_calculo) else 0 end as VL_RED_BC, 
                        sum(dl.ipi_valor) as VL_IPI
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line dl
                            on dl.invoice_id = d.id 
                    left join
                        invoice_eletronic il
                            on il.invoice_id = d.id
                    left join
                        account_tax at
                            on at.id = dl.tax_icms_id
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    inner join
                        br_account_cfop cfop
                            on dl.cfop_id = cfop.id
                    inner join
                        product_product pp
                            on pp.id = dl.product_id
                    inner join
                        product_template pt
                            on pt.id = pp.product_tmpl_id
                    where    
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null
                        and ((il.state is null) or (il.state = 'done'))
                        and d.id = '%s' 
                    group by 
                        dl.icms_aliquota_reducao_base,
                        dl.icms_cst_normal,
                        cfop.code,
                        at.amount,
                        pt.origin 
                    order by 1,2,3    
                """ % (fatura)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_c190 = registros.RegistroC190()
            registro_c190.CST_ICMS = id[0]
            registro_c190.CFOP = id[1]
            registro_c190.ALIQ_ICMS = self.transforma_valor(id[2])
            registro_c190.VL_OPR = self.transforma_valor(id[3])
            registro_c190.VL_BC_ICMS = self.transforma_valor(id[4])
            registro_c190.VL_ICMS = self.transforma_valor(id[5])
            registro_c190.VL_BC_ICMS_ST = self.transforma_valor(id[6])
            registro_c190.VL_ICMS_ST = self.transforma_valor(id[7])
            registro_c190.VL_RED_BC = self.transforma_valor(id[8])
            registro_c190.VL_IPI = self.transforma_valor(id[9])

            lista.append(registro_c190)

        return lista

    def query_registroE110(self):
        query = """
                select  
                    sum(dl.icms_valor) as VL_ICMS 
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line dl
                            on dl.invoice_id = d.id    
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    left join
                        invoice_eletronic as ie
                            on ie.invoice_id = d.id                             
                    inner join
                        br_account_cfop cfop
                            on dl.cfop_id = cfop.id
                    where    
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((ie.state is null) or (ie.state = 'done'))
                        and ((substr(cfop.code, 1,1) in ('5','6','7')) or (cfop.code = '1605'))
                        and d.date_invoice between '%s' and '%s'
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        registro_E110 = RegistroE110()
        sld_transp = 0.0
        for id in query_resposta:
            registro_E110.VL_TOT_DEBITOS = self.transforma_valor(id[0])
            sld_transp = id[0]

        query = """
                select  
                    sum(dl.icms_valor) as VL_ICMS 
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line dl
                            on dl.invoice_id = d.id    
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    left join
                        invoice_eletronic as ie
                            on ie.invoice_id = d.id 
                    inner join
                        br_account_cfop cfop
                            on dl.cfop_id = cfop.id
                    where    
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((ie.state is null) or (ie.state = 'done'))
                        and (((substr(cfop.code, 1,1) in ('1','2','3')) and cfop.code not in ('1605')) or (cfop.code = '5605'))
                        and d.date_invoice between '%s' and '%s'
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        for id in query_resposta:
            registro_E110.VL_TOT_CREDITOS = self.transforma_valor(id[0])
            sld_transp -= id[0]
        if sld_transp < 0.0:
            sld_transp = 0.0

        registro_E110.VL_AJ_DEBITOS = '0'
        registro_E110.VL_TOT_AJ_DEBITOS = '0'
        registro_E110.VL_ESTORNOS_CRED = '0'
        registro_E110.VL_AJ_CREDITOS = '0'
        registro_E110.VL_TOT_AJ_CREDITOS = '0'
        registro_E110.VL_ESTORNOS_DEB = '0'
        registro_E110.VL_SLD_CREDOR_ANT = '0'
        registro_E110.VL_SLD_APURADO = '0'
        registro_E110.VL_TOT_DED = '0'
        registro_E110.VL_ICMS_RECOLHER = '0'
        registro_E110.VL_SLD_CREDOR_TRANSPORTAR = self.transforma_valor(sld_transp)
        registro_E110.DEB_ESP = '0'

        lista.append(registro_E110)
        return lista

    def query_registroE300(self):
        query = """
                    select distinct 
                        rs.code, rp.state_id
                    from
                        account_invoice as d
                    inner join
                        res_partner as rp
                            on rp.id = d.partner_id
                    inner join
                        res_country_state as rs
                            on rs.id = rp.state_id                            
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    where
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and d.date_invoice between '%s' and '%s'
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        uf_emitente = ''
        for id in query_resposta:
            if id[0] == self.company_id.state_id.code:
                uf_emitente = self.company_id.state_id.code
            registro_e300 = registros.RegistroE300()
            registro_e300.UF = self.limpa_formatacao(id[0])
            registro_e300.DT_INI = self.transforma_data(self.date_start)
            registro_e300.DT_FIM = self.transforma_data(self.date_end)
            lista.append(registro_e300)
        if not uf_emitente and query_resposta:
            registro_e300 = registros.RegistroE300()
            registro_e300.UF = self.limpa_formatacao(self.company_id.state_id.code)
            registro_e300.DT_INI = self.transforma_data(self.date_start)
            registro_e300.DT_FIM = self.transforma_data(self.date_end)
            lista.append(registro_e300)

        return lista

    def query_registroE310(self, uf_informante, uf_dif):
        query = """
                    select 
                        sum(d.valor_icms_uf_remet) as icms_uf_remet, 
                        sum(d.valor_icms_uf_dest) as icms_uf_dest,
                        sum(d.valor_icms_fcp_uf_dest) as fcp_uf_dest,
                        fp.fiscal_type
                    from
                        account_invoice as d
                    inner join
                        res_partner as rp
                            on rp.id = d.partner_id
                    inner join
                        res_country_state as rs
                            on rs.id = rp.state_id                                                        
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    where
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                        and d.date_invoice between '%s' and '%s'
                    group by fp.fiscal_type
                """ % (uf_informante, self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        vl_tot_creditos = 0.0
        vl_tot_debitos = 0.0
        tot_fcp_deb = 0.0
        tot_fcp_cred = 0.0
        for id in query_resposta:
            if id[3] == 'entrada':
                tot_fcp_cred += id[2]
            else:
                tot_fcp_deb += id[2]
            if id[1]:
                vl_tot_creditos += id[1]
            if id[0]:
                vl_tot_debitos += id[0]
        #cred_ent = vl_tot_creditos        
        query = """
                    select 
                        sum(d.valor_icms_uf_remet) as icms_uf_remet, 
                        sum(d.valor_icms_uf_dest) as icms_uf_dest,
                        sum(d.valor_icms_fcp_uf_dest) as fcp_uf_dest,
                        fp.fiscal_type
                    from
                        account_invoice as d
                    inner join
                        res_partner as rp
                            on rp.id = d.partner_id
                    inner join
                        res_country_state as rs
                            on rs.id = rp.state_id                                                        
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    where
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                        and d.date_invoice between '%s' and '%s'
                    group by fp.fiscal_type
                """ % (uf_dif, self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        tot_deb_uf_inf = 0.0
        for id in query_resposta:
            if id[3] == 'entrada':
                tot_fcp_cred += id[2]
            else:
                tot_fcp_deb += id[2]
            if id[0]:
                vl_tot_creditos += id[0]
            if id[1]:    
                tot_deb_uf_inf += id[1]
                vl_tot_debitos += id[1]
        #cred_ent += vl_tot_creditos   
        tot_fcp_deb = tot_fcp_deb + tot_fcp_cred                               
        tot_fcp_cred = 0.0
        lista = []
        registro_e310 = registros.RegistroE310()
        sld_ant_difal = vl_tot_debitos - self.vl_sld_cred_ant_difal - vl_tot_creditos
        if sld_ant_difal < 0.0:
            sld_ant_difal = 0.0
        sld_transp_difal = self.vl_sld_cred_ant_difal - vl_tot_debitos + vl_tot_creditos    
        if sld_transp_difal < 0.0:
            sld_transp_difal = 0.0
    
        if not query_resposta:
            registro_e310.IND_MOV_FCP_DIFAL = '0'
            registro_e310.VL_SLD_CRED_ANT_DIFAL = '0'
            registro_e310.VL_TOT_DEBITOS_DIFAL = '0'
            registro_e310.VL_OUT_DEB_DIFAL = '0'
            registro_e310.VL_TOT_DEB_FCP = self.transforma_valor(tot_fcp_deb)
            registro_e310.VL_TOT_CREDITOS_DIFAL = '0'
            registro_e310.VL_TOT_CRED_FCP = self.transforma_valor(tot_fcp_cred)
            registro_e310.VL_OUT_CRED_DIFAL = '0'
            registro_e310.VL_SLD_DEV_ANT_DIFAL = '0'
            registro_e310.VL_DEDUCOES_DIFAL = '0'
            registro_e310.VL_RECOL_DIFAL = '0'
            registro_e310.VL_SLD_CRED_TRANSPORTAR_DIFAL = self.transforma_valor(sld_transp_difal)
            registro_e310.DEB_ESP_DIFAL = '0'
            registro_e310.VL_SLD_CRED_ANT_FCP = '0'
            registro_e310.VL_OUT_DEB_FCP = '0'
            registro_e310.VL_TOT_CRED_FCP = '0'
            registro_e310.VL_OUT_CRED_FCP = '0'
            registro_e310.VL_SLD_DEV_ANT_FCP = '0'
            registro_e310.VL_DEDUCOES_FCP = '0'
            registro_e310.VL_RECOL_FCP = '0'
            registro_e310.VL_SLD_CRED_TRANSPORTAR_FCP = '0'
            registro_e310.DEB_ESP_FCP = '0'
        else:
            registro_e310.IND_MOV_FCP_DIFAL = '1'
            registro_e310.VL_SLD_CRED_ANT_DIFAL = self.transforma_valor(self.vl_sld_cred_ant_difal)
            registro_e310.VL_TOT_DEBITOS_DIFAL = self.transforma_valor(vl_tot_debitos)
            registro_e310.VL_OUT_DEB_DIFAL = '0'
            registro_e310.VL_TOT_DEB_FCP = self.transforma_valor(tot_fcp_deb)
            registro_e310.VL_TOT_CREDITOS_DIFAL = self.transforma_valor(vl_tot_creditos)
            registro_e310.VL_TOT_CRED_FCP = self.transforma_valor(tot_fcp_cred)
            registro_e310.VL_OUT_CRED_DIFAL = '0'
            registro_e310.VL_SLD_DEV_ANT_DIFAL = self.transforma_valor(sld_ant_difal)
            registro_e310.VL_DEDUCOES_DIFAL = '0'
            registro_e310.VL_RECOL_DIFAL = '0'
            registro_e310.VL_SLD_CRED_TRANSPORTAR_DIFAL = self.transforma_valor(sld_transp_difal)
            registro_e310.DEB_ESP_DIFAL = '0'
            registro_e310.VL_SLD_CRED_ANT_FCP = '0'
            registro_e310.VL_OUT_DEB_FCP = '0'
            registro_e310.VL_TOT_CRED_FCP = '0'
            registro_e310.VL_OUT_CRED_FCP = '0'
            registro_e310.VL_SLD_DEV_ANT_FCP = '0'
            registro_e310.VL_DEDUCOES_FCP = '0'
            registro_e310.VL_RECOL_FCP = '0'
            registro_e310.VL_SLD_CRED_TRANSPORTAR_FCP = '0'
            registro_e310.DEB_ESP_FCP = '0'             
                
        lista.append(registro_e310)

        return lista

    def query_registroE510(self):
        query = """
                select distinct
                        dl.ipi_cst,
                        cfop.code,
                        sum(dl.ipi_base_calculo) as VL_BC_IPI,
                        sum(dl.ipi_valor) as VL_IPI
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line dl
                            on dl.invoice_id = d.id    
                    left join
                        account_tax at
                            on at.id = dl.tax_icms_id
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    inner join
                        br_account_cfop cfop
                            on dl.cfop_id = cfop.id
                    where    
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and d.date_invoice between '%s' and '%s'
                    group by dl.ipi_cst,
                        cfop.code
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_E510 = RegistroE510()
            registro_E510.CFOP = str(id[1])
            registro_E510.CST_IPI = str(id[0])
            registro_E510.VL_CONT_IPI = '0'
            registro_E510.VL_BC_IPI = self.transforma_valor(id[2])
            registro_E510.VL_IPI = self.transforma_valor(id[3])
            lista.append(registro_E510)
        return lista

    def query_registroE520(self):
        query = """
                select 
                       sum(dl.ipi_valor) as VL_IPI
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line dl
                            on dl.invoice_id = d.id    
                    left join
                        account_tax at
                            on at.id = dl.tax_icms_id
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    inner join
                        br_account_cfop cfop
                            on dl.cfop_id = cfop.id
                    where    
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and substr(cfop.code, 1,1) in ('5','6')
                        and d.date_invoice between '%s' and '%s'
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        registro_E520 = RegistroE520()
        for id in query_resposta:
            registro_E520.VL_DEB_IPI = self.transforma_valor(id[0])
        registro_E520.VL_SD_ANT_IPI = '0'            
        registro_E520.VL_OD_IPI = '0'
        registro_E520.VL_OC_IPI = '0'
        registro_E520.VL_SC_IPI = '0'
        registro_E520.VL_SD_IPI = '0'

        query = """
                select 
                       sum(dl.ipi_valor) as VL_IPI
                    from
                        account_invoice as d
                    inner join
                        account_invoice_line dl
                            on dl.invoice_id = d.id    
                    left join
                        account_tax at
                            on at.id = dl.tax_icms_id
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    inner join 
                        account_fiscal_position fp 
                            on d.fiscal_position_id = fp.id
                    inner join
                        br_account_cfop cfop
                            on dl.cfop_id = cfop.id
                    where    
                        ((fd.code='55') or (d.nfe_modelo = '55') or (d.nfe_modelo = '1'))
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and substr(cfop.code, 1,1) in ('1','2','3')
                        and d.date_invoice between '%s' and '%s'
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        for id in query_resposta:            
            registro_E520.VL_CRED_IPI = self.transforma_valor(id[0])            
        lista.append(registro_E520)
        return lista
