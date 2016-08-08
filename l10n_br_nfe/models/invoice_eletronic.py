# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
from uuid import uuid4
from datetime import datetime
from openerp import api, models
from pytrustnfe.nfe import NFe
from pytrustnfe.certificado import extract_cert_and_key_from_pfx


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    
    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        prod = {
            'cProd': 22,
            'cEAN': '00000011111115',
            'xProd': item.product_id.name,
            'NCM': '39259090',
            'CFOP': item.cfop,
            'uCom': 'un',
            'qCom': item.quantity,
            'vUnCom': item.unit_price,
            'vProd': "100.00",
            'cEANTrib': '00000011111115',
            'uTrib': 'un',
            'qTrib': item.quantity,
            'vUnTrib': item.unit_price,
            'indTot': 1
        }
        imposto = {
            'vTotTrib': '12.00',
            'ICMS': {
                'ICMS00': {
                    'orig': 0,
                    'CST': '00',
                    'modBC': 0,
                    'vBC': '100.00',
                    'pICMS': '12.00',
                    'vICMS': '12.00'
                }
            },
            'IPI': {
                'cEnq': 999,
                'IPITrib': {
                    'CST': '50',
                    'vBC': '100.00',
                    'pIPI': '5.00',
                    'vIPI': '5.00'
                }
            },
            'PIS': {
                'PISAliq': {
                    'CST': '01',
                    'vBC': '100.00',
                    'pPIS': '0.6500',
                    'vPIS': '0.65'
                }
            },
            'COFINS': {
                'COFINSAliq': {
                    'CST': '01',
                    'vBC': '100.00',
                    'pCOFINS': '3.0000',
                    'vCOFINS': '3.00'
                }
            }
        }
        return {'prod': prod, 'imposto': imposto}

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        ide = {
            'cUF': self.company_id.state_id.ibge_code,
            'cNF': '16255086',
            'natOp': self.fiscal_position_id.name,
            'indPag': 1,
            'mod': self.model,
            'serie': self.serie.code,
            'nNF': self.numero,
            'dhEmi': '2016-05-05T11:28:14-03:00',
            'dhSaiEnt': '2016-05-05T11:28:14-03:00',
            'tpNF': self.finalidade_emissao,
            'idDest': 2,
            'cMunFG': 4321667,
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
            'xNome': self.company_id.legal_name,
            'xFant': self.company_id.name,
            'enderEmit': {
                'xLgr': self.company_id.street,
                'nro': self.company_id.number,
                'xBairro': self.company_id.district,
                'cMun': '%s%s' % (self.company_id.partner_id.state_id.ibge_code,
                                  self.company_id.partner_id.l10n_br_city_id.ibge_code),
                'xMun': self.company_id.l10n_br_city_id.name,
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
                'cMun': '%s%s'  % (self.partner_id.state_id.ibge_code,
                                   self.partner_id.l10n_br_city_id.ibge_code),
                'xMun': self.partner_id.l10n_br_city_id.name,
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
            'vBC': '100.00',
            'vICMS': '12.00',
            'vICMSDeson': '0.00',
            'vBCST': '0.00',
            'vST': '0.00',
            'vProd': '100.00',
            'vFrete': '0.00',
            'vSeg': '0.00',
            'vDesc': '0.00',
            'vII': '0.00',
            'vIPI': '5.00',
            'vPIS': '0.65',
            'vCOFINS': '3.00',
            'vOutro': '0.00',
            'vNF': '100.00',
            'vTotTrib': '12.00'
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
            'Id': 'NFe43160502261542000143550010000003391162550863',
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

        cert, key = extract_cert_and_key_from_pfx(
            cert_pfx, self.company_id.nfe_a1_password)

        autorizacao = NFe(cert, key)
        resposta = autorizacao.autorizar_nfe(
            lote, 'NFe43160502261542000143550010000003391162550863')

        if resposta['object'].retEnviNFe.cStat != 104:
            self.codigo_retorno = resposta['object'].retEnviNFe.cStat
            self.mensagem_retorno = resposta['object'].retEnviNFe.xMotivo
        else:
            self.codigo_retorno = resposta['object'].retEnviNFe.protNFe.infProt.cStat
            self.mensagem_retorno = resposta['object'].retEnviNFe.protNFe.infProt.xMotivo
        
        event = self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment(self, resposta['sent_xml'])
        self._create_attachment(self, resposta['received_xml'])
