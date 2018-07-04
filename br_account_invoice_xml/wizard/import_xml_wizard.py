# -*- coding: utf-8 -*-
from odoo import api, fields, models
import base64
import re
from datetime import datetime
from datetime import timedelta
from odoo.exceptions import UserError
from lxml import objectify
from pytrustnfe.nfe import consulta_distribuicao_nfe
from pytrustnfe.nfe import download_nfe
from pytrustnfe.nfe import recepcao_evento_manifesto
from pytrustnfe.nfe import xml_consulta_distribuicao_nfe
from pytrustnfe.certificado import Certificado

class ImportXmlWizard(models.TransientModel):

    _name='import.xml.wizard'

    not_found_product = fields.Many2many('not.found.products', string="Produtos não encontrados")
    fatura = fields.Integer(string = 'Fatura de origem')
    cnpj = fields.Char(string='CNPJ')
    confirma = fields.Boolean(string='Todos os produtos encontrados', default=False)
    data_entrada = fields.Date(string='Data Entrada')
    nfe_xml = fields.Binary(u'XML da NFe')
    localiza_produto = fields.Boolean(string='Usar Cadastro se existir.', default=True)
    #Criar campo que eu não sei, que vai armazenar todas as NFes
    #nfe_ids = fields.Many2one('receita.nfes',string='Nota fiscais')
    #-----------------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------------ROTINA DE IMPORTAÇÃO---------------------------------------------------#
    #-----------------------------------------------------------------------------------------------------------------------------#

    def retorna_data(self, ide):
        
        day_emissao = str(ide.dhEmi).split('T')
        hour_emissao = day_emissao[1].split('-')
        if hour_emissao[0] == '00:00:00':
            datehour_emissao = day_emissao[0] + ' ' + '03:00:01'
            dt = datetime.strptime(datehour_emissao, '%Y-%m-%d %H:%M:%S')
        else:
            datehour_emissao = day_emissao[0] + ' ' + hour_emissao[0]
            dt = datetime.strptime(datehour_emissao, '%Y-%m-%d %H:%M:%S')
            dt = dt + timedelta(hours=+3)
        datetime_obj_emissao = dt #datetime.strptime(, '%Y-%m-%d %H:%M:%S')
        return datetime_obj_emissao

    def arruma_cpf_cnpj(self, partner_doc):        
        if len(partner_doc) > 11:
            partner_doc = partner_doc.zfill(14)
            partner_doc = "%s.%s.%s/%s-%s" % ( partner_doc[0:2], partner_doc[2:5], partner_doc[5:8], partner_doc[8:12], partner_doc[12:14] )
        else:
            partner_doc = partner_doc.zfill(11)
            partner_doc = "%s.%s.%s-%s" % (partner_doc[0:3], partner_doc[3:6], partner_doc[6:9], partner_doc[9:11])
        return partner_doc

    def get_invoice_eletronic_vals(self, nfe, fatura, edoc):
        if not edoc:
            raise UserError(
                'Fatura não é do Tipo NFe ou Cte')

        if fatura.product_document_id.code == '55' or self._context.get('tipo') == '55':
            try:
                ide = nfe.NFe.infNFe.ide            
                dest = nfe.NFe.infNFe.dest
                emit = nfe.NFe.infNFe.emit
                protNFe = nfe.protNFe.infProt
                finalidade = '%d' % ide.finNFe
                numero = ide.nNF
                serie = ide.serie
                numero_controle = ide.cNF
                chave_nfe = protNFe.chNFe
                protocolo = protNFe.nProt
                motivo = protNFe.xMotivo
                nome = 'Documento %d' % ide.nNF
            except:
                raise UserError(
                    'Tipo do XML diferente do documento na fatura')

        if fatura.product_document_id.code in ('57','67') or self._context.get('tipo') in ('57','67'):
            try:
                if fatura.product_document_id.code == '57' or self._context.get('tipo') == '57':
                    ide = nfe.CTe.infCte.ide            
                    dest = nfe.CTe.infCte.dest
                    emit = nfe.CTe.infCte.emit
                if fatura.product_document_id.code == '67' or self._context.get('tipo') == '67':
                    ide = nfe.CTeOS.infCte.ide            
                    dest = nfe.CTeOS.infCte.toma
                    emit = nfe.CTeOS.infCte.emit
                    
                protNFe = nfe.protCTe.infProt
                finalidade = '%d' % ide.tpEmis
                numero = ide.nCT
                serie = ide.serie
                numero_controle = ide.cCT
                chave_nfe = protNFe.chCTe
                protocolo = protNFe.nProt
                motivo = protNFe.xMotivo
                mun_origem = ide.cMunIni
                mun_destino = ide.cMunFim
                nome = 'Documento + %d' % ide.nCT
            except:
                raise UserError(
                    'Tipo do XML diferente do documento na fatura')
                
        partner_doc = emit.CNPJ if hasattr(emit, 'CNPJ') else emit.CPF
        partner_doc = str(partner_doc)
        partner_doc = self.arruma_cpf_cnpj(partner_doc)
        
        partner = self.env['res.partner'].search([
            ('cnpj_cpf', '=', partner_doc)])
        if not partner:
            raise UserError(
                'Fornecedor não encontrado, por favor, crie um fornecedor com CPF/CNPJ igual a ' + partner_doc)
        partner_ok = False
                
        for prt in partner:        
            if prt.id == fatura.partner_id.id:
                partner_ok = True
        if not partner_ok:        
            raise UserError(
                'Fornecedor do XML diferente do Fornecedor da Fatura.')

        data_emissao = self.retorna_data(ide)
        model = '%d' % ide.mod
        if ide.tpAmb == 1:
            ambiente = 'producao'
        else:
            ambiente = 'homologacao'
        
        company_id = fatura.company_id.id
        
        itens = []
        if fatura.product_document_id.code == '55' or self._context.get('tipo') == '55':
            itens = self.get_itens(nfe,edoc)
        
        data_entrada = self.data_entrada + ' ' + '15:00:00'
        vals = {
            'tipo_operacao':'entrada',
            'model':model,
            'numero':int(numero),
            'name':nome,
            'data_emissao':data_emissao,
            'data_fatura':data_entrada,
            'serie_documento':str(serie),
            'ambiente':ambiente,
            'finalidade_emissao':finalidade,
            'state': 'done',
            'emissao_doc': '2',
            'chave_nfe': int(chave_nfe),
            'protocolo_nfe': int(protocolo),
            'codigo_retorno': str(motivo),
        }
        if self._context.get('tipo') == '57':
            vals['cod_mun_ini'] = mun_origem
            vals['cod_mun_fim'] = mun_destino
        return vals
        
    #Função que cria os itens da NFe
    def create_order_line(self, item, nfe, edoc, num_item):
        uom_id = self.env['product.uom'].search([
            ('name', '=ilike', str(item.prod.uCom))], limit=1).id
        if not uom_id:
            uom_id = self.env['product.uom'].create({'type_uom':'ext','name':str(item.prod.uCom),'category_id':4}).id
        product = ''
        if item.prod.cEAN:
            product = self.env['product.product'].search([
                ('barcode', '=', item.prod.cEAN)], limit=1)
        if not product:
            product_code = self.env['product.supplierinfo'].search([
                ('product_code', '=', item.prod.cProd), ('name', '=', edoc.partner_id.id)
            ],limit=1)
            product = self.env['product.product'].browse(product_code.product_id.id)
        if not product:
            if self.not_found_product:
                for line in self.not_found_product:
                    if not self.localiza_produto:
                        continue
                    if line.name == item.prod.xProd:
                        if line.product_invoice:
                            product = self.env['product.product'].browse(line.product_invoice.product_id.id)
                            if self.localiza_produto:
                                #Atribui o código do produto no fornecedor para o produto no sistema
                                self.env['product.supplierinfo'].create({
                                    'name':edoc.partner_id.id,
                                    'product_tmpl_id': product.product_tmpl_id.id,
                                    'product_id': product.id,
                                    'price':item.prod.vUnCom,
                                    'min_qty':0,
                                    'delay':0,
                                    'product_code':item.prod.cProd,
                                })
                            #line.product_invoice.product_id.id,
                            break
                        else:
                            vals = {}
                            vals['name'] = str(item.prod.xProd)
                            vals['default_code'] = str(item.prod.cProd)
                            if uom_id:
                                vals['uom_id'] = uom_id
                            else:
                                vals['uom_id'] = 1
                            vals['type'] = 'product'
                            vals['list_price'] = float(item.prod.vUnCom)
                            vals['purchase_method'] = 'receive'
                            vals['tracking'] = 'lot'
                            ncm = str(item.prod.NCM)
                            ncm = '%s.%s.%s' % (ncm[:4], ncm[4:6], ncm[6:8])
                            pf_ids = self.env['product.fiscal.classification'].search([('code', '=', ncm)])
                            vals['fiscal_classification_id'] = pf_ids.id
                            product = self.env['product.product'].create(vals)
                            break
        import pudb;pu.db
        if not self.localiza_produto:
            product = self.not_found_product[num_item-1].product_invoice.product_id
        #item_edoc = edoc.eletronic_item_ids[num_item-1]
        item_num = 1
        codigo_diferentes = True
        codigo_dif = 0
        for item_edoc in edoc.eletronic_item_ids:
            if codigo_dif == item_edoc.product_id.id:
                codigo_diferentes = False
            if codigo_dif != item_edoc.product_id.id:
                codigo_dif = item_edoc.product_id.id
        if codigo_diferentes:
            for item_edoc in edoc.eletronic_item_ids:
                if item_edoc.product_id.id == product.id:
                    edc = item_edoc
                    item_num = int(item.get('nItem'))
        else:
            edc = edoc.eletronic_item_ids
        for item_edoc in edc:
            if item_edoc.product_id.id == product.id and item_num == int(item.get('nItem')):
                quantidade = item.prod.qCom
                preco_unitario = item.prod.vUnCom
                #indicador_total = '1'
                try:
                    desc = item.prod.vDesc
                except:
                    desc = 0.0
                valor_bruto = (quantidade * preco_unitario)
                valor_liquido = valor_bruto - desc
                if valor_liquido > item_edoc.valor_liquido:
                    valor_liquido = valor_liquido - item_edoc.valor_liquido
                else:
                    valor_liquido = item_edoc.valor_liquido - valor_liquido
                if valor_liquido > 0.009:
                    raise UserError('Valor Líquido do Produto ' + product.name + 
                        ' diferente do informado na fatura')
                item_edoc.write({
                    'name': item.prod.xProd,
                    'num_item': int(item.get('nItem')),
                    'uom_id': uom_id,
                    'quantidade': quantidade,
                    'preco_unitario': preco_unitario,
                })
                """ NÃO posso mudar o VALOR tem q ser o mesmo da Fatura
                   'desconto': desc,
                    'valor_liquido': valor_liquido,
                    'valor_bruto': valor_bruto,
                """
            item_num += 1
        return True    

    #Função que gera todas as linhas do campo itens
    def get_itens(self,nfe, edoc):
        items = []
        for det in nfe.NFe.infNFe.det:
            item = self.create_order_line(det, nfe, edoc, int(det.get('nItem')))
            #items.append((4, item.id, False))
        return True

    #Verifica a existência ou não de itens não encontrados
    ##############################################################################
    def consulta_produtos_nfe(self):
        fatura = self.env['account.invoice'].browse(self._context.get('invoice_id'))
        self.fatura = self._context.get('invoice_id')
        #lista_produtos = [line.product_id.id for line in fatura.invoice_line_ids]
        if not self.nfe_xml:
            raise UserError('Por favor, insira um arquivo de NFe.')
        nfe_string = base64.b64decode(self.nfe_xml)
        nfe = objectify.fromstring(nfe_string)
        items = []
        if fatura.product_document_id.code == '55' or self._context.get('tipo') == '55':
            nfe_ids = nfe.NFe.infNFe.det
        if fatura.product_document_id.code == '57' or self._context.get('tipo') == '57':
            nfe_ids = nfe.CTe.infCte.vPrest
            self.consulta_nfe()
            return
        for det in nfe_ids:
            item = self.carrega_produtos(det, fatura)
            if item:
                items.append(item.id)
        if items:
            self.not_found_product = self.env['not.found.products'].browse(items)
            self.confirma = True
        else:
            self.consulta_nfe()
            return

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.xml.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


    def carrega_produtos(self, item, fatura):
        if not self.localiza_produto:
            return self.env['not.found.products'].create({
                'name':item.prod.xProd,
                'fatura':self._context.get('invoice_id')
            })            
        product = ''
        product_code = self.env['product.supplierinfo'].search([
            ('product_code','=',item.prod.cProd),
            ('name','=',fatura.partner_id.id)
            ], limit=1)
        if product_code:    
            product = product_code.product_id # self.env['product.product'].browse(product_code.product_tmpl_id.id)

        if not product:
            if item.prod.cEAN:
                product = self.env['product.product'].search([
                    ('barcode', '=', item.prod.cEAN)], limit=1)
        if not product:
            return self.env['not.found.products'].create({
                'name':item.prod.xProd,
                'fatura':self._context.get('invoice_id')
            })
        else:
            return False
###############################################################################################################################

    def consulta_dist_nfe(self):
        fatura = self.env['account.invoice'].browse(self._context.get('invoice_id'))
        cert = fatura.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(
            cert_pfx, fatura.company_id.nfe_a1_password)
        
        obj = {
            'cnpj_cpf': re.sub(
                "[^0-9]", "", fatura.company_id.cnpj_cpf or ''),
            'estado': '35',
            'ambiente':1,
            'chave_nfe': '35180563910657000106550010000054201000054204',
            }
        #'ultimo_nsu':'000000000008023',
        #valida_xml = xml_consulta_distribuicao_nfe(certificado, **obj)            
        #erro_xml = self.validar(valida_xml)
        
        #resposta = consulta_distribuicao_nfe(certificado, obj=obj, ambiente=2, estado='35', ultNSU= '000000000000008')
        #resposta = consulta_distribuicao_nfe(certificado, **obj)
        resposta = download_nfe(certificado, **obj)
        data = resposta['received_xml']
        
        #self.eletronic_doc_id._create_attachment(
        #        'cce_ret', self.eletronic_doc_id, resposta['received_xml'])
        file_name = 'xxxx.xml'
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data.encode()),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'account.invoice',
                'res_id': fatura.id
            })                
                
        print (resposta)
        print (resposta['received_xml'])

    def manifestar_nfe(self):
        #certificado = open("/path/certificado.pfx", "r").read()
        #certificado = Certificado(certificado, 'senha_pfx')
        import pudb;pu.db
        fatura = self.env['account.invoice'].browse(self._context.get('invoice_id'))
        cert = fatura.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(
            cert_pfx, fatura.company_id.nfe_a1_password)
        
        obj = {
            'manifesto.cnpj_empresa': re.sub(
                "[^0-9]", "", fatura.company_id.cnpj_cpf or ''),
            'estado': '35',
            'ambiente':1,
            'manifesto.chave_nfe': '35180563910657000106550010000054201000054204',
            
            }
        #'ultimo_nsu':'000000000008023',
        #valida_xml = xml_consulta_distribuicao_nfe(certificado, **obj)            
        #erro_xml = self.validar(valida_xml)
        
        #resposta = consulta_distribuicao_nfe(certificado, obj=obj, ambiente=2, estado='35', ultNSU= '000000000000008')
        #resposta = consulta_distribuicao_nfe(certificado, **obj)
        resposta = download_nfe(certificado, **obj)
        data = resposta['received_xml']
        
        #self.eletronic_doc_id._create_attachment(
        #        'cce_ret', self.eletronic_doc_id, resposta['received_xml'])
        file_name = 'xxxx.xml'
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data.encode()),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'account.invoice',
                'res_id': fatura.id
            })                
                
        print (resposta)
        print (resposta['received_xml'])


    def consulta_nfe(self):
        if not self.nfe_xml:
            raise UserError('Por favor, insira um arquivo de NFe.')
        nfe_string = base64.b64decode(self.nfe_xml)
        nfe = objectify.fromstring(nfe_string)
        fatura = self.env['account.invoice'].browse(self._context.get('invoice_id'))
        edoc = self.env['invoice.eletronic'].search([
            ('invoice_id', '=', fatura.id),
            ('emissao_doc','=','2')])
        
        vals = self.get_invoice_eletronic_vals(nfe, fatura, edoc)
        fatura.write({
            'nfe_number_static': str(vals['numero']),
            'nfe_emissao': vals['data_emissao'],
            'nfe_data_entrada':self.data_entrada,
            'nfe_serie': vals['serie_documento'],
            'nfe_modelo': vals['model'],
            'nfe_chave': str(vals['chave_nfe']), 
            })  
        edoc.write(vals)
        #else:    
        #    self.env['invoice.eletronic'].create(vals)
        
        #self.consulta_dist_nfe()
        return

###############################################################################################################################

class NotFoundProduct(models.Model):
    _inherit = 'not.found.products'

    product_invoice = fields.Many2one('account.invoice.line',string='Produto da fatura')
    fatura = fields.Integer(string='Fatura de origem')
