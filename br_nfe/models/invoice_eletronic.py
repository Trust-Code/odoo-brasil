# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import io
import base64
import logging
import hashlib
from lxml import etree
from datetime import datetime
from pytz import timezone
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import autorizar_nfe
    from pytrustnfe.nfe import xml_autorizar_nfe
    from pytrustnfe.nfe import retorno_autorizar_nfe
    from pytrustnfe.nfe import recepcao_evento_cancelamento
    from pytrustnfe.nfe import consultar_protocolo_nfe
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.utils import ChaveNFe, gerar_chave, gerar_nfeproc, \
        gerar_nfeproc_cancel
    from pytrustnfe.nfe.danfe import danfe
    from pytrustnfe.xml.validate import valida_nfe
    from pytrustnfe.urls import url_qrcode, url_qrcode_exibicao
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)

STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    @api.depends('chave_nfe')
    def _compute_format_danfe_key(self):
        for item in self:
            item.chave_nfe_danfe = re.sub("(.{4})", "\\1.",
                                          item.chave_nfe, 10, re.DOTALL)

    @api.multi
    def generate_correction_letter(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "wizard.carta.correcao.eletronica",
            "views": [[False, "form"]],
            "name": _("Carta de Correção"),
            "target": "new",
            "context": {'default_eletronic_doc_id': self.id},
        }

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string='Modo de Pagamento',
        readonly=True, states=STATE)
    state = fields.Selection(selection_add=[('denied', 'Denegado')])
    iest = fields.Char(string="IE Subst. Tributário")
    ambiente_nfe = fields.Selection(
        string=u"Ambiente NFe", related="company_id.tipo_ambiente",
        readonly=True)
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Consumidor Final', readonly=True, states=STATE, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('5', u'Operação presencial, fora do estabelecimento'),
        ('9', u'Operação não presencial, outros'),
    ], u'Indicador de Presença', readonly=True, states=STATE, required=False,
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.', default='0')
    ind_dest = fields.Selection([
        ('1', u'1 - Operação Interna'),
        ('2', u'2 - Operação Interestadual'),
        ('3', u'3 - Operação com exterior')],
        string=u"Indicador Destinatário", readonly=True, states=STATE)
    ind_ie_dest = fields.Selection([
        ('1', u'1 - Contribuinte ICMS'),
        ('2', u'2 - Contribuinte Isento de Cadastro'),
        ('9', u'9 - Não Contribuinte')],
        string=u"Indicador IE Dest.", help=u"Indicador da IE do desinatário",
        readonly=True, states=STATE)
    tipo_emissao = fields.Selection([
        ('1', u'1 - Emissão normal'),
        ('2', u'2 - Contingência FS-IA, com impressão do DANFE em formulário \
         de segurança'),
        ('3', u'3 - Contingência SCAN'),
        ('4', u'4 - Contingência DPEC'),
        ('5', u'5 - Contingência FS-DA, com impressão do DANFE em \
         formulário de segurança'),
        ('6', u'6 - Contingência SVC-AN'),
        ('7', u'7 - Contingência SVC-RS'),
        ('9', u'9 - Contingência off-line da NFC-e')],
        string=u"Tipo de Emissão", readonly=True, states=STATE, default='1')

    # Transporte
    data_entrada_saida = fields.Datetime(
        string="Data Entrega", help="Data para saída/entrada das mercadorias")
    modalidade_frete = fields.Selection(
        [('0', '0 - Contratação do Frete por conta do Remetente (CIF)'),
         ('1', '1 - Contratação do Frete por conta do Destinatário (FOB)'),
         ('2', '2 - Contratação do Frete por conta de Terceiros'),
         ('3', '3 - Transporte Próprio por conta do Remetente'),
         ('4', '4 - Transporte Próprio por conta do Destinatário'),
         ('9', '9 - Sem Ocorrência de Transporte')],
        string=u'Modalidade do frete', default="9",
        readonly=True, states=STATE)
    transportadora_id = fields.Many2one(
        'res.partner', string=u"Transportadora", readonly=True, states=STATE)
    placa_veiculo = fields.Char(
        string=u'Placa do Veículo', size=7, readonly=True, states=STATE)
    uf_veiculo = fields.Char(
        string=u'UF da Placa', size=2, readonly=True, states=STATE)
    rntc = fields.Char(
        string="RNTC", size=20, readonly=True, states=STATE,
        help=u"Registro Nacional de Transportador de Carga")

    reboque_ids = fields.One2many(
        'nfe.reboque', 'invoice_eletronic_id',
        string=u"Reboques", readonly=True, states=STATE)
    volume_ids = fields.One2many(
        'nfe.volume', 'invoice_eletronic_id',
        string=u"Volumes", readonly=True, states=STATE)

    # Exportação
    uf_saida_pais_id = fields.Many2one(
        'res.country.state', domain=[('country_id.code', '=', 'BR')],
        string="UF Saída do País", readonly=True, states=STATE)
    local_embarque = fields.Char(
        string='Local de Embarque', size=60, readonly=True, states=STATE)
    local_despacho = fields.Char(
        string='Local de Despacho', size=60, readonly=True, states=STATE)

    # Cobrança
    numero_fatura = fields.Char(
        string=u"Fatura", readonly=True, states=STATE)
    fatura_bruto = fields.Monetary(
        string=u"Valor Original", readonly=True, states=STATE)
    fatura_desconto = fields.Monetary(
        string=u"Desconto", readonly=True, states=STATE)
    fatura_liquido = fields.Monetary(
        string=u"Valor Líquido", readonly=True, states=STATE)

    duplicata_ids = fields.One2many(
        'nfe.duplicata', 'invoice_eletronic_id',
        string=u"Duplicatas", readonly=True, states=STATE)

    # Compras
    nota_empenho = fields.Char(
        string="Nota de Empenho", size=22, readonly=True, states=STATE)
    pedido_compra = fields.Char(
        string="Pedido Compra", size=60, readonly=True, states=STATE)
    contrato_compra = fields.Char(
        string="Contrato Compra", size=60, readonly=True, states=STATE)

    sequencial_evento = fields.Integer(
        string=u"Sequêncial Evento", default=1, readonly=True, states=STATE)
    recibo_nfe = fields.Char(
        string=u"Recibo NFe", size=50, readonly=True, states=STATE)
    chave_nfe = fields.Char(
        string=u"Chave NFe", size=50, readonly=True, states=STATE)
    chave_nfe_danfe = fields.Char(
        string=u"Chave Formatado", compute="_compute_format_danfe_key")
    protocolo_nfe = fields.Char(
        string=u"Protocolo", size=50, readonly=True, states=STATE,
        help=u"Protocolo de autorização da NFe")
    nfe_processada = fields.Binary(string=u"Xml da NFe", readonly=True)
    nfe_processada_name = fields.Char(
        string=u"Xml da NFe", size=100, readonly=True)

    valor_icms_uf_remet = fields.Monetary(
        string=u"ICMS Remetente", readonly=True, states=STATE,
        help=u'Valor total do ICMS Interestadual para a UF do Remetente')
    valor_icms_uf_dest = fields.Monetary(
        string=u"ICMS Destino", readonly=True, states=STATE,
        help=u'Valor total do ICMS Interestadual para a UF de destino')
    valor_icms_fcp_uf_dest = fields.Monetary(
        string=u"Total ICMS FCP", readonly=True, states=STATE,
        help=u'Total total do ICMS relativo Fundo de Combate à Pobreza (FCP) \
        da UF de destino')

    # NFC-e
    qrcode_hash = fields.Char(string='QR-Code hash')
    qrcode_url = fields.Char(string='QR-Code URL')
    metodo_pagamento = fields.Selection(
        [('01', 'Dinheiro'),
         ('02', 'Cheque'),
         ('03', 'Cartão de Crédito'),
         ('04', 'Cartão de Débito'),
         ('05', 'Crédito Loja'),
         ('10', 'Vale Alimentação'),
         ('11', 'Vale Refeição'),
         ('12', 'Vale Presente'),
         ('13', 'Vale Combustível'),
         ('15', 'Boleto Bancário'),
         ('90', 'Sem pagamento'),
         ('99', 'Outros')],
        string="Forma de Pagamento", default="01")
    valor_pago = fields.Monetary(string='Valor pago')
    troco = fields.Monetary(string='Troco')

    # Documentos Relacionados
    fiscal_document_related_ids = fields.One2many(
        'br_account.document.related', 'invoice_eletronic_id',
        'Documentos Fiscais Relacionados', readonly=True, states=STATE)

    # CARTA DE CORRECAO
    cartas_correcao_ids = fields.One2many(
        'carta.correcao.eletronica.evento', 'eletronic_doc_id',
        string=u"Cartas de Correção", readonly=True, states=STATE)

    def can_unlink(self):
        res = super(InvoiceEletronic, self).can_unlink()
        if self.state == 'denied':
            return False
        return res

    @api.multi
    def unlink(self):
        for item in self:
            if item.state in ('denied'):
                raise UserError(
                    _('Documento Eletrônico Denegado - Proibido excluir'))
        super(InvoiceEletronic, self).unlink()

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model in ('55', '65'):
            if not self.company_id.partner_id.inscr_est:
                errors.append(u'Emitente / Inscrição Estadual')

            for eletr in self.eletronic_item_ids:
                prod = u"Produto: %s - %s" % (eletr.product_id.default_code,
                                              eletr.product_id.name)
                if not eletr.cfop:
                    errors.append(u'%s - CFOP' % prod)
                if eletr.tipo_produto == 'product':
                    if not eletr.icms_cst:
                        errors.append(u'%s - CST do ICMS' % prod)
                    if not eletr.ipi_cst:
                        errors.append(u'%s - CST do IPI' % prod)
                if eletr.tipo_produto == 'service':
                    if not eletr.issqn_codigo:
                        errors.append(u'%s - Código de Serviço' % prod)
                if not eletr.pis_cst:
                    errors.append(u'%s - CST do PIS' % prod)
                if not eletr.cofins_cst:
                    errors.append(u'%s - CST do Cofins' % prod)
        # NF-e
        if self.model == '55':
            if not self.fiscal_position_id:
                errors.append(u'Configure a posição fiscal')
            if self.company_id.accountant_id and not \
               self.company_id.accountant_id.cnpj_cpf:
                errors.append(u'Emitente / CNPJ do escritório contabilidade')
        # NFC-e
        if self.model == '65':
            if not self.company_id.id_token_csc:
                errors.append("Identificador do CSC inválido")
            if not len(self.company_id.csc or ''):
                errors.append("CSC Inválido")
            if self.partner_id.cnpj_cpf is None:
                errors.append("CNPJ/CPF do Parceiro inválido")
            if len(self.serie) == 0:
                errors.append("Número de Série da NFe Inválido")

        return errors

    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_item(
            item, invoice)
        if self.model not in ('55', '65'):
            return res

        if self.ambiente != 'homologacao':
            xProd = item.product_id.with_context(
                display_default_code=False).name_get()[0][1]
        else:
            xProd = 'NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO -\
 SEM VALOR FISCAL'

        price_precis = dp.get_precision('Product Price')(self.env.cr)
        qty_precis = dp.get_precision('Product Unit of Measure')(self.env.cr)
        qty_frmt = '{:.%sf}' % qty_precis[1]
        price_frmt = '{:.%sf}' % price_precis[1]
        prod = {
            'cProd': item.product_id.default_code,
            'cEAN': item.product_id.barcode or 'SEM GTIN',
            'xProd': xProd,
            'NCM': re.sub('[^0-9]', '', item.ncm or '00')[:8],
            'CFOP': item.cfop,
            'uCom': '{:.6}'.format(item.uom_id.name or ''),
            'qCom': qty_frmt.format(item.quantidade),
            'vUnCom': price_frmt.format(item.preco_unitario),
            'vProd':  "%.02f" % item.valor_bruto,
            'cEANTrib': item.product_id.barcode or 'SEM GTIN',
            'uTrib': '{:.6}'.format(item.uom_id.name or ''),
            'qTrib': qty_frmt.format(item.quantidade),
            'vUnTrib': price_frmt.format(item.preco_unitario),
            'vFrete': "%.02f" % item.frete if item.frete else '',
            'vSeg': "%.02f" % item.seguro if item.seguro else '',
            'vDesc': "%.02f" % item.desconto if item.desconto else '',
            'vOutro': "%.02f" % item.outras_despesas
            if item.outras_despesas else '',
            'indTot': item.indicador_total,
            'cfop': item.cfop,
            'CEST': re.sub('[^0-9]', '', item.cest or ''),
            'xPed': item.pedido_compra or invoice.pedido_compra or '',
            'nItemPed': item.item_pedido_compra or '',
        }
        if item.informacao_adicional:
            infAdProd = item.informacao_adicional
        else:
            infAdProd = ''
        if item.product_id.tracking == 'lot':
            pick = self.env['stock.picking'].search([
                ('origin','=', self.invoice_id.origin),
                ('state','=', 'done')])
            for line in pick.move_line_ids:
                lotes = []
                if line.product_id.id == item.product_id.id:
                    for lot in line.lot_id:
                        lote = {
                            'nLote': lot.name, 
                            'qLote': line.qty_done,
                            'dVal': lot.life_date.strftime('%Y-%m-%d'),
                            'dFab': lot.use_date.strftime('%Y-%m-%d'),
                        }
                        lotes.append(lote)
                        fab = fields.Datetime.from_string(lot.use_date)
                        vcto = fields.Datetime.from_string(lot.life_date)
                        infAdProd += ' Lote: %s, Fab.: %s, Vencto.: %s' \
                            %(lot.name, fab, vcto)
                prod["rastro"] = lotes
        di_vals = []
        for di in item.import_declaration_ids:
            adicoes = []
            for adi in di.line_ids:
                adicoes.append({
                    'nAdicao': adi.name,
                    'nSeqAdic': adi.sequence,
                    'cFabricante': adi.manufacturer_code,
                    'vDescDI': "%.02f" % adi.amount_discount
                    if adi.amount_discount else '',
                    'nDraw': adi.drawback_number or '',
                })

            di_vals.append({
                'nDI': di.name,
                'dDI': di.date_registration.strftime('%Y-%m-%d'),
                'xLocDesemb': di.location,
                'UFDesemb': di.state_id.code,
                'dDesemb': di.date_release.strftime('%Y-%m-%d'),
                'tpViaTransp': di.type_transportation,
                'vAFRMM': "%.02f" % di.afrmm_value if di.afrmm_value else '',
                'tpIntermedio': di.type_import,
                'CNPJ': di.thirdparty_cnpj or '',
                'UFTerceiro': di.thirdparty_state_id.code or '',
                'cExportador': di.exporting_code,
                'adi': adicoes,
            })

        prod["DI"] = di_vals

        imposto = {
            'vTotTrib': "%.02f" % item.tributos_estimados,
            'PIS': {
                'CST': item.pis_cst,
                'vBC': "%.02f" % item.pis_base_calculo,
                'pPIS': "%.02f" % item.pis_aliquota,
                'vPIS': "%.02f" % item.pis_valor
            },
            'COFINS': {
                'CST': item.cofins_cst,
                'vBC': "%.02f" % item.cofins_base_calculo,
                'pCOFINS': "%.02f" % item.cofins_aliquota,
                'vCOFINS': "%.02f" % item.cofins_valor
            },
            'II': {
                'vBC': "%.02f" % item.ii_base_calculo,
                'vDespAdu': "%.02f" % item.ii_valor_despesas,
                'vII': "%.02f" % item.ii_valor,
                'vIOF': "%.02f" % item.ii_valor_iof
            },
        }
        if item.tipo_produto == 'service':
            retencoes = item.pis_valor_retencao + \
                item.cofins_valor_retencao + item.inss_valor_retencao + \
                item.irrf_valor_retencao + item.csll_valor_retencao
            imposto.update({
                'ISSQN': {
                    'vBC': "%.02f" % item.issqn_base_calculo,
                    'vAliq': "%.02f" % item.issqn_aliquota,
                    'vISSQN': "%.02f" % item.issqn_valor,
                    'cMunFG': "%s%s" % (invoice.company_id.state_id.ibge_code,
                                        invoice.company_id.city_id.ibge_code),
                    'cListServ': item.issqn_codigo,
                    'vDeducao': '',
                    'vOutro': "%.02f" % retencoes if retencoes else '',
                    'vISSRet': "%.02f" % item.issqn_valor_retencao
                    if item.issqn_valor_retencao else '',
                    'indISS': 1,  # Exigivel
                    'cServico': item.issqn_codigo,
                    'cMun': "%s%s" % (invoice.company_id.state_id.ibge_code,
                                      invoice.company_id.city_id.ibge_code),
                    'indIncentivo': 2,  # Não
                }
            })
        else:
            imposto.update({
                'ICMS': {
                    'orig':  item.origem,
                    'CST': item.icms_cst,
                    'modBC': item.icms_tipo_base,
                    'vBC': "%.02f" % item.icms_base_calculo,
                    'pRedBC': "%.02f" % item.icms_aliquota_reducao_base,
                    'pICMS': "%.02f" % item.icms_aliquota,
                    'vICMS': "%.02f" % item.icms_valor,
                    'modBCST': item.icms_st_tipo_base,
                    'pMVAST': "%.02f" % item.icms_st_aliquota_mva,
                    'pRedBCST': "%.02f" % item.icms_st_aliquota_reducao_base,
                    'vBCST': "%.02f" % item.icms_st_base_calculo,
                    'pICMSST': "%.02f" % item.icms_st_aliquota,
                    'vICMSST': "%.02f" % item.icms_st_valor,
                    'pCredSN': "%.02f" % item.icms_aliquota_credito,
                    'vCredICMSSN': "%.02f" % item.icms_valor_credito,
                    'vICMSSubstituto': "%.02f" % item.icms_substituto,
                    'vBCSTRet': "%.02f" % item.icms_bc_st_retido,
                    'pST': "%.02f" % item.icms_aliquota_st_retido,
                    'vICMSSTRet': "%.02f" % item.icms_st_retido,
                },
                'IPI': {
                    'clEnq': item.classe_enquadramento_ipi or '',
                    'cEnq': item.codigo_enquadramento_ipi,
                    'CST': item.ipi_cst,
                    'vBC': "%.02f" % item.ipi_base_calculo,
                    'pIPI': "%.02f" % item.ipi_aliquota,
                    'vIPI': "%.02f" % item.ipi_valor
                },
            })
        if item.tem_difal:
            imposto['ICMSUFDest'] = {
                'vBCUFDest': "%.02f" % item.icms_bc_uf_dest,
                'vBCFCPUFDest': "%.02f" % item.icms_bc_uf_dest,
                'pFCPUFDest': "%.02f" % item.icms_aliquota_fcp_uf_dest,
                'pICMSUFDest': "%.02f" % item.icms_aliquota_uf_dest,
                'pICMSInter': "%.02f" % item.icms_aliquota_interestadual,
                'pICMSInterPart': "%.02f" % item.icms_aliquota_inter_part,
                'vFCPUFDest': "%.02f" % item.icms_fcp_uf_dest,
                'vICMSUFDest': "%.02f" % item.icms_uf_dest,
                'vICMSUFRemet': "%.02f" % item.icms_uf_remet, }
        return {'prod': prod, 'imposto': imposto,
                'infAdProd': infAdProd}

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model not in ('55', '65'):
            return res

        tz = timezone(self.env.user.tz or 'America/Sao_Paulo')
        dt_emissao = datetime.now(tz).replace(microsecond=0).isoformat()
        dt_saida = fields.Datetime.from_string(self.data_entrada_saida)
        if dt_saida:
            dt_saida = tz.localize(dt_saida).replace(microsecond=0).isoformat()
        else:
            dt_saida = dt_emissao

        ide = {
            'cUF': self.company_id.state_id.ibge_code,
            'cNF': "%08d" % self.numero_controle,
            'natOp': self.fiscal_position_id.name,
            'mod': self.model,
            'serie': self.serie.code,
            'nNF': self.numero,
            'dhEmi': dt_emissao,
            'dhSaiEnt': dt_saida,
            'tpNF': '0' if self.tipo_operacao == 'entrada' else '1',
            'idDest': self.ind_dest or 1,
            'cMunFG': "%s%s" % (self.company_id.state_id.ibge_code,
                                self.company_id.city_id.ibge_code),
            # Formato de Impressão do DANFE - 1 - Danfe Retrato, 4 - Danfe NFCe
            'tpImp': '1' if self.model == '55' else '4',
            'tpEmis': int(self.tipo_emissao),
            'tpAmb': 2 if self.ambiente == 'homologacao' else 1,
            'finNFe': self.finalidade_emissao,
            'indFinal': self.ind_final or '1',
            'indPres': self.ind_pres or '1',
            'procEmi': 0,
            'verProc': 'Odoo 11 - Trustcode',
        }
        # Documentos Relacionados
        documentos = []
        for doc in self.fiscal_document_related_ids:
            data = fields.Datetime.from_string(doc.date)
            if doc.document_type == 'nfe':
                documentos.append({
                    'refNFe': doc.access_key
                })
            elif doc.document_type == 'nf':
                documentos.append({
                    'refNF': {
                        'cUF': doc.state_id.ibge_code,
                        'AAMM': data.strftime("%y%m"),
                        'CNPJ': re.sub('[^0-9]', '', doc.cnpj_cpf),
                        'mod': doc.fiscal_document_id.code,
                        'serie': doc.serie,
                        'nNF': doc.internal_number,
                    }
                })

            elif doc.document_type == 'cte':
                documentos.append({
                    'refCTe': doc.access_key
                })
            elif doc.document_type == 'nfrural':
                cnpj_cpf = re.sub('[^0-9]', '', doc.cnpj_cpf)
                documentos.append({
                    'refNFP': {
                        'cUF': doc.state_id.ibge_code,
                        'AAMM': data.strftime("%y%m"),
                        'CNPJ': cnpj_cpf if len(cnpj_cpf) == 14 else '',
                        'CPF': cnpj_cpf if len(cnpj_cpf) == 11 else '',
                        'IE': doc.inscr_est,
                        'mod': doc.fiscal_document_id.code,
                        'serie': doc.serie,
                        'nNF': doc.internal_number,
                    }
                })
            elif doc.document_type == 'cf':
                documentos.append({
                    'refECF': {
                        'mod': doc.fiscal_document_id.code,
                        'nECF': doc.serie,
                        'nCOO': doc.internal_number,
                    }
                })

        ide['NFref'] = documentos
        emit = {
            'tipo': self.company_id.partner_id.company_type,
            'cnpj_cpf': re.sub('[^0-9]', '', self.company_id.cnpj_cpf),
            'xNome': self.company_id.legal_name,
            'xFant': self.company_id.name,
            'enderEmit': {
                'xLgr': self.company_id.street,
                'nro': self.company_id.number,
                'xCpl': self.company_id.street2 or '',
                'xBairro': self.company_id.district,
                'cMun': '%s%s' % (
                    self.company_id.partner_id.state_id.ibge_code,
                    self.company_id.partner_id.city_id.ibge_code),
                'xMun': self.company_id.city_id.name,
                'UF': self.company_id.state_id.code,
                'CEP': re.sub('[^0-9]', '', self.company_id.zip),
                'cPais': self.company_id.country_id.ibge_code,
                'xPais': self.company_id.country_id.name,
                'fone': re.sub('[^0-9]', '', self.company_id.phone or '')
            },
            'IE': re.sub('[^0-9]', '', self.company_id.inscr_est),
            'IEST': re.sub('[^0-9]', '', self.iest or ''),
            'CRT': self.company_id.fiscal_type,
        }
        if self.company_id.cnae_main_id and self.company_id.inscr_mun:
            emit['IM'] = re.sub('[^0-9]', '', self.company_id.inscr_mun or '')
            emit['CNAE'] = re.sub(
                '[^0-9]', '', self.company_id.cnae_main_id.code or '')
        dest = None
        exporta = None
        if self.commercial_partner_id:
            partner = self.commercial_partner_id
            dest = {
                'tipo': partner.company_type,
                'cnpj_cpf': re.sub('[^0-9]', '', partner.cnpj_cpf or ''),
                'xNome': partner.legal_name or partner.name,
                'enderDest': {
                    'xLgr': partner.street,
                    'nro': partner.number,
                    'xCpl': partner.street2 or '',
                    'xBairro': partner.district,
                    'cMun': '%s%s' % (partner.state_id.ibge_code,
                                      partner.city_id.ibge_code),
                    'xMun': partner.city_id.name,
                    'UF': partner.state_id.code,
                    'CEP': re.sub('[^0-9]', '', partner.zip or ''),
                    'cPais': (partner.country_id.bc_code or '')[-4:],
                    'xPais': partner.country_id.name,
                    'fone': re.sub('[^0-9]', '', partner.phone or '')
                },
                'indIEDest': self.ind_ie_dest,
                'IE':  re.sub('[^0-9]', '', partner.inscr_est or ''),
                'ISUF': partner.suframa or '',
            }
            if self.model == '65':
                dest['IE'] = ''
                dest.update(
                    {'CPF': re.sub('[^0-9]', '', partner.cnpj_cpf or '')})

            if self.ambiente == 'homologacao':
                dest['xNome'] = \
                    u'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO -\
 SEM VALOR FISCAL'
            if partner.country_id.id != self.company_id.country_id.id:
                dest['idEstrangeiro'] = re.sub(
                    '[^0-9]', '', partner.cnpj_cpf or '')
                dest['enderDest']['UF'] = 'EX'
                dest['enderDest']['xMun'] = 'Exterior'
                dest['enderDest']['cMun'] = '9999999'
                dest['enderDest']['CEP'] = ''
                exporta = {
                    'UFSaidaPais': self.uf_saida_pais_id.code or '',
                    'xLocExporta': self.local_embarque or '',
                    'xLocDespacho': self.local_despacho or '',
                }

        entrega = None

        if self.partner_shipping_id:
            shipping_id = self.partner_shipping_id

            entrega = {
                'xNome': shipping_id.legal_name or shipping_id.name,
                'xLgr': shipping_id.street,
                'nro': shipping_id.number,
                'xCpl': shipping_id.street2 or '',
                'xBairro': shipping_id.district,
                'cMun': '%s%s' % (shipping_id.state_id.ibge_code,
                                  shipping_id.city_id.ibge_code),
                'xMun': shipping_id.city_id.name,
                'UF': shipping_id.state_id.code,
                'CEP': re.sub('[^0-9]', '', shipping_id.zip or ''),
                'cPais': (shipping_id.country_id.bc_code or '')[-4:],
                'xPais': shipping_id.country_id.name,
                'fone': re.sub('[^0-9]', '', shipping_id.phone or '')
            }
            cnpj_cpf = re.sub(
                "[^0-9]", "", shipping_id.cnpj_cpf or partner.cnpj_cpf or ""
            )

            if len(cnpj_cpf) == 14:
                entrega.update({'CNPJ': cnpj_cpf})
            else:
                entrega.update({'CPF': cnpj_cpf})

        autorizados = []
        if self.company_id.accountant_id:
            autorizados.append({
                'CNPJ': re.sub(
                    '[^0-9]', '', self.company_id.accountant_id.cnpj_cpf)
            })

        eletronic_items = []
        for item in self.eletronic_item_ids:
            eletronic_items.append(
                self._prepare_eletronic_invoice_item(item, self))
        total = {
            # ICMS
            'vBC': "%.02f" % self.valor_bc_icms,
            'vICMS': "%.02f" % self.valor_icms,
            'vICMSDeson': '0.00',
            'vFCP': '0.00',  # TODO Implementar aqui
            'vBCST': "%.02f" % self.valor_bc_icmsst,
            'vST': "%.02f" % self.valor_icmsst,
            'vFCPST': '0.00',
            'vFCPSTRet': '0.00',
            'vProd': "%.02f" % self.valor_bruto,
            'vFrete': "%.02f" % self.valor_frete,
            'vSeg': "%.02f" % self.valor_seguro,
            'vDesc': "%.02f" % self.valor_desconto,
            'vII': "%.02f" % self.valor_ii,
            'vIPI': "%.02f" % self.valor_ipi,
            'vIPIDevol': '0.00',
            'vPIS': "%.02f" % self.valor_pis,
            'vCOFINS': "%.02f" % self.valor_cofins,
            'vOutro': "%.02f" % self.valor_despesas,
            'vNF': "%.02f" % self.valor_final,
            'vFCPUFDest': "%.02f" % self.valor_icms_fcp_uf_dest,
            'vICMSUFDest': "%.02f" % self.valor_icms_uf_dest,
            'vICMSUFRemet': "%.02f" % self.valor_icms_uf_remet,
            'vTotTrib': "%.02f" % self.valor_estimado_tributos,
        }
        if self.valor_servicos > 0.0:
            issqn_total = {
                'vServ': "%.02f" % self.valor_servicos
                if self.valor_servicos else "",
                'vBC': "%.02f" % self.valor_bc_issqn
                if self.valor_bc_issqn else "",
                'vISS': "%.02f" % self.valor_issqn if self.valor_issqn else "",
                'vPIS': "%.02f" % self.valor_pis_servicos
                if self.valor_pis_servicos else "",
                'vCOFINS': "%.02f" % self.valor_cofins_servicos
                if self.valor_cofins_servicos else "",
                'dCompet': dt_emissao[:10],
                'vDeducao': "",
                'vOutro': "",
                'vISSRet': "%.02f" % self.valor_retencao_issqn
                if self.valor_retencao_issqn else '',
            }
            tributos_retidos = {
                'vRetPIS': "%.02f" % self.valor_retencao_pis
                if self.valor_retencao_pis else '',
                'vRetCOFINS': "%.02f" % self.valor_retencao_cofins
                if self.valor_retencao_cofins else '',
                'vRetCSLL': "%.02f" % self.valor_retencao_csll
                if self.valor_retencao_csll else '',
                'vBCIRRF': "%.02f" % self.valor_bc_irrf
                if self.valor_retencao_irrf else '',
                'vIRRF': "%.02f" % self.valor_retencao_irrf
                if self.valor_retencao_irrf else '',
                'vBCRetPrev': "%.02f" % self.valor_bc_inss
                if self.valor_retencao_inss else '',
                'vRetPrev': "%.02f" % self.valor_retencao_inss
                if self.valor_retencao_inss else '',
            }
        if self.transportadora_id.street:
            end_transp = "%s - %s, %s" % (self.transportadora_id.street,
                                          self.transportadora_id.number or '',
                                          self.
                                          transportadora_id.district or '')
        else:
            end_transp = ''
        transp = {
            'modFrete': self.modalidade_frete,
            'transporta': {
                'xNome': self.transportadora_id.legal_name or
                self.transportadora_id.name or '',
                'IE': re.sub('[^0-9]', '',
                             self.transportadora_id.inscr_est or ''),
                'xEnder': end_transp
                if self.transportadora_id else '',
                'xMun': self.transportadora_id.city_id.name or '',
                'UF': self.transportadora_id.state_id.code or ''
            },
            'veicTransp': {
                'placa': self.placa_veiculo or '',
                'UF': self.uf_veiculo or '',
                'RNTC': self.rntc or '',
            }
        }
        cnpj_cpf = re.sub('[^0-9]', '', self.transportadora_id.cnpj_cpf or '')
        if self.transportadora_id.is_company:
            transp['transporta']['CNPJ'] = cnpj_cpf
        else:
            transp['transporta']['CPF'] = cnpj_cpf

        reboques = []
        for item in self.reboque_ids:
            reboques.append({
                'placa': item.placa_veiculo or '',
                'UF': item.uf_veiculo or '',
                'RNTC': item.rntc or '',
                'vagao': item.vagao or '',
                'balsa': item.balsa or '',
            })
        transp['reboque'] = reboques
        volumes = []
        for item in self.volume_ids:
            volumes.append({
                'qVol': item.quantidade_volumes or '',
                'esp': item.especie or '',
                'marca': item.marca or '',
                'nVol': item.numeracao or '',
                'pesoL': "%.03f" % item.peso_liquido
                if item.peso_liquido else '',
                'pesoB': "%.03f" % item.peso_bruto if item.peso_bruto else '',
            })
        transp['vol'] = volumes

        duplicatas = []
        for dup in self.duplicata_ids:
            vencimento = fields.Datetime.from_string(dup.data_vencimento)
            duplicatas.append({
                'nDup': dup.numero_duplicata,
                'dVenc':  vencimento.strftime('%Y-%m-%d'),
                'vDup': "%.02f" % dup.valor
            })
        cobr = {
            'fat': {
                'nFat': self.numero_fatura or '',
                'vOrig': "%.02f" % (
                    self.fatura_liquido + self.fatura_desconto),
                'vDesc': "%.02f" % self.fatura_desconto,
                'vLiq': "%.02f" % self.fatura_liquido,
            },
            'dup': duplicatas
        }
        pag = {
            'indPag': self.payment_term_id.indPag or '0',
            'tPag': self.payment_mode_id.tipo_pagamento or '90',
            'vPag': '0.00',
        }
        self.informacoes_complementares = self.informacoes_complementares.\
            replace('\n', '<br />')
        self.informacoes_legais = self.informacoes_legais.replace(
            '\n', '<br />')
        infAdic = {
            'infCpl': self.informacoes_complementares or '',
            'infAdFisco': self.informacoes_legais or '',
        }
        compras = {
            'xNEmp': self.nota_empenho or '',
            'xPed': self.pedido_compra or '',
            'xCont': self.contrato_compra or '',
        }

        responsavel_tecnico = self.company_id.responsavel_tecnico_id
        infRespTec = {}

        if responsavel_tecnico:
            if len(responsavel_tecnico.child_ids) == 0:
                raise UserError(
                    "Adicione um contato para o responsável técnico!")

            cnpj = re.sub('[^0-9]', '', responsavel_tecnico.cnpj_cpf)
            fone = re.sub('[^0-9]', '', responsavel_tecnico.phone or '')
            infRespTec = {
                'CNPJ': cnpj or '',
                'xContato': responsavel_tecnico.child_ids[0].name or '',
                'email': responsavel_tecnico.email or '',
                'fone': fone,
                'idCSRT': self.company_id.id_token_csrt or '',
                'hashCSRT': self._get_hash_csrt() or '',
            }

        vals = {
            'Id': '',
            'ide': ide,
            'emit': emit,
            'dest': dest,
            'entrega': entrega,
            'autXML': autorizados,
            'detalhes': eletronic_items,
            'total': total,
            'pag': [pag],
            'transp': transp,
            'infAdic': infAdic,
            'exporta': exporta,
            'compra': compras,
            'infRespTec': infRespTec,
        }
        if self.valor_servicos > 0.0:
            vals.update({
                'ISSQNtot': issqn_total,
                'retTrib': tributos_retidos,
            })
        if len(duplicatas) > 0 and\
                self.fiscal_position_id.finalidade_emissao not in ('2', '4'):
            vals['cobr'] = cobr
            pag['tPag'] = '01' if pag['tPag'] == '90' else pag['tPag']
            pag['vPag'] = "%.02f" % self.valor_final

        if self.model == '65':
            vals['pag'][0]['tPag'] = self.metodo_pagamento
            vals['pag'][0]['vPag'] = "%.02f" % self.valor_pago
            vals['pag'][0]['vTroco'] = "%.02f" % self.troco or '0.00'

            chave_nfe = self.chave_nfe
            ambiente = 1 if self.ambiente == 'producao' else 2
            estado = self.company_id.state_id.ibge_code

            cid_token = int(self.company_id.id_token_csc)
            csc = self.company_id.csc

            c_hash_QR_code = "{0}|2|{1}|{2}{3}".format(
                chave_nfe, ambiente, int(cid_token), csc)
            c_hash_QR_code = hashlib.sha1(c_hash_QR_code.encode()).hexdigest()

            QR_code_url = "p={0}|2|{1}|{2}|{3}".format(
                chave_nfe, ambiente, int(cid_token), c_hash_QR_code)
            qr_code_server = url_qrcode(estado, str(ambiente))
            vals['qrCode'] = qr_code_server + QR_code_url
            vals['urlChave'] = url_qrcode_exibicao(estado, str(ambiente))
        return vals

    @api.multi
    def _prepare_lote(self, lote, nfe_values):
        return {
            'idLote': lote,
            'indSinc': 1 if self.company_id.nfe_sinc else 0,
            'estado': self.company_id.partner_id.state_id.ibge_code,
            'ambiente': 1 if self.ambiente == 'producao' else 2,
            'NFes': [{
                'infNFe': nfe_values
            }],
            'modelo': self.model,
        }

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        if self.model not in ('55'):
            return atts

        attachment_obj = self.env['ir.attachment']
        nfe_xml = base64.decodestring(self.nfe_processada)
        logo = base64.decodestring(self.invoice_id.company_id.logo)

        tmpLogo = io.BytesIO()
        tmpLogo.write(logo)
        tmpLogo.seek(0)

        xml_element = etree.fromstring(nfe_xml)
        oDanfe = danfe(list_xml=[xml_element], logo=tmpLogo)

        tmpDanfe = io.BytesIO()
        oDanfe.writeto_pdf(tmpDanfe)

        if danfe:
            danfe_id = attachment_obj.create(dict(
                name="Danfe-%08d.pdf" % self.numero,
                datas_fname="Danfe-%08d.pdf" % self.numero,
                datas=base64.b64encode(tmpDanfe.getvalue()),
                mimetype='application/pdf',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(danfe_id.id)
        if nfe_xml:
            xml_id = attachment_obj.create(dict(
                name=self.nfe_processada_name,
                datas_fname=self.nfe_processada_name,
                datas=base64.encodestring(nfe_xml),
                mimetype='application/xml',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(xml_id.id)
        return atts

    @api.multi
    def recriar_xml(self):
        self.action_post_validate()

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('55', '65'):
            return
        chave_dict = {
            'cnpj': re.sub('[^0-9]', '', self.company_id.cnpj_cpf),
            'estado': self.company_id.state_id.ibge_code,
            'emissao': self.data_emissao.strftime("%y%m"),
            'modelo': self.model,
            'numero': self.numero,
            'serie': self.serie.code.zfill(3),
            'tipo': int(self.tipo_emissao),
            'codigo': "%08d" % self.numero_controle
        }
        self.chave_nfe = gerar_chave(ChaveNFe(**chave_dict))

        cert = self.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(
            cert_pfx, self.company_id.nfe_a1_password)

        nfe_values = self._prepare_eletronic_invoice_values()

        lote = self._prepare_lote(self.id, nfe_values)

        xml_enviar = xml_autorizar_nfe(certificado, **lote)

        mensagens_erro = valida_nfe(xml_enviar)
        if mensagens_erro:
            raise UserError(mensagens_erro)

        self.sudo().write({
            'xml_to_send': base64.encodestring(xml_enviar.encode('utf-8')),
            'xml_to_send_name': 'nfe-enviar-%s.xml' % self.numero,
        })

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()

        if self.model not in ('55', '65') or self.state in (
           'done', 'denied', 'cancel'):
            return

        _logger.info('Sending NF-e (%s) (%.2f) - %s' % (
            self.numero, self.valor_final, self.partner_id.name))
        self.write({
            'state': 'error',
            'data_emissao': datetime.now()
        })

        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        xml_to_send = base64.decodestring(self.xml_to_send).decode('utf-8')

        resposta_recibo = None
        resposta = autorizar_nfe(
            certificado, xml=xml_to_send,
            estado=self.company_id.state_id.ibge_code,
            ambiente=1 if self.ambiente == 'producao' else 2,
            modelo=self.model)
        retorno = resposta['object'].getchildren()[0]
        if retorno.cStat == 103:
            obj = {
                'estado': self.company_id.partner_id.state_id.ibge_code,
                'ambiente': 1 if self.ambiente == 'producao' else 2,
                'obj': {
                    'ambiente': 1 if self.ambiente == 'producao' else 2,
                    'numero_recibo': retorno.infRec.nRec
                },
                'modelo': self.model,
            }
            self.recibo_nfe = obj['obj']['numero_recibo']
            import time
            while True:
                time.sleep(2)
                resposta_recibo = retorno_autorizar_nfe(certificado, **obj)
                retorno = resposta_recibo['object'].getchildren()[0]
                if retorno.cStat != 105:
                    break

        if retorno.cStat != 104:
            self.write({
                'codigo_retorno': retorno.cStat,
                'mensagem_retorno': retorno.xMotivo,
            })
            self.notify_user()
        else:
            self.write({
                'codigo_retorno': retorno.protNFe.infProt.cStat,
                'mensagem_retorno': retorno.protNFe.infProt.xMotivo,
            })
            if self.codigo_retorno == '100':
                self.write({
                    'state': 'done',
                    'protocolo_nfe': retorno.protNFe.infProt.nProt,
                    'data_autorizacao': retorno.protNFe.infProt.dhRecbto
                })
            else:
                self.notify_user()
            # Duplicidade de NF-e significa que a nota já está emitida
            # TODO Buscar o protocolo de autorização, por hora só finalizar
            if self.codigo_retorno == '204':
                self.write({
                    'state': 'done', 'codigo_retorno': '100',
                    'mensagem_retorno': 'Autorizado o uso da NF-e'
                })

            # Denegada e nota já está denegada
            if self.codigo_retorno in ('302', '205'):
                self.write({'state': 'denied'})

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('nfe-envio', self, resposta['sent_xml'])
        self._create_attachment('nfe-ret', self, resposta['received_xml'])
        recibo_xml = resposta['received_xml']
        if resposta_recibo:
            self._create_attachment('rec', self, resposta_recibo['sent_xml'])
            self._create_attachment('rec-ret', self,
                                    resposta_recibo['received_xml'])
            recibo_xml = resposta_recibo['received_xml']

        if self.codigo_retorno == '100':
            nfe_proc = gerar_nfeproc(resposta['sent_xml'], recibo_xml)
            self.sudo().write({
                'nfe_processada': base64.encodestring(nfe_proc),
                'nfe_processada_name': "NFe%08d.xml" % self.numero,
            })
        _logger.info('NF-e (%s) was finished with status %s' % (
            self.numero, self.codigo_retorno))

    @api.multi
    def generate_nfe_proc(self):
        if self.state in ['cancel', 'done', 'denied']:
            recibo = self.env['ir.attachment'].search([
                ('res_model', '=', 'invoice.eletronic'),
                ('res_id', '=', self.id),
                ('datas_fname', 'like', 'rec-ret')], limit=1)
            if not recibo:
                recibo = self.env['ir.attachment'].search([
                    ('res_model', '=', 'invoice.eletronic'),
                    ('res_id', '=', self.id),
                    ('datas_fname', 'like', 'nfe-ret')], limit=1)
            nfe_envio = self.env['ir.attachment'].search([
                ('res_model', '=', 'invoice.eletronic'),
                ('res_id', '=', self.id),
                ('datas_fname', 'like', 'nfe-envio')], limit=1)
            if nfe_envio.datas and recibo.datas:
                nfe_proc = gerar_nfeproc(
                    base64.decodestring(nfe_envio.datas).decode('utf-8'),
                    base64.decodestring(recibo.datas).decode('utf-8'),
                )
                self.sudo().write({
                    'nfe_processada': base64.encodestring(nfe_proc),
                    'nfe_processada_name': "NFe%08d.xml" % self.numero,
                })
        else:
            raise UserError(_('A NFe não está validada'))

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('55', '65'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        if not justificativa:
            return {
                'name': _('Cancelamento NFe'),
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.cancel.nfe',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_edoc_id': self.id
                }
            }

        _logger.info('Cancelling NF-e (%s)' % self.numero)
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        id_canc = "ID110111%s%02d" % (
            self.chave_nfe, self.sequencial_evento)

        tz = timezone(self.env.user.tz)
        dt_evento = datetime.now(tz).replace(microsecond=0).isoformat()

        cancelamento = {
            'idLote': self.id,
            'estado': self.company_id.state_id.ibge_code,
            'ambiente': 2 if self.ambiente == 'homologacao' else 1,
            'eventos': [{
                'Id': id_canc,
                'cOrgao': self.company_id.state_id.ibge_code,
                'tpAmb': 2 if self.ambiente == 'homologacao' else 1,
                'CNPJ': re.sub('[^0-9]', '', self.company_id.cnpj_cpf),
                'chNFe': self.chave_nfe,
                'dhEvento': dt_evento,
                'nSeqEvento': self.sequencial_evento,
                'nProt': self.protocolo_nfe,
                'xJust': justificativa,
                'tpEvento': '110111',
                'descEvento': 'Cancelamento',
            }],
            'modelo': self.model,
        }

        resp = recepcao_evento_cancelamento(certificado, **cancelamento)
        resposta = resp['object'].getchildren()[0]
        if resposta.cStat == 128 and \
                resposta.retEvento.infEvento.cStat in (135, 136, 155):
            self.write({
                'state': 'cancel',
                'codigo_retorno': resposta.retEvento.infEvento.cStat,
                'mensagem_retorno': resposta.retEvento.infEvento.xMotivo,
                'sequencial_evento': self.sequencial_evento + 1,
            })
        else:
            code, motive = None, None
            if resposta.cStat == 128:
                code = resposta.retEvento.infEvento.cStat
                motive = resposta.retEvento.infEvento.xMotivo
            else:
                code = resposta.cStat
                motive = resposta.xMotivo
            if code == 573:  # Duplicidade, já cancelado
                return self.action_get_status()

            return self._create_response_cancel(
                code, motive, resp, justificativa)

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, resp['sent_xml'])
        self._create_attachment('canc-ret', self, resp['received_xml'])
        nfe_processada = base64.decodestring(self.nfe_processada)

        nfe_proc_cancel = gerar_nfeproc_cancel(
            nfe_processada, resp['received_xml'].encode())
        if nfe_proc_cancel:
            self.nfe_processada = base64.encodestring(nfe_proc_cancel)
        _logger.info('Cancelling NF-e (%s) was finished with status %s' % (
            self.numero, self.codigo_retorno))

    def action_get_status(self):
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)
        consulta = {
            'estado': self.company_id.state_id.ibge_code,
            'ambiente': 2 if self.ambiente == 'homologacao' else 1,
            'modelo': self.model,
            'obj': {
                'chave_nfe': self.chave_nfe,
                'ambiente': 2 if self.ambiente == 'homologacao' else 1,
            }
        }
        resp = consultar_protocolo_nfe(certificado, **consulta)
        retorno_consulta = resp['object'].getchildren()[0]
        if retorno_consulta.cStat == 101:
            self.state = 'cancel'
            self.codigo_retorno = retorno_consulta.cStat
            self.mensagem_retorno = retorno_consulta.xMotivo
            resp['received_xml'] = etree.tostring(
                retorno_consulta, encoding=str)

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })
            self._create_attachment('canc', self, resp['sent_xml'])
            self._create_attachment('canc-ret', self, resp['received_xml'])
            nfe_processada = base64.decodestring(self.nfe_processada)

            nfe_proc_cancel = gerar_nfeproc_cancel(
                nfe_processada, resp['received_xml'].encode())
            if nfe_proc_cancel:
                self.sudo().write({
                    'nfe_processada': base64.encodestring(nfe_proc_cancel),
                })
        elif self.codigo_retorno == '100':
            self.action_post_validate()
            nfe_processada = base64.decodestring(self.xml_to_send).decode('utf-8')
            nfe_proc = gerar_nfeproc(nfe_processada, resp['received_xml'])
            self.nfe_processada = base64.encodestring(nfe_proc)
            self.nfe_processada_name = "NFe%08d.xml" % self.numero
        else:
            message = "%s - %s" % (retorno_consulta.cStat,
                                   retorno_consulta.xMotivo)
            raise UserError(message)

    def _create_response_cancel(self, code, motive, response, justificativa):
        message = "%s - %s" % (code, motive)
        wiz = self.env['wizard.cancel.nfe'].create({
            'edoc_id': self.id,
            'justificativa': justificativa,
            'state': 'error',
            'message': message,
            'sent_xml': base64.b64encode(
                response['sent_xml'].encode('utf-8')),
            'sent_xml_name': 'cancelamento-envio.xml',
            'received_xml': base64.b64encode(
                response['received_xml'].encode('utf-8')),
            'received_xml_name': 'cancelamento-retorno.xml',
        })
        return {
            'name': _('Cancelamento NFe'),
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.cancel.nfe',
            'res_id': wiz.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_hash_csrt(self):
        chave_nfe = self.chave_nfe
        csrt = self.company_id.csrt

        if not csrt:
            return

        hash_csrt = "{0}{1}".format(csrt, chave_nfe)
        hash_csrt = base64.b64encode(
            hashlib.sha1(hash_csrt.encode()).digest())

        return hash_csrt.decode("utf-8")
