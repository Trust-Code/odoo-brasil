# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import logging
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import autorizar_nfe
    from pytrustnfe.nfe import retorno_autorizar_nfe
    from pytrustnfe.nfe import recepcao_evento_cancelamento
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.utils import ChaveNFe, gerar_chave, gerar_nfeproc
except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)

STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    @api.depends('chave_nfe')
    def _format_danfe_key(self):
        for item in self:
            item.chave_nfe_danfe = re.sub("(.{4})", "\\1.",
                                          item.chave_nfe, 10, re.DOTALL)

    @api.multi
    def generate_correction_letter(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "wizard.carta.correcao.eletronica",
            "views": [[False, "form"]],
            "name": "Carta de Correção",
            "target": "new",
            "context": {'default_eletronic_doc_id': self.id},
        }

    state = fields.Selection(selection_add=[('denied', 'Denegado')])
    ambiente_nfe = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente")
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
        string="Indicador IE Dest.", help="Indicador da IE do desinatário",
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
        string="Tipo de Emissão", readonly=True, states=STATE, default='1')

    # Transporte
    modalidade_frete = fields.Selection(
        [('0', u'0 - Emitente'),
         ('1', u'1 - Destinatário'),
         ('2', u'2 - Terceiros'),
         ('9', u'9 - Sem Frete')],
        string=u'Modalidade do frete', default="9",
        readonly=True, states=STATE)
    transportadora_id = fields.Many2one(
        'res.partner', string="Transportadora", readonly=True, states=STATE)
    placa_veiculo = fields.Char(
        string=u'Placa do Veículo', size=7, readonly=True, states=STATE)
    uf_veiculo = fields.Char(
        string='UF da Placa', size=2, readonly=True, states=STATE)
    rntc = fields.Char(
        string="RNTC", size=20, readonly=True, states=STATE,
        help="Registro Nacional de Transportador de Carga")

    reboque_ids = fields.One2many(
        'nfe.reboque', 'invoice_eletronic_id',
        string="Reboques", readonly=True, states=STATE)
    volume_ids = fields.One2many(
        'nfe.volume', 'invoice_eletronic_id',
        string="Volumes", readonly=True, states=STATE)

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
        string="Fatura", readonly=True, states=STATE)
    fatura_bruto = fields.Monetary(
        string="Valor Original", readonly=True, states=STATE)
    fatura_desconto = fields.Monetary(
        string="Desconto", readonly=True, states=STATE)
    fatura_liquido = fields.Monetary(
        string=u"Valor Líquido", readonly=True, states=STATE)

    duplicata_ids = fields.One2many(
        'nfe.duplicata', 'invoice_eletronic_id',
        string="Duplicatas", readonly=True, states=STATE)

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
        string="Recibo NFe", size=50, readonly=True, states=STATE)
    chave_nfe = fields.Char(
        string="Chave NFe", size=50, readonly=True, states=STATE)
    chave_nfe_danfe = fields.Char(
        string="Chave Formatado", compute="_format_danfe_key")
    protocolo_nfe = fields.Char(
        string="Protocolo", size=50, readonly=True, states=STATE,
        help=u"Protocolo de autorização da NFe")
    nfe_processada = fields.Binary(string="Xml da NFe", readonly=True)
    nfe_processada_name = fields.Char(
        string="Xml da NFe", size=100, readonly=True)

    valor_icms_uf_remet = fields.Monetary(
        string="ICMS Remetente", readonly=True, states=STATE,
        help='Valor total do ICMS Interestadual para a UF do Remetente')
    valor_icms_uf_dest = fields.Monetary(
        string="ICMS Destino", readonly=True, states=STATE,
        help='Valor total do ICMS Interestadual para a UF de destino')
    valor_icms_fcp_uf_dest = fields.Monetary(
        string="Total ICMS FCP", readonly=True, states=STATE,
        help=u'Total total do ICMS relativo Fundo de Combate à Pobreza (FCP) \
        da UF de destino')

    # Documentos Relacionados
    fiscal_document_related_ids = fields.One2many(
        'br_account.document.related', 'invoice_eletronic_id',
        'Documentos Fiscais Relacionados', readonly=True, states=STATE)

    # CARTA DE CORRECAO
    cartas_correcao_ids = fields.One2many(
        'carta.correcao.eletronica.evento', 'eletronic_doc_id',
        string="Cartas de Correção", readonly=True, states=STATE)

    def barcode_url(self):
        url = '<img style="width:380px;height:50px;margin:2px 1px;"\
src="/report/barcode/Code128/' + self.chave_nfe + '" />'
        return url

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
                    u'Documento Eletrônico Denegado - Proibido excluir')
        super(InvoiceEletronic, self).unlink()

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '55':
            if not self.company_id.partner_id.inscr_est:
                errors.append(u'Emitente / Inscrição Estadual')
            if not self.fiscal_position_id:
                errors.append(u'Configure a posição fiscal')

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

        return errors

    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_item(
            item, invoice)
        if self.model not in ('55', '65'):
            return res

        prod = {
            'cProd': item.product_id.default_code,
            'cEAN': item.product_id.barcode or '',
            'xProd': item.product_id.name,
            'NCM': re.sub('[^0-9]', '', item.ncm or '')[:8],
            'EXTIPI': re.sub('[^0-9]', '', item.ncm or '')[8:],
            'CFOP': item.cfop,
            'uCom': '{:.6}'.format(item.uom_id.name or ''),
            'qCom': item.quantidade,
            'vUnCom': "%.02f" % item.preco_unitario,
            'vProd':  "%.02f" % (item.preco_unitario * item.quantidade),
            'cEANTrib': item.product_id.barcode or '',
            'uTrib': '{:.6}'.format(item.uom_id.name or ''),
            'qTrib': item.quantidade,
            'vUnTrib': "%.02f" % item.preco_unitario,
            'vFrete': "%.02f" % item.frete if item.frete else '',
            'vSeg': "%.02f" % item.seguro if item.seguro else '',
            'vDesc': "%.02f" % item.desconto if item.desconto else '',
            'vOutro': "%.02f" % item.outras_despesas
            if item.outras_despesas else '',
            'indTot': item.indicador_total,
            'cfop': item.cfop,
            'CEST': re.sub('[^0-9]', '', item.cest or ''),
        }
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

            dt_registration = datetime.strptime(
                di.date_registration, DATE_FORMAT)
            dt_release = datetime.strptime(di.date_release, DATE_FORMAT)
            di_vals.append({
                'nDI': di.name,
                'dDI': dt_registration.strftime('%Y-%m-%d'),
                'xLocDesemb': di.location,
                'UFDesemb': di.state_id.code,
                'dDesemb': dt_release.strftime('%Y-%m-%d'),
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
                'pCredSN': "%.02f" % item.icms_valor_credito,
                'vCredICMSSN': "%.02f" % item.icms_aliquota_credito
            },
            'IPI': {
                'clEnq': item.classe_enquadramento_ipi or '',
                'cEnq': item.codigo_enquadramento_ipi,
                'CST': item.ipi_cst,
                'vBC': "%.02f" % item.ipi_base_calculo,
                'pIPI': "%.02f" % item.ipi_aliquota,
                'vIPI': "%.02f" % item.ipi_valor
            },
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
        }
        if item.tem_difal:
            imposto['ICMSUFDest'] = {
                'vBCUFDest': "%.02f" % item.icms_bc_uf_dest,
                'pFCPUFDest': "%.02f" % item.icms_aliquota_fcp_uf_dest,
                'pICMSUFDest': "%.02f" % item.icms_aliquota_uf_dest,
                'pICMSInter': "%.02f" % item.icms_aliquota_interestadual,
                'pICMSInterPart': "%.02f" % item.icms_aliquota_inter_part,
                'vFCPUFDest': "%.02f" % item.icms_fcp_uf_dest,
                'vICMSUFDest': "%.02f" % item.icms_uf_dest,
                'vICMSUFRemet': "%.02f" % item.icms_uf_remet, }
        return {'prod': prod, 'imposto': imposto,
                'infAdProd': item.informacao_adicional}

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model not in ('55', '65'):
            return res

        dt_emissao = datetime.strptime(self.data_emissao, DTFT)

        ide = {
            'cUF': self.company_id.state_id.ibge_code,
            'cNF': "%08d" % self.numero_controle,
            'natOp': self.fiscal_position_id.name,
            'indPag': self.payment_term_id.indPag or '0',
            'mod': self.model,
            'serie': self.serie.code,
            'nNF': self.numero,
            'dhEmi': dt_emissao.strftime('%Y-%m-%dT%H:%M:%S-00:00'),
            'dhSaiEnt': dt_emissao.strftime('%Y-%m-%dT%H:%M:%S-00:00'),
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
            'procEmi': 0
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
            'IE':  re.sub('[^0-9]', '', self.company_id.inscr_est),
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
            }
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
                exporta = {
                    'UFSaidaPais': self.uf_saida_pais_id.code or '',
                    'xLocExporta': self.local_embarque or '',
                    'xLocDespacho': self.local_despacho or '',
                }

        eletronic_items = []
        for item in self.eletronic_item_ids:
            eletronic_items.append(
                self._prepare_eletronic_invoice_item(item, self))
        total = {
            # ICMS
            'vBC': "%.02f" % self.valor_bc_icms,
            'vICMS': "%.02f" % self.valor_icms,
            'vICMSDeson': '0.00',
            'vBCST': "%.02f" % self.valor_bc_icmsst,
            'vST': "%.02f" % self.valor_icmsst,
            'vProd': "%.02f" % self.valor_bruto,
            'vFrete': "%.02f" % self.valor_frete,
            'vSeg': "%.02f" % self.valor_seguro,
            'vDesc': "%.02f" % self.valor_desconto,
            'vII': "%.02f" % self.valor_ii,
            'vIPI': "%.02f" % self.valor_ipi,
            'vPIS': "%.02f" % self.valor_pis,
            'vCOFINS': "%.02f" % self.valor_cofins,
            'vOutro': "%.02f" % self.valor_despesas,
            'vNF': "%.02f" % self.valor_final,
            'vTotTrib': "%.02f" % self.valor_estimado_tributos,
            # ISSQn
            'vServ': '0.00',
            # Retenções

        }
        transp = {
            'modFrete': self.modalidade_frete,
            'transporta': {
                'xNome': self.transportadora_id.legal_name or
                self.transportadora_id.name or '',
                'IE': re.sub('[^0-9]', '',
                             self.transportadora_id.inscr_est or ''),
                'xEnder': "%s - %s, %s" % (self.transportadora_id.street,
                                           self.transportadora_id.number,
                                           self.transportadora_id.district)
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
                'vOrig': "%.02f" % self.fatura_bruto
                if self.fatura_bruto else '',
                'vDesc': "%.02f" % self.fatura_desconto
                if self.fatura_desconto else '',
                'vLiq': "%.02f" % self.fatura_liquido
                if self.fatura_liquido else '',
            },
            'dup': duplicatas
        }
        infAdic = {
            'infCpl': self.informacoes_complementares or '',
            'infAdFisco': self.informacoes_legais or '',
        }
        compras = {
            'xNEmp': self.nota_empenho or '',
            'xPed': self.pedido_compra or '',
            'xCont': self.contrato_compra or '',
        }
        vals = {
            'Id': '',
            'ide': ide,
            'emit': emit,
            'dest': dest,
            'detalhes': eletronic_items,
            'total': total,
            'transp': transp,
            'infAdic': infAdic,
            'exporta': exporta,
            'compra': compras,
        }
        if len(duplicatas) > 0:
            vals['cobr'] = cobr
        return vals

    @api.multi
    def _prepare_lote(self, lote, nfe_values):
        return {
            'idLote': lote,
            'indSinc': 1,
            'estado': self.company_id.partner_id.state_id.ibge_code,
            'ambiente': 1 if self.ambiente == 'producao' else 2,
            'NFes': [{
                'infNFe': nfe_values
            }]
        }

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()

        attachment_obj = self.env['ir.attachment']
        danfe_report = self.env['ir.actions.report.xml'].search(
            [('name', '=', 'Impressão de Danfe')])

        nfe_xml = self.nfe_processada
        report_service = danfe_report.report_name

        danfe = self.env['report'].get_pdf([self.id], report_service)

        if danfe:
            danfe_id = attachment_obj.create(dict(
                name='Danfe.pdf',
                datas_fname='Danfe.pdf',
                datas=base64.b64encode(danfe),
                mimetype='application/pdf',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(danfe_id.id)
        if nfe_xml:
            xml_id = attachment_obj.create(dict(
                name='NFe.xml',
                datas_fname='NFe.xml',
                datas=nfe_xml,
                mimetype='application/xml',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(xml_id.id)
        return atts

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('55', '65'):
            return
        for item in self:
            chave_dict = {
                'cnpj': re.sub('[^0-9]', '', item.company_id.cnpj_cpf),
                'estado': item.company_id.state_id.ibge_code,
                'emissao': item.data_emissao[2:4] + item.data_emissao[5:7],
                'modelo': item.model,
                'numero': item.numero,
                'serie': item.serie.code.zfill(3),
                'tipo': int(item.tipo_emissao),
                'codigo': "%08d" % item.numero_controle
            }
            item.chave_nfe = gerar_chave(ChaveNFe(**chave_dict))

    @api.multi
    def action_send_eletronic_invoice(self):
        self.state = 'error'
        self.data_emissao = datetime.now()
        super(InvoiceEletronic, self).action_send_eletronic_invoice()

        if self.model not in ('55', '65'):
            return

        nfe_values = self._prepare_eletronic_invoice_values()
        lote = self._prepare_lote(self.id, nfe_values)
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        resposta_recibo = None
        resposta = autorizar_nfe(certificado, **lote)
        retorno = resposta['object'].Body.nfeAutorizacaoLoteResult
        retorno = retorno.getchildren()[0]
        if retorno.cStat == 103:
            obj = {
                'estado': self.company_id.partner_id.state_id.ibge_code,
                'ambiente': 1 if self.ambiente == 'producao' else 2,
                'obj': {
                    'ambiente': 1 if self.ambiente == 'producao' else 2,
                    'numero_recibo': retorno.infRec.nRec
                }
            }
            self.recibo_nfe = obj['obj']['numero_recibo']
            import time
            while True:
                time.sleep(2)
                resposta_recibo = retorno_autorizar_nfe(certificado, **obj)
                retorno = resposta_recibo['object'].Body.\
                    nfeRetAutorizacaoLoteResult.retConsReciNFe
                if retorno.cStat != 105:
                    break

        if retorno.cStat != 104:
            self.codigo_retorno = retorno.cStat
            self.mensagem_retorno = retorno.xMotivo
        else:
            self.codigo_retorno = retorno.protNFe.infProt.cStat
            self.mensagem_retorno = retorno.protNFe.infProt.xMotivo
            if self.codigo_retorno == '100':
                self.write({
                    'state': 'done', 'nfe_exception': False,
                    'protocolo_nfe': retorno.protNFe.infProt.nProt,
                    'data_autorizacao': retorno.protNFe.infProt.dhRecbto})
            # Duplicidade de NF-e significa que a nota já está emitida
            # TODO Buscar o protocolo de autorização, por hora só finalizar
            if self.codigo_retorno == '204':
                self.write({'state': 'done', 'codigo_retorno': '100',
                            'nfe_exception': False,
                            'mensagem_retorno': 'Autorizado o uso da NF-e'})

            # Denegada e nota já está denegada
            if self.codigo_retorno in ('302', '205'):
                self.write({'state': 'denied',
                            'nfe_exception': True})

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
            self.nfe_processada = base64.encodestring(nfe_proc)
            self.nfe_processada_name = "NFe%08d.xml" % self.numero

    @api.multi
    def generate_nfe_proc(self):
        if self.state == 'done':
            recibo = self.env['ir.attachment'].search([
                ('res_model', '=', 'invoice.eletronic'),
                ('res_id', '=', self.id),
                ('datas_fname', 'like', 'rec-ret')])
            if not recibo:
                recibo = self.env['ir.attachment'].search([
                    ('res_model', '=', 'invoice.eletronic'),
                    ('res_id', '=', self.id),
                    ('datas_fname', 'like', 'nfe-ret')])
            nfe_envio = self.env['ir.attachment'].search([
                ('res_model', '=', 'invoice.eletronic'),
                ('res_id', '=', self.id),
                ('datas_fname', 'like', 'nfe-envio')])
            nfe_proc = gerar_nfeproc(
                base64.decodestring(nfe_envio.datas),
                base64.decodestring(recibo.datas)
            )
            self.nfe_processada = base64.encodestring(nfe_proc)
            self.nfe_processada_name = "NFe%08d.xml" % self.numero
        else:
            raise UserError('A NFe não está validada')

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('55', '65'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        if not justificativa:
            return {
                'name': 'Cancelamento NFe',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.cancel.nfe',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_edoc_id': self.id
                }
            }

        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        id_canc = "ID110111%s%02d" % (self.chave_nfe, self.sequencial_evento)
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
                'dhEvento': datetime.utcnow().strftime(
                    '%Y-%m-%dT%H:%M:%S-00:00'),
                'nSeqEvento': self.sequencial_evento,
                'nProt': self.protocolo_nfe,
                'xJust': justificativa
                }]
            }
        resp = recepcao_evento_cancelamento(certificado, **cancelamento)
        resposta = resp['object'].Body.nfeRecepcaoEventoResult.retEnvEvento
        if resposta.cStat == 128 and \
           resposta.retEvento.infEvento.cStat in (135, 136, 155):
            self.state = 'cancel'
            self.codigo_retorno = resposta.retEvento.infEvento.cStat
            self.mensagem_retorno = resposta.retEvento.infEvento.xMotivo
            self.sequencial_evento += 1
        else:
            if resposta.cStat == 128:
                self.codigo_retorno = resposta.retEvento.infEvento.cStat
                self.mensagem_retorno = resposta.retEvento.infEvento.xMotivo
            else:
                self.codigo_retorno = resposta.cStat
                self.mensagem_retorno = resposta.xMotivo

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, resp['sent_xml'])
        self._create_attachment('canc-ret', self, resp['received_xml'])
