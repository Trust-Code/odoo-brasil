# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from unicodedata import normalize 
import datetime
from datetime import timedelta
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
from sped.efd.icms_ipi.registros import RegistroD001
from sped.efd.icms_ipi.registros import RegistroD100
from sped.efd.icms_ipi.registros import RegistroD110
from sped.efd.icms_ipi.registros import RegistroD120
from sped.efd.icms_ipi.registros import RegistroD190
from sped.efd.icms_ipi.registros import Registro9001
from sped.efd.icms_ipi.registros import RegistroE100
from sped.efd.icms_ipi.registros import RegistroE110
from sped.efd.icms_ipi.registros import RegistroE200
from sped.efd.icms_ipi.registros import RegistroE210
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
    data_vencimento_e316 = fields.Date(string='Vencimento E-316')
    cod_obrigacao = fields.Char(
        string=u"Código Obrigação", dafault='090')
    cod_receita = fields.Char(
        string=u"Código Receita", default='100102')
        
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

    def normalize_str(self, string):
        """
        Remove special characters and strip spaces
        """
        if string:
            if not isinstance(string, str):
                string = str(string, 'utf-8', 'replace')

            string = string.encode('utf-8')
            return normalize(
                'NFKD', string.decode('utf-8')).encode('ASCII', 'ignore').decode()
        return ''

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
        dt = data
        if len(data) > 10:
            data = datetime.datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
            dt = data + timedelta(hours=-3)
            dt = datetime.datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')
        data = self.limpa_formatacao(dt)
        return data[6:8] + data[4:6] + data[:4]

    def limpa_caracteres(self, data):
        if data:
            replace = ['|']
            for i in replace:
                data = data.replace(i, ' ')
        return data

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
            # 0205 - ALTERACAO NO ITEM
            for item_alt in self.query_registro0205(item_lista.COD_ITEM):
                arq.read_registro(self.junta_pipe(item_alt))
            # 0220 - Conversão Unidade Medida
            for item_unit in self.query_registro0220(item_lista.COD_ITEM):            
                arq.read_registro(self.junta_pipe(item_unit))
            
            
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
                        d.id, d.state, ie.emissao_doc, d.product_document_id 
                    from
                        account_invoice as d
                    inner join
                        invoice_eletronic as ie
                            on ie.invoice_id = d.id
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    where
                        ie.data_emissao between '%s' and '%s'
                        and (fd.code in ('55','01'))
                        and ie.state in ('done', 'cancel')
                        and d.fiscal_position_id is not null                        
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            if id[2] == '2' and id[1] == 'cancel':
                continue
            self.fatura = id[0]
            #if self.fatura == 222:
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
                
        # TODO BLOCO D - prestações ou contratações de serviços 
        # de comunicação, transporte interestadual e intermunicipa
        # TODO D100 - Periodo Apuracao

        query = """
                    select distinct
                        d.id, d.state, d.product_document_id 
                    from
                        account_invoice as d
                    inner join
                        invoice_eletronic as ie
                            on ie.invoice_id = d.id
                    left join     
                        br_account_fiscal_document fd
                            on fd.id = d.product_document_id  
                    where
                        ie.data_emissao between '%s' and '%s'
                        and (fd.code in ('57','67'))
                        and ie.state = 'done'
                        and d.fiscal_position_id is not null                        
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1

        registro_D001 = RegistroD001()
        if query_resposta:
            registro_D001.IND_MOV = '0'
        else:
            registro_D001.IND_MOV = '1'
        arq._blocos['D'].add(registro_D001)

        resposta_cte = self.env['invoice.eletronic'].search([
            ('model','in',('57','67')),
            ('state', '=','done'),
            ('data_emissao','>=',self.date_start),
            ('data_emissao','<=',self.date_end),
            ])
        for cte in resposta_cte:
            # TODO D100 - Documentos Transporte
            for item_lista in self.query_registroD100(cte.invoice_id.id):
                arq.read_registro(self.junta_pipe(item_lista))
                
            # TODO D190 - Totalizacao por CST
            for item_lista in self.query_registroD190(cte.invoice_id.id):
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

        # TODO E200 - Apuracao do ICMS ST
        for item_lista in self.query_registroE200():
            arq.read_registro(self.junta_pipe(item_lista))
            # TODO E200 - Apuracao do ICMS ST Valor
            for item in self.query_registroE210(item_lista.UF):
                arq.read_registro(self.junta_pipe(item))

        
        # TODO E300 - DIFAL
        for item_lista in self.query_registroE300():
            arq.read_registro(self.junta_pipe(item_lista))      
            # TODO E310 - DIFAL - Detalhe
            for uf_lista in self.query_registroE310(self.company_id.state_id.code, item_lista.UF):
                arq.read_registro(self.junta_pipe(uf_lista))
            # TODO E316 - DIFAL - Detalhe
            for uf_lista in self.query_registroE316(self.company_id.state_id.code, item_lista.UF):
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
        #if inv:
        #    reg9001.IND_MOV = '0'
        #else:
        #    reg9001.IND_MOV = '1'
        #arq._blocos['9'].add(reg9001)
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
                    inner join
                        invoice_eletronic nf
                            on nf.invoice_id = d.id        
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        nf.data_emissao between '%s' and '%s'       
                        and (fd.code in ('55','01','57','67'))
                        and d.state in ('open','paid', 'cancel')
                        and ((nf.state = 'done') or (nf.state = 'cancel'))
                        and d.fiscal_position_id is not null 
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for id in query_resposta:
            resposta_participante = self.env['res.partner'].browse(id[0])
            registro_0150 = registros.Registro0150()
            registro_0150.COD_PART = str(resposta_participante.id)
            registro_0150.NOME = self.normalize_str(resposta_participante.legal_name or resposta_participante.name) 
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
            registro_0150.END = self.normalize_str(resposta_participante.street)
            registro_0150.NUM = resposta_participante.number
            registro_0150.COMPL = self.normalize_str(resposta_participante.street2)
            registro_0150.BAIRRO = self.normalize_str(resposta_participante.district)
            lista.append(registro_0150)

        return lista

    def query_registro0190(self):
        query = """
                    select distinct
                        substr(UPPER(pu.name), 1,6)
                        , UPPER(pu.description)
                    from
                        account_invoice as d
                    inner join
                        invoice_eletronic as ie
                            on d.id = ie.invoice_id 
                    inner join
                        invoice_eletronic_item as det
                            on ie.id = det.invoice_eletronic_id 
                    inner join
                        product_uom pu
                            on pu.id = det.uom_id
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        ie.data_emissao between '%s' and '%s' 
                        and (fd.code in ('55','01'))
                        and ie.state = 'done'
                        and det.uom_id is not null
                    order by 2
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for id in query_resposta:
            #resposta = self.env['product.uom'].search([('name','=',id[0])],limit=1)
            #if resposta:
            registro_0190 = registros.Registro0190()
            if id[0].find('-') != -1:
                unidade = id[0][:id[0].find('-')]
            else:
                unidade = id[0]
            registro_0190.UNID = self.normalize_str(unidade[:6])
            registro_0190.DESCR = self.normalize_str(id[1])
            lista.append(registro_0190)
        return lista

    def query_registro0200(self):
        query = """
                    select distinct
                        det.product_id
                    from
                        account_invoice as d
                    inner join 
                        invoice_eletronic as ie
                            on ie.invoice_id = d.id
                    left join
                        account_invoice_line as det 
                            on d.id = det.invoice_id 
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        d.date_invoice between '%s' and '%s' 
                        and (fd.code in ('55','01'))
                        and ie.emissao_doc = '2'
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
            registro_0200.DESCR_ITEM = self.normalize_str(resposta_produto.name.strip())
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

    def query_registro0205(self, item):
        lista = []
        resposta_produto = self.env['product.template.sped'].search([
            ('product_id.default_code','=',item),
            ('date_change', '>=', self.date_start),
            ('date_change', '<=', self.date_end)
            ],limit=1,order='date_change desc')
        # 0205 - Alteracao no Item
        ultima_alteracao = self.date_start
        for alterado in resposta_produto:
            ultima_mudanca = self.env['product.template.sped'].search([
                ('product_id.default_code','=',item),
                ('date_change', '<', ultima_alteracao)
                ],limit=1,order='date_change desc')
            if ultima_mudanca:
                data_inicio = ultima_mudanca.date_change
            else:
                data_inicio = alterado.product_id.create_date    
            registro_0205 = registros.Registro0205()
            if alterado.name == 'Descrição':
                registro_0205.DESCR_ANT_ITEM = self.normalize_str(alterado.valor_anterior.strip())
                registro_0205.DT_INI = self.transforma_data(data_inicio)
                registro_0205.DT_FIM = self.transforma_data(alterado.date_change)
                registro_0205.COD_ANT_ITEM = ''
            if alterado.name == 'Código':
                registro_0205.DESCR_ANT_ITEM = ''
                registro_0205.DT_INI = self.transforma_data(data_inicio)
                registro_0205.DT_FIM = self.transforma_data(alterado.date_change)
                registro_0205.COD_ANT_ITEM = alterado.valor_anterior
            ultima_alteracao = alterado.date_change    
            lista.append(registro_0205)

        return lista

    def query_registro0220(self, ITEM):
        query = """
            select distinct
                   sum(dl.quantity) as fatura
                   ,sum(det.quantidade) as xml
                   ,UPPER(TRIM(pu.name))
                   ,det.product_id
                   ,UPPER(TRIM(uom_edoc.name))
                    from
                        invoice_eletronic as d                
                    inner join
                        invoice_eletronic_item as det
                            on d.id = det.invoice_eletronic_id
                    inner join 
                        account_invoice_line as dl
                            on dl.invoice_id = d.invoice_id
                            and dl.product_id = det.product_id
                    inner join
                        product_product p
                            on p.id = det.product_id
                    inner join
                        product_template pt
                            on p.product_tmpl_id = pt.id                            
                    inner join
                        product_uom pu
                            on pu.id = pt.uom_id
                    inner join
                        product_uom as uom_edoc
                            on uom_edoc.id = det.uom_id
                            
                    where
                        d.data_emissao between '%s' and '%s'
                        and (d.model in ('55','01'))
                        and d.state = 'done'
                        and d.emissao_doc = '2' 
                        and UPPER(TRIM(pu.name)) <> UPPER(TRIM(uom_edoc.name))
                        and p.default_code = '%s'
                        group by  det.product_id ,pu.name,uom_edoc.name                                 
                """ % (self.date_start, self.date_end, ITEM)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for resposta in query_resposta:
            registro_0220 = registros.Registro0220()
            conversao = 0.0
            if resposta[1] > 0.0:
                conversao = resposta[0]/resposta[1]
            registro_0220.UNID_CONV = str(resposta[4])
            registro_0220.FAT_CONV = self.transforma_valor(conversao)
            lista.append(registro_0220)
        return lista
        
    def query_registro0400(self):
        query = """
                    select distinct
                        d.fiscal_position_id
                    from
                        account_invoice as d
                    inner join
                        invoice_eletronic as ie
                            on ie.invoice_id = d.id
                    left join     
                        br_account_fiscal_document fd 
                            on fd.id = d.product_document_id
                    where
                        ie.data_emissao between '%s' and '%s'                        
                        and (ie.model in ('55','01'))
                        and ie.emissao_doc = '2'
                        and ie.state in ('done','cancel')
                        and d.fiscal_position_id is not null 
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for resposta in query_resposta:
            resposta_nat = self.env['account.fiscal.position'].browse(resposta[0])
            registro_0400 = registros.Registro0400()
            registro_0400.COD_NAT = str(resposta_nat.id)
            registro_0400.DESCR_NAT = self.normalize_str(resposta_nat.natureza_operacao)
            lista.append(registro_0400)
        return lista        

    def transforma_valor(self, valor):
        valor = ("%.2f" % (float(valor)))
        return str(valor).replace('.', ',')

    def query_registroC100(self, fatura):
        lista = []
        resposta = self.env['account.invoice'].browse(self.fatura)
        resposta_nfe = self.env['invoice.eletronic'].search([('invoice_id','=',self.fatura)])
        if (resposta.product_document_id or resposta.state in ['open','paid','cancel']) and \
            (resposta.product_document_id.code == '55'):
            # removendo Emissao de Terceiros canceladas
            if resposta_nfe.emissao_doc == '2' and resposta.state == 'cancel':
                 return True
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
                if resposta_nfe.emissao_doc == '1':    
                    registro_c100.IND_EMIT = '0'
                else:
                    registro_c100.IND_EMIT = '1'
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
                #if resposta_nfe.numero == 487769:
                #    import pudb;pu.db
                registro_c100.NUM_DOC = self.limpa_formatacao(str(resposta_nfe.numero))
                if not cancel:
                    try:
                        registro_c100.DT_DOC  = self.transforma_data( 
                            resposta_nfe.data_emissao)
                        registro_c100.DT_E_S  = self.transforma_data( 
                            resposta_nfe.data_fatura)
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

                    registro_c100.VL_MERC = self.transforma_valor(resposta.total_bruto)
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
                        and (fd.code='55')
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
                        and (fd.code='55')
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
        if r_nfe.emissao_doc == '2':
            n_item = 1
            for item in r_nfe.eletronic_item_ids:
                registro_c170 = registros.RegistroC170()
                #registro_c170.NUM_ITEM = str(n_item)
                registro_c170.NUM_ITEM = str(item.num_item or n_item) # str(item.num_item_xml or n_item)
                #if item.product_id.default_code == '02805':
                registro_c170.COD_ITEM = item.product_id.default_code
                registro_c170.DESCR_COMPL = self.normalize_str(self.limpa_caracteres(item.name.strip()))
                #if item.product_qty_xml:
                #    registro_c170.QTD = self.transforma_valor(item.product_qty_xml)
                #else:
                registro_c170.QTD = self.transforma_valor(item.quantidade)
                if item.uom_id.name.find('-') != -1:
                    unidade = item.uom_id.name[:item.uom_id.name.find('-')]
                else:
                    unidade = item.uom_id.name
                registro_c170.UNID = unidade[:6]
                #registro_c170.VL_ITEM = self.transforma_valor(item.price_subtotal+item.outras_despesas)
                
                desc = 0.0
                if item.outras_despesas < -0.01:
                    desc = item.outras_despesas*(-1)
                if item.desconto:
                    desc = desc + item.desconto
                registro_c170.VL_DESC = self.transforma_valor(float(desc))
                registro_c170.VL_ITEM = self.transforma_valor(item.valor_bruto-desc)
                if item.cfop in ['5922', '6922']:
                    registro_c170.IND_MOV = '1'
                else:
                    registro_c170.IND_MOV = '0'
                try:
                    registro_c170.CST_ICMS = item.product_id.origin + item.icms_cst
                except:
                    msg_err = 'Sem CST na Fatura %s. <br />' %(str(resposta.number or resposta.id))
                    #raise UserError(msg_err)
                    self.log_faturamento += msg_err

                registro_c170.CFOP = str(item.cfop)
                registro_c170.COD_NAT = str(resposta.fiscal_position_id.id)
                registro_c170.VL_BC_ICMS = self.transforma_valor(item.icms_base_calculo)
                if item.icms_aliquota:
                    registro_c170.ALIQ_ICMS = self.transforma_valor(item.icms_aliquota)
                else:
                    registro_c170.ALIQ_ICMS = '0'
                registro_c170.VL_ICMS = self.transforma_valor(item.icms_valor)
                registro_c170.VL_BC_ICMS_ST = self.transforma_valor(item.icms_st_base_calculo)
                if item.icms_st_aliquota:
                    registro_c170.ALIQ_ST = self.transforma_valor(item.icms_st_aliquota)
                registro_c170.VL_ICMS_ST = self.transforma_valor(item.icms_st_valor)
                # TODO incluir na empresa o IND_APUR
                registro_c170.IND_APUR = '0'
                registro_c170.CST_IPI = item.ipi_cst
                #if item.codigo_enquadramento_ipi:
                #    registro_c170.COD_ENQ = item.codigo_enquadramento_ipi
                #elif item.fiscal_classification_id.codigo_enquadramento != '999':
                #    registro_c170.COD_ENQ = item.fiscal_classification_id.codigo_enquadramento
                registro_c170.VL_BC_IPI = self.transforma_valor(item.ipi_base_calculo)
                if item.ipi_aliquota:
                    registro_c170.ALIQ_IPI = self.transforma_valor(item.ipi_aliquota)
                registro_c170.VL_IPI = self.transforma_valor(item.ipi_valor)
                registro_c170.CST_PIS = item.pis_cst
                registro_c170.VL_BC_PIS = self.transforma_valor(item.pis_base_calculo)
                if item.pis_aliquota:
                    registro_c170.ALIQ_PIS = self.transforma_valor(item.pis_aliquota)
                #registro_c170.QUANT_BC_PIS = self.transforma_valor(
                registro_c170.VL_PIS = self.transforma_valor(item.pis_valor)
                registro_c170.CST_COFINS = item.cofins_cst
                registro_c170.VL_BC_COFINS = self.transforma_valor(item.cofins_base_calculo)
                if item.cofins_aliquota:
                    registro_c170.ALIQ_COFINS = self.transforma_valor(item.cofins_aliquota)
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
                        (fd.code='55')
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

    # transporte
    def query_registroD100(self, fatura):
        lista = []
        resposta_cte = self.env['account.invoice'].browse(fatura)
        for resposta in resposta_cte:
            cte = self.env['invoice.eletronic'].search([('invoice_id','=',fatura)])
            registro_d100 = registros.RegistroD100()
            registro_d100.IND_OPER = '0' # Aquisicao
            registro_d100.IND_EMIT = '1' # Terceiros
            registro_d100.COD_PART = str(resposta.partner_id.id)
            registro_d100.COD_MOD = str(resposta.nfe_modelo)  # or resposta_nfe.product_document_id.code).zfill(2)
            registro_d100.COD_SIT = '00'
            registro_d100.SER = resposta.nfe_serie[:3] # resposta.product_serie_id.code
            if resposta.nfe_chave:
                if len(resposta.nfe_chave) != 44:
                    msg_err = 'Tamanho da Chave NFe invalida - Fatura %s.' %(str(resposta.number or resposta.id))
                    #raise UserError(msg_err)
                    self.log_faturamento += msg_err
            registro_d100.CHV_CTE = str(resposta.nfe_chave) # or resposta_nfe.chave_nfe
            registro_d100.NUM_DOC = self.limpa_formatacao(str(cte.numero)) # or resposta_nfe.numero))
            registro_d100.DT_A_P = self.transforma_data(cte.data_fatura or resposta.date_invoice)
            registro_d100.DT_DOC = self.transforma_data(cte.data_emissao or resposta.date_invoice)
            #registro_d100.TP_CT-e = '0' # NORMAL
            registro_d100.VL_DOC = self.transforma_valor(resposta.amount_total)
            registro_d100.VL_DESC = self.transforma_valor(resposta.total_desconto)
            registro_d100.IND_FRT = '1' # Destinatario
            registro_d100.VL_SERV = self.transforma_valor(resposta.amount_total)
            registro_d100.VL_BC_ICMS = self.transforma_valor(resposta.icms_base)
            registro_d100.VL_ICMS = self.transforma_valor(resposta.icms_value)
            registro_d100.VL_NT = '0'
            registro_d100.COD_INF = ''
            registro_d100.COD_MUN_ORIG = cte.cod_mun_ini
            registro_d100.COD_MUN_DEST = cte.cod_mun_fim
            lista.append(registro_d100)

        return lista

    """ SOMENTE DE SAIDA    
    # transporte - detalhe
    def query_registroD110(self, fatura):
        lista = []
        resposta = self.env['account.invoice'].search([
            ('nfe_modelo','in',('57','67')),
            ('state', 'in',('open','paid'))
            ])
        item = 1    
        for itens in resposta.invoice_line_ids:
            registro_d110 = registros.RegistroD110()
            registro_d110.NUM_ITEM = str(item) # 
            registro_d110.COD_ITEM = itens.product_id.default_code # Terceiros
            registro_d110.VL_SERV = self.transforma_valor(itens.price_subtotal)
            registro_d110.VL_OUT = '0'
            item += 1

    # transporte - complemento
    def query_registroD120(self, fatura):
        lista = []
        resposta = self.env['account.invoice'].search([
            ('nfe_modelo','in',('57','67')),
            ('state', 'in',('open','paid'))
            ])
        item = 1    
        for itens in resposta.invoice_line_ids:
            registro_d110 = registros.RegistroD110()
            registro_d110.NUM_ITEM = str(item) # 
            registro_d110.COD_ITEM = itens.product_id.default_code # Terceiros
            registro_d110.VL_SERV = self.transforma_valor(itens.price_subtotal)
            registro_d110.VL_OUT = '0'
            item += 1
    """        

    # transporte - analitico
    def query_registroD190(self, fatura):
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
                        fd.code in ('57','67')
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
            registro_d190 = registros.RegistroD190()
            registro_d190.CST_ICMS = id[0]
            registro_d190.CFOP = id[1]
            registro_d190.ALIQ_ICMS = self.transforma_valor(id[2])
            registro_d190.VL_OPR = self.transforma_valor(id[3])
            registro_d190.VL_BC_ICMS = self.transforma_valor(id[4])
            registro_d190.VL_ICMS = self.transforma_valor(id[5])
            registro_d190.VL_RED_BC = self.transforma_valor(id[8])
            registro_d190.COD_OBS = ''

            lista.append(registro_d190)

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
                        (fd.code in ('55','1','57','67'))
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
                        (fd.code in ('55','1','57','67'))
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
        if sld_transp > 0.0:
            sld_transp = 0.0
        else:
            sld_transp = sld_transp * (-1)

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

    def query_registroE200(self):
        query = """
                select distinct
                        rs.code
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
                        res_partner rp
                            on rp.id = d.partner_id
                    inner join 
                        res_country_state rs
                            on rs.id = rp.state_id                                                        
                    where    
                        (fd.code='55')
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null
                        and ((il.state is null) or (il.state = 'done'))
                        and dl.icms_st_valor > 0
                        and d.date_invoice between '%s' and '%s'
                """ % (self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_e200 = registros.RegistroE200()
            registro_e200.DT_INI = self.transforma_data(self.date_start)
            registro_e200.DT_FIN = self.transforma_data(self.date_end)
            registro_e200.UF = str(id[0])

            lista.append(registro_e200)

        return lista

    def query_registroE210(self, uf):
        query = """
                select sum(dl.icms_st_valor),
                      sum(dl.icms_st_base_calculo)
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
                        res_partner rp
                            on rp.id = d.partner_id
                    inner join 
                        res_country_state rs
                            on rs.id = rp.state_id                                                        
                    where    
                        (fd.code='55')
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null
                        and ((il.state is null) or (il.state = 'done'))
                        and dl.icms_st_valor > 0
                        and rs.code = '%s'
                        and d.date_invoice between '%s' and '%s'
                """ % (uf, self.date_start, self.date_end)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_e210 = registros.RegistroE210()
            registro_e210.IND_MOV_ST = '1'
            registro_e210.VL_ICMS_RECOL_ST = self.transforma_valor(id[0])
            registro_e210.VL_RETENÇAO_ST = self.transforma_valor(id[0])
            registro_e210.VL_SLD_CRED_ANT_ST = '0'
            registro_e210.VL_DEVOL_ST = '0'
            registro_e210.VL_RESSARC_ST = '0'
            registro_e210.VL_OUT_CRED_ST = '0'
            registro_e210.VL_AJ_CREDITOS_ST = '0'
            registro_e210.VL_OUT_DEB_ST = '0'
            registro_e210.VL_AJ_DEBITOS_ST = '0'
            registro_e210.VL_SLD_DEV_ANT_ST = self.transforma_valor(id[0])
            registro_e210.VL_DEDUÇÕES_ST = '0'
            registro_e210.VL_SLD_CRED_ST_TRANSPORTAR = '0'
            registro_e210.DEB_ESP_ST = '0'
            lista.append(registro_e210)

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
                        (fd.code='55')
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
        if uf_informante != uf_dif:
            tipo_mov = '1'
            query = """
                    select 
                        sum(d.valor_icms_uf_dest) as icms_uf_dest,
                        0,
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
                        (fd.code='55')
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                        and d.date_invoice between '%s' and '%s'
                    group by fp.fiscal_type
                """ % (uf_dif, self.date_start, self.date_end)
        else:   
            # mesmo uf
            tipo_mov = '0'
            query = """
                    select 
                        sum(d.valor_icms_uf_remet) as icms_uf_remet,
                        0, 
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
                        (fd.code='55')
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and d.date_invoice between '%s' and '%s'
                    group by fp.fiscal_type
                """ % (self.date_start, self.date_end)
               
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        registro_e310 = registros.RegistroE310()
        lista = []
        for id in query_resposta:
            registro_e310.IND_MOV_FCP_DIFAL = tipo_mov
            registro_e310.VL_SLD_CRED_ANT_DIFAL = self.transforma_valor(self.vl_sld_cred_ant_difal)
            registro_e310.VL_TOT_DEBITOS_DIFAL = self.transforma_valor(id[0])
            registro_e310.VL_OUT_DEB_DIFAL = '0'
            registro_e310.VL_TOT_DEB_FCP = self.transforma_valor(id[2])            
            registro_e310.VL_TOT_CREDITOS_DIFAL = '0'
            registro_e310.VL_TOT_CRED_FCP = '0'
            registro_e310.VL_OUT_CRED_DIFAL = '0'
            registro_e310.VL_SLD_DEV_ANT_DIFAL = self.transforma_valor(id[0])
            registro_e310.VL_DEDUCOES_DIFAL = '0'
            registro_e310.VL_RECOL_DIFAL = self.transforma_valor(id[0])
            registro_e310.VL_SLD_CRED_TRANSPORTAR_DIFAL = '0'
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

    def query_registroE316(self, uf_informante, uf_dif):
        if uf_informante != uf_dif:
            tipo_mov = '1'
            query = """
                    select 
                        sum(d.valor_icms_uf_dest) as icms_uf_dest,
                        0,
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
                        (fd.code='55')
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                        and d.date_invoice between '%s' and '%s'
                    group by fp.fiscal_type
                """ % (uf_dif, self.date_start, self.date_end)
        else:   
            # mesmo uf
            tipo_mov = '0'
            query = """
                    select 
                        sum(d.valor_icms_uf_remet) as icms_uf_remet,
                        0, 
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
                        (fd.code='55')
                        and d.state in ('open','paid')
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and d.date_invoice between '%s' and '%s'
                    group by fp.fiscal_type
                """ % (self.date_start, self.date_end)
               
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        registro_e316 = registros.RegistroE316()
        lista = []
        data = self.transforma_data(self.data_vencimento_e316)
        data = data[2:4] + data[4:8]
        
        for id in query_resposta:
            registro_e316.COD_OR = self.cod_obrigacao
            registro_e316.VL_OR = self.transforma_valor(id[0]+id[2])
            registro_e316.DT_VCTO = self.transforma_data(self.data_vencimento_e316)
            registro_e316.COD_REC = self.cod_receita
            registro_e316.NUM_PROC = ''
            registro_e316.IND_PROC = ''
            registro_e316.PROC = ''
            registro_e316.TXT_COMPL = ''
            registro_e316.MES_REF = data
            
        lista.append(registro_e316)
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
                        (fd.code='55')
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
                        (fd.code='55')
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
                        (fd.code='55')
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
