# Copyright (C) 2020 - Carlos R. Silveira - ATSti Soluções
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from unidecode import unidecode
from datetime import datetime, timedelta
import pytz
import base64
try:
    from sped.efd.icms_ipi.arquivos import ArquivoDigital
    from sped.efd.icms_ipi import registros
    from sped.efd.icms_ipi.registros import Registro0100
    from sped.efd.icms_ipi.registros import Registro0001
    # from sped.efd.icms_ipi.registros import Registro0002
    from sped.efd.icms_ipi.registros import Registro0005
    from sped.efd.icms_ipi.registros import RegistroB001
    from sped.efd.icms_ipi.registros import RegistroB990
    from sped.efd.icms_ipi.registros import RegistroC001
    from sped.efd.icms_ipi.registros import RegistroC100
    from sped.efd.icms_ipi.registros import RegistroC101
    from sped.efd.icms_ipi.registros import RegistroC170
    from sped.efd.icms_ipi.registros import RegistroC190
    # from sped.efd.icms_ipi.registros import RegistroC191
    from sped.efd.icms_ipi.registros import RegistroC197
    from sped.efd.icms_ipi.registros import RegistroC300
    from sped.efd.icms_ipi.registros import RegistroD001
    from sped.efd.icms_ipi.registros import RegistroD100
    from sped.efd.icms_ipi.registros import RegistroD110
    from sped.efd.icms_ipi.registros import RegistroD120
    from sped.efd.icms_ipi.registros import RegistroD190
    from sped.efd.icms_ipi.registros import Registro9001
    from sped.efd.icms_ipi.registros import RegistroE100
    from sped.efd.icms_ipi.registros import RegistroE110
    from sped.efd.icms_ipi.registros import RegistroE116
    from sped.efd.icms_ipi.registros import RegistroE200
    from sped.efd.icms_ipi.registros import RegistroE210
    from sped.efd.icms_ipi.registros import RegistroE500
    from sped.efd.icms_ipi.registros import RegistroE510
    from sped.efd.icms_ipi.registros import RegistroE520
    from sped.efd.icms_ipi.registros import RegistroK100
    from sped.efd.icms_ipi.registros import RegistroK200
    from sped.efd.icms_ipi.registros import Registro1001
    from sped.efd.icms_ipi.registros import Registro1010
except ImportError:
    pass

class SpedEfdIcmsIpi(models.Model):
    _name = "sped.efd.icms.ipi"
    _description = "Cria o arquivo para o Sped ICMS / IPI"
    _order = "date_start desc"

    date_start= fields.Date(string='Inicio de')
    date_end = fields.Date(string='até')
    data_vencimento_e316 = fields.Date(string='Vencimento E-316')
    
    cod_obrigacao = fields.Selection([
        ('000', 'ICMS a recolher'),
        ('003', 'Antecipação do diferencial de alíquotas do ICMS'),
        ('004', 'Antecipação do ICMS da importação'),
        ('005', 'Antecipação tributária'),
        ('006', 'ICMS resultante da alíquota adicional dos itens incluídos no Fundo de Combate à Pobreza'),
        ('090', 'Outras obrigações do ICMS'),       
        ], string= 'Código Obrigação', dafault='000')
        
    cod_receita = fields.Selection([     
        ('046-2', 'Regime Periódico de Apuração'),
        ('060-7', 'Regime de Estimativa'),
        ('063-2', 'Outros recolhimentos especiais'),
        ('075-9', 'Dívida ativa – cobrança amigável'),
        ('077-2', 'Dívida ativa ajuizada - parcelamento'),
        ('078-4', 'Dívida ativa ajuizada'),
        ('081-4', 'Parcelamento de débito fiscal não inscrito'),
        ('087-5', 'ICM/ICMS - Programa de Parcelamento Incentivado - PPI'),
        ('089-9', 'ICM/ICMS - Programa Especial de Parcelamento - PEP'),
        ('091-7', 'ICM/ICMS - Programa Especial de Parcelamento PEP 2017'),
        ('100-4', 'ICMS recolhimento antecipado (outra UF)'),
        ('101-6', 'Consumidor final não contribuinte por operação (outra UF)'),
        ('102-8', 'Consumidor final não contribuinte por apuração (outra UF)'),
        ('103-0', 'Fundo estadual de combate e erradicação da pobreza (FECOEP) - por operação'),
        ('104-1', 'Fundo estadual de combate e erradicação da pobreza (FECOEP) - por apuração'),
        ('106-5', 'Exigido em Auto de Infração e Imposição de Multa - AIIM'),
        ('107-7', 'Exigido em Auto de Infração e Imposição de Multa - AIIM (outra UF)'),
        ('110-7', 'Transporte (Transportador autônomo do Estado de São Paulo)'),
        ('111-9', 'Transporte (outra UF)'),
        ('112-0', 'Comunicação (no Estado de São Paulo)'),
        ('113-2', 'Comunicação (outra UF)'),
        ('114-4', 'Mercadorias destina a consumo ou a ativo imobilizado'),
        ('115-6', 'Energia elétrica (no Estado de São Paulo)'),
        ('116-8', 'Energia elétrica (outra UF)'),
        ('117-0', 'Combustível (no Estado de São Paulo)'),
        ('118-1', 'Combustível (outra UF)'),
        ('119-3', 'Recolhimentos especiais (outra UF)'),
        ('120-0', 'Mercadoria importada (desembaraçada no Estado de São Paulo)'),
        ('123-5', 'Exportação de café cru'),
        ('128-4', 'Operações internas e interestaduais com café cru'),
        ('137-5', 'Abate de gado'),
        ('141-7', 'Operações com feijão'),
        ('146-6', 'Substituição tributária (contribuinte do Estado de São Paulo)'),
        ('154-5', 'Diferença de estimativa'),
        ('214-8', 'Mercadoria importada (desembaraçada em outra UF)'),
        ('246-0', 'Substituição tributária por apuração (contribuinte de outra UF )'),
        ('247-1', 'Substituição tributária por operação (outra UF)'),		
        ], string='Código Receita') 
        
    tipo_arquivo = fields.Selection([
        ('0', 'Remessa do arquivo original'),
        ('1', 'Remessa do arquivo substituto'),
        ], string='Finalidade do Arquivo', default='0')
    ind_apur = fields.Selection([
        ('0', 'Mensal'),
        ('1', 'Decendial'),
        ], string='Período apuração IPI', default='0')
    ind_ativ = fields.Selection([
        ('0', 'Industrial ou equiparado a industrial'),
        ('1', 'Outros'),
        ], string='Indicador tipo atividade', default='0')
    log_faturamento = fields.Html('Log de Faturamento')
    company_id = fields.Many2one('res.company', string='Empresa', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    sped_file = fields.Binary(string=u"Sped")
    sped_file_name = fields.Char(
        string=u"Arquivo Sped")
    vl_sld_cred_ant_difal = fields.Float('Saldo Credor per. ant. Difal', default=0.0)
    vl_sld_cred_transp_difal = fields.Float('Saldo Credor per. seguinte Difal', default=0.0)
    vl_sld_cred_ant_fcp = fields.Float('Saldo Credor per. ant. FCP', default=0.0)
    vl_sld_cred_transp_fcp = fields.Float('Saldo Credor per. seguinte FCP', default=0.0)
    clas_estab_ind = fields.Selection([
        ('00', 'Industrial - Transformação'),
        ('01', 'Industrial - Beneficiamento'),
        ('02', 'Industrial - Montagem'),
        ('03', 'Industrial - Acondicionamento ou Reacondicionamento'),
        ('04', 'Industrial - Renovação ou Recondicionamento'),
        ('05', 'Equiparado a industrial - Por opção'),
        ('06', 'Equiparado a industrial - Importação Direta'),
        ('07', 'Equiparado a industrial - Por lei específica'),
        ('08', 'Equiparado a industrial - Não enquadrado nos códigos 05, 06 ou 07'),
        ('09', 'Outros'),        
        ], string='Classif. estabelecimento')

    @api.multi
    def create_file(self):
        if self.date_start > self.date_end:
            raise UserError('Erro, a data de início é maior que a data de encerramento!')
        self.log_faturamento = 'Gerando arquivo .. <br />'
        self.registro0000()
        if not self.log_faturamento:
            self.log_faturamento = 'Arquivo gerado com sucesso. <br />'
        return {
            "type": "ir.actions.do_nothing",
        }

    def versao(self):
        if self.date_start.year == 2018:
            return '012'
        elif self.date_start.year == 2019:
            return '013'
        else:
            return '014'

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
        arq._registro_abertura.COD_FIN = self.tipo_arquivo
        arq._registro_abertura.DT_INI = self.date_start
        arq._registro_abertura.DT_FIN = self.date_end
        arq._registro_abertura.NOME = self.company_id.legal_name
        arq._registro_abertura.CNPJ = self.limpa_formatacao(self.company_id.cnpj_cpf)
        arq._registro_abertura.UF = self.company_id.state_id.code
        arq._registro_abertura.IE = self.limpa_formatacao(self.company_id.inscr_est)
        arq._registro_abertura.COD_MUN = self.formata_cod_municipio(cod_mun)
        arq._registro_abertura.IM = ''
        arq._registro_abertura.SUFRAMA = ''
        arq._registro_abertura.IND_PERFIL = 'A'
        arq._registro_abertura.IND_ATIV = self.ind_ativ
        #reg0001 = Registro0001()
        #if inv:
        #    reg0001.IND_MOV = '0'
        #else:
        #    reg0001.IND_MOV = '1'
        if self.ind_ativ == '0':
            reg0002 = Registro0002()
            reg0002.CLAS_ESTAB_IND = self.clas_estab_ind
            arq._blocos['0'].add(reg0002)
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
        dt = self.date_start
        dta_s = '%s-%s-%s' %(str(dt.year),str(dt.month).zfill(2),
            str(dt.day).zfill(2))
        dt = self.date_end
        dta_e = '%s-%s-%s' %(str(dt.year),str(dt.month).zfill(2),
            str(dt.day).zfill(2))
        periodo = 'date_trunc(\'day\', ie.data_fatura) \
            between \'%s\' and \'%s\'' %(dta_s, dta_e)
        com_movimento = '1'
        for item_lista in self.query_registro0150(periodo):
            com_movimento = '0'
            arq.read_registro(self.junta_pipe(item_lista))
            
        for item_lista in self.query_registro0190(periodo):
            arq.read_registro(self.junta_pipe(item_lista))

        for item_lista in self.query_registro0200(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
            # 0205 - ALTERACAO NO ITEM
            for item_alt in self.query_registro0205(item_lista.COD_ITEM):
                arq.read_registro(self.junta_pipe(item_alt))
            # 0220 - Conversão Unidade Medida
            for item_unit in self.query_registro0220(item_lista.COD_ITEM, periodo):
                arq.read_registro(self.junta_pipe(item_unit))
            
            
        for item_lista in self.query_registro0400(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
        
        regB001 = RegistroB001()
        #arq._blocos['B'].add(regB001)        
        
        regC001 = RegistroC001()
        regC001.IND_MOV = com_movimento
        #arq._blocos['C'].add(regC001)
        query = """
                    select distinct
                        ie.id, ie.state, ie.emissao_doc
                    from
                        invoice_eletronic as ie
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state in ('done', 'cancel')
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            if id[2] == '2' and id[1] == 'cancel':
                continue
            nf = id[0]
            for item_lista in self.query_registroC100(nf):
                arq.read_registro(self.junta_pipe(item_lista))
                for item_lista in self.query_registroC101(nf):
                    arq.read_registro(self.junta_pipe(item_lista))

            # TODO C110 - Inf. Adiciontal
            if id[2] == '2':
                for item_lista in self.query_registroC170(nf):
                    arq.read_registro(self.junta_pipe(item_lista))
                        
            for item_lista in self.query_registroC190(nf):
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
        #arq._blocos['D'].add(registro_D001)

        for cte_id in query_resposta:
            for item_lista in self.query_registroD100(cte_id[0]):
                arq.read_registro(self.junta_pipe(item_lista))
            for item_lista in self.query_registroD190(cte_id[0]):
                arq.read_registro(self.junta_pipe(item_lista))

        registro_E100 = RegistroE100()
        registro_E100.DT_INI = self.date_start
        registro_E100.DT_FIN = self.date_end
        arq._blocos['E'].add(registro_E100)

        for item_lista in self.query_registroE110(periodo):
            arq.read_registro(self.junta_pipe(item_lista))  
        
        for item_lista in self.query_registroE200(periodo):
            arq.read_registro(self.junta_pipe(item_lista))
            for item in self.query_registroE210(item_lista.UF, periodo):
                arq.read_registro(self.junta_pipe(item))

        for item_lista in self.query_registroE300(periodo):
            arq.read_registro(self.junta_pipe(item_lista))      
            for uf_lista in self.query_registroE310(
                self.company_id.state_id.code,
                item_lista.UF,
                perido):
                arq.read_registro(self.junta_pipe(uf_lista))
            for uf_lista in self.query_registroE316(
                self.company_id.state_id.code,
                item_lista.UF,
                periodo):
                arq.read_registro(self.junta_pipe(uf_lista))

        if self.ind_ativ == '0':
            registro_E500 = RegistroE500()
            registro_E500.IND_APUR = self.ind_apur
            registro_E500.DT_INI = self.date_start
            registro_E500.DT_FIN = self.date_end
            arq._blocos['E'].add(registro_E500)
            for item_lista in self.query_registroE510(periodo):
                arq.read_registro(self.junta_pipe(item_lista))
            for item_lista in self.query_registroE520(periodo):
                arq.read_registro(self.junta_pipe(item_lista))

        # K100
        registro_K100 = RegistroK100()
        registro_K100.DT_INI = self.date_start
        registro_K100.DT_FIN = self.date_end
        arq._blocos['K'].add(registro_K100)
            
        # K200
        for item_lista in self.query_registroK200():
            arq.read_registro(self.junta_pipe(item_lista))
        
        registro_1001 = Registro1001()
        registro_1001.IND_MOV = '0'
        #arq._blocos['1'].add(registro_1001)

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
        registro_1010.IND_GIAF1 = 'N'
        registro_1010.IND_GIAF3 = 'N'
        registro_1010.IND_GIAF4 = 'N'
        registro_1010.IND_REST_RESSARC_COMPL_ICMS = 'N'
        arq._blocos['1'].add(registro_1010)
        arq.prepare()
        self.sped_file_name =  'Sped-%s_%s.txt' % (
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
                        invoice_eletronic as ie
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
            registro_0150.END = resposta_participante.street
            registro_0150.NUM = resposta_participante.number
            registro_0150.COMPL = ''
            if resposta_participante.street2:
                registro_0150.COMPL = str(resposta_participante.street2.split())
            registro_0150.BAIRRO = ''
            if resposta_participante.district:
                registro_0150.BAIRRO = str(resposta_participante.district.split())
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
        # adicionar Lista dos itens q tem estoque e nao estao aqui
        data_estoque = '%s 23:59:00' %(datetime.strftime(
            self.date_end, '%Y-%m-%d'))   
        context = dict(self.env.context, to_date=data_estoque)
        product = self.env['product.product'].with_context(context)
        resposta_inv = product.search([])
        produtos = []
        for inv in resposta_inv:
            if inv.qty_available > 0.0 and \
                inv.l10n_br_sped_type in ('00','01','02','03','04','05','06','10'):
                produtos.append(inv.id)
        un = ''
        lista_unk = []
        for prd in produtos:
            resposta_produto = self.env['product.product'].browse(prd)
            unidade = resposta_produto.uom_id.name
            unidade = unidade[:6].upper()
            if not resposta_produto:
                continue
            if un == resposta_produto.uom_id.name:
                continue 
            if resposta_produto.uom_id.name in lista_unk:        
                continue
            lista_unk.append(resposta_produto.uom_id.name)
            if resposta_produto.uom_id.name.upper() not in lista_un:        
                registro_0190 = registros.Registro0190()
                registro_0190.UNID = resposta_produto.uom_id.name
                registro_0190.DESCR = resposta_produto.uom_id.l10n_br_description
                lista.append(registro_0190)
                un = resposta_produto.uom_id.name
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
                        and ie.emissao_doc = '2'
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
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
                #desc_item = desc_item.encode('iso-8859-1')
                desc_item = resposta_produto.name.strip()
            except:
                desc_item = desc_item
            registro_0200.DESCR_ITEM = unidecode(desc_item)
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
        # adicionar Lista dos itens q tem estoque e nao estao aqui   
        data_estoque = '%s 23:59:00' %(datetime.strftime(
            self.date_end, '%Y-%m-%d'))
        context = dict(self.env.context, to_date=data_estoque)
        product = self.env['product.product'].with_context(context)
        resposta_inv = product.search([])
        produtos = []
        for inv in resposta_inv:
            if inv.qty_available > 0.0 and \
                inv.l10n_br_sped_type in ('00','01','02','03','04','05','06','10'): 
                produtos.append(inv.id)
        for prd in produtos:
            if prd not in lista_item:        
                resposta_produto = self.env['product.product'].browse(prd)
                if not resposta_produto:
                    continue
                registro_0200 = registros.Registro0200()
                cprod = resposta_produto.default_code
                registro_0200.COD_ITEM = cprod[:60]
                registro_0200.DESCR_ITEM = unidecode(resposta_produto.name.strip())
                if resposta_produto.barcode != resposta_produto.default_code:
                    registro_0200.COD_BARRA = resposta_produto.barcode
                if resposta_produto.uom_id.name.find('-') != -1:
                    unidade = resposta_produto.uom_id.name[:resposta_produto.uom_id.name.find('-')]
                else:
                    unidade = resposta_produto.uom_id.name
                registro_0200.UNID_INV = unidade[:6].upper()
                registro_0200.TIPO_ITEM = resposta_produto.l10n_br_sped_type
                registro_0200.COD_NCM = self.limpa_formatacao(resposta_produto.fiscal_classification_id.code)
                lista.append(registro_0200)
        return lista

    def query_registro0205(self, item):
        # TODO Caso não tenha ocorrido movimentação no período da \
        # alteração do item, deverá ser informada no primeiro período \
        # em que houver movimentação do item ou no inventário.
        lista = []
        # O valor informado deve ser menor que no campo DT_FIN do registro 0000. 
        # tem q buscar a partir do ultimo dia do mes anterior
        # pois, se alterou no ultimo dia nao entrou no arquivo anterior
        data_final = datetime.strptime('%s 23:59:00' %(datetime.strftime(
            self.date_end, '%Y-%m-%d')), '%Y-%m-%d %H:%M:%S')
        data_final = data_final - timedelta(days=1) 
        #data_final = datetime.strftime(data_final, '%Y-%m-%d %H:%M:%S') 
        data_ini = datetime.strptime('%s 01:00:00' %(datetime.strftime(
            self.date_end, '%Y-%m-%d')), '%Y-%m-%d %H:%M:%S')
        data_ini = data_ini - timedelta(days=1) 
        #data_ini = datetime.strftime(data_ini, '%Y-%m-%d %H:%M:%S') 
        resposta_produto = self.env['l10n_br.product.changes'].search([
            ('product_id.default_code','=',item),
            ('changed_date', '>=', data_ini),
            ('changed_date', '<=', data_final)
            ],limit=1,order='changed_date desc')
        ultima_alteracao = data_ini
        for alterado in resposta_produto:
            ultima_mudanca = self.env['l10n_br.product.changes'].search([
                ('product_id.default_code','=',item),
                ('changed_date', '<', ultima_alteracao)
                ],limit=1,order='changed_date desc')
            if ultima_mudanca:
                data_inicio = ultima_mudanca.changed_date
            else:
                data_inicio = alterado.product_id.create_date    
            registro_0205 = registros.Registro0205()
            if not alterado.old_value:
                continue
            desc_item = alterado.old_value
            if alterado.name == 'name':
                try:
                    desc_item = alterado.new_value.encode('iso-8859-1')
                    desc_item = alterado.old_value
                except:
                    desc_item = unidecode(alterado.old_value)
                registro_0205.DESCR_ANT_ITEM = unidecode(desc_item.strip())
                registro_0205.DT_INI = data_inicio
                registro_0205.DT_FIM = alterado.changed_date
                registro_0205.COD_ANT_ITEM = ''
            if alterado.name == 'default_code':
                registro_0205.DESCR_ANT_ITEM = ''
                registro_0205.DT_INI = data_inicio
                registro_0205.DT_FIM = alterado.changed_date
                registro_0205.COD_ANT_ITEM = alterado.old_value
            ultima_alteracao = alterado.changed_date
            lista.append(registro_0205)
        return lista

    def query_registro0220(self, ITEM, periodo):
        query = """
            select distinct
                   sum(dl.quantity) as fatura
                   ,sum(it.quantidade) as xml
                   ,UPPER(TRIM(pu.name))
                   ,it.product_id
                   ,UPPER(TRIM(uom_edoc.name))
                    from
                        invoice_eletronic as ie                
                    inner join
                        invoice_eletronic_item as it
                            on ie.id = it.invoice_eletronic_id
                    inner join 
                        account_invoice_line as dl
                            on dl.invoice_id = ie.invoice_id
                            and dl.product_id = it.product_id
                    inner join
                        product_product p
                            on p.id = it.product_id
                    inner join
                        product_template pt
                            on p.product_tmpl_id = pt.id                            
                    inner join
                        uom_uom pu
                            on pu.id = pt.uom_id
                    inner join
                        uom_uom as uom_edoc
                            on uom_edoc.id = it.uom_id                            
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state = 'done'
                        and ie.emissao_doc = '2' 
                        and UPPER(TRIM(pu.name)) <> UPPER(TRIM(uom_edoc.name))
                        and p.default_code = '%s'
                        group by it.product_id, pu.name, uom_edoc.name 
                """ % (periodo, ITEM)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for resposta in query_resposta:
            registro_0220 = registros.Registro0220()
            conversao = 0.0
            if resposta[1] > 0.01:
                conversao = resposta[0]/resposta[1]
            try:
                registro_0220.UNID_CONV = str(resposta[4][:6])
                registro_0220.FAT_CONV = conversao
            except:
                x_error = 'Erro, fator conversao : %s - %s' %(str(resposta[4][:6]), str(conversao))
                raise UserError(x_error)
            lista.append(registro_0220)
        return lista
        
    def query_registro0400(self, periodo):
        query = """
                    select distinct
                        ie.fiscal_position_id
                    from
                        invoice_eletronic as ie
                    where
                        %s
                        and (ie.model in ('55','01'))
                        and ie.state in ('done','cancel')
                        and ie.emissao_doc = '2'
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        for resposta in query_resposta:
            resposta_nat = self.env['account.fiscal.position'].browse(resposta[0])
            registro_0400 = registros.Registro0400()
            registro_0400.COD_NAT = str(resposta_nat.id)
            registro_0400.DESCR_NAT = unidecode(resposta_nat.l10n_br_operation)
            lista.append(registro_0400)
        return lista        

    def transforma_valor(self, valor):
        #valor = ("%.2f" % (float(valor)))
        #return str(valor).replace('.', ',')
        return valor

    def query_registroC100(self, nf):
        lista = []
        nfe_ids = self.env['invoice.eletronic'].browse(nf)
        for nfe in nfe_ids:    
            # removendo Emissao de Terceiros canceladas
            if nfe.emissao_doc == '2' and nfe.state == 'cancel':
                return True
            cancel = False 
            registro_c100 = registros.RegistroC100()
            if nfe.tipo_operacao == 'entrada':
                registro_c100.IND_OPER = '0'
            else:
                registro_c100.IND_OPER = '1'
            if nfe.emissao_doc == '1':    
                registro_c100.IND_EMIT = '0'
            else:
                registro_c100.IND_EMIT = '1'
            registro_c100.COD_MOD = nfe.model
            if nfe.state == 'cancel':
                registro_c100.COD_SIT = '02'
                cancel = True
            elif nfe.finalidade_emissao == '1':
                registro_c100.COD_SIT = '00'
            elif nfe.finalidade_emissao == '2':
                registro_c100.COD_SIT = '06'                    
            elif nfe.finalidade_emissao == '4':
                registro_c100.COD_SIT = '00'                    
            elif nfe.state  == 'denied':
                registro_c100.COD_SIT = '04'                    
            if not nfe.state == 'cancel' and nfe.chave_nfe[6:20] != \
                self.limpa_formatacao(nfe.partner_id.cnpj_cpf):
                registro_c100.COD_SIT = '08'                    
            if nfe.serie_documento:
                registro_c100.SER = nfe.serie_documento
            if nfe.chave_nfe:
                registro_c100.CHV_NFE = nfe.chave_nfe
            registro_c100.NUM_DOC = self.limpa_formatacao(str(nfe.numero))
            if not cancel:
                try:
                    registro_c100.DT_DOC = nfe.data_emissao
                    if nfe.data_fatura:
                        registro_c100.DT_E_S = nfe.data_fatura
                    else:
                        registro_c100.DT_E_S = nfe.data_emissao
                except:
                    msg_err = 'Data Emissao Fatura %s , invalida. \
                        <br />' %(str(nfe.numero or nfe.id))
                    self.log_faturamento += msg_err
                if nfe.duplicata_ids:
                    if len(nfe.duplicata_ids) == 1:
                        if nfe.duplicata_ids.data_vencimento == nfe.data_agendada:
                            registro_c100.IND_PGTO = '0'
                        else:
                            registro_c100.IND_PGTO = '1'
                    else:
                        registro_c100.IND_PGTO = '1'
                else:
                    registro_c100.IND_PGTO = '2'
                registro_c100.VL_MERC = nfe.valor_bruto
                registro_c100.IND_FRT = str(nfe.modalidade_frete)
                registro_c100.VL_FRT = nfe.valor_frete
                registro_c100.VL_SEG = nfe.valor_seguro
                registro_c100.VL_OUT_DA = nfe.valor_despesas
                registro_c100.VL_DESC = nfe.valor_desconto
                registro_c100.VL_DOC  = nfe.valor_final
                registro_c100.VL_BC_ICMS = nfe.valor_bc_icms
                registro_c100.VL_ICMS = nfe.valor_icms
                registro_c100.VL_BC_ICMS_ST = nfe.valor_bc_icmsst
                registro_c100.VL_ICMS_ST = nfe.valor_icmsst
                registro_c100.VL_IPI = nfe.valor_ipi
                registro_c100.VL_PIS = nfe.valor_pis
                registro_c100.VL_COFINS = nfe.valor_cofins
                registro_c100.COD_PART = str(nfe.partner_id.id)
            lista.append(registro_c100)                
        return lista
                
    def query_registroC101(self, nf):
        query = """
                    select 
                        sum(ie.valor_icms_uf_remet) as icms_uf_remet, 
                        sum(ie.valor_icms_uf_dest) as icms_uf_dest,
                        sum(ie.valor_icms_fcp_uf_dest) as fcp_uf_dest,
                        ie.tipo_operacao
                    from
                        invoice_eletronic as ie
                    where
                        ie.id = '%s'
                        and (ie.model in ('55', '1'))
                        and ie.state in ('done')
                        and ((ie.valor_icms_uf_dest > 0) or 
                        (ie.valor_icms_uf_remet > 0))
                    group by ie.tipo_operacao
                """ % (nf)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
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

    def query_registroC170(self, nf):
        lista = []
        nfe_line = self.env['invoice.eletronic.item'].search([
                ('invoice_eletronic_id','=', nf),
                ], order='num_item')
        n_item = 1
        for item in nfe_line:
            registro_c170 = registros.RegistroC170()
            # TODO precisa corrigir no br_nfe para gravar o num_item nota
            # saida
            if item.num_item > 1:
                registro_c170.NUM_ITEM = str(item.num_item)
            else:
                registro_c170.NUM_ITEM = str(n_item)
            cprod = item.product_id.default_code
            registro_c170.COD_ITEM = cprod
            registro_c170.DESCR_COMPL = self.limpa_caracteres(item.name.strip())
            registro_c170.QTD = self.transforma_valor(item.quantidade)
            if not item.uom_id:
                msg_err = 'Sem cadastro UN : %s, NF : %s' %(item.name.strip(), nf.numero)
                raise UserError(msg_err)                    
            if item.uom_id.name.find('-') != -1:
                unidade = item.uom_id.name[:item.uom_id.name.find('-')]
            else:
                unidade = item.uom_id.name
            registro_c170.UNID = unidade[:6].strip()
            registro_c170.VL_DESC = item.desconto
            registro_c170.VL_ITEM = item.valor_bruto
            if item.cfop in ['5922', '6922']:
                registro_c170.IND_MOV = '1'
            else:
                registro_c170.IND_MOV = '0'
            try:
                registro_c170.CST_ICMS = item.product_id.origin + item.icms_cst
            except:
                msg_err = 'Sem CST na Fatura %s. <br />' %(
                    str(item.invoice_eletronic_id.numero or 
                    item.invoice_eletronic_id.id))
                self.log_faturamento += msg_err
            if item.cfop:
                registro_c170.CFOP = str(item.cfop)
            else:
                registro_c170.CFOP = '0000'
            registro_c170.COD_NAT = str(item.invoice_eletronic_id.fiscal_position_id.id)
            registro_c170.VL_BC_ICMS = item.icms_base_calculo
            registro_c170.ALIQ_ICMS = '0'
            registro_c170.ALIQ_ICMS = item.icms_aliquota
            registro_c170.VL_ICMS = item.icms_valor
            registro_c170.VL_BC_ICMS_ST = item.icms_st_base_calculo
            if item.icms_st_aliquota:
                registro_c170.ALIQ_ST = item.icms_st_aliquota
            registro_c170.VL_ICMS_ST = item.icms_st_valor
            registro_c170.IND_APUR = self.ind_apur
            registro_c170.CST_IPI = item.ipi_cst
            registro_c170.VL_BC_IPI = item.ipi_base_calculo
            if item.ipi_aliquota:
                registro_c170.ALIQ_IPI = item.ipi_aliquota
            registro_c170.VL_IPI = item.ipi_valor
            registro_c170.CST_PIS = item.pis_cst
            registro_c170.VL_BC_PIS = item.pis_base_calculo
            if item.pis_aliquota:
                registro_c170.ALIQ_PIS = item.pis_aliquota
            registro_c170.VL_PIS = item.pis_valor
            registro_c170.CST_COFINS = item.cofins_cst
            registro_c170.VL_BC_COFINS = item.cofins_base_calculo
            if item.cofins_aliquota:
                registro_c170.ALIQ_COFINS = item.cofins_aliquota
            registro_c170.VL_COFINS = item.cofins_valor
            n_item += 1
            lista.append(registro_c170)
        return lista
        
    def query_registroC190(self, nf):
        query = """
                select distinct
                        it.origem || it.icms_cst, it.cfop,
                        COALESCE(it.icms_aliquota, 0.0) as ALIQUOTA ,
                        sum(it.valor_liquido) as VL_OPR,
                        sum(it.icms_base_calculo) as VL_BC_ICMS,
                        sum(it.icms_valor) as VL_ICMS,
                        sum(it.icms_st_base_calculo) as VL_BC_ICMS_ST,
                        sum(it.icms_st_valor) as VL_ICMS_ST,
                        case when (cast(it.icms_aliquota_reducao_base as integer) > 0) then
                          sum((it.valor_liquido)-it.icms_base_calculo) else 0 end as VL_RED_BC, 
                        sum(it.ipi_valor) as VL_IPI, 
                        sum(it.icms_fcp_uf_dest), 
                        it.icms_cst
                    from
                        invoice_eletronic ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where    
                        ie.model in ('55', '1')
                        and ie.state = 'done'
                        and ie.id = '%s'
                    group by 
                        cast(it.icms_aliquota_reducao_base as integer),
                        it.icms_cst,
                        it.cfop,
                        it.icms_aliquota,
                        it.origem 
                    order by 1,2,3    
                """ % (nf)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_c190 = registros.RegistroC190()
            registro_c190.CST_ICMS = id[0]
            registro_c190.CFOP = id[1]
            registro_c190.ALIQ_ICMS = id[2]
            registro_c190.VL_OPR = id[3]
            registro_c190.VL_BC_ICMS = id[4]
            registro_c190.VL_ICMS = id[5]
            registro_c190.VL_BC_ICMS_ST = id[6]
            registro_c190.VL_ICMS_ST = id[7]
            registro_c190.VL_RED_BC = id[8]
            registro_c190.VL_IPI = id[9]
            lista.append(registro_c190)
            """
            registro_c191 = registros.RegistroC191()
            if id[11] in ('00','10','20','51','70','90'):
                registro_c191.VL_FCP_OP = id[10]
            if id[11] in ('10','30','70','90'):
                registro_c191.VL_FCP_ST = 0.0
            if id[11] == '60':
                registro_c191.VL_FCP_RET = id[10]
            lista.append(registro_c191)
            
            registro_c195 = registros.RegistroC195()
            registro_c195.COD_OBS = ''
            registro_c195.TXT_COMPL = ''
            lista.append(registro_c195)
            
            registro_c197 = registros.RegistroC197()
            registro_c197.COD_AJ = ''
            registro_c197.DESCR_COMPL_AJ = ''
            registro_c197.COD_ITEM = ''
            registro_c197.VL_BC_ICMS = 0.0
            registro_c197.ALIQ_ICMS = 0.0
            registro_c197.VL_ICMS = 0.0
            registro_c197.VL_OUTROS = 0.0
            lista.append(registro_c197)
            
            registro_C300 = RegistroC300()
            registro_C300.COD_MOD = ''
            registro_C300.SER = ''
            registro_C300.SUB = ''
            registro_C300.NUM_DOC_INI = 0.0
            registro_C300.NUM_DOC_FIN = 0.0
            registro_C300.DT_DOC = ''
            registro_C300.VL_DOC = 0.0
            registro_C300.VL_PIS = 0.0
            registro_C300.VL_COFINS = 0.0
            registro_C300.COD_CTA = ''
            lista.append(registro_C300)
            """
        return lista

    # transporte
    def query_registroD100(self, cte):
        lista = []
        cte_ids = self.env['invoice.eletronic'].browse(cte)
        for cte in cte_ids:
            registro_d100 = registros.RegistroD100()
            if cte.tipo_operacao == 'entrada':
                registro_d100.IND_OPER = '0' # Aquisicao
            else:
                registro_d100.IND_OPER = '1' # Prestação
            if cte.emissao_doc == 2:
                registro_d100.IND_EMIT = '1' # Terceiros
            else:
                registro_d100.IND_EMIT = '0' # Propria
            registro_d100.COD_PART = str(cte.partner_id.id)
            registro_d100.COD_MOD = str(cte.model)
            if cte.tp_emiss_cte == '1':
               registro_d100.COD_SIT = '00'
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
            registro_d100.SER = cte.serie_documento
            if cte.chave_nfe:
                registro_d100.CHV_CTE = str(cte.chave_nfe)
            registro_d100.NUM_DOC = self.limpa_formatacao(str(cte.numero))
            registro_d100.DT_A_P = cte.data_fatura or cte.date_invoice
            registro_d100.DT_DOC = cte.data_emissao or cte.date_invoice
            registro_d100.VL_DOC = cte.valor_final
            registro_d100.VL_DESC = cte.valor_desconto
            registro_d100.IND_FRT = cte.modalidade_frete
            registro_d100.VL_SERV = cte.valor_final
            registro_d100.VL_BC_ICMS = cte.valor_bc_icms
            registro_d100.VL_ICMS = cte.valor_icms
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
    def query_registroD190(self, nf):
        query = """
                select distinct
                        it.origem || it.icms_cst, it.cfop,
                        COALESCE(it.icms_aliquota, 0.0) as ALIQUOTA ,
                        sum(it.valor_liquido) as VL_OPR,
                        sum(it.icms_base_calculo) as VL_BC_ICMS,
                        sum(it.icms_valor) as VL_ICMS,
                        sum(it.icms_st_base_calculo) as VL_BC_ICMS_ST,
                        sum(it.icms_st_valor) as VL_ICMS_ST,
                        case when (cast(it.icms_aliquota_reducao_base as integer) > 0) then
                          sum((it.valor_liquido)-it.icms_base_calculo) else 0 end as VL_RED_BC, 
                        sum(it.ipi_valor) as VL_IPI               
                    from
                        invoice_eletronic ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where    
                        ie.model in ('57','67')
                        and ie.state = 'done'
                        and ie.id = '%s'
                    group by 
                        it.icms_aliquota_reducao_base,
                        it.icms_aliquota,
                        it.icms_cst,
                        it.cfop,
                        it.valor_liquido,
                        it.origem 
                    order by 1,2,3    
                """ % (nf)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_d190 = registros.RegistroD190()
            registro_d190.CST_ICMS = id[0]
            registro_d190.CFOP = id[1]
            registro_d190.ALIQ_ICMS = id[2]
            registro_d190.VL_OPR = id[3]
            registro_d190.VL_BC_ICMS = id[4]
            registro_d190.VL_ICMS = id[5]
            registro_d190.VL_RED_BC = id[8]
            registro_d190.COD_OBS = ''
            lista.append(registro_d190)
        return lista

    def query_registroE110(self, periodo):
        #SAIDA
        query = """
                select  
                    sum(COALESCE(ie.valor_icms,0.0)) as VL_ICMS 
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where
                        %s 
                        and (ie.model in ('55','1','57','67'))
                        and (ie.state = 'done')
                        and ((substr(it.cfop, 1,1) in ('5','6','7')) or 
                            (it.cfop = '1605'))
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        registro_E110 = RegistroE110()
        sld_transp = 0.0
        sld_icms = 0.0
        for id in query_resposta:
            if not id[0]:
                continue
            registro_E110.VL_TOT_DEBITOS = id[0]
            if id[0]:
                sld_icms = id[0]
                sld_transp = id[0]
        #ENTRADA
        query = """
                select  
                    sum(COALESCE(ie.valor_icms,0.0)) as VL_ICMS 
                    from
                        invoice_eletronic as ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where
                        %s    
                        and (ie.model in ('55','1','57','67'))
                        and (ie.state = 'done')
                        and (((substr(it.cfop, 1,1) in ('1','2','3')) 
                        and it.cfop not in ('1605')) or (it.cfop = '5605'))
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        for id in query_resposta:
            registro_E110.VL_TOT_CREDITOS = self.transforma_valor(id[0])
            if not id[0]:
                registro_E110.VL_ICMS_RECOLHER = self.transforma_valor(sld_icms)
                registro_E110.VL_SLD_APURADO = self.transforma_valor(sld_icms)
                continue
            if id[0] > sld_icms:
                sld_icms = id[0] - sld_icms
                registro_E110.VL_ICMS_RECOLHER = '0'
                registro_E110.VL_SLD_APURADO = '0'
            else:
                sld_icms = sld_icms - id[0]
                registro_E110.VL_ICMS_RECOLHER = self.transforma_valor(sld_icms)
                registro_E110.VL_SLD_APURADO = self.transforma_valor(sld_icms)
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
        registro_E110.VL_TOT_DED = '0'
        registro_E110.VL_SLD_CREDOR_TRANSPORTAR = self.transforma_valor(sld_transp)
        registro_E110.DEB_ESP = '0'
        lista.append(registro_E110)
        registro_E116 = RegistroE116()
        registro_E116.COD_OR = self.cod_obrigacao
        registro_E116.VL_OR = self.transforma_valor(sld_icms)
        registro_E116.DT_VCTO = self.data_vencimento_e316
        # remover
        #'%s%s%s' %(
        #    str(self.data_vencimento_e316.day).zfill(2), 
        #    str(self.data_vencimento_e316.month).zfill(2), 
        #    str(self.data_vencimento_e316.year))
        registro_E116.COD_REC = self.cod_receita
        #registro_E116.NUM_PROC
        #registro_E116.IND_PROC 
        #registro_E116.PROC
        #registro_E116.COMPL
        registro_E116.MES_REF = '%s%s' %(
            str(self.date_start.month).zfill(2), 
            str(self.date_start.year))
        lista.append(registro_E116)
        return lista

    def query_registroE200(self, periodo):
        query = """
                select distinct
                        rs.code
                    from
                        invoice_eletronic ie
                    inner join
                        res_partner rp
                            on rp.id = ie.partner_id
                    inner join
                        res_country_state rs
                            on rs.id = rp.state_id
                    where
                        %s
                        and (ie.model in ('55','1'))
                        and ie.state = 'done'
                        and ie.valor_icmsst > 0
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_e200 = registros.RegistroE200()
            registro_e200.DT_INI = self.date_start
            registro_e200.DT_FIN = self.date_end
            registro_e200.UF = str(id[0])
            lista.append(registro_e200)
        return lista

    def query_registroE210(self, uf, periodo):
        query = """
                select sum(ie.valor_icmsst),
                       sum(ie.valor_br_icmsst)
                    from
                        invoice_eletronic ie
                    inner join
                        res_partner rp
                            on rp.id = ie.partner_id
                    inner join
                        res_country_state rs
                            on rs.id = rp.state_id
                    where
                        %s    
                        and (ie.model in ('55','1'))
                        and ie.state = 'done'
                        and ie.valor_icmsst > 0
                        and rs.code = '%s'
                """ % (periodo, uf)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_e210 = registros.RegistroE210()
            registro_e210.IND_MOV_ST = '1'
            registro_e210.VL_ICMS_RECOL_ST = '0'
            registro_e210.VL_RETENCAO_ST = '0'
            registro_e210.VL_SLD_CRED_ANT_ST = '0'
            registro_e210.VL_DEVOL_ST = '0'
            registro_e210.VL_RESSARC_ST = '0'
            registro_e210.VL_OUT_CRED_ST = id[0]
            registro_e210.VL_AJ_CREDITOS_ST = '0'
            registro_e210.VL_OUT_DEB_ST = '0'
            registro_e210.VL_AJ_DEBITOS_ST = '0'
            registro_e210.VL_SLD_DEV_ANT_ST = '0'
            registro_e210.VL_DEDUCOES_ST = '0'
            registro_e210.VL_SLD_CRED_ST_TRANSPORTAR = id[0]
            registro_e210.DEB_ESP_ST = '0'
            lista.append(registro_e210)
        return lista

    def query_registroE300(self, periodo):
        query = """
                    select distinct 
                        rs.code, rp.state_id
                    from
                        invoice_eletronic ie
                    inner join
                        res_partner as rp
                            on rp.id = ie.partner_id
                    inner join
                        res_country_state as rs
                            on rs.id = rp.state_id                            
                    where
                        %s
                        and (ie.model in ('55','1'))
                        and ie.state = 'done'
                        and ((ie.valor_icms_uf_dest > 0) or 
                        (ie.valor_icms_uf_remet > 0))
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        uf_emitente = ''
        for id in query_resposta:
            if id[0] == self.company_id.state_id.code:
                uf_emitente = self.company_id.state_id.code
            registro_e300 = registros.RegistroE300()
            registro_e300.UF = self.limpa_formatacao(id[0])
            registro_e300.DT_INI = self.date_start
            registro_e300.DT_FIN = self.date_end
            lista.append(registro_e300)
        if not uf_emitente and query_resposta:
            registro_e300 = registros.RegistroE300()
            registro_e300.UF = self.limpa_formatacao(self.company_id.state_id.code)
            registro_e300.DT_INI = self.date_start
            registro_e300.DT_FIN = self.date_end
            lista.append(registro_e300)
        return lista

    def query_registroE310(self, uf_informante, uf_dif, periodo):
        if uf_informante != uf_dif:
            tipo_mov = '1'
            query = """
                    select 
                        sum(ie.valor_icms_uf_dest) as icms_uf_dest,
                        0,
                        sum(ie.valor_icms_fcp_uf_dest) as fcp_uf_dest,
                        ie.tipo_operacao
                    from
                        invoice_eletronic ie
                    inner join
                        res_partner as rp
                            on rp.id = ie.partner_id
                    inner join
                        res_country_state as rs
                            on rs.id = rp.state_id                                                        
                    where
                        %s
                        and (ie.model in ('55','1'))
                        and (ie.state = 'done'))
                        and ((ie.valor_icms_uf_dest > 0) or 
                        (ie.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                    group by ie.tipo_operacao
                """ % (periodo, uf_dif)
        else:   
            # mesmo uf
            tipo_mov = '0'
            query = """
                    select 
                        sum(ie.valor_icms_uf_remet) as icms_uf_remet,
                        0, 
                        sum(ie.valor_icms_fcp_uf_dest) as fcp_uf_dest,
                        ie.tipo_operacao
                    from
                        invoice_eletronic ie
                    inner join
                        res_partner as rp
                            on rp.id = ie.partner_id
                    inner join
                        res_country_state as rs
                            on rs.id = rp.state_id                                                        
                    where
                        %s
                        and (ie.model in ('55','1'))
                        and (ie.state = 'done'))
                        and ((ie.valor_icms_uf_dest > 0) or 
                        (ie.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                    group by ie.tipo_operacao
                """ % (periodo, uf_informante)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        registro_e310 = registros.RegistroE310()
        lista = []
        for id in query_resposta:
            registro_e310.IND_MOV_FCP_DIFAL = tipo_mov
            registro_e310.VL_SLD_CRED_ANT_DIFAL = self.vl_sld_cred_ant_difal
            registro_e310.VL_TOT_DEBITOS_DIFAL = id[0]
            registro_e310.VL_OUT_DEB_DIFAL = '0'
            registro_e310.VL_TOT_DEB_FCP = id[2]
            registro_e310.VL_TOT_CREDITOS_DIFAL = '0'
            registro_e310.VL_TOT_CRED_FCP = '0'
            registro_e310.VL_OUT_CRED_DIFAL = '0'
            registro_e310.VL_SLD_DEV_ANT_DIFAL = id[0]
            registro_e310.VL_DEDUCOES_DIFAL = '0'
            registro_e310.VL_RECOL_DIFAL = id[0]
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
        
        registro_e316 = registros.RegistroE316()
        if not self.data_vencimento_e316:
            raise UserError('Erro, a data de vencimento (E-316) não informada.')
        
        for id in query_resposta:
            registro_e316.COD_OR = self.cod_obrigacao
            registro_e316.VL_OR = id[0]+id[2]
            registro_e316.DT_VCTO = self.data_vencimento_e316
            registro_e316.COD_REC = self.cod_receita
            registro_e316.NUM_PROC = ''
            registro_e316.IND_PROC = ''
            registro_e316.PROC = ''
            registro_e316.TXT_COMPL = ''
            registro_e316.MES_REF = data
        lista.append(registro_e316)
        return lista

    # remover se funcionou acima
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
                        invoice_eletronic ie
                            on ie.invoice_id = d.id
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
                        and ((ie.state is null) or (ie.state = 'done'))
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and rs.code = '%s'
                        and %s
                    group by fp.fiscal_type
                """ % (uf_dif, periodo)
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
                        invoice_eletronic ie
                            on ie.invoice_id = d.id
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
                        and ((ie.state is null) or (ie.state = 'done'))
                        and d.fiscal_position_id is not null 
                        and ((d.valor_icms_uf_dest > 0) or 
                        (d.valor_icms_uf_remet > 0))
                        and %s
                    group by fp.fiscal_type
                """ % (periodo)
        """
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        registro_e316 = registros.RegistroE316()
        lista = []
        data = self.data_vencimento_e316
        data = str(data.month).zfill(2) + str(data.year)

        if not self.data_vencimento_e316:
            raise UserError('Erro, a data de vencimento (E-316) não informada.')
        
        for id in query_resposta:
            registro_e316.COD_OR = self.cod_obrigacao
            registro_e316.VL_OR = self.transforma_valor(id[0]+id[2])
            registro_e316.DT_VCTO = self.data_vencimento_e316
            registro_e316.COD_REC = self.cod_receita
            registro_e316.NUM_PROC = ''
            registro_e316.IND_PROC = ''
            registro_e316.PROC = ''
            registro_e316.TXT_COMPL = ''
            registro_e316.MES_REF = data
            
        lista.append(registro_e316)
        return lista
        """
        
    def query_registroE510(self, periodo):
        query = """
                select distinct
                        it.ipi_cst,
                        it.cfop,
                        sum(it.ipi_base_calculo) as VL_BC_IPI,
                        sum(it.ipi_valor) as VL_IPI
                    from
                        invoice_eletronic ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where    
                        %s
                        and (ie.model in ('55', '1'))
                        and (ie.state = 'done')
                    group by it.ipi_cst,
                        it.cfop
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        cont = 1
        for id in query_resposta:
            registro_E510 = RegistroE510()
            registro_E510.CFOP = str(id[1])
            registro_E510.CST_IPI = str(id[0])
            registro_E510.VL_CONT_IPI = '0'
            registro_E510.VL_BC_IPI = id[2]
            registro_E510.VL_IPI = id[3]
            lista.append(registro_E510)
        return lista

    def query_registroE520(self, periodo):
        query = """
                select 
                       sum(COALESCE(ie.valor_ipi,0.0)) as VL_IPI
                    from
                        invoice_eletronic ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where    
                        %s
                        and (ie.model in ('55', '1'))
                        and (ie.state = 'done')
                        and substr(it.cfop, 1,1) in ('5','6')
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        lista = []
        registro_E520 = RegistroE520()
        sld_ipi = 0.0
        for id in query_resposta:
            if not id[0]:
                continue
            registro_E520.VL_DEB_IPI = self.transforma_valor(id[0])
            if id[0]:
                sld_ipi = id[0]
        registro_E520.VL_SD_ANT_IPI = '0'            
        registro_E520.VL_OD_IPI = '0'
        registro_E520.VL_OC_IPI = '0'
        query = """
                select 
                       sum(COALESCE(ie.valor_ipi,0.0)) as VL_IPI
                    from
                        invoice_eletronic ie
                    inner join
                        invoice_eletronic_item it
                        on it.invoice_eletronic_id = ie.id
                    where    
                        %s
                        and (ie.model in ('55', '1'))
                        and (ie.state = 'done')
                        and substr(it.cfop, 1,1) in ('1','2','3')
                """ % (periodo)
        self._cr.execute(query)
        query_resposta = self._cr.fetchall()
        for id in query_resposta:            
            registro_E520.VL_CRED_IPI = self.transforma_valor(id[0])
            if id[0] and id[0] > sld_ipi:
               sld_ipi = id[0] - sld_ipi
               registro_E520.VL_SC_IPI = self.transforma_valor(sld_ipi)
               registro_E520.VL_SD_IPI = '0'
            else:
               if id[0]:
                   sld_ipi = sld_ipi - id[0]
               registro_E520.VL_SD_IPI = self.transforma_valor(sld_ipi)
               registro_E520.VL_SC_IPI = '0'
        lista.append(registro_E520)
        return lista

    def query_registroK200(self):
        lista = []
        data_estoque = '%s 23:59:00' %(datetime.strftime(
            self.date_end, '%Y-%m-%d'))
        context = dict(self.env.context, to_date=data_estoque)
        product = self.env['product.product'].with_context(context)
        resposta_inv = product.search([])
        for inv in resposta_inv:
            if inv.qty_available > 0.0 and \
                inv.l10n_br_sped_type in ('00','01','02','03','04','05','06','10'):
                registro_K200 = RegistroK200()                                                                                                           
                registro_K200.DT_EST = self.date_end
                registro_K200.COD_ITEM = inv.default_code
                registro_K200.QTD = inv.qty_available
                registro_K200.IND_EST = '0'
                lista.append(registro_K200)
        return lista
