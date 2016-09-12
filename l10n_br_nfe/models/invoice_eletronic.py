# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
from uuid import uuid4
from datetime import datetime
from openerp import api, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from pytrustnfe.nfe import autorizar_nfe
from pytrustnfe.utils import gerar_chave
from pytrustnfe.certificado import Certificado


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()

        for inv_line in self.eletronic_item_ids:
            prod = u"Produto: %s - %s" % (inv_line.product_id.default_code,
                                          inv_line.product_id.name)

            if not inv_line.cfop:
                errors.append(u'%s - CFOP' % prod)
        return errors

    @api.one
    def _id_dest(self):
        id_dest = '1'
        if self.company_id.state_id != self.partner_id.state_id:
            id_dest = '2'
        if self.company_id.country_id != self.partner_id.country_id:
            id_dest = '3'
        return id_dest

    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        prod = {
            'cProd': item.product_id.default_code,
            'cEAN': item.product_id.barcode or '',
            'xProd': item.product_id.name,
            'NCM': '39259090',
            'CFOP': item.cfop,
            'uCom': item.uom_id.name,
            'qCom': item.quantity,
            'vUnCom': item.unit_price,
            'vProd':  "%.02f" % item.total,
            'cEANTrib': item.product_id.barcode or '',
            'uTrib': item.uom_id.name,
            'qTrib': item.quantity,
            'vUnTrib': item.unit_price,
            'indTot': 0,
            'cfop': item.cfop
        }
        imposto = {
            'vTotTrib': 00,
            'ICMS': {
                'orig':  item.origem,
                'CST': item.icms_cst,
                'modBC': item.icms_modalidade_BC,
                'vBC': "%.02f" % self.valor_BC,
                'pICMS': "%.02f" % item.icms_aliquota,
                'vICMS': "%.02f" % self.valor_icms,
                'pCredSN': "%.02f" % item.icms_value_credit,
                'vCredICMSSN': "%.02f" % item.icms_value_percentual
            },
            'IPI': {
                'cEnq': 999,
                'IPITrib': {
                    'CST': '50',
                    'vBC': '100.00',
                    'pIPI': "%.02f" % item.tax_ipi_id.aliquota,
                    'vIPI': "%.02f" % self.valor_ipi
                }
            },
            'PIS': {
                'PISAliq': {
                    'CST': '01',
                    'vBC': '100.00',
                    'pPIS': '0.0000',
                    'vPIS': '0.00'
                }
            },
            'COFINS': {
                'COFINSAliq': {
                    'CST': '01',
                    'vBC': '100.00',
                    'pCOFINS': '0.0000',
                    'vCOFINS': '0.00'
                }
            }
        }
        return {'prod': prod, 'imposto': imposto}

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        ide = {
            'cUF': self.company_id.state_id.ibge_code,
            'cNF': "%08d" % self.numero_controle,
            'natOp': self.fiscal_position_id.name,
            'indPag': 1,
            'mod': self.model,
            'serie': self.serie.code,
            'nNF': self.numero,
            'dhEmi': datetime.strptime(
                self.data_emissao, DTFT).strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            'dhSaiEnt': datetime.strptime(
                self.data_emissao, DTFT).strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            'tpNF': self.finalidade_emissao,
            'idDest': self._id_dest()[0],
            'cMunFG': "%s%s" % (self.company_id.state_id.ibge_code,
                                self.company_id.city_id.ibge_code),
            'tpImp': 1,
            'tpEmis': 1,
            'cDV': 3,
            'tpAmb': 2,
            'finNFe': self.finalidade_emissao,
            'indFinal': self.consumidor_final,
            'indPres': 0,
            'procEmi': 0
        }
        emit = {
            'tipo': self.company_id.partner_id.company_type,
            'cnpj_cpf': re.sub('[^0-9]', '', self.company_id.cnpj_cpf),
            'xNome': self.company_id.name if
            self.company_id.tipo_ambiente == 1 else
            'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL',
            'xFant': self.company_id.legal_name if
            self.company_id.tipo_ambiente == 1 else
            'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL',
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
            'CRT': '3'
        }
        dest = {
            'tipo': self.partner_id.company_type,
            'cnpj_cpf': re.sub('[^0-9]', '', self.partner_id.cnpj_cpf),
            'xNome': self.partner_id.legal_name,
            'xFant': self.partner_id.name,
            'enderDest': {
                'xLgr': self.partner_id.street,
                'nro': self.partner_id.number,
                'xBairro': self.partner_id.district,
                'cMun': '%s%s' % (self.partner_id.state_id.ibge_code,
                                  self.partner_id.city_id.ibge_code),
                'xMun': self.partner_id.city_id.name,
                'UF': self.partner_id.state_id.code,
                'CEP': re.sub('[^0-9]', '', self.partner_id.zip),
                'cPais': self.partner_id.country_id.ibge_code,
                'xPais': self.partner_id.country_id.name,
                'fone': re.sub('[^0-9]', '', self.partner_id.phone or '')
            },
            'indIEDest': 9,
            'IE':  re.sub('[^0-9]', '', self.partner_id.inscr_est or ''),
        }
        eletronic_items = []
        for item in self.eletronic_item_ids:
            eletronic_items.append(
                self._prepare_eletronic_invoice_item(item, self))
        total = {
            'vBC': "%.02f" % self.valor_bruto,
            'vICMS': '0.00',
            'vICMSDeson': '0.00',
            'vBCST': '0.00',
            'vST': '0.00',
            'vProd': "%.02f" % self.valor_bruto,
            'vFrete': "%.02f" % self.valor_frete,
            'vSeg': "%.02f" % self.valor_seguro,
            'vServ': '0.00',
            'vDesc': '0.00',
            'vII': '0.00',
            'vIPI': '0.00',
            'vPIS': '0.00',
            'vCOFINS': '0.00',
            'vOutro': "%.02f" % self.valor_despesas,
            'vNF': "%.02f" % self.valor_final,
            'vTotTrib': '0.00'
        }
        transp = {
            'modFrete': 9
        }
        cobr = {
            'dup': [{
                'nDup': '1',
                'dVenc': self.data_emissao,
                'vDup': self.valor_final
            }]
        }
        infAdic = {
            'infCpl': 'Agora vai'
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
        }
        return vals

    @api.multi
    def _prepare_lote(self, lote, nfe_values):
        return {
            'idLote': lote,
            'indSinc': 1,
            'estado': self.company_id.partner_id.state_id.ibge_code,
            'ambiente': self.company_id.tipo_ambiente,
            'NFes': [{
                'infNFe': nfe_values
            }]
        }

    def _create_attachment(self, event, data):
        file_name = 'nfe-%s.xml' % datetime.now().strftime('%Y-%m-%d-%H-%M')
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'invoice.eletronic',
                'res_id': event.id
            })

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()

        nfe_values = self._prepare_eletronic_invoice_values()
        lote = self._prepare_lote(1, nfe_values)
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        resposta = autorizar_nfe(certificado, **lote)

        if resposta['object'].Body.nfeAutorizacaoLoteResult.\
                retEnviNFe.cStat != 104:
            self.codigo_retorno = resposta['object'].Body.\
                nfeAutorizacaoLoteResult.retEnviNFe.cStat
            self.mensagem_retorno = resposta['object'].Body.\
                nfeAutorizacaoLoteResult.retEnviNFe.xMotivo
        else:
            self.codigo_retorno = resposta['object'].Body.\
                nfeAutorizacaoLoteResult.retEnviNFe.protNFe.infProt.cStat
            self.mensagem_retorno = resposta['object'].Body.\
                nfeAutorizacaoLoteResult.retEnviNFe.protNFe.infProt.xMotivo

        event = self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment(self, resposta['sent_xml'])
        # self._create_attachment(self, resposta['received_xml'])
