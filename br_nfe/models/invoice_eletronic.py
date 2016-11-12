# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import logging
from datetime import datetime
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import autorizar_nfe
    from pytrustnfe.nfe import retorno_autorizar_nfe
    from pytrustnfe.nfe import recepcao_evento_cancelamento
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.utils import ChaveNFe, gerar_chave
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    @api.depends('chave_nfe')
    def _format_danfe_key(self):
        for item in self:
            item.chave_nfe_danfe = re.sub("(.{4})", "\\1.",
                                          item.chave_nfe, 10, re.DOTALL)

    ambiente_nfe = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente")
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Consumidor final', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('9', u'Operação não presencial, outros'),
    ], u'Tipo de operação', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.', default='0')
    ind_dest = fields.Selection([
        ('1', '1 - Operação Interna'),
        ('2', '2 - Operação Interestadual'),
        ('3', '3 - Operação com exterior')],
        string="Indicador Destinatário", readonly=True,
        states={'draft': [('readonly', False)]})
    ind_ie_dest = fields.Selection([
        ('1', '1 - Contribuinte ICMS'),
        ('2', '2 - Contribuinte Isento de Cadastro'),
        ('9', '9 - Não Contribuinte')],
        string="Indicador IE Dest.", help="Indicador da IE do desinatário")

    # Transporte
    modalidade_frete = fields.Selection([('0', '0 - Emitente'),
                                         ('1', '1 - Destinatário'),
                                         ('2', '2 - Terceiros'),
                                         ('9', '9 - Sem Frete')],
                                        u'Modalidade do frete', default="9")
    transportadora_id = fields.Many2one('res.partner', string="Transportadora")
    placa_veiculo = fields.Char('Placa do Veiculo', size=7)
    uf_veiculo = fields.Char(string='UF da Placa', size=2)
    rntc = fields.Char(string="RNTC", size=20,
                       help="Registro Nacional de Transportador de Carga")

    reboque_ids = fields.One2many('nfe.reboque', 'invoice_eletronic_id',
                                  string="Reboques")
    volume_ids = fields.One2many('nfe.volume', 'invoice_eletronic_id',
                                 string="Volumes")

    # Exportação
    uf_saida_pais_id = fields.Many2one(
        'res.country.state', domain=[('country_id.code', '=', 'BR')],
        string="UF Saída do País")
    local_embarque = fields.Char('Local de Embarque', size=60)
    local_despacho = fields.Char('Local despacho', size=60)

    # Cobrança
    numero_fatura = fields.Char(string="Fatura")
    fatura_bruto = fields.Monetary(string="Valor Original")
    fatura_desconto = fields.Monetary(string="Desconto")
    fatura_liquido = fields.Monetary(string="Valor Líquido")

    duplicata_ids = fields.One2many('nfe.duplicata', 'invoice_eletronic_id',
                                    string="Duplicatas")

    # Compras
    nota_empenho = fields.Char(string="Nota de Empenho", size=22)
    pedido_compra = fields.Char(string="Pedido Compra", size=60)
    contrato_compra = fields.Char(string="Contrato Compra", size=60)

    sequencial_evento = fields.Integer(string="Sequêncial Evento", default=1)
    recibo_nfe = fields.Char(string="Recibo NFe", size=50)
    chave_nfe = fields.Char(string="Chave NFe", size=50)
    chave_nfe_danfe = fields.Char(string="Chave Formatado",
                                  compute="_format_danfe_key")
    protocolo_nfe = fields.Char(string="Protocolo", size=50,
                                help="Protocolo de autorização da NFe")

    valor_icms_uf_remet = fields.Float(
        string="ICMS Remetente",
        help='Valor total do ICMS Interestadual para a UF do Remetente')
    valor_icms_uf_dest = fields.Float(
        string="ICMS Destino",
        help='Valor total do ICMS Interestadual para a UF de destino')
    valor_icms_fcp_uf_dest = fields.Float(
        string="Total ICMS FCP",
        help='Total total do ICMS relativo Fundo de Combate à Pobreza (FCP) \
        da UF de destino')

    def barcode_url(self):
        url = '<img style="width:470px;height:50px;margin-top:5px;"\
src="/report/barcode/Code128/' + self.chave_nfe + '" />'
        return url

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

        xprod = item.product_id.name if self.company_id.\
            tipo_ambiente != '2' else\
            'NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR \
FISCAL'
        prod = {
            'cProd': item.product_id.default_code,
            'cEAN': item.product_id.barcode or '',
            'xProd': xprod,
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
        return {'prod': prod, 'imposto': imposto}

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
            'tpEmis': 1,  # Tipo de Emissão da NF-e - 1 - Emissão Normal
            'tpAmb': 2 if self.ambiente == 'homologacao' else 1,
            'finNFe': self.finalidade_emissao,
            'indFinal': self.ind_final or '1',
            'indPres': self.ind_pres or '1',
            'procEmi': 0
        }
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
        dest = None
        exporta = None
        if self.partner_id:
            dest = {
                'tipo': self.partner_id.company_type,
                'cnpj_cpf': re.sub('[^0-9]', '',
                                   self.partner_id.cnpj_cpf or ''),
                'xNome': self.partner_id.legal_name or self.partner_id.name,
                'enderDest': {
                    'xLgr': self.partner_id.street,
                    'nro': self.partner_id.number,
                    'xBairro': self.partner_id.district,
                    'cMun': '%s%s' % (self.partner_id.state_id.ibge_code,
                                      self.partner_id.city_id.ibge_code),
                    'xMun': self.partner_id.city_id.name,
                    'UF': self.partner_id.state_id.code,
                    'CEP': re.sub('[^0-9]', '', self.partner_id.zip or ''),
                    'cPais': (self.partner_id.country_id.bc_code or '')[-4:],
                    'xPais': self.partner_id.country_id.name,
                    'fone': re.sub('[^0-9]', '', self.partner_id.phone or '')
                },
                'indIEDest': self.ind_ie_dest,
                'IE':  re.sub('[^0-9]', '', self.partner_id.inscr_est or ''),
            }
            if self.ambiente == 'homologacao':
                dest['xNome'] = \
                    'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO -\
 SEM VALOR FISCAL'
            if self.partner_id.country_id.id != self.company_id.country_id.id:
                dest['idEstrangeiro'] = re.sub(
                    '[^0-9]', '', self.partner_id.cnpj_cpf or '')
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
                'CNPJ': re.sub(
                    '[^0-9]', '', self.transportadora_id.cnpj_cpf or ''),
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
                'pesoL': item.peso_liquido or '',
                'pesoB': item.peso_bruto or '',
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
            'cobr': cobr,
            'infAdic': infAdic,
            'exporta': exporta,
            'compra': compras,
        }
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

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        for item in self:
            chave_dict = {
                'cnpj': re.sub('[^0-9]', '', item.company_id.cnpj_cpf),
                'estado': item.company_id.state_id.ibge_code,
                'emissao': item.data_emissao[2:4] + item.data_emissao[5:7],
                'modelo': item.model,
                'numero': item.numero,
                'serie': item.serie.code.zfill(3),
                'tipo': 0 if item.tipo_operacao == 'entrada' else 1,
                'codigo': item.numero_controle
            }
            item.chave_nfe = gerar_chave(ChaveNFe(**chave_dict))

    @api.multi
    def action_send_eletronic_invoice(self):
        self.ambiente = 'homologacao'  # Evita esquecimentos
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
        retorno = resposta['object'].Body.nfeAutorizacaoLoteResult.retEnviNFe
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

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('nfe-envio', self, resposta['sent_xml'])
        self._create_attachment('nfe-ret', self, resposta['received_xml'])
        if resposta_recibo:
            self._create_attachment('rec', self, resposta_recibo['sent_xml'])
            self._create_attachment('rec-ret', self,
                                    resposta_recibo['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
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

        super(InvoiceEletronic, self).action_cancel_document()
        if self.model not in ('55', '65'):
            return

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
            self.codigo_retorno = resposta.retEvento.infEvento.cStat
            self.mensagem_retorno = resposta.retEvento.infEvento.xMotivo
            self.sequencial_evento += 1
        else:
            self.state = 'done'
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
