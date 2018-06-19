import base64, re

from lxml import objectify
from decimal import Decimal, ROUND_HALF_UP

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.addons.br_base.tools import fiscal
from odoo.addons import decimal_precision as dp

from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD



icms_tags = [u'ICMS00', u'ICMS10', u'ICMS20', u'ICMS30', u'ICMS40', u'ICMS51', u'ICMS60', u'ICMS70', u'ICMS90',
             u'ICMSSN101', u'ICMSSN102', u'ICMSSN101', u'ICMSSN201',  u'ICMSSN202', u'ICMSSN500', u'ICMSSN900']

desoneracao_motivos = [('1', 'Táxi'), ('3', 'Produtor Agropecuário'), ('4', 'Frotista/Locadora'),
                        ('5', 'Diplomático/Consular'), ('6', 'Utilitários e Motocicletas da Amazônia Ocidental '
                                                             'e Áreas de Livre Comércio (Resolução 714/88 e 790/94 – '
                                                             'CONTRAN e suas alterações)'),
                        ('7', 'SUFRAMA'), ('8', 'Venda a órgão Público'), ('9', 'Outros'),('10', 'Deficiente Condutor'),
                        ('11', 'Deficiente não condutor'), ('16', 'Olimpíadas Rio 2016')]

class BrAccountInvoiceImport(models.Model):

    _name = 'br.account.invoice.import.wizard'

    # Dados de Controle da Importação
    procedure_state = fields.Selection([('draft', 'Rascunho'), ('partner_check','Verificação do Parceiro'),
                                        ('product_check', 'Verificação dos Produtos'),
                                        ('payment_check', 'Verificação dos Pagamentos')],
                                        default='draft')

    currency_id = fields.Many2one("res.currency", string="Moeda", readonly=True, compute='_get_default_values')

    # Dados do Arquivo XML
    xml_file = fields.Binary(u'Arquivo XML')
    name = fields.Char()
    file_validate = fields.Boolean(string=u'Arquivo Válidado', default=False, store=True)

    # Dados do Parceiro/Fornecedor
    cnpj = fields.Char(string='CNPJ', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'Parceiro', readonly=True)
    partner_not_found = fields.Many2many('partner.not.found', string=u'Fornecedor não Cadastrado', readonly=True)
    partner_crt = fields.Selection([('1', u'Simples Nacional'),
                                    ('2', u'Simples Nacional – excesso de sublimite de receita bruta'),
                                    ('3', u'Regime Normal')], string=u'CRT do Forneceddor',
                                   help=u'Código de Regime Tributário do Fornecedor')

    # Informações Gerais da Fatura
    fatura = fields.Integer(string=u'Fatura de Origem')
    nro_nfe = fields.Char(string=u'Nro da NF-e')
    chave_nfe = fields.Char(string=u'Chave da NF-e')
    dt_emissao = fields.Datetime(string=u'Data de Emissão')
    fiscal_comment = fields.Char(string=u'Informações Complementares')

    # Valores Totais da Fatura
    vlr_produtos = fields.Monetary(string=u'Valor dos Produtos ( + )', readonly=True)
    vlr_desconto = fields.Monetary(string=u'Desconto ( - )', readonly=True)
    vlr_frete = fields.Monetary(string=u'Valor do Frete ( + )', readonly=True)
    base_icms = fields.Monetary(string=u'Base de Cálculo do ICMS ( % )', digits=dp.get_precision('Account'),
                                readonly=True)
    vlr_icms = fields.Monetary(string=u'Valor do ICMS ( + )', readonly=True)
    base_icms_st = fields.Monetary(string=u'Base de Cálculo do ICMS ( % )', digits=dp.get_precision('Account'),
                                readonly=True)
    vlr_icms_st = fields.Monetary(string=u'Valor do ICMS ST ( + )', readonly=True)
    vlr_icms_desonerado = fields.Monetary(string=u'Valor do ICMS Desonerado ( - )', readonly=True)
    vlr_ii = fields.Monetary(string=u'Valor do II ( + )', readonly=True)
    vlr_ipi = fields.Monetary(string=u'Valor do IPI ( + )', readonly=True)
    vlr_pis = fields.Monetary(string=u'Valor do PIS ( + )', readonly=True)
    vlr_cofins = fields.Monetary(string=u'Valor do COFINS ( + )', readonly=True)
    vlr_fatura = fields.Monetary(string=u'Valor da Nota Fiscal ( = )', readonly=True)

    data_entrada = fields.Date(string=u'Data de Entrada')

    # Dados dos Produtos
    localiza_produto = fields.Boolean(string=u'Usar Cadastro se Existir.', default=True)
    confirma = fields.Boolean(string=u'Todos os Produtos Encontrados', default=False)
    product_not_found = fields.One2many('product.not.found', 'order_id', string=u'Produtos Não Encontrados')
    geral_cfop_id = fields.Many2one('br_account.cfop', string=u"CFOP")
    all_product_validate = fields.Boolean(string='Produto Válidado', default=False, store=True)

    # Dados da Cobrança
    payment_lines = fields.One2many('br.account.invoice.import.payment', 'order_id', string=u'Vencimentos da Fatura',
                                    auto_join=True)
    payment_balance = fields.Monetary(string=u'Balanço', compute='check_amount_payments')
    payment_create_type = fields.Selection([('invoice', u'Dados da Cobrança Gerados Através da NF-e'),
                                            ('manual', u'Informar Dados da Cobrança Manualmente'), ],
                                           string=u'Lançar Cobranças',
                                           help=u'Modo de Lançamento das Cobranças no Contas a Pagar')

    @api.multi
    @api.onchange('geral_cfop_id')
    def compute_all_cfop(self):
        products = self.product_not_found
        cfop = self.geral_cfop_id.id
        for product in products:
            product.cfop_id = cfop


    @api.multi
    def _get_default_values(self):
        for record in self:
            record.currency_id = record.env.user.company_id.currency_id.id

    def _compute_file_info(self, inv_object):
        ide = inv_object.NFe.infNFe.ide
        emit = inv_object.NFe.infNFe.emit
        total = inv_object.NFe.infNFe.total
        inf_protocolo = inv_object.protNFe.infProt
        nome_fornecedor = emit.xNome
        num_nfe = ide.cNF.text
        self.name = nome_fornecedor + ' - NF-e: ' + num_nfe
        self.nro_nfe = num_nfe
        self.chave_nfe = inf_protocolo.chNFe.text
        self.fiscal_comment = inv_object.NFe.infNFe.infAdic.infCpl.text if hasattr(inv_object.NFe.infNFe, 'infAdic')\
            and hasattr(inv_object.NFe.infNFe.infAdic, 'infCpl') else '',
        self.dt_emissao = datetime.strptime(ide.dhEmi.text[0:19], '%Y-%m-%dT%H:%M:%S')
        self.vlr_produtos = total.ICMSTot.vProd
        self.vlr_fatura = total.ICMSTot.vNF
        self.vlr_desconto = total.ICMSTot.vDesc
        self.vlr_frete = total.ICMSTot.vFrete
        self.vlr_ii = total.ICMSTot.vII
        self.vlr_pis = total.ICMSTot.vPIS
        self.vlr_ipi = total.ICMSTot.vIPI
        self.base_icms = total.ICMSTot.vBC
        self.vlr_icms = total.ICMSTot.vICMS
        self.vlr_icms_desonerado = total.ICMSTot.vICMSDeson
        self.base_icms_st = total.ICMSTot.vBCST
        self.vlr_icms_st = total.ICMSTot.vST
        self.vlr_cofins = total.ICMSTot.vCOFINS

    @api.multi
    def _check_truth_einvoice(self):
        '''
        Função para checar a autenticidade do documento eletrônico
        '''
        pass

    @api.multi
    def compute_payments(self):
        file_string = base64.b64decode(self.xml_file)
        inv_object = objectify.fromstring(file_string)
        if hasattr(inv_object.NFe.infNFe, 'cobr') and hasattr(inv_object.NFe.infNFe.cobr, 'dup'):
            payments = inv_object.NFe.infNFe.cobr.dup
            self.prepare_payment_lines(payments)
        else:
            self.payment_create_type = 'manual'

    @api.multi
    def prepare_payment_lines(self, payments):
        for payment in payments:
            payment_values = {
                'order_id': self.id,
                'currency_id': self.currency_id.id,
                'payment_create_type': 'invoice',
                'payment_dup': payment.nDup if hasattr(payment, 'nDup') else '',
                'payment_venc': datetime.strptime(payment.dVenc.text, '%Y-%m-%d').date() if hasattr(payment, 'dVenc')
                    else '',
                'payment_amount': payment.vDup if hasattr(payment, 'vDup') else '',
            }
            self.create_payment(payment_values)

    @api.multi
    def create_payment(self, payment_values):
        self.env['br.account.invoice.import.payment'].create(payment_values)
        payments = self.env['br.account.invoice.import.payment'].search([('order_id', '=', self.id)])
        self.check_amount_payments()
        self.payment_lines = payments.browse(payments.ids)



    @api.multi
    @api.depends('payment_lines.payment_amount')
    def check_amount_payments(self):
        amount_total = self.vlr_fatura
        amount_payment_lines = 0
        '''
        if self.payment_lines:
            for payment in self.payment_lines:
                amount_payment_lines += payment.payment_amount
            balance = amount_total - amount_payment_lines
            if balance < 0:
                raise UserError(_(u'O Valor das cobranças não pode ser maior que o valor da Nota Fiscal!\n'
                                  u'Por Favor corrija o(s) lançamento(s) da(s) cobrança(s)'))
            else:
                self.payment_balance = balance
        else:
            self.payment_balance = amount_total
        '''


    @api.multi
    def prepare_products(self, item):

        inv_prod_vals = {
            'currency_id': self.currency_id.id,
            'order_id': self.id,
            'inv_prod_name': item.prod.xProd,
            'inv_prod_code': item.prod.cProd,
            'inv_prod_uom': item.prod.uCom,
            'inv_prod_ean': item.prod.cEAN.text,
            'inv_prod_ncm': item.prod.NCM,
            'inv_prod_qty': item.prod.qCom,
            'inv_cest': item.prod.CEST if hasattr(item.prod, 'CEST') else '',
            'product_uom_qty': item.prod.qCom,
            'inv_prod_price_unit': item.prod.vUnCom,
            'product_price_unit': item.prod.vUnCom,
            'inv_prod_desc': item.prod.vDesc if hasattr(item.prod, 'vDesc') else 0,
            'inv_prod_vlr': item.prod.vProd,
        }

        icms_values = self.prepare_values_icms(item.imposto.ICMS)
        inv_prod_vals.update(icms_values)
        pis_values = self.prepare_values_pis(item.imposto.PIS)
        inv_prod_vals.update(pis_values)
        cofins_values = self.prepare_values_cofins(item.imposto.COFINS)
        inv_prod_vals.update(cofins_values)
        if hasattr(item.imposto, 'IPI'):
            ipi_values = self.prepare_values_ipi(item.imposto.IPI)
            inv_prod_vals.update(ipi_values)

        return inv_prod_vals

    def prepare_values_icms(self, icms_values):

        for icms in icms_values.iterchildren():
            icms_values = {
                'icms_cst': icms.CST.text if hasattr(icms, 'CST') else icms.CSOSN.text,
                'icms_aliquota': icms.pICMS if hasattr(icms, 'pICMS') else '',
                'icms_base_calculo': icms.vBC if hasattr(icms, 'vBC') else '',
                'icms_aliquota_reducao_base': icms.pRedBC if hasattr(icms, 'pRedBC') else '',
                'icms_valor_credito': icms.vCredICMSSN if hasattr(icms, 'vCredICMSSN') else '',
                'icms_valor': icms.vICMS if hasattr(icms, 'vICMS') else '',
                'inv_origem': icms.orig.text if hasattr(icms, 'orig') else '',
                'icms_valor_desonerado': icms.vICMSDeson if hasattr(icms, 'vICMSDeson') else '',
                'icms_motivo_desoneracao': icms.motDesICMS.text if hasattr(icms, 'motDesICMS') else '',
                'icms_st_aliquota': icms.pICMSST.text if hasattr(icms, 'pICMSST') else '',
                'icms_st_aliquota_mva': icms.pMVAST.text if hasattr(icms, 'pMVAST') else '',
                'icms_st_base_calculo': icms.vBCST.text if hasattr(icms, 'vBCST') else '',
                'icms_st_aliquota_reducao_base': '',
                'icms_st_valor_credito': '',
                'icms_st_valor': icms.vICMSST.text if hasattr(icms, 'vICMSST') else '',
            }

        return icms_values

    def prepare_values_pis(self, pis_values):
        for pis in pis_values.iterchildren():
            pis_values = {
                'pis_cst': pis.CST.text if hasattr(pis, 'CST') else '',
                'pis_aliquota': pis.pPIS if hasattr(pis, 'pPIS') else '',
                'pis_base_calculo': pis.vBC if hasattr(pis, 'vBC') else '',
                'pis_valor': pis.vPIS if hasattr(pis, 'vPIS') else '',
                'pis_valor_retencao': '',
            }

        return pis_values

    def prepare_values_cofins(self, cofins_values):
        for cofins in cofins_values.iterchildren():
            cofins_values = {
                'cofins_cst': cofins.CST.text if hasattr(cofins, 'CST') else '',
                'cofins_aliquota': cofins.pCOFINS if hasattr(cofins, 'pCOFINS') else '',
                'cofins_base_calculo': cofins.vBC if hasattr(cofins, 'vBC') else '',
                'cofins_valor': cofins.vCOFINS if hasattr(cofins, 'vCOFINS') else '',
                'cofins_valor_retencao': '',
            }

        return cofins_values

    def prepare_values_ipi(self, ipi_values):
        for ipi in ipi_values.iterchildren():
            ipi_values = {
                'ipi_cst': ipi.CST.text if hasattr(ipi, 'CST') else '',
                'ipi_aliquota': ipi.pIPI if hasattr(ipi, 'pIPI') else '',
                'ipi_base_calculo': ipi.vBC if hasattr(ipi, 'vBC') else '',
                'ipi_valor': ipi.vIPI if hasattr(ipi, 'vIPI') else '',
            }

        return ipi_values

    @api.multi
    def create_product_lines(self, nfe):
        products = []
        for det in nfe.NFe.infNFe.det:
            prod_vals = self.prepare_products(det)
            search_products = self.discovery_products(prod_vals)
            if search_products.id != False:
                prod_vals['product_id'] = search_products.id
                prod_vals['product_match'] = True
                prod_vals['product_uom'] = search_products.uom_id.id

                domain = {'product_uom': [('category_id', '=', search_products.uom_id.category_id.id)]}
                prod_vals['domain'] = domain

            prod_not_found = self.env['product.not.found'].create(prod_vals)
            products.append(prod_not_found.id)

        self.product_not_found = self.env['product.not.found'].browse(products)

    @api.multi
    def discovery_products(self, product_vals):
        products = self.env['product.product']
        if product_vals['inv_prod_ean'] != None:
            product = products.search([('barcode', '=', product_vals['inv_prod_ean'])], limit=1)
        else:
            partner_id = self.partner_id
            product_code = self.env['product.supplierinfo'].search([('product_code', '=', product_vals['inv_prod_code']),
                                                                    ('name', '=', partner_id.id)], limit=1)
            product = self.env['product.product'].browse(product_code.product_tmpl_id.id)

        return product

    def format_doc_number(self, cnpj):
        if len(cnpj) == 14:
            cnpj_cpf = "%s.%s.%s/%s-%s" % (cnpj[0:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14])
        elif len(cnpj) == 11:
            cnpj_cpf = "%s.%s.%s-%s" % (cnpj[0:3], cnpj[3:6], cnpj[6:9], cnpj[9:11])

        return cnpj_cpf

    @api.multi
    def search_partner(self, emit):
        '''
        Função para buscar os dados do emitente no banco de dados do sistema
        '''
        partners = self.env['res.partner']
        cnpj_cpf = emit.CNPJ.text if hasattr(emit, 'CNPJ') else emit.CPF.text
        cnpj_cpf = self.format_doc_number(cnpj_cpf)
        partner = partners.search([('cnpj_cpf', '=', cnpj_cpf)])
        if len(partner) > 0:
            self.partner_id = partner.id
            self.partner_crt = emit.CRT.text
            return self.compute_xml()
        else:
            partner_vals = self.create_partner_vals()
            partner = self.env['partner.not.found'].create(partner_vals)
            self.partner_not_found = self.env['partner.not.found'].browse(partner.id)
            self.procedure_state = 'partner_check'


    @api.multi
    def create_partner_vals(self):
        '''
        Cadastrar parceiro no sistema apartir das informações obtidas no arquivo XML,
        caso o parceiro ainda não possua cadastro no sistema
        '''
        for record in self:
            file_string = base64.b64decode(record.xml_file)
            inv_object = objectify.fromstring(file_string)
            partner_obj = inv_object.NFe.infNFe.emit
            cnpj_cpf = self.format_doc_number(partner_obj)
            country = self.env['res.country'].search([('ibge_code', '=', partner_obj.enderEmit.cPais.text)])
            state = self.env['res.country.state'].search([('country_id', '=', country.id),
                                                          ('code', '=', partner_obj.enderEmit.UF)])
            city = self.env['res.state.city'].search([('state_id', '=', state.id),
                                                      ('ibge_code', 'like', partner_obj.enderEmit.cMun.text[2:7])])
            partner_vals = {
                'xml_file': record.xml_file,
                'name': partner_obj.xFant,
                'legal_name': partner_obj.xNome,
                'cnpj_cpf': cnpj_cpf,
                'zip': partner_obj.enderEmit.CEP.text,
                'street': partner_obj.enderEmit.xLgr,
                'number': partner_obj.enderEmit.nro.text,
                'district': partner_obj.enderEmit.xBairro,
                'state_id': state.id,
                'city_id': city.id,
                'country_id': country.id,
                'supplier': True,
            }
            if hasattr(partner_obj.enderEmit, 'fone'):
                partner_vals['phone'] = partner_obj.enderEmit.fone.text
            if hasattr(partner_obj, 'IE'):
                partner_vals['inscr_est'] = partner_obj.IE.text

            return partner_vals

    @api.multi
    def _reopen_wizard(self, id):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'br.account.invoice.import.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': id,
        }

    @api.multi
    def document_validation(self, inv_object):
        '''
        Função para validar o documento carregado
        '''
        dest = inv_object.NFe.infNFe.dest
        cnpj_file = self.format_doc_number(dest.CNPJ.text)
        cnpj = self.env.user.company_id.partner_id.cnpj_cpf
        # Verifica o destinatário no arquivo de XML
        if cnpj_file != cnpj:
            self.xml_file = None
            raise UserError(_(u'O CNPJ de destinatário no Documento Fiscal é diferente do CNPJ da empresa.\n'
                                u'CNPJ na NF-e: ' + cnpj_file +'\n'
                                u'CNPJ da Empresa: ' + cnpj))
        documents = self.env['br.account.invoice.import.wizard']
        chave_nfe = self.chave_nfe = inv_object.protNFe.infProt.chNFe.text
        if documents.search([('chave_nfe', '=', chave_nfe)]):
            raise UserError(_(u'Já existe um registro de importação deste documento em andamento.'))


    @api.multi
    @api.onchange('xml_file')
    def validate_xml(self):
        if self.xml_file != False:
            file_string = base64.b64decode(self.xml_file)
            inv_object = objectify.fromstring(file_string)
            self.document_validation(inv_object)


    @api.multi
    def validate_xml_file(self):
        file_string = base64.b64decode(self.xml_file)
        inv_object = objectify.fromstring(file_string)
        emit = inv_object.NFe.infNFe.emit
        ide = inv_object.NFe.infNFe.ide
        self.name = emit.xNome + ' - NF-e: ' + ide.cNF.text
        self.file_validate = True
        self.compute_xml()

    @api.multi
    def validate_products(self):
        products = self.product_not_found
        msg = []
        for product in products:
            if product.product_validate == False:
                msg.append(u'O Produto %s não esta validado, verifique se todos os campos foram preenchidos'
                           u' corretamente\n' %(product.inv_prod_name))

        if len(msg) > 0:
            errors = ''
            for error in msg:
                errors += error

            raise ValidationError(_(errors))
        else:
            self.procedure_state = 'payment_check'


            

    @api.multi
    def validate_all_product(self):
        for product in self.product_not_found:
            if product.product_validate == False:
                return
            else:
                self.all_prod_validate = True

    @api.multi
    @api.onchange('name')
    def compute_xml(self):
        if self.xml_file != False and self.name != False:
            file_string = base64.b64decode(self.xml_file)
            inv_object = objectify.fromstring(file_string)
            emit = inv_object.NFe.infNFe.emit
            ide = inv_object.NFe.infNFe.ide
            dest = inv_object.NFe.infNFe.dest
            total = inv_object.NFe.infNFe.total

            self._get_default_values()
            self._compute_file_info(inv_object)
            if self.partner_id.id == False:
                return self.search_partner(emit)
            if len(self.product_not_found) == 0:
                self.procedure_state = 'product_check'
                return self.create_product_lines(inv_object)

    def prepare_purchase_order_values(self):
        '''
        Prepara os valores para criação do pedido de compras através do documento importado
        '''
        for value in self:
            values = {
                'partner_id': value.partner_id.id,
                'partner_ref': value.nro_nfe,
                'date_order': value.dt_emissao,
            }
        return values

    @api.multi
    def prepare_purchase_item_values(self, order_id, product):
        '''
        Prepara os valores para criação das linhas dos itens do pedido de compras criado apartir do documento eletrônico
        :param order_id: número do pedido de compras criado
        :param product: objeto produto do documento eletrônico
        :return: retorna dicionário com valores para criação da linha do pedido de compras
        '''

        values = {
            'order_id': order_id,
            'name': product.inv_prod_name,
            'date_planned': self.dt_emissao,
            'product_id': product.product_id.id,
            'product_qty': product.product_uom_qty,
            'product_uom': product.product_uom.id,
            'price_unit': product.product_price_unit,
            'cfop_id': product.cfop_id.id,
            'partner_id': self.partner_id.id,
            'icms_cst_normal': product.icms_cst if int(product.icms_cst) < 100 else '',
            'icms_csosn_simples': product.icms_cst if int(product.icms_cst) >= 100 else '',
            'icms_st_aliquota_mva': product.icms_st_aliquota_mva,
            'aliquota_icms_proprio': product.icms_aliquota,
            'ipi_cst': product.ipi_cst,
            'pis_cst': product.pis_cst,
            'cofins_cst': product.cofins_cst,
            'mot_desoneracao_icms': product.icms_motivo_desoneracao,
            'icms_des_valor': product.icms_valor_desonerado,
            'valor_desconto': product.inv_prod_desc_percent,
        }

        return values

    @api.multi
    def update_supplierinfo(self, order_id, product):
        '''
        Funão para atualizar os dados da tabela supplierinfo conforme informações do documento eletrônico
        :param order_id: número do pedido que foi criado
        :param product: objeto produto do documento eletrônico
        '''

        supplierinfo_lines = self.env['product.supplierinfo'].search([('purchase_order_id', '=', order_id)])
        for line in supplierinfo_lines:
            if line.product_id.id in [product.product_id.id, product.product_id.product_tmpl_id.id]\
                    or line.product_tmpl_id.id in [product.product_id.id, product.product_id.product_tmpl_id.id]:
                vals = {
                    'product_name': product.inv_prod_name,
                    'product_code': product.inv_prod_code,
                    'partner_product_uom': product.inv_prod_uom,
                    'partner_product_uom_qty': product.inv_prod_qty,
                }
                line.write(vals)

    @api.multi
    def create_purchase_order(self):
        '''
        Função para criar pedido de compras e demais objetos relacionados ao pedido de compras
        :return: objeto purchase.order criado
        '''
        purchase_order = self.env['purchase.order']
        po_values = self.prepare_purchase_order_values()
        new_order = purchase_order.create(po_values)
        new_order_lines = self.env['purchase.order.line']
        for product in self.product_not_found:
            item = self.prepare_purchase_item_values(new_order.id, product)
            new_order_lines.create(item)
        new_order.button_confirm()
        for product in self.product_not_found:
            self.update_supplierinfo(new_order.id, product)

        return new_order

    @api.multi
    def prepare_account_invoice_values(self, purchase_order):
        '''
        Prepara os valores para criação do pedido de compras através do documento importado
        '''
        for i in purchase_order:
            values = {
                # Pedido de Origem
                'origin': i.name,
                # Tipo de Invoice(Entrada)
                'type': 'in_invoice',
                # Comentários
                'comment': u'FATURA GERADA AUTOMATICAMENTE ATRAVES DE IMPORATACAO DE DOCUMENTO ELETRONICO\n'
                           u'CHAVE DA NFE DE ORIGEM: ' + self.chave_nfe,
                # Informações Complementares da NF-e
                'fiscal_comment': self.fiscal_comment,
                # Partner/Fornecedor
                'partner_id': i.partner_id.id,
                'commercial_partner_id': i.partner_id.id,
                # Pedido de Compras
                'purchase_id': i.id,
                # Data de Emissao da NF-e
                'date_invoice': self.dt_emissao,
                # Diário Contábil
                # :TODO: CRIAR MODELO OPERACAO
                'journal_id': 2,
                # Conta Contábil
                # :TODO: CRIAR MODELO OPERACAO
                'account_id': 13,
                # VALORES TOTAIS DA INVOICE
                'amount_untaxed': self.vlr_fatura,
                'amount_untaxed_signed': self.vlr_fatura,
                # Total de Imposto
                'amount_tax': self.vlr_icms + self.vlr_icms_st + self.vlr_ipi + self.vlr_pis + self.vlr_cofins,
                # Total da Fatura
                'amount_total': self.vlr_fatura,
                'amount_total_signed': self.vlr_fatura,
                'currency_id': self.currency_id.id,
                # Total da Fatura
                'total_bruto': self.vlr_fatura,
                # Total de Desconto
                'total_desconto': self.vlr_desconto,
                # Base de Cálculo do ICMS
                'icms_base': self.base_icms,
                # Valor Total do ICMS
                'icms_value': self.vlr_icms,
                # Base de Cálculo ICMS ST
                'icms_st_base': self.base_icms_st,
                # Valor ICMS ST
                'icms_st_value': self.vlr_icms_st,
                # Base Cálculo do IPI
                'ipi_base': sum([x['ipi_base_calculo'] for x in self.product_not_found]),
                # Valor do IPI
                'ipi_value': self.vlr_ipi,
                # Base Cálculo PIS
                'pis_base': sum([x['pis_base_calculo'] for x in self.product_not_found]),
                # Valor do PIS
                'pis_value': self.vlr_pis,
                # Base Cálculo Cofins
                'cofins_base': sum([x['cofins_base_calculo'] for x in self.product_not_found]),
                # Valor do Cofins
                'cofins_value': self.vlr_cofins,
                # Valor do ICMS Desonerado
                'icms_des_value': self.vlr_icms_desonerado,
            }
        return values

    @api.multi
    def prepare_account_invoice_item_values(self, new_invoice, purchase_order_line, product_not_found):
        '''
        Prepara os valores para criação do pedido de compras através do documento importado
        '''

        inv = new_invoice
        p_order = purchase_order_line
        p = product_not_found


        values = {

            # Linha do Pedido de Compra do Produto
            'purchase_line_id': p_order.id,
            'invoice_id': inv.id,
            'account_id': 24,
            'cfop_id': p.cfop_id.id,

            # Dados da Linha do Produto
            'name': p_order.product_id.name,
            'origin': p_order.order_id.name,
            'uom_id': p_order.product_uom.id,
            'product_id': p_order.product_id.id,
            'price_unit': p_order.price_unit,
            'price_subtotal': p_order.price_subtotal,
            'price_total': p_order.price_total,
            'price_subtotal_signed': p_order.price_total,
            'quantity': p_order.product_qty,
            'discount': round(p.inv_prod_desc / p.inv_prod_vlr, 2) * 100,
            'partner_id': p_order.partner_id.id,
            'currency_id': self.currency_id.id,
            'product_type': p_order.product_id.type,

            # Dados do ICMS
            'icms_cst': p.icms_cst,
            'icms_csosn_simples': p.icms_cst if int(p.icms_cst) > 100 else '',
            'icms_cst_normal': p.icms_cst if int(p.icms_cst) <= 100 else '',
            'icms_origem': p.inv_origem,
            'icms_base_calculo': p.icms_base_calculo,
            'icms_valor': p.icms_valor,
            'icms_aliquota': p.icms_aliquota,
            'icms_aliquota_reducao_base': p.icms_aliquota_reducao_base,
            'icms_base_calculo_manual': p.icms_base_calculo,

            # Dados do ICMS ST
            'icms_st_valor': p.icms_st_valor,
            'icms_st_aliquota': p.icms_st_aliquota,
            'icms_st_aliquota_reducao_base': p.icms_st_aliquota_reducao_base,
            'icms_st_aliquota_mva': p.icms_st_aliquota_mva,
            'icms_st_base_calculo_manual': p.icms_st_base_calculo,

            # Dados do IPI
            'ipi_cst': p.ipi_cst,
            'ipi_tipo': 'percent',
            'ipi_base_calculo': p.ipi_base_calculo,
            'ipi_reducao_base_calculo': p.ipi_reducao_bc,
            'ipi_valor': p.ipi_valor,
            'ipi_aliquota': p.ipi_aliquota,
            'ipi_base_calculo_manual': p.ipi_base_calculo,

            # Dados do PIS
            'pis_cst': p.pis_cst,
            'pis_tipo': 'percent',
            'pis_base_calculo': p.pis_base_calculo,
            'pis_valor': p.pis_valor,
            'pis_aliquota': p.pis_aliquota,
            'pis_base_calculo_manual': p.pis_base_calculo,

            # Dados do Cofins
            'cofins_cst': p.cofins_cst,
            'cofins_tipo': 'percent',
            'cofins_base_calculo': p.cofins_base_calculo,
            'cofins_valor': p.cofins_valor,
            'cofins_aliquota': p.cofins_aliquota,
            'cofins_base_calculo_manual': p.cofins_base_calculo,

            # Dados da Desoneração do ICMS
            'desoneracao_icms': True if p.icms_valor_desonerado > 0 else False,
            'mot_desoneracao_icms': p.icms_motivo_desoneracao,
            'icms_des_valor': p.icms_valor_desonerado,
        }

        return values


    @api.multi
    def create_account_invoice(self, purchase_order):
        '''
        Função para criar invoices relacionadas ao documento importado
        :return:
        '''
        invoice = self.env['account.invoice']
        invoice_values = self.prepare_account_invoice_values(purchase_order)
        new_invoice = invoice.create(invoice_values)
        invoice_items = self.env['account.invoice.line']
        new_invoice_item = []
        taxes = []
        for line in purchase_order.order_line:
            product_not_found = self.product_not_found.search([('product_id', '=', line.product_id.id),
                                                               ('order_id', '=', self.id)])
            invoice_item_values = self.prepare_account_invoice_item_values(new_invoice, line, product_not_found)
            invoice_item = invoice_items.create(invoice_item_values)
            new_tax = self.discovery_taxes_ids(invoice, invoice_item, product_not_found)
            if new_tax != None:
                taxes.append(new_tax)

            new_invoice_item.append(invoice_item)

        account_invoice_taxes = {}

        for tax in taxes:
            for t in tax:
                key = str(t['tax_id'])
                if key not in account_invoice_taxes:
                    account_invoice_taxes[key] = t
                    account_invoice_taxes[key]['invoice_id'] = new_invoice.id
                    account_invoice_taxes[key]['manual'] = True
                    account_invoice_taxes[key]['amount'] = float(Decimal(Decimal(t['value']).quantize(Decimal('.01'),
                                                                                                rounding=ROUND_HALF_UP)))

                elif key in account_invoice_taxes:
                    account_invoice_taxes[key]['amount'] += float(Decimal(Decimal(t['value']).quantize(Decimal('.01'),
                                                                                            rounding=ROUND_HALF_UP)))

        if len(account_invoice_taxes) > 0:
            for t in account_invoice_taxes:
                self.env['account.invoice.tax'].create(account_invoice_taxes[t])

        account_move = self.action_move_create(new_invoice)

        return new_invoice

    @api.multi
    def discovery_taxes_ids(self, invoice, invoice_line, product_not_found):
        '''
        Função para descobrir regras de imposto no sistema que atendam aos impostos
        destacados na NF-e
        :return:
        '''

        domains = ['icms', 'icmsst', 'ipi', 'pis', 'cofins']
        names = {
            'icms': 'ICMS Entrada',
            'icmsst': 'ICMS ST Entrada',
            'ipi': 'IPI Entrada',
            'pis': 'PIS Entrada',
            'cofins': 'COFINS Entrada',
        }

        invoice_tax_lines = []
        tax_ids = []

        for tax in domains:
            taxes = self.env['account.tax']
            if tax == 'icms':
                aliquota = product_not_found.icms_aliquota
                base = product_not_found.icms_base_calculo
                amount = product_not_found.icms_valor
            elif tax == 'icmsst':
                aliquota = product_not_found.icms_st_aliquota
                base = product_not_found.icms_st_base_calculo
                amount = product_not_found.icms_st_valor
            elif tax == 'ipi':
                aliquota = product_not_found.ipi_aliquota
                base = product_not_found.ipi_base_calculo
                amount = product_not_found.ipi_valor
            elif tax == 'pis':
                aliquota = product_not_found.pis_aliquota
                base = product_not_found.pis_base_calculo
                amount = product_not_found.pis_valor
            elif tax == 'cofins':
                aliquota = product_not_found.cofins_aliquota
                base = product_not_found.cofins_base_calculo
                amount = product_not_found.cofins_valor

            if amount != 0:
                tax_id = taxes.search([('domain', '=', tax), ('amount', '=', aliquota),
                                       ('type_tax_use', '=', 'purchase'),
                                       ('active', '=', True), ('price_include', '=', True)])

                if len(tax_id) == 0:
                    taxes.create({
                        'name': names[tax] + ' ' + str(aliquota) + '%',
                        'type_tax_use': 'purchase',
                        'amount_type': 'percent',
                        'amount': aliquota,
                        'description': names[tax] + ' ' + str(aliquota) + '%',
                        'tax_exigibility': 'on_invoice',
                        'domain': tax,
                    })
                if len(tax_id) > 0:
                    #invoice_line.update({'invoice_line_tax_ids': [(6, _, [tax_id.id])]})
                    tax_ids.append(tax_id.id)
                    invoice_tax_lines.append({
                        'tax_id': tax_id.id,
                        'name': tax_id.name,
                        'base': base,
                        'value': amount,
                        'account_id': 24,
                    })
        invoice_line.write({'invoice_line_tax_ids': [(6, _, tax_ids)]})

        return invoice_tax_lines



    @api.multi
    def create_account_invoice_taxes(self):
        pass

    @api.multi
    def invoice_line_move_line_get(self, invoice):
        res = []
        for line in invoice.invoice_line_ids:
            if line.quantity == 0:
                continue

            tax_ids = []

            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))

            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'invoice_id': invoice.id,
                'analytic_tag_ids': analytic_tag_ids
            }

            if line.quantity == 0:
                continue

            move_line_dict['price'] = line.price_total
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            ctx = line._prepare_tax_context()
            tax_ids = line.invoice_line_tax_ids.with_context(**ctx)
            taxes_dict = tax_ids.compute_all(price, invoice.currency_id, line.quantity, product=line.product_id,
                                             partner=invoice.partner_id)

            for tax in line.invoice_line_tax_ids:
                import pudb;pu.db
                tax_dict = next(x for x in taxes_dict['taxes'] if x['id'] == tax.id)
                if not tax.price_include and tax.account_id:
                    move_line_dict['price'] += tax_dict['amount']
                if tax.price_include and (not tax.account_id or not tax.deduced_account_id):
                    if tax_dict['amount'] > 0.0:  # Negativo é retido
                        move_line_dict['price'] -= float(Decimal(Decimal(tax_dict['amount']).quantize(Decimal('.01'),
                                                                                            rounding=ROUND_HALF_UP)))

            res.append(move_line_dict)

        return res

    @api.multi
    def tax_line_move_line_get(self, invoice):
        res = []
        done_taxes = []
        for tax_line in sorted(invoice.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount_total:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount_total,
                    'quantity': 1,
                    'price': tax_line.amount_total,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': invoice.id,
                    'tax_ids': [(6, 0, list(done_taxes))] if tax_line.tax_id.include_base_amount else []
                })
                done_taxes.append(tax.id)

        return res

    @api.multi
    def action_move_create(self, invoice):
        '''
        Função para criação dos lançamentos da tabela account.move
        :return:
        '''

        account_move = self.env['account.move']

        for i in invoice:
            if i.move_id:
                continue
            ctx = dict(invoice._context, lang=i.partner_id.lang)
            company_currency = self.currency_id
            iml = self.invoice_line_move_line_get(invoice)
            print(iml)
            iml += self.tax_line_move_line_get(invoice)
            diff_currency = i.currency_id != company_currency
            total, total_currency, iml = i.with_context(ctx).compute_invoice_totals(company_currency, iml)
            print('Total')
            print(total)
            print('Total Currency')
            print(total_currency)
            for l in iml:
                l['price'] = round(l['price'], 4)
            print('IML')
            print(iml)
            name = i.name or '/'
            for pay in self.payment_lines:

                # last line: add the diff
                #res_amount_currency -= amount_currency or 0
                #if i + 1 == len(totlines):
                #    amount_currency += res_amount_currency

                pay_values = {
                    'type': 'dest',
                    'name': name,
                    'price': - (pay.payment_amount),
                    'account_id': i.account_id.id,
                    'date_maturity': pay.payment_venc,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': i.id
                }

                iml.append(pay_values)

            part = self.env['res.partner']._find_accounting_partner(i.partner_id)
            line = [(0, 0, i.line_get_convert(l, part.id)) for l in iml]
            line = i.group_lines(iml, line)

            journal = i.journal_id.with_context(ctx)
            line = i.finalize_invoice_move_lines(line)

            date = i.date or i.date_invoice
            move_vals = {
                'ref': i.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': i.comment,
            }

            ctx['company_id'] = i.company_id.id
            ctx['invoice'] = i
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            i.with_context(ctx).write(vals)

        return True


    @api.multi
    def import_edoc(self):
        '''
        Função para finalizar a importação do documento eletrônico e gravar as informações nas
        suas respectivas tabelas(purchase_order, account_invoice, invoice_eletronic, etc)
        :return:
        '''

        purchase_order = self.create_purchase_order()
        invoice = self.create_account_invoice(purchase_order)

        return


class PartnerNotFound(models.Model):

    _name = 'partner.not.found'

    xml_file = fields.Binary(u'Arquivo XML')
    name = fields.Char('Nome Fantasia')
    legal_name = fields.Char('Razão Social')
    cnpj_cpf = fields.Char('CNPJ/CPF', size=18)
    inscr_est = fields.Char('Insc. Estadual', size=16)
    zip = fields.Char('CEP')
    street = fields.Char('Logradouro')
    number = fields.Char('Nro.')
    district = fields.Char('Bairro')
    state_id = fields.Many2one("res.country.state", string='UF')
    city_id = fields.Many2one('res.state.city', u'Cidade')
    country_id = fields.Many2one('res.country', string='País')
    supplier = fields.Boolean('Fornecedor', default=True)
    phone = fields.Char('Telefone p/ Contato')

    @api.multi
    def create_partner_from_file(self):
        '''
        Cadastrar parceiro no sistema apartir das informações obtidas no arquivo XML,
        caso o parceiro ainda não possua cadastro no sistema
        '''
        for record in self:
            partners = self.env['res.partner']
            partner_vals = {
                'name': record.name, 'legal_name': record.legal_name, 'cnpj_cpf': record.cnpj_cpf,
                'zip': record.zip, 'street': record.street, 'number': record.number, 'district': record.district,
                'state_id': record.state_id.id, 'city_id': record.city_id.id, 'country_id': record.country_id.id,
                'supplier': True, 'inscr_est': record.inscr_est, 'is_company': True,
            }

            partners.create(partner_vals)
            return self._reopen_form()
            #self.invoice_import_id.compute_xml()

    @api.multi
    def _reopen_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'br.account.invoice.import.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'inline',
            'context': {'default_xml_file': self.xml_file}
        }

class ProductNotFound(models.Model):

    _name = 'product.not.found'

    currency_id = fields.Many2one("res.currency", string="Moeda", readonly=True)
    order_id = fields.Many2one('br.account.invoice.import.wizard', string='Invoice Reference', required=True,
                               ondelete='cascade', index=True, copy=False)
    # Dados do Produto na NF-e
    inv_prod_name = fields.Char(string='Produto na NF-e', readonly=True)
    inv_prod_code = fields.Char(string='Cód do Fornecedor', readonly=True)
    inv_prod_uom = fields.Char(string='UoM na NF-e', readonly=True)
    inv_prod_ean = fields.Char(string='EAN na NF-e', readonly=True)
    inv_prod_ncm = fields.Char(string='NCM na NF-e', readonly=True)
    inv_prod_qty = fields.Float(string='Qtd na NF-e', digits=dp.get_precision('Product Unit of Measure'),
                                 readonly=True)
    inv_prod_price_unit = fields.Monetary(string='Vlr Unit na NF-e', digits=dp.get_precision('Product Price'),
                                       readonly=True)
    inv_prod_desc = fields.Float(string=u'Desc', digits=(10, 4), readonly=True)
    inv_prod_desc_percent = fields.Float(string=u'Percentual Desc', readonly=True, compute='compute_discount',
                                         digits=dp.get_precision('Product Price'))
    inv_prod_vlr = fields.Monetary(string=u'Valor do Produto', readonly=True)
    inv_cest = fields.Char(string=u'CEST', size=10, readonly=True,
                           help=u'Código Especificador da Substituição Tributária')
    inv_origem = fields.Selection(ORIGEM_PROD, string=u'Origem Mercadoria', readonly=True)

    # Dados do Produto no Sistema
    product_id = fields.Many2one('product.product', string='Produto no Sistema')
    product_hint = fields.Many2one('product.product', string='Produtos Semelhantes')
    product_force_all = fields.Boolean(string=u'Buscar Todos', defaul=False)
    product_match = fields.Boolean(string=u'Produto Combinou')
    product_uom = fields.Many2one('product.uom', string=u'UoM no Sistema')
    product_uom_qty = fields.Float(string=u'Qtd no Sistema', digits=dp.get_precision('Product Unit of Measure'))
    product_price_unit = fields.Monetary(u'Vlr Unit no Sistema', required=True, digits=dp.get_precision('Product Price'),
                                      readonly=True)

    # Dados dos Impostos dos Produtos - ICMS
    icms_cst = fields.Selection(CST_ICMS + CSOSN_SIMPLES, string=u'Situação Tributária', readonly=True)
    icms_aliquota = fields.Float(string=u'Alíquota ( % )', digits=dp.get_precision('Account'), readonly=True)
    icms_base_calculo = fields.Monetary(string=u'Base de Cálculo', digits=dp.get_precision('Account'), readonly=True)
    icms_aliquota_reducao_base = fields.Float(string=u'Redução Base ( % )', digits=dp.get_precision('Account'),
                                              readonly=True)
    icms_valor_credito = fields.Monetary(string=u"Valor de Crédito", digits=dp.get_precision('Account'), readonly=True)
    icms_valor = fields.Monetary(string=u'Valor ICMS', digits=dp.get_precision('Account'), readonly=True)

    # Dados dos Impostos dos Produtos - ICMS-ST
    icms_motivo_desoneracao = fields.Selection(desoneracao_motivos, string=u'Motivo Desoneração', readonly=True)
    icms_valor_desonerado = fields.Monetary(string=u'Valor ICMS Desonerado', digits=dp.get_precision('Account'),
        readonly=True)

    # Dados dos Impostos dos Produtos - ICMS-ST
    icms_st_aliquota = fields.Float(string=u'Alíquota ( % )', digits=dp.get_precision('Account'), readonly=True)
    icms_st_aliquota_mva = fields.Float(string=u'% MVA', digits=dp.get_precision('Account'), readonly=True)
    icms_st_base_calculo = fields.Monetary(string=u'Base de Cálculo', digits=dp.get_precision('Account'), readonly=True)
    icms_st_aliquota_reducao_base = fields.Float(string=u'Redução Base ( % )', digits=dp.get_precision('Account'),
                                              readonly=True)
    icms_st_valor_credito = fields.Monetary(string=u"Valor de Crédito", digits=dp.get_precision('Account'), readonly=True)
    icms_st_valor = fields.Monetary(string=u'Valor ICMS ST', digits=dp.get_precision('Account'), readonly=True)

    # Dados dos Impostos dos Produtos - IPI
    ipi_cst = fields.Selection(CST_IPI, string=u'Situação tributária', readonly=True)
    ipi_aliquota = fields.Float(string=u'Alíquota ( % )', digits=dp.get_precision('Account'), readonly=True)
    ipi_base_calculo = fields.Monetary(string=u'Base de cálculo', digits=dp.get_precision('Account'), readonly=True)
    ipi_reducao_bc = fields.Float(string=u'% Redução Base', digits=dp.get_precision('Account'), readonly=True)
    ipi_valor = fields.Monetary(string=u'Valor IPI', digits=dp.get_precision('Account'), readonly=True)

    # Dados dos Impostos dos Produtos - PIS
    pis_cst = fields.Selection(CST_PIS_COFINS, string=u'Situação Tributária', readonly=True)
    pis_aliquota = fields.Float(string=u'Alíquota ( % )', digits=dp.get_precision('Account'), readonly=True)
    pis_base_calculo = fields.Monetary(string=u'Base de Cálculo', digits=dp.get_precision('Account'), readonly=True)
    pis_valor = fields.Monetary(string=u'Valor PIS', digits=dp.get_precision('Account'), readonly=True)
    pis_valor_retencao = fields.Monetary(string=u'Valor Retido', digits=dp.get_precision('Account'), readonly=True)

    # Dados dos Impostos dos Produtos - COFINS
    cofins_cst = fields.Selection(CST_PIS_COFINS, string=u'Situação Tributária', readonly=True)
    cofins_aliquota = fields.Float(string=u'Alíquota ( % )', digits=dp.get_precision('Account'), readonly=True)
    cofins_base_calculo = fields.Monetary(string=u'Base de Cálculo', digits=dp.get_precision('Account'), readonly=True)
    cofins_valor = fields.Monetary(string=u'Valor COFINS', digits=dp.get_precision('Account'), readonly=True)
    cofins_valor_retencao = fields.Monetary(string=u'Valor Retido', digits=dp.get_precision('Account'), readonly=True)

    # Dados Gerais
    cfop_id = fields.Many2one('br_account.cfop', string=u'CFOP')
    aliquota_mva = fields.Float(string=u'Alíq MVA ( % )')

    # Boolean Para confirmar se os dados do produto estão ok
    product_validate = fields.Boolean(string='Produto Válidado', default=False, store=True, compute='validate_product')

    @api.multi
    @api.onchange('inv_prod_desc', 'inv_prod_vlr', )
    def compute_discount(self):
        for record in self:
            if record.inv_prod_desc_percent != 0:
                record.inv_prod_desc_percent = (record.inv_prod_desc / record.inv_prod_vlr) * 100


    @api.multi
    @api.onchange('product_hint')
    def _set_product(self):
        for record in self:
            if record.product_hint != False:
                record.product_id = record.product_hint

    @api.multi
    def product_hint_domain(self):
        if not self.product_id:
            domain = {'product_hint': [('fiscal_classification_id.code', '=', self.inv_prod_ncm)]}
            result = {'domain': domain}

            return result

    @api.multi
    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'cfop_id')
    def validate_product(self):
        for record in self:
            record.product_price_unit = record.inv_prod_vlr / record.product_uom_qty
            if record.product_id.id == False or record.product_uom.id == False\
                    or record.product_uom_qty == 0 or record.cfop_id.id == False:
                record.product_validate = False
            else:
                record.product_validate = True

    @api.multi
    @api.onchange('product_force_all')
    def force_search_all_products(self):
        '''Retira o domínio dos produtos e busca dentro de todos os cadastros de produtos'''
        if self.product_force_all == True:
            vals = {}
            domain = {'product_hint': []}
            result = {'domain': domain}
            self.update(vals)

            return result

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id

        result = {'domain': domain}
        self.update(vals)

        return result

    @api.onchange('product_uom_qty')
    def _check_product_qty(self):
        for record in self:
            if record.product_uom_qty == 0:
                record.write({'product_uom_qty': record.inv_prod_qty})
                raise ValidationError(_('Quantidade não pode ser igual a zero.'))

    @api.multi
    @api.depends('inv_prod_qty')
    def get_default_values(self):
        for record in self:
            # Qtd. dos produtos
            record.product_uom_qty = record.inv_prod_qty

    @api.multi
    def create_product(self):
        for record in self:
            if record.product_match == True:
                raise UserError(_(u'O Produto foi localizado, não pode ser criado novamente.'))

            new_product = {
                'name': record.inv_prod_name,
                'ncm': record.inv_prod_ncm,
                'barcode': record.inv_prod_ean,
                'type': 'product',
            }

            product = self.env['product.template'].create(new_product)
            product = self.env['product.product'].search([('product_tmpl_id', '=', product.id)])

            record.update({
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_match': True,
            })



class BrAccountInvoiceImportPayment(models.Model):

    _name = 'br.account.invoice.import.payment'
    '''
    Modelo transitório para salvar os dados de cobrança das faturas importadas
    '''
    # Dados Gerais
    currency_id = fields.Many2one("res.currency", string=u'Moeda', readonly=True)
    order_id = fields.Many2one('br.account.invoice.import.wizard', string='Invoice Reference', required=True,
                               ondelete='cascade', index=True, copy=False)
    payment_create_type = fields.Selection([('invoice', u'Dados da Cobrança Gerados Através da NF-e'),
                                            ('payment_type', u'Gerar Através de Modos de Pagamento')],
                                           string=u'Modo de Lançamento das Cobranças no Contas a Pagar')
    # Dados da Parcela
    payment_dup = fields.Char(string=u'Número da Duplicata')
    payment_venc = fields.Date(string=u'Data de Vencimento', required=True)
    payment_amount = fields.Monetary(string=u'Valor da Parcela')

    @api.multi
    @api.onchange('payment_amount')
    def validate_payment(self):
        for record in self:
            record.order_id.check_amount_payments()
            '''
            if record.payment_amount > record.order_id.vlr_fatura:
                raise UserError(_(u'O Valor das cobranças não pode ser maior que o valor da Nota Fiscal!\n'
                                  u'Por Favor corrija o(s) lançamento(s) da(s) cobrança(s)'))
            '''