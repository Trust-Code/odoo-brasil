# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from unidecode import unidecode
from datetime import datetime, timedelta
import pytz
import base64
try:
    from sped.efd.pis_cofins.arquivos import ArquivoDigital
    from sped.efd.pis_cofins import registros
    from sped.efd.pis_cofins.registros import Registro0100
    from sped.efd.pis_cofins.registros import Registro0001
    from sped.efd.pis_cofins.registros import Registro0110
    from sped.efd.pis_cofins.registros import Registro0140
    from sped.efd.pis_cofins.registros import Registro0500
    from sped.efd.pis_cofins.registros import RegistroA001
    from sped.efd.pis_cofins.registros import RegistroA990
    from sped.efd.pis_cofins.registros import RegistroC001
    from sped.efd.pis_cofins.registros import RegistroC010
    from sped.efd.pis_cofins.registros import RegistroC100
    from sped.efd.pis_cofins.registros import RegistroC170
    from sped.efd.pis_cofins.registros import RegistroD001
    from sped.efd.pis_cofins.registros import RegistroD100
    from sped.efd.pis_cofins.registros import RegistroF001
    from sped.efd.pis_cofins.registros import RegistroI001
    from sped.efd.pis_cofins.registros import Registro9001
    from sped.efd.pis_cofins.registros import RegistroM200
    from sped.efd.pis_cofins.registros import RegistroM205
    from sped.efd.pis_cofins.registros import RegistroM210
    from sped.efd.pis_cofins.registros import RegistroM400
    from sped.efd.pis_cofins.registros import RegistroM410
    from sped.efd.pis_cofins.registros import RegistroM600
    from sped.efd.pis_cofins.registros import RegistroM605
    from sped.efd.pis_cofins.registros import RegistroM610
    from sped.efd.pis_cofins.registros import RegistroM800
    from sped.efd.pis_cofins.registros import RegistroM810
    from sped.efd.pis_cofins.registros import RegistroP001
    from sped.efd.pis_cofins.registros import Registro9900
    from sped.efd.pis_cofins.registros import Registro1001
    from sped.efd.pis_cofins.registros import Registro1010
except ImportError:
    pass


class SpedEfdContribuicoes(models.Model):
    _name = "sped.efd.contribuicoes"
    _description = "Cria o arquivo para o Sped Contribuicoes Pis/Cofins"
    _order = "date_start desc"

    date_start= fields.Date(string='Inicio de')
    date_end = fields.Date(string='até')
    tipo_escrit = fields.Selection([
        ('0', 'Original'),
        ('1', 'Retificadora'),
        ], string='Tipo Escrituração', default='0')
    num_rec_anterior = fields.Char(
        string=u"Número recibo anterior")    
    ind_nat_pj = fields.Selection([
        ('0', 'Sociedade empresárial geral'),
        ('1', 'Sociedade Cooperativa'),
        ('2', 'Sujeita ao PIS/Pasep exclusivamente com base na folha de salários'),
        ('3', 'Pessoa jurídica participante SCP como sócia ostensiva'),
        ('4', 'Sociedade cooperativa participante SCP como sócia ostensiva'),
        ('5', 'Sociedade em Conta de Participação - SCP'),
        ], string='Indicador natureza pessoa jurídica', default='0')
    ind_ativ = fields.Selection([
        ('0', 'Industrial ou equiparado a industrial'),
        ('1', 'Prestador de serviços'),
        ('2', 'Atividade de comércio'),
        ('3', 'Pessoas jurídicas Lei no 9.718, de 1998'),
        ('4', 'Atividade imobiliária'),
        ('9', 'Outros'),
        ], string='Indicador atividade preponderante')
    # 0110
    cod_inc_trib = fields.Selection([
        ('1', 'Escrit. oper. incid. exclus. regime não-cumulativo'),
        ('2', 'Escrit. oper. incid. exclus. regime cumulativo'),
        ('3', 'Escrit. oper. incid. regimes não-cumulativo e cumulativo'),
        ], string='Cód. incidência tributária')
    ind_apro_cred = fields.Selection([
        ('1', 'Método de Apropriação Direta'),
        ('2', 'Método de Rateio Proporcional (Receita Bruta)'),
        ], string='Método apropriação de créditos')
    cod_tipo_cont = fields.Selection([
        ('1', 'Apuração da Contribuição Exclusivamente a Alíquota Básica'),
        ('2', 'Apuração da Contribuição a Alíquotas Específicas (Diferenciadas e/ou por Unidade de Medida de Produto)'),
        ], string='Tipo de Contribuição Apurada')    
    ind_reg_cum = fields.Selection([
        ('1', 'Regime de Caixa –Escrituração consolidada (Registro F500)'),
        ('2', 'Regime de Competência -Escrituração consolidada (Registro F550)'),
        ('9', 'Regime de Competência -Escrituração detalhada, com base nos registros dos Blocos “A”, “C”, “D” e “F”'),
        ], string='Critério de Escrituração e Apuração Adotado')    
    
    log_faturamento = fields.Html('Log de Faturamento')
    company_id = fields.Many2one('res.company', string='Empresa', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    sped_file = fields.Binary(string=u"Sped")
    sped_file_name = fields.Char(
        string=u"Arquivo Sped Contribuições")

    @api.multi
    def create_file(self):
        if self.date_start > self.date_end:
            raise UserError('Erro, a data de início é maior que a data de encerramento!')
        self.log_faturamento = 'Gerando arquivo .. <br />'
        if self.date_start and self.date_end:
            self.registro0000()
            if not self.log_faturamento:
                self.log_faturamento = 'Arquivo gerado com sucesso. <br />'
        return {
            "type": "ir.actions.do_nothing",
        }

    def versao(self):
        #if fields.Datetime.from_string(self.dt_ini) >= datetime.datetime(2018, 1, 1):
        #    return '012'
        return '006'  

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

    def registro0000(self):
        arq = ArquivoDigital()
        cod_mun = '%s%s' %(self.company_id.state_id.ibge_code, self.company_id.city_id.ibge_code)
        arq._registro_abertura.COD_VER = self.versao()
        arq._registro_abertura.TIPO_ESCRIT = 0 # 0 - Original , 1 - Retificadora
        arq._registro_abertura.DT_INI = self.date_start
        arq._registro_abertura.DT_FIN = self.date_end
        arq._registro_abertura.NOME = self.company_id.legal_name
        arq._registro_abertura.CNPJ = self.limpa_formatacao(self.company_id.cnpj_cpf)
        arq._registro_abertura.UF = self.company_id.state_id.code
        arq._registro_abertura.COD_MUN = self.formata_cod_municipio(cod_mun)
        arq._registro_abertura.SUFRAMA = ''
        arq._registro_abertura.IND_NAT_PJ = '00' # 00 – Pessoa jurídica em geral
        arq._registro_abertura.IND_ATIV = '2' # 2 - Atividade de comércio;
        if self.company_id.accountant_id:
            contabilista = Registro0100()
            ctd = self.company_id.accountant_id
            if len(self.company_id.accountant_id.cnpj_cpf) > 14:
                if self.company_id.accountant_id.child_ids:
                    ctd = self.company_id.accountant_id.child_ids[0]
                else:  
                    msg_err = 'Cadastre o contador Pessoa Fisica dentro do Contato da Contabilidade'
                    raise UserError(msg_err)
            contador = ctd.name
            cpf = ctd.cnpj_cpf
            cod_mun = '%s%s' %(ctd.state_id.ibge_code, ctd.city_id.ibge_code)
            contabilista.NOME = contador
            contabilista.CPF = self.limpa_formatacao(cpf)
            contabilista.CRC = self.limpa_formatacao(ctd.rg_fisica)
            contabilista.END = ctd.street
            contabilista.CEP = self.limpa_formatacao(ctd.zip)
            contabilista.NUM = ctd.number
            contabilista.COMPL = ctd.street2
            contabilista.BAIRRO = ctd.district
            contabilista.FONE = self.limpa_formatacao(ctd.phone)
            contabilista.EMAIL = ctd.email
            contabilista.COD_MUN = cod_mun
            arq._blocos['0'].add(contabilista)
         
        reg110 = Registro0110()
        reg110.COD_INC_TRIB = self.cod_inc_trib # Cód. ind. da incidência tributária
        reg110.IND_APRO_CRED = self.ind_apro_cred # Cód. ind. de método de apropriação de créditos comuns
        reg110.COD_TIPO_CONT = self.cod_tipo_cont # Cód. ind. do Tipo de Contribuição Apurada
        reg110.IND_REG_CUM = self.ind_reg_cum # Cód. ind. do critério de escrituração e apuração adotado
        arq._blocos['0'].add(reg110)
        
        reg0140 = Registro0140()
        reg0140.COD_EST = str(self.company_id.id)
        reg0140.NOME = self.company_id.name
        reg0140.CNPJ = self.limpa_formatacao(self.company_id.cnpj_cpf)
        reg0140.UF = self.company_id.state_id.code
        reg0140.IE = self.limpa_formatacao(self.company_id.inscr_est)
        reg0140.COD_MUN = cod_mun
        reg0140.IM = ''
        reg0140.SUFRAMA = ''
        arq._blocos['0'].add(reg0140)            

        dt = self.date_start
        dta_s = '%s-%s-%s' %(str(dt.year),str(dt.month).zfill(2),
            str(dt.day).zfill(2))
        dt = self.date_end
        dta_e = '%s-%s-%s' %(str(dt.year),str(dt.month).zfill(2),
            str(dt.day).zfill(2))
        periodo = 'date_trunc(\'day\', ie.data_fatura) \
            between \'%s\' and \'%s\'' %(dta_s, dta_e)
        # FORNECEDORES
        for item_lista in self.query_registro0150(periodo):
            arq.read_registro(self.junta_pipe(item_lista))

        for item_lista in self.query_registro0190(periodo):
            arq.read_registro(self.junta_pipe(item_lista))

        for item_lista in self.query_registro0200(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
            """ # TODO PRECIDO DISTO ??
            # 0205 - ALTERACAO NO ITEM
            for item_alt in self.query_registro0205(item_lista.COD_ITEM):
                arq.read_registro(self.junta_pipe(item_alt))
            # 0220 - Conversão Unidade Medida
            for item_unit in self.query_registro0220(item_lista.COD_ITEM):            
                arq.read_registro(self.junta_pipe(item_unit))
            """
            
        for item_lista in self.query_registro0400(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
           
        # TODO - Colocar Na Tela pra ser informado a CONTA e DESCRICAO
        reg500 = Registro0500()
        reg500.DT_ALT = datetime.strptime('2017-11-01', '%Y-%m-%d')
        reg500.COD_NAT_CC = '01'
        reg500.IND_CTA = 'S'
        reg500.NÍVEL = '5'
        reg500.COD_CTA = '1.1.06.11.00.00'
        reg500.NOME_CTA = 'MERCADORIA REVENDA ISENTA'
        arq._blocos['0'].add(reg500)
        
        reg500 = Registro0500()
        reg500.DT_ALT = datetime.strptime('2017-11-01', '%Y-%m-%d')
        reg500.COD_NAT_CC = '01'
        reg500.IND_CTA = 'S'
        reg500.NÍVEL = '5'
        reg500.COD_CTA = '1.1.06.05.00.00'
        reg500.NOME_CTA = 'MERCADORIA REVENDA TRIBUTADA'
        arq._blocos['0'].add(reg500)
       
        query = """
                    select distinct
                        ie.id, ie.state, ie.emissao_doc
                    from
                        invoice_eletronic as ie
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state in ('done')
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        regA001 = RegistroA001()
        regA001.IND_MOV = '1'
        regA990 = RegistroA990()
        regA990.QTD_LIN_A = 1
        regC001 = RegistroC001()
        regC001.IND_MOV = '1'
        regC010 = RegistroC010()
        regC010.CNPJ = self.limpa_formatacao(self.company_id.cnpj_cpf)
        regC010.IND_ESCRI = '2'
        arq._blocos['C'].add(regC010)
        for id in query_resposta:
            if id[2] == '2' and id[1] == 'cancel':
                continue
            regC001.IND_MOV = '0'
            # TODO C100 - Notas Fiscais - Feito        
            for item_lista in self.query_registroC100(id[0]):
                arq.read_registro(self.junta_pipe(item_lista))
                # TODO C101 - DIFAL - Feito 
                #for item_lista in self.query_registroC101(self.fatura):
                #    arq.read_registro(self.junta_pipe(item_lista))

            # TODO C110 - Inf. Adiciontal
            
            # TODO C170 - Itens Nota Fiscal de Compras = Fazendo
            for item_lista in self.query_registroC170(id[0]):
                arq.read_registro(self.junta_pipe(item_lista))
                                        
        # TODO BLOCO D - prestações ou contratações de serviços 
        # de comunicação, transporte interestadual e intermunicipa
        # TODO D100 - Periodo Apuracao
        
        query = """
                    select distinct
                        ie.id, ie.state
                    from
                        invoice_eletronic as ie
                    where
                        %s
                        and (ie.model in ('57','67'))
                        and ((ie.valor_pis > 0) or (ie.valor_cofins > 0))
                        and ie.state = 'done'
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        registro_D001 = RegistroD001()
        if query_resposta:
            registro_D001.IND_MOV = '0'
        else:
            registro_D001.IND_MOV = '1'
        """
        resposta_cte = self.env['invoice.eletronic'].search([
            ('model','in',('57','67')),
            ('state', '=','done'),
            ('data_fatura','>=',g_intervalo[0]),
            ('data_fatura','<=',g_intervalo[1]),
            ])
        """
        #for cte in resposta_cte:
            # TODO D100 - Documentos Transporte
            #TODO DEIXAMOS FORA POIS NAO EXISTE NO ATS ADMIN
            #for item_lista in self.query_registroD100(cte.invoice_id.id):
                #arq.read_registro(self.junta_pipe(item_lista))
                
            # TODO D190 - Totalizacao por CST
            #for item_lista in self.query_registroD190(cte.invoice_id.id):
            #    arq.read_registro(self.junta_pipe(item_lista))
        regF001 = RegistroF001()
        regF001.IND_MOV = '1'
            
        #regF990 = RegistroF990()
        #regF990.QTD_LIN_F = 1
        #arq._blocos['F'].add(regF001)

        regI001 = RegistroI001()
        regI001.IND_MOV = '1'
        #arq._blocos['I'].add(regI990)
            
        # é gerados pelo VALIDADOR
        for item_lista in self.query_registroM200(periodo):
            arq.read_registro(self.junta_pipe(item_lista))

        for item_lista in self.query_registroM400(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
            for item_lista in self.query_registroM410(item_lista.CST_PIS, periodo):
                arq.read_registro(self.junta_pipe(item_lista))

        # é gerados pelo VALIDADOR
        for item_lista in self.query_registroM600(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
        
        
        """
        regM800 = RegistroM800()
        regM800.CST_COFINS = '06'
        #TODO VL_TOT_REC CARREGAR VALOR.
        regM800.VL_TOT_REC = '0'
        regM800.COD_CTA = '1.1.06.11.00.00'
        arq._blocos['M'].add(regM800)
        """
        for item_lista in self.query_registroM800(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
            for item_lista in self.query_registroM810(item_lista.CST_COFINS, periodo):
                arq.read_registro(self.junta_pipe(item_lista))
       
        regP001 = RegistroP001()
        regP001.IND_MOV = '1'
        
        #import pudb;pu.db
        registro_1001 = Registro1001()
        registro_1001.IND_MOV = '1'
        #arq._blocos['1'].add(registro_1001)
        arq.prepare()
        self.sped_file_name =  'PisCofins-%s_%s.txt' % (
            str(dt.month).zfill(2), str(dt.year))
        #arqxx = open('/opt/odoo/novo_arquivo.txt', 'w')
        #arqxx.write(arq.getstring())
        #arqxx.close()
        self.sped_file = base64.encodestring(bytes(arq.getstring(), 'iso-8859-1'))

    def query_registro0150(self, periodo):
        query = """
                    select distinct
                        ie.partner_id
                    from
                        invoice_eletronic ie
                    where
                        %s
                        and (ie.model in ('55','01','57','67'))
                        and (ie.state = 'done')
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for id in query_resposta:
            resposta_participante = self.env['res.partner'].browse(id[0])
            registro_0150 = registros.Registro0150()
            registro_0150.COD_PART = str(resposta_participante.id)
            registro_0150.NOME = resposta_participante.legal_name or resposta_participante.name
            cod_pais = resposta_participante.country_id.bc_code
            registro_0150.COD_PAIS = cod_pais
            cpnj_cpf = self.limpa_formatacao(resposta_participante.cnpj_cpf)
            cod_mun = '%s%s' %(resposta_participante.state_id.ibge_code, resposta_participante.city_id.ibge_code)
            if cod_pais == '01058':
                registro_0150.COD_MUN = self.formata_cod_municipio(cod_mun)
                if len(cpnj_cpf) == 11:
                    registro_0150.CPF = cpnj_cpf
                else:
                    registro_0150.CNPJ = cpnj_cpf
                    registro_0150.IE = self.limpa_formatacao(resposta_participante.inscr_est)
            else:
                registro_0150.COD_MUN = '9999999'
            registro_0150.SUFRAMA = self.limpa_formatacao(resposta_participante.suframa)
            if resposta_participante.street:
                registro_0150.END = resposta_participante.street.strip()
            if resposta_participante.number:
                registro_0150.NUM = resposta_participante.number.strip()
            if resposta_participante.street2:
                registro_0150.COMPL = resposta_participante.street2.strip()
            if resposta_participante.district:
                registro_0150.BAIRRO = resposta_participante.district.strip()
            lista.append(registro_0150)

        return lista

    def query_registro0190(self, periodo):
        query = """
                    select distinct
                        substr(UPPER(pu.name), 1,6)
                        , UPPER(pu.l10n_br_description)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det
                            on ie.id = det.invoice_eletronic_id 
                    inner join product_product pp
                        on pp.id = det.product_id    
                    inner join product_template pt
                       on pt.id = pp.product_tmpl_id
                    inner join
                        uom_uom pu
                            on pu.id = det.uom_id or pu.id = pt.uom_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and ie.emissao_doc = '2'
                    order by 1
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_un = []
        un = ''
        for id in query_resposta:
            registro_0190 = registros.Registro0190()
            unidade = ''
            if id[0].find('-') != -1:
                unidade = id[0][:id[0].find('-')]
            else:
                unidade = id[0]
            unidade = unidade[:6]
            if un == unidade:
                continue 
            lista_un.append(unidade)
            registro_0190.UNID = unidade
            desc = id[1]
            if not desc:
                msg_err = 'Unidade de medida sem descricao - Un %s.' %(unidade)
                raise UserError(msg_err)
            registro_0190.DESCR = desc.strip()
            lista.append(registro_0190)
            un = unidade
        return lista

    def query_registro0200(self, periodo):
        query = """
                    select distinct
                        det.product_id
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        #hash = {}
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            resposta_produto = self.env['product.product'].browse(resposta[0])
            if not resposta_produto:
                continue
            lista_item.append(resposta_produto.id)
            registro_0200 = registros.Registro0200()
            cprod = resposta_produto.default_code
            registro_0200.COD_ITEM = cprod
            desc_item = resposta_produto.name.strip()
            try:
                desc_item = desc_item.encode('iso-8859-1')
                desc_item = resposta_produto.name.strip()
            except:
                desc_item = unidecode(desc_item)
            registro_0200.DESCR_ITEM = desc_item
            if resposta_produto.barcode != resposta_produto.default_code:
                registro_0200.COD_BARRA = resposta_produto.barcode
            if resposta_produto.uom_id.name.find('-') != -1:
                unidade = resposta_produto.uom_id.name[:resposta_produto.uom_id.name.find('-')]
            else:
                unidade = resposta_produto.uom_id.name
            unidade = unidade.strip()
            unidade = unidade.upper()
            unidade = unidade[:6]
            registro_0200.UNID_INV = unidade[:6]
            registro_0200.TIPO_ITEM = resposta_produto.l10n_br_sped_type
            registro_0200.COD_NCM = self.limpa_formatacao(resposta_produto.fiscal_classification_id.code)
            lista.append(registro_0200)                        
        return lista

    def query_registro0400(self, periodo):
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
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state in ('done')
                        and d.fiscal_position_id is not null 
                """ % (periodo)
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

    def query_registroC100(self, doc):
        lista = []
        nfe_ids = self.env['invoice.eletronic'].browse(doc)
        for nf in nfe_ids:    
            if (nf.state == 'done') and (nf.model == '55'):
                cancel = False 
                registro_c100 = registros.RegistroC100()
                if nf.tipo_operacao == 'entrada':
                    registro_c100.IND_OPER = '0'
                else:
                    registro_c100.IND_OPER = '1'
                if nf.emissao_doc == '1':    
                    registro_c100.IND_EMIT = '0'
                else:
                    registro_c100.IND_EMIT = '1'
                registro_c100.COD_MOD = nf.model
                if nf.state == 'cancel':
                    registro_c100.COD_SIT = '02'
                    cancel = True
                else:
                    registro_c100.COD_SIT = '00'
                registro_c100.SER = nf.serie_documento
                registro_c100.CHV_NFE = nf.chave_nfe
                registro_c100.NUM_DOC = self.limpa_formatacao(str(nf.numero))
                if not cancel:
                    registro_c100.DT_DOC  = nf.data_emissao
                    if nf.data_fatura:
                        registro_c100.DT_E_S  = nf.data_fatura
                    else:
                        registro_c100.DT_E_S  = nf.data_emissao
                    if nf.metodo_pagamento:
                        registro_c100.IND_PGTO = nf.metodo_pagamento
                    registro_c100.VL_MERC = self.transforma_valor(nf.valor_bruto)
                    registro_c100.IND_FRT = str(nf.modalidade_frete)
                    registro_c100.VL_FRT = self.transforma_valor(nf.valor_frete)
                    registro_c100.VL_SEG = self.transforma_valor(nf.valor_seguro)
                    registro_c100.VL_OUT_DA = self.transforma_valor(nf.valor_despesas)
                    registro_c100.VL_DESC = self.transforma_valor(nf.valor_desconto)
                    registro_c100.VL_DOC  = self.transforma_valor(nf.valor_final)
                    registro_c100.VL_BC_ICMS = self.transforma_valor(nf.valor_bc_icms)
                    registro_c100.VL_ICMS = self.transforma_valor(nf.valor_icms)
                    registro_c100.VL_BC_ICMS_ST = self.transforma_valor(nf.valor_bc_icmsst)
                    registro_c100.VL_ICMS_ST = self.transforma_valor(nf.valor_icmsst)
                    registro_c100.VL_IPI = self.transforma_valor(nf.valor_ipi)
                    registro_c100.VL_PIS = self.transforma_valor(nf.valor_pis)
                    registro_c100.VL_COFINS = self.transforma_valor(nf.valor_cofins)
                    registro_c100.COD_PART = str(nf.partner_id.id)
                lista.append(registro_c100)
        return lista

    def query_registroC170(self, doc):
        lista = []
        nfe_line = self.env['invoice.eletronic.item'].search([
                ('invoice_eletronic_id','=', doc),
                ], order='num_item')
        n_item = 1
        for item in nfe_line:
            registro_c170 = registros.RegistroC170()
            if item.num_item > 1:
                registro_c170.NUM_ITEM = str(item.num_item)
            else:
                registro_c170.NUM_ITEM = str(n_item) # str(item.num_item_xml or n_item)                
            cprod = item.product_id.default_code #.replace('.','')
            registro_c170.COD_ITEM = cprod
            registro_c170.DESCR_COMPL = self.limpa_caracteres(item.name.strip())
            registro_c170.QTD = self.transforma_valor(item.quantidade)
            if item.uom_id.name.find('-') != -1:
                unidade = item.uom_id.name[:item.uom_id.name.find('-')]
            else:
                unidade = item.uom_id.name
            registro_c170.UNID = unidade[:6]
            registro_c170.VL_DESC = self.transforma_valor(item.desconto)
            registro_c170.VL_ITEM = self.transforma_valor(item.valor_bruto)
            if item.cfop in ['5922', '6922']:
                registro_c170.IND_MOV = '1'
            else:
                registro_c170.IND_MOV = '0'
            try:
                registro_c170.CST_ICMS = '%s%s' %(str(item.origem), str(item.icms_cst))
            except:
                msg_err = 'Sem CST na Fatura %s. <br />' %(str(resposta.number or resposta.id))
                #raise UserError(msg_err)
                self.log_faturamento += msg_err
            if item.cfop:
                registro_c170.CFOP = str(item.cfop)
            else:
                registro_c170.CFOP = '0000'
            #if r_nfe.id == 407:
            #    import pudb;pu.db
            registro_c170.COD_NAT = str(item.invoice_eletronic_id.fiscal_position_id.id)
            registro_c170.VL_BC_ICMS = self.transforma_valor(item.icms_base_calculo)
            registro_c170.ALIQ_ICMS = '0'
            registro_c170.ALIQ_ICMS = self.transforma_valor(item.icms_aliquota)
            
            registro_c170.VL_ICMS = self.transforma_valor(item.icms_valor)
            registro_c170.VL_BC_ICMS_ST = self.transforma_valor(item.icms_st_base_calculo)
            if item.icms_st_aliquota:
                registro_c170.ALIQ_ST = self.transforma_valor(item.icms_st_aliquota)
            registro_c170.VL_ICMS_ST = self.transforma_valor(item.icms_st_valor)
            # TODO incluir na empresa o IND_APUR
            registro_c170.IND_APUR = '0'
            registro_c170.CST_IPI = item.ipi_cst
            registro_c170.VL_BC_IPI = self.transforma_valor(item.ipi_base_calculo)
            if item.ipi_aliquota:
                registro_c170.ALIQ_IPI = self.transforma_valor(item.ipi_aliquota)
            registro_c170.VL_IPI = self.transforma_valor(item.ipi_valor)
            registro_c170.CST_PIS = item.pis_cst
            registro_c170.VL_BC_PIS = self.transforma_valor(item.pis_base_calculo)
            registro_c170.ALIQ_PIS = self.transforma_valor(item.pis_aliquota)
            #registro_c170.QUANT_BC_PIS = self.transforma_valor(
            registro_c170.VL_PIS = self.transforma_valor(item.pis_valor)
            registro_c170.CST_COFINS = item.cofins_cst
            registro_c170.VL_BC_COFINS = self.transforma_valor(item.cofins_base_calculo)
            registro_c170.ALIQ_COFINS = self.transforma_valor(item.cofins_aliquota)
            #registro_c170.QUANT_BC_COFINS = self.transforma_valor(
            registro_c170.VL_COFINS = self.transforma_valor(item.cofins_valor)
            n_item += 1
       
            lista.append(registro_c170)

        return lista

    # transporte
    #TODO DEIXAMOS FORA POIS NAO EXISTE NO ATS ADMIN
    def query_registroD100(self, doc):
        lista = []
        resposta_cte = self.env['account.invoice'].browse(fatura)
        for resposta in resposta_cte:
            cte = self.env['invoice.eletronic'].search([('invoice_id','=',fatura)])
            registro_d100 = registros.RegistroD100()
            registro_d100.IND_OPER = '0' # Aquisicao
            registro_d100.IND_EMIT = '1' # Terceiros
            registro_d100.COD_PART = str(resposta.partner_id.id)
            registro_d100.COD_MOD = str(resposta.nfe_modelo)  # or resposta_nfe.product_document_id.code).zfill(2)
            #if cte.tp_emiss_cte == '1':
            registro_d100.COD_SIT = '00'
            """
            elif cte.tp_emiss_cte == '2':
               registro_d100.COD_SIT = '01'
            elif cte.tp_emiss_cte == '3':
               registro_d100.COD_SIT = '02'
            elif cte.tp_emiss_cte == '4':
               registro_d100.COD_SIT = '03'
            elif cte.tp_emiss_cte == '5':
               registro_d100.COD_SIT = '04'
            elif cte.tp_emiss_cte == '6':
               registro_d100.COD_SIT = '05'
            elif cte.tp_emiss_cte == '7':
               registro_d100.COD_SIT = '06'
            elif cte.tp_emiss_cte == '8':
               registro_d100.COD_SIT = '07'
            elif cte.tp_emiss_cte == '9':
               registro_d100.COD_SIT = '08'
            """
            registro_d100.SER = resposta.nfe_serie[:3] # resposta.product_serie_id.code
            if resposta.nfe_chave:
                if len(resposta.nfe_chave) != 44:
                    msg_err = 'Tamanho da Chave NFe invalida - Fatura %s.' %(str(resposta.number or resposta.id))
                    #raise UserError(msg_err)
                    self.log_faturamento += msg_err
            registro_d100.CHV_CTE = str(resposta.nfe_chave) # or resposta_nfe.chave_nfe
            registro_d100.NUM_DOC = self.limpa_formatacao(str(cte.numero)) # or resposta_nfe.numero))
            registro_d100.DT_A_P = cte.data_fatura or resposta.date_invoice
            registro_d100.DT_DOC = cte.data_emissao or resposta.date_invoice
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
                        d.nfe_modelo in ('57','67')
                        and d.state in ('open','paid')
                        and ((il.valor_pis > 0) or (il.valor_cofins > 0))
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

    def query_registroM200(self, periodo):
        query = """
                    select 
                        sum(det.valor_liquido),
                        det.pis_aliquota,
                        sum(det.pis_valor)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and det.pis_valor > 0
                        and (det.cofins_cst in ('01','02','03'))
                    group by det.pis_aliquota
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            regM200 = RegistroM200()
            regM200.VL_TOT_CONT_NC_PER = '0'
            regM200.VL_TOT_CRED_DESC = '0'
            regM200.VL_TOT_CRED_DESC_ANT = '0'
            regM200.VL_TOT_CONT_NC_DEV = '0'
            regM200.VL_RET_NC = '0'
            regM200.VL_OUT_DED_NC = '0'
            regM200.VL_CONT_NC_REC = '0'
            regM200.VL_TOT_CONT_CUM_PER = resposta[2]
            regM200.VL_RET_CUM = '0'
            regM200.VL_OUT_DED_CUM = '0'
            regM200.VL_CONT_CUM_REC = resposta[2]
            regM200.VL_TOT_CONT_REC = resposta[2]
            lista.append(regM200)

            regM205 = RegistroM205()
            regM205.NUM_CAMPO = '12'
            regM205.COD_REC = '810902'
            regM205.VL_DEBITO = resposta[2]
            lista.append(regM205)

            regM210 = RegistroM210()
            regM210.COD_CONT = '51'
            regM210.VL_REC_BRT = self.transforma_valor(resposta[0])
            regM210.VL_BC_CONT = self.transforma_valor(resposta[0])
            regM210.VL_AJUS_ACRES_BC_PIS = '0' 
            regM210.VL_AJUS_REDUC_BC_PIS = '0'  
            regM210.VL_BC_CONT_AJUS = self.transforma_valor(resposta[0])
            regM210.ALIQ_PIS = self.transforma_valor(resposta[1])
            regM210.QUANT_BC_PIS = '0'
            regM210.ALIQ_PIS_QUANT = '0'
            regM210.VL_CONT_APUR = self.transforma_valor(resposta[2])
            regM210.VL_AJUS_ACRES = '0'
            regM210.VL_AJUS_REDUC = '0'
            regM210.VL_CONT_DIFER = '0'
            regM210.VL_CONT_DIFER_ANT = '0'
            regM210.VL_CONT_PER = self.transforma_valor(resposta[2])
            lista.append(regM210)
            
        return lista

    """


    """

    def query_registroM400(self, periodo):
        query = """
                    select 
                        det.pis_cst,
                        sum(det.valor_liquido)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and (det.pis_cst in ('04','06','07','08','09'))
                    group by det.pis_cst
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            registro_M400 = registros.RegistroM400()
            registro_M400.CST_PIS = resposta[0]
            registro_M400.VL_TOT_REC = self.transforma_valor(resposta[1])
            registro_M400.COD_CTA = '1.1.06.11.00.00'
            lista.append(registro_M400)
        return lista

    def query_registroM410(self, cst_pis, periodo):
        query = """
                    select distinct
                        substr(pr.name, 1,3),
                        sum(det.valor_liquido)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    inner join
                        product_product as pp
                            on pp.id = det.product_id
                    inner join
                        product_template as pt
                            on pt.id = pp.product_tmpl_id
                    inner join
                        product_category as pc
                            on pc.id = pt.categ_id
                    inner join
                        product_category as pr
                            on pr.id = pc.parent_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and (det.pis_cst = \'%s\')
                    group by substr(pr.name, 1,3)
                """ % (periodo, cst_pis)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            registro_M410 = registros.RegistroM410()
            registro_M410.NAT_REC = resposta[0]
            registro_M410.VL_REC = self.transforma_valor(resposta[1])
            registro_M410.COD_CTA = '1.1.06.11.00.00'
            lista.append(registro_M410)                        
        return lista

    def query_registroM600(self, periodo):
        query = """
                    select
                        sum(det.valor_liquido),
                        det.cofins_aliquota,
                        sum(det.cofins_valor)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and (det.cofins_cst in ('01','02','03'))
                    group by det.cofins_aliquota
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            regM600 = RegistroM600()
            regM600.VL_TOT_CONT_NC_PER = '0'
            regM600.VL_TOT_CRED_DESC = '0'
            regM600.VL_TOT_CRED_DESC_ANT = '0'
            regM600.VL_TOT_CONT_NC_DEV = '0'
            regM600.VL_RET_NC = '0'
            regM600.VL_OUT_DED_NC = '0'
            regM600.VL_CONT_NC_REC = '0'
            regM600.VL_TOT_CONT_CUM_PER = self.transforma_valor(resposta[2])
            regM600.VL_RET_CUM = '0'
            regM600.VL_OUT_DED_CUM = '0'
            regM600.VL_CONT_CUM_REC = self.transforma_valor(resposta[2])
            regM600.VL_TOT_CONT_REC = self.transforma_valor(resposta[2])
            lista.append(regM600)

            regM605 = RegistroM605()
            regM605.NUM_CAMPO = '12'
            regM605.COD_REC = '217201'
            regM605.VL_DEBITO = self.transforma_valor(resposta[2])
            lista.append(regM605)

            regM610 = RegistroM610()
            regM610.COD_CONT = '51'
            regM610.VL_REC_BRT = self.transforma_valor(resposta[0])
            regM610.VL_BC_CONT = self.transforma_valor(resposta[0])
            regM610.VL_AJUS_ACRES_BC_COFINS = '0' 
            regM610.VL_AJUS_REDUC_BC_COFINS = '0'  
            regM610.VL_BC_CONT_AJUS = self.transforma_valor(resposta[0])
            regM610.ALIQ_COFINS = self.transforma_valor(resposta[1])
            regM610.QUANT_BC_COFINS = '0'
            regM610.ALIQ_COFINS_QUANT = '0'
            regM610.VL_CONT_APUR = self.transforma_valor(resposta[2])
            regM610.VL_AJUS_ACRES = '0'
            regM610.VL_AJUS_REDUC = '0'
            regM610.VL_CONT_DIFER = '0'
            regM610.VL_CONT_DIFER_ANT = '0'
            regM610.VL_CONT_PER = self.transforma_valor(resposta[2])
            lista.append(regM610)
        return lista

    def query_registroM800(self, periodo):
        query = """
                    select 
                        det.cofins_cst,
                        sum(det.valor_liquido)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and (det.cofins_cst in ('04','06','07','08','09'))
                    group by det.cofins_cst
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            registro_M800 = registros.RegistroM800()
            registro_M800.CST_COFINS = resposta[0]
            registro_M800.VL_TOT_REC = self.transforma_valor(resposta[1])
            registro_M800.COD_CTA = '1.1.06.11.00.00'
            lista.append(registro_M800)
        return lista

    def query_registroM810(self, cofins_cst, periodo):
        query = """
                    select 
                        substr(pr.name,1,3),
                        sum(det.valor_liquido)
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item as det 
                            on ie.id = det.invoice_eletronic_id
                    inner join
                        product_product as pp
                            on pp.id = det.product_id
                    inner join
                        product_template as pt
                            on pt.id = pp.product_tmpl_id
                    inner join
                        product_category as pc
                            on pc.id = pt.categ_id
                    inner join
                        product_category as pr
                            on pr.id = pc.parent_id
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and (det.cofins_cst = \'%s\')
                    group by substr(pr.name,1,3)
                """ % (periodo, cofins_cst)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        lista_item = []
        cont = 1
        for resposta in query_resposta:
            registro_M810 = registros.RegistroM810()
            cod_nat = resposta[0]
            registro_M810.NAT_REC = cod_nat[:3]
            registro_M810.VL_REC = self.transforma_valor(resposta[1])
            registro_M810.COD_CTA = '1.1.06.11.00.00'
            lista.append(registro_M810)                        
        return lista
