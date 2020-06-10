# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import logging
from odoo import fields, models, _
from dateutil import parser
from datetime import datetime
from lxml import objectify
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


def convert(obj, conversion=None):
    if conversion:
        return conversion(obj.text)
    if isinstance(obj, objectify.StringElement):
        return str(obj)
    if isinstance(obj, objectify.IntElement):
        return int(obj)
    if isinstance(obj, objectify.FloatElement):
        return float(obj)
    raise u"Tipo não implementado %s" % str(type(obj))


def get(obj, path, conversion=None):
    paths = path.split(".")
    index = 0
    for item in paths:
        if not item:
            continue
        if hasattr(obj, item):
            obj = obj[item]
            index += 1
        else:
            return None
    if len(paths) == index:
        return convert(obj, conversion=conversion)
    return None


def remove_none_values(dict):
    res = {}
    res.update({k: v for k, v in dict.items() if v})
    return res


def cnpj_cpf_format(cnpj_cpf):
    if len(cnpj_cpf) == 14:
        cnpj_cpf = (cnpj_cpf[0:2] + '.' + cnpj_cpf[2:5] +
                    '.' + cnpj_cpf[5:8] +
                    '/' + cnpj_cpf[8:12] +
                    '-' + cnpj_cpf[12:14])
    else:
        cnpj_cpf = (cnpj_cpf[0:3] + '.' + cnpj_cpf[3:6] +
                    '.' + cnpj_cpf[6:9] + '-' + cnpj_cpf[9:11])
    return cnpj_cpf


def format_ncm(ncm):
    if len(ncm) == 4:
        ncm = ncm[:2] + '.' + ncm[2:4]
    elif len(ncm) == 6:
        ncm = ncm[:4] + '.' + ncm[4:6]
    else:
        ncm = ncm[:4] + '.' + ncm[4:6] + '.' + ncm[6:8]

    return ncm


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    state = fields.Selection(selection_add=[('imported', 'Importado')])

    def get_ide(self, nfe, operacao):
        ''' Importa a seção <ide> do xml'''
        ide = nfe.NFe.infNFe.ide
        modelo = ide.mod
        serie = ide.serie
        num_controle = ide.cNF
        numero_nfe = ide.nNF
        data_emissao = parser.parse(str(ide.dhEmi))
        data_fatura = get(ide, 'dhSaiEnt')
        if data_fatura:
            data_fatura = parser.parse(str(data_fatura))
        indicador_destinatario = ide.idDest
        ambiente = 'homologacao' if ide.tpAmb == 2\
            else 'producao'
        finalidade_emissao = str(ide.finNFe)

        return dict(
            tipo_operacao=operacao,
            model=str(modelo),
            serie_documento=serie,
            numero_controle=num_controle,
            numero=numero_nfe,
            data_emissao=data_emissao,
            data_fatura=data_fatura,
            ind_dest=str(indicador_destinatario),
            ambiente=ambiente,
            finalidade_emissao=finalidade_emissao,
            code='AUTO',
            state='imported',
            name='Documento Eletrônico: n° ' + str(numero_nfe),
        )

    def get_partner_nfe(self, nfe, destinatary, partner_automation):
        '''Importação da sessão <emit> do xml'''
        tag_nfe = None
        if destinatary:
            tag_nfe = nfe.NFe.infNFe.emit
        else:
            tag_nfe = nfe.NFe.infNFe.dest

        if hasattr(tag_nfe, 'CNPJ'):
            cnpj_cpf = cnpj_cpf_format(str(tag_nfe.CNPJ.text).zfill(14))
        else:
            cnpj_cpf = cnpj_cpf_format(str(tag_nfe.CPF.text).zfill(11))

        partner_id = self.env['res.partner'].search([
            ('cnpj_cpf', '=', cnpj_cpf)], limit=1)
        if not partner_id and partner_automation:
            partner_id = self._create_partner(tag_nfe, destinatary)
        elif not partner_id and not partner_automation:
            raise UserError((
                'Parceiro não cadastrado. Selecione a opção cadastrar ' +
                'parceiro, ou realize o cadastro manualmente.'))

        return dict(partner_id=partner_id.id)

    def get_ICMSTot(self, nfe):
        ICMSTot = nfe.NFe.infNFe.total.ICMSTot
        return dict(
            valor_bc_icms=get(ICMSTot, 'vBC'),
            valor_icms=get(ICMSTot, 'vICMS'),
            valor_icms_deson=get(ICMSTot, 'vICMSDeson'),
            valor_bc_icmsst=get(ICMSTot, 'vBCST'),
            valor_icmsst=get(ICMSTot, 'vST'),
            valor_bruto=get(ICMSTot, 'vProd'),
            valor_frete=get(ICMSTot, 'vFrete'),
            valor_seguro=get(ICMSTot, 'vSeg'),
            valor_desconto=get(ICMSTot, 'vDesc'),
            valor_ii=get(ICMSTot, 'vII'),
            valor_ipi=get(ICMSTot, 'vIPI'),
            valor_pis=get(ICMSTot, 'vPIS'),
            valor_cofins=get(ICMSTot, 'vCOFINS'),
            valor_final=get(ICMSTot, 'vNF'),
            valor_estimado_tributos=get(ICMSTot, 'vTotTrib'),
            # TODO Inserir novos campos
            # vOutro=ICMSTot.vOutro,
        )

    def get_retTrib(self, nfe):
        retTrib = nfe.NFe.infNFe.total.retTrib
        return dict(
            valor_retencao_pis=retTrib.vRetPIS,
            valor_retencao_cofins=retTrib.vRetCOFINS,
            valor_retencao_csll=retTrib.vRetCSLL,
            valor_retencao_irrf=retTrib.vIRRF,
            valor_retencao_previdencia=retTrib.vRetPrev
            # TODO Inserir novos campos
            # vBCIRRF=retTrib.vBCIRRF,
            # vBCRetPrev=retTrib.vBCRetPrev,
        )

    def get_transp(self, nfe):
        transportadora = {}

        if hasattr(nfe.NFe.infNFe, 'transp'):
            transp = nfe.NFe.infNFe.transp

            modFrete = get(transp, 'modFrete', str)

            if transp.modFrete == 9:
                return dict(
                    modalidade_frete=modFrete
                )

            if hasattr(transp, 'transporta'):
                cnpj_cpf = get(transp, 'transporta.CNPJ', str)

                if cnpj_cpf:
                    cnpj_cpf = cnpj_cpf_format(str(cnpj_cpf).zfill(14))

                transportadora_id = self.env['res.partner'].search([
                    ('cnpj_cpf', '=', cnpj_cpf)], limit=1)

                if not transportadora_id:
                    state_obj = self.env['res.country.state']
                    state_id = state_obj.search([
                        ('code', '=', get(transp, 'transporta.UF')),
                        ('country_id.code', '=', 'BR')])

                    vals = {
                        'cnpj_cpf': cnpj_cpf,
                        'name': get(transp, 'transporta.xNome'),
                        'inscr_est': get(transp, 'transporta.IE', str),
                        'street': get(transp, 'transporta.xEnder'),
                        'city': get(transp, 'transporta.xMun'),
                        'state_id': state_id.id,
                        'legal_name': get(transp, 'transporta.xNome'),
                        'company_type': 'company',
                        'is_company': True,
                        'supplier': True,
                        'company_id': None,
                    }
                    transportadora_id = self.env['res.partner'].create(vals)

                transportadora.update({
                    'transportadora_id': transportadora_id.id,
                    'placa_veiculo': get(transp, 'veicTransp.placa'),
                    'uf_veiculo': get(transp, 'veicTransp.UF'),
                    'rntc': get(transp, 'veicTransp.RNTC'),
                })

        return transportadora

    def get_reboque(self, nfe):
        if hasattr(nfe.NFe.infNFe.transp, 'reboque'):
            reboque = nfe.NFe.infNFe.transp.reboque

            reboque_ids = {
                'balsa': get(reboque, '.balsa'),
                'uf_veiculo': get(reboque, '.UF'),
                'vagao': get(reboque, '.vagao'),
                'rntc': get(reboque, '.RNTC'),
                'placa_veiculo': get(reboque, '.placa'),
            }

            return remove_none_values(reboque_ids)

        return {}

    def get_vol(self, nfe):
        if hasattr(nfe.NFe.infNFe.transp, 'vol'):
            vol = nfe.NFe.infNFe.transp.vol
            volume_ids = {
                'especie': get(vol, '.esp'),
                'quantidade_volumes': get(vol, 'qVol'),
                'numeracao': get(vol, 'nVol'),
                'peso_liquido': get(vol, 'pesoL'),
                'peso_bruto': get(vol, '.pesoB'),
                'marca': get(vol, '.marca'),
            }

            return remove_none_values(volume_ids)

        return {}

    def get_cobr_fat(self, nfe):
        if hasattr(nfe.NFe.infNFe, 'cobr'):
            cobr = nfe.NFe.infNFe.cobr

            if hasattr(cobr, 'fat'):
                fatura = {
                    'numero_fatura': get(cobr, 'fat.nFat', str),
                    'fatura_bruto': get(cobr, 'fat.vOrig'),
                    'fatura_desconto': get(cobr, 'fat.vDesc'),
                    'fatura_liquido': get(cobr, 'fat.vLiq'),
                }
                return fatura

        return {}

    def get_cobr_dup(self, nfe):
        if hasattr(nfe.NFe.infNFe, 'cobr'):
            cobr = nfe.NFe.infNFe.cobr

            if len(cobr) and hasattr(cobr, 'dup'):
                duplicatas = []
                for dup in cobr.dup:
                    duplicata = {
                        'data_vencimento': get(dup, 'dVenc'),
                        'valor': dup.vDup,
                        'numero_duplicata': get(dup, 'nDup'),
                    }
                    duplicatas.append((0, None, remove_none_values(duplicata)))

                return {'duplicata_ids': duplicatas}

        return {}

    def get_protNFe(self, nfe, company_id):
        protNFe = nfe.protNFe.infProt

        if protNFe.cStat in [100, 150] or\
                protNFe.cStat == 110 and company_id.cnpj_cpf in protNFe.chNFe:
            return dict(
                chave_nfe=protNFe.chNFe,
                data_autorizacao=parser.parse(
                    str(nfe.protNFe.infProt.dhRecbto)),
                mensagem_retorno=protNFe.xMotivo,
                protocolo_nfe=protNFe.nProt,
                codigo_retorno=protNFe.cStat,
                eletronic_event_ids=[(0, None, {
                    'code': protNFe.cStat,
                    'name': protNFe.xMotivo,
                })]
            )

    def get_infAdic(self, nfe):
        info_adicionais = {
            'informacoes_legais': get(
                nfe, 'NFe.infNFe.infAdic.infAdFisco'),
            'informacoes_complementares': get(
                nfe, 'NFe.infNFe.infAdic.infCpl'),
        }

        return info_adicionais

    def get_main(self, nfe):
        return dict(
            payment_term_id=self.payment_term_id.id,
            fiscal_position_id=self.fiscal_position_id.id,
        )

    def create_invoice_eletronic_item(self, item, company_id, partner_id,
                                      supplier, product_automation):
        codigo = get(item.prod, 'cProd', str)

        seller_id = self.env['product.supplierinfo'].search([
            ('name', '=', partner_id),
            ('product_code', '=', codigo)])

        product = None
        if seller_id:
            product = seller_id.product_id

        if not product and item.prod.cEAN and \
           str(item.prod.cEAN) != 'SEM GTIN':
            product = self.env['product.product'].search(
                [('barcode', '=', item.prod.cEAN)], limit=1)

        uom_id = self.env['uom.uom'].search([
            ('name', '=', str(item.prod.uCom))], limit=1).id

        if not product and product_automation:
            product = self._create_product(
                company_id, supplier, item.prod, uom_id=uom_id)

        if not uom_id:
            uom_id = product and product.uom_id.id or False
        product_id = product and product.id or False

        quantidade = item.prod.qCom
        preco_unitario = item.prod.vUnCom
        valor_bruto = item.prod.vProd
        desconto = 0
        if hasattr(item.prod, 'vDesc'):
            desconto = item.prod.vDesc
        seguro = 0
        if hasattr(item.prod, 'vSeg'):
            seguro = item.prod.vSeg
        frete = 0
        if hasattr(item.prod, 'vFrete'):
            frete = item.prod.vFrete
        outras_despesas = 0
        if hasattr(item.prod, 'vOutro'):
            outras_despesas = item.prod.vOutro
        indicador_total = str(item.prod.indTot)
        tipo_produto = product and product.fiscal_type or 'product'
        cfop = item.prod.CFOP
        ncm = item.prod.NCM
        cest = get(item, 'item.prod.CEST')
        nItemPed = get(item, 'prod.nItemPed')

        invoice_eletronic_Item = {
            'product_id': product_id, 'uom_id': uom_id,
            'quantidade': quantidade, 'preco_unitario': preco_unitario,
            'valor_bruto': valor_bruto, 'desconto': desconto, 'seguro': seguro,
            'frete': frete, 'outras_despesas': outras_despesas,
            'valor_liquido': valor_bruto - desconto + frete + seguro + outras_despesas,
            'indicador_total': indicador_total, 'tipo_produto': tipo_produto,
            'cfop': cfop, 'ncm': ncm, 'product_ean': item.prod.cEAN,
            'product_cprod': codigo, 'product_xprod': item.prod.xProd,
            'cest': cest, 'item_pedido_compra': nItemPed,
        }
        if hasattr(item.imposto, 'ICMS'):
            invoice_eletronic_Item.update(self._get_icms(item.imposto))
        if hasattr(item.imposto, 'ISSQN'):
            invoice_eletronic_Item.update(self._get_issqn(item.imposto.ISSQN))

        if hasattr(item.imposto, 'IPI'):
            invoice_eletronic_Item.update(self._get_ipi(item.imposto.IPI))

        invoice_eletronic_Item.update(self._get_pis(item.imposto.PIS))
        invoice_eletronic_Item.update(self._get_cofins(item.imposto.COFINS))

        if hasattr(item.imposto, 'II'):
            invoice_eletronic_Item.update(self._get_ii(item.imposto.II))

        return self.env['invoice.eletronic.item'].create(
            invoice_eletronic_Item)

    def _get_icms(self, imposto):
        csts = ['00', '10', '20', '30', '40', '41', '50',
                '51', '60', '70', '90']
        csts += ['101', '102', '103', '201', '202', '203',
                 '300', '400', '500', '900']

        cst_item = None
        vals = {}

        for cst in csts:
            tag_icms = None
            if hasattr(imposto.ICMS, 'ICMSSN%s' % cst):
                tag_icms = 'ICMSSN'
                cst_item = get(imposto, 'ICMS.ICMSSN%s.CSOSN' % cst, str)
            elif hasattr(imposto.ICMS, 'ICMS%s' % cst):
                tag_icms = 'ICMS'
                cst_item = get(imposto, 'ICMS.ICMS%s.CST' % cst, str)
                cst_item = str(cst_item).zfill(2)
            if tag_icms:
                icms = imposto.ICMS
                vals = {
                    'icms_cst': cst_item,
                    'origem': get(
                        icms, '%s%s.orig' % (tag_icms, cst), str),
                    'icms_tipo_base': get(
                        icms, '%s%s.modBC' % (tag_icms, cst), str),
                    'icms_aliquota_diferimento': get(
                        icms, '%s%s.pDif' % (tag_icms, cst)),
                    'icms_valor_diferido': get(
                        icms, '%s%s.vICMSDif' % (tag_icms, cst)),
                    'icms_motivo_desoneracao': get(
                        icms, '%s%s.motDesICMS' % (tag_icms, cst)),
                    'icms_valor_desonerado': get(
                        icms, '%s%s.vICMSDeson' % (tag_icms, cst)),
                    'icms_base_calculo': get(
                        icms, '%s%s.vBC' % (tag_icms, cst)),
                    'icms_aliquota_reducao_base': get(
                        icms, '%s%s.pRedBC' % (tag_icms, cst)),
                    'icms_aliquota': get(
                        icms, '%s%s.pICMS' % (tag_icms, cst)),
                    'icms_valor': get(
                        icms, '%s%s.vICMS' % (tag_icms, cst)),
                    'icms_aliquota_credito': get(
                        icms, '%s%s.pCredSN' % (tag_icms, cst)),
                    'icms_valor_credito': get(
                        icms, '%s%s.vCredICMSSN' % (tag_icms, cst)),
                    'icms_st_tipo_base': get(
                        icms, '%s%s.modBCST' % (tag_icms, cst), str),
                    'icms_st_aliquota_mva': get(
                        icms, '%s%s.pMVAST' % (tag_icms, cst)),
                    'icms_st_base_calculo': get(
                        icms, '%s%s.vBCST' % (tag_icms, cst)),
                    'icms_st_aliquota_reducao_base': get(
                        icms, '%s%s.pRedBCST' % (tag_icms, cst)),
                    'icms_st_aliquota': get(
                        icms, '%s%s.pICMSST' % (tag_icms, cst)),
                    'icms_st_valor': get(
                        icms, '%s%s.vICMSST' % (tag_icms, cst)),
                    'icms_bc_uf_dest': get(
                        imposto, 'ICMSUFDest.vBCUFDest'),
                    'icms_aliquota_fcp_uf_dest': get(
                        imposto, 'ICMSUFDest.pFCPUFDest'),
                    'icms_aliquota_uf_dest': get(
                        imposto, 'ICMSUFDest.pICMSUFDest'),
                    'icms_aliquota_interestadual': get(
                        imposto, 'ICMSUFDest.pICMSInter'),
                    'icms_aliquota_inter_part': get(
                        imposto, 'ICMSUFDest.pICMSInterPart'),
                    'icms_fcp_uf_dest': get(
                        imposto, 'ICMSUFDest.vFCPUFDest'),
                    'icms_uf_dest': get(
                        imposto, 'ICMSUFDest.vICMSUFDest'),
                    'icms_uf_remet': get(
                        imposto, 'ICMSUFDest.vICMSUFRemet'),
                }

        return remove_none_values(vals)

    def _get_issqn(self, issqn):

        vals = {
            'issqn_codigo': get(issqn, 'cListServ'),
            'issqn_aliquota': get(issqn, 'vAliq'),
            'issqn_base_calculo': get(issqn, 'vBC'),
            'issqn_valor': get(issqn, 'vISSQN'),
            'issqn_valor_retencao': get(issqn, 'vISSRet'),
        }

        return remove_none_values(vals)

    def _get_ipi(self, ipi):
        classe_enquadramento_ipi = get(ipi, 'clEnq')
        codigo_enquadramento_ipi = get(ipi, 'cEnq')

        vals = {}
        for item in ipi.getchildren():
            ipi_cst = get(ipi, '%s.CST' % item.tag[36:])
            ipi_cst = str(ipi_cst).zfill(2)

            vals = {
                'ipi_cst': ipi_cst,
                'ipi_base_calculo': get(ipi, '%s.vBC' % item.tag[36:]),
                'ipi_aliquota': get(ipi, '%s.pIPI' % item.tag[36:]),
                'ipi_valor': get(ipi, '%s.vIPI' % item.tag[36:]),
                'classe_enquadramento_ipi': classe_enquadramento_ipi,
                'codigo_enquadramento_ipi': codigo_enquadramento_ipi,
            }

        return remove_none_values(vals)

    def _get_pis(self, pis):
        vals = {}
        for item in pis.getchildren():
            pis_cst = get(pis, '%s.CST' % item.tag[36:])
            pis_cst = str(pis_cst).zfill(2)

            vals = {
                'pis_cst': pis_cst,
                'pis_base_calculo': get(pis, '%s.vBC' % item.tag[36:]),
                'pis_aliquota': get(pis, '%s.pPIS' % item.tag[36:]),
                'pis_valor': get(pis, '%s.vPIS' % item.tag[36:]),
            }

        return remove_none_values(vals)

    def _get_cofins(self, cofins):
        vals = {}
        for item in cofins.getchildren():
            cofins_cst = get(cofins, '%s.CST' % item.tag[36:])
            cofins_cst = str(cofins_cst).zfill(2)

            vals = {
                'cofins_cst': cofins_cst,
                'cofins_base_calculo': get(cofins, '%s.vBC' % item.tag[36:]),
                'cofins_aliquota': get(cofins, '%s.pCOFINS' % item.tag[36:]),
                'cofins_valor': get(cofins, '%s.vCOFINS' % item.tag[36:]),
            }

        return remove_none_values(vals)

    def _get_ii(self, ii):
        vals = {}
        for item in ii.getchildren():
            vals = {
                'ii_base_calculo': get(ii, '%s.vBC' % item),
                'ii_valor_despesas': get(ii, '%s.vDespAdu' % item),
                'ii_valor_iof': get(ii, '%s.vIOF' % item),
                'ii_valor': get(ii, '%s.vII' % item),
            }

        return remove_none_values(vals)

    def get_items(self, nfe, company_id, partner_id,
                  supplier, product_automation):
        items = []
        for det in nfe.NFe.infNFe.det:
            item = self.create_invoice_eletronic_item(
                det, company_id, partner_id, supplier, product_automation)
            items.append((4, item.id, False))
        return {'eletronic_item_ids': items}

    def get_compra(self, nfe):
        if hasattr(nfe.NFe.infNFe, 'compra'):
            compra = nfe.NFe.infNFe.compra

            return {
                'nota_empenho': get(compra, 'xNEmp'),
                'pedido_compra': get(compra, 'xPed'),
                'contrato_compra': get(compra, 'xCont'),
            }

        return {}

    def import_nfe(self, company_id, nfe, nfe_xml, partner_automation=False,
                   account_invoice_automation=False, tax_automation=False,
                   supplierinfo_automation=False, fiscal_position_id=False,
                   payment_term_id=False, invoice_dict=None):
        invoice_dict = invoice_dict or {}
        if self.existing_invoice(nfe):
            raise UserError('Documento Eletrônico já importado!')

        partner_vals = self._get_company_invoice(nfe, partner_automation)
        company_id = self.env['res.company'].browse(
            partner_vals['company_id'])
        invoice_dict.update(partner_vals)
        invoice_dict.update({
            'nfe_processada': base64.encodestring(nfe_xml),
            'nfe_processada_name': "NFe%08d.xml" % nfe.NFe.infNFe.ide.nNF
        })
        invoice_dict.update(self.get_protNFe(nfe, company_id))
        invoice_dict.update(self.get_main(nfe))
        partner = self.get_partner_nfe(
            nfe, partner_vals['destinatary'], partner_automation)
        invoice_dict.update(
            self.get_ide(nfe, partner_vals['tipo_operacao']))
        invoice_dict.update(partner)
        invoice_dict.update(self.get_ICMSTot(nfe))
        invoice_dict.update(self.get_items(
            nfe, company_id, partner['partner_id'],
            invoice_dict['partner_id'],
            supplierinfo_automation))
        invoice_dict.update(self.get_infAdic(nfe))
        invoice_dict.update(self.get_cobr_fat(nfe))
        invoice_dict.update(self.get_transp(nfe))
        invoice_dict.update(
            {'reboque_ids': [(0, None, self.get_reboque(nfe))]})
        invoice_dict.update({'volume_ids': [(0, None, self.get_vol(nfe))]})
        invoice_dict.update(self.get_cobr_dup(nfe))
        invoice_dict.update(self.get_compra(nfe))
        invoice_dict.pop('destinatary', False)
        invoice_eletronic = self.env['invoice.eletronic'].create(
            invoice_dict)

        if account_invoice_automation:
            invoice = invoice_eletronic.prepare_account_invoice_vals(
                company_id, tax_automation=tax_automation,
                supplierinfo_automation=supplierinfo_automation,
                fiscal_position_id=fiscal_position_id,
                payment_term_id=payment_term_id)
            invoice_eletronic.invoice_id = invoice.id

    def existing_invoice(self, nfe):
        if hasattr(nfe, 'protNFe'):
            protNFe = nfe.protNFe.infProt
        else:
            raise UserError('XML invalido!')

        chave_nfe = protNFe.chNFe

        invoice_eletronic = self.env['invoice.eletronic'].search([
            ('chave_nfe', '=', chave_nfe)])

        return invoice_eletronic

    def _create_partner(self, tag_nfe, destinatary):
        cnpj_cpf = None
        company_type = None
        is_company = None
        ender_tag = 'enderEmit' if destinatary else 'enderDest'

        if hasattr(tag_nfe, 'CNPJ'):
            cnpj_cpf = str(tag_nfe.CNPJ.text).zfill(14)
            company_type = 'company'
            is_company = True
        else:
            cnpj_cpf = str(tag_nfe.CPF.text).zfill(11)
            company_type = 'person'
            is_company = False

        cnpj_cpf = cnpj_cpf_format(cnpj_cpf)

        state_id = self.env['res.country.state'].search([
            ('code', '=', get(tag_nfe, ender_tag + '.UF')),
            ('country_id.code', '=', 'BR')])

        city_id = self.env['res.state.city'].search([
            ('ibge_code', '=', get(tag_nfe, ender_tag + '.cMun', str)[2:]),
            ('state_id', '=', state_id.id)])

        partner = {
            'name': get(tag_nfe, 'xFant') or get(tag_nfe, 'xNome'),
            'street': get(tag_nfe, ender_tag + '.xLgr'),
            'number': get(tag_nfe, ender_tag + '.nro', str),
            'district': get(tag_nfe, ender_tag + '.xBairro'),
            'city_id': city_id.id,
            'state_id': state_id.id,
            'zip': get(tag_nfe, ender_tag + '.CEP', str),
            'country_id': state_id.country_id.id,
            'phone': get(tag_nfe, ender_tag + '.fone'),
            'inscr_est': tag_nfe.IE.text if get(tag_nfe, 'IE', str) else None,
            'inscr_mun': tag_nfe.IM.text if get(tag_nfe, 'IM', str) else None,
            'cnpj_cpf': str(cnpj_cpf),
            'legal_name': get(tag_nfe, 'xNome'),
            'company_type': company_type,
            'is_company': is_company,
            'supplier': True,
            'customer': False,
            'company_id': None,
        }
        partner_id = self.env['res.partner'].create(partner)
        partner_id.message_post(body="<ul><li>Parceiro criado através da importação\
                                de xml</li></ul>")

        return partner_id

    def _create_product(self, company_id, supplier, nfe_item, uom_id=False):
        params = self.env['ir.config_parameter'].sudo()
        seq_id = int(params.get_param(
            'br_nfe_import.product_sequence', default=0))
        if not seq_id:
            raise UserError(
                'A empresa não possui uma sequência de produto configurado!')
        ncm = get(nfe_item, 'NCM', str)
        ncm_id = self.env['product.fiscal.classification'].search([
            ('code', '=', ncm)])

        category = self.env['product.category'].search(
            [('l10n_br_ncm_category_ids.name', '=', ncm[:4])], limit=1)

        sequence = self.env['ir.sequence'].browse(seq_id)
        code = sequence.next_by_id()
        product = {
            'default_code': code,
            'name': get(nfe_item, 'xProd'),
            'purchase_ok': True,
            'sale_ok': False,
            'fiscal_type': 'product',
            'type': 'product',
            'fiscal_classification_id': ncm_id.id,
            'standard_price': get(nfe_item, 'vUnCom'),
            'lst_price': 0.0,
            'cest': get(nfe_item, 'CEST', str),
            'taxes_id': [],
            'supplier_taxes_id': [],
            'company_id': None,
        }
        if uom_id:
            product.update(dict(uom_id=uom_id))
        if category:
            product.update(dict(categ_id=category.id))
        if category and category.l10n_br_fiscal_category_id:
            product.update({
                'fiscal_category_id': category.l10n_br_fiscal_category_id.id,
            })

        ean = get(nfe_item, 'cEAN', str)
        if ean != 'None' and ean != 'SEM GTIN':
            product['barcode'] = ean
        product_id = self.env['product.product'].create(product)

        self.env['product.supplierinfo'].create({
            'product_id': product_id.id,
            'product_tmpl_id': product_id.product_tmpl_id.id,
            'name': supplier,
            'product_code': get(nfe_item, 'cProd', str),
        })

        product_id.message_post(
            body="<ul><li>Produto criado através da importação \
            de xml</li></ul>")
        return product_id

    def _prepare_account_invoice_vals(self, company_id, tax_automation=False,
                                      supplierinfo_automation=False,
                                      fiscal_position_id=False,
                                      payment_term_id=False):
        operation = 'in_invoice' \
            if self.tipo_operacao == 'entrada' else 'out_invoice'
        journal_id = self.env['account.invoice'].with_context(
            type=operation, company_id=company_id.id
        ).default_get(['journal_id'])['journal_id']
        partner = self.partner_id.with_context(force_company=company_id.id)
        account_id = partner.property_account_payable_id.id \
            if operation == 'in_invoice' else \
            partner.property_account_receivable_id.id
        if not fiscal_position_id:
            fiscal_position_id = partner.property_account_position_id
            if not fiscal_position_id:
                fpos = self.env['account.fiscal.position'].search(
                    [('auto_apply', '=', True),
                     ('fiscal_type', '=', self.tipo_operacao),
                     ('company_id', '=', company_id.id)], limit=1)
                fiscal_position_id = fpos
        if not payment_term_id:
            payment_term_id = partner.property_supplier_payment_term_id
        if not journal_id:
            raise UserError(
                _('Please define an accounting sale journal for\
                    this company.'))
        vals = {
            'company_id': company_id.id,
            'fiscal_position_id':
            fiscal_position_id and fiscal_position_id.id or False,
            'payment_term_id': payment_term_id and payment_term_id.id or False,
            'type': operation,
            'state': 'draft',
            'origin': self.pedido_compra,
            'reference': "%s/%s" % (self.numero, self.serie_documento),
            'date_invoice': datetime.strftime(self.data_emissao,
                                              "%Y-%m-%d %H:%M:%S"),
            'partner_id': self.partner_id.id,
            'journal_id': journal_id,
            'account_id': account_id,
            'icms_value': self.valor_icms,
            'icms_st_value': self.valor_icmsst,
            'ipi_value': self.valor_ipi,
            'pis_value': self.valor_pis,
            'cofins_value': self.valor_cofins,
            'ii_value': self.valor_ii,
            'total_bruto': self.valor_bruto,
            'total_desconto': self.valor_desconto,
            'amount_total': self.valor_final,
            'icms_base': self.valor_bc_icms,
            'icms_st_base': self.valor_bc_icmsst,
            'total_tributos_estimados': self.valor_estimado_tributos,
            'issqn_retention': self.valor_retencao_issqn,
            'pis_retention': self.valor_retencao_pis,
            'cofins_retention': self.valor_retencao_cofins,
            'irrf_base': self.valor_bc_irrf,
            'irrf_retention': self.valor_retencao_irrf,
            'csll_base': self.valor_bc_csll,
            'csll_retention': self.valor_retencao_csll,
            'inss_base': self.valor_bc_inss,
            'inss_retention': self.valor_retencao_inss,
        }
        return vals

    def prepare_account_invoice_vals(
            self, company_id, tax_automation=False,
            supplierinfo_automation=False, fiscal_position_id=False,
            payment_term_id=False):

        vals = self._prepare_account_invoice_vals(
            company_id, tax_automation, supplierinfo_automation,
            fiscal_position_id, payment_term_id)
        if vals['payment_term_id']:
            payment_term = self.env['account.payment.term'].browse(
                vals['payment_term_id'])
            date_invoice = self.data_emissao
            if not date_invoice:
                date_invoice = fields.Date.context_today(self)
            pterm_list = payment_term.with_context(
                currency_id=company_id.currency_id.id).compute(
                    value=1, date_ref=date_invoice)[0]
            vals['date_due'] = max(line[0] for line in pterm_list)

        purchase_order_vals = self._get_purchase_order_vals(self.pedido_compra)
        purchase_order_id = None
        if purchase_order_vals:
            vals.update(purchase_order_vals)
            purchase_order_id = vals['purchase_id']

        items = []
        messages_log = []
        for item in self.eletronic_item_ids:
            invoice_item, message_log = self.prepare_account_invoice_line_vals(
                item, purchase_order_id, supplierinfo_automation,
                tax_automation, company_id)
            items.append((0, 0, invoice_item))
            messages_log.append(message_log)

        vals['invoice_line_ids'] = items
        account_invoice = self.env['account.invoice'].create(vals)
        account_invoice.message_post(body=u"<ul><li>Fatura criada através da do xml\
                                     da NF-e %s</li></ul>" % self.numero)

        for message in messages_log:
            if message:
                account_invoice.message_post(body=message)

        return account_invoice

    def prepare_account_invoice_line_vals(
            self, item, purchase_order_id, supplierinfo_automation,
            tax_automation, company_id):
        if item.product_id:
            product = item.product_id.with_context(force_company=company_id.id)
            if product.property_account_expense_id:
                account_id = product.property_account_expense_id
            else:
                account_id =\
                    product.categ_id.property_account_expense_categ_id
        else:
            account_id = self.env['ir.property'].with_context(
                force_company=company_id.id).get(
                    'property_account_expense_categ_id', 'product.category')

        cfop = self.env['br_account.cfop'].search([('code', '=', item.cfop)])
        ncm = self.env['product.fiscal.classification'].search([
            ('code', '=', item.ncm)])

        tax_icms_id = None
        tax_icms_st_id = None
        tax_ipi_id = None
        tax_pis_id = None
        tax_cofins_id = None
        tax_issqn_id = None
        message_log = ''
        purchase_line_id = None

        if item.item_pedido_compra:
            purchase_line_id, message_log = self._get_purchase_line_id(
                item, purchase_order_id, supplierinfo_automation)

        if purchase_line_id:
            taxes_id = purchase_line_id.taxes_id
            tax_icms_id = taxes_id.filtered(
                lambda x: x.domain == 'icms' and x.amount > 0)
            tax_icms_st_id = taxes_id.filtered(
                lambda x: x.domain == 'icmsst' and x.amount > 0)
            tax_ipi_id = taxes_id.filtered(
                lambda x: x.domain == 'ipi' and x.amount > 0)
            tax_pis_id = taxes_id.filtered(
                lambda x: x.domain == 'pis' and x.amount > 0)
            tax_cofins_id = taxes_id.filtered(
                lambda x: x.domain == 'cofins' and x.amount > 0)

            vals = {
                'imported': True,
                'product_id': purchase_line_id.product_id.id,
                'uom_id': purchase_line_id.product_id.uom_po_id.id,
                'name': purchase_line_id.name,
                'cfop_id': purchase_line_id.cfop_id.id,
                'icms_csosn_simples': purchase_line_id.icms_csosn_simples,
                'icms_cst': purchase_line_id.icms_cst_normal,
                'icms_aliquota_reducao_base':
                purchase_line_id.icms_aliquota_reducao_base,
                'icms_aliquota_credito':
                purchase_line_id.aliquota_icms_proprio,
                'icms_st_aliquota_mva': purchase_line_id.icms_st_aliquota_mva,
                'icms_st_aliquota_reducao_base':
                purchase_line_id.icms_st_aliquota_reducao_base,
                'icms_st_aliquota_deducao':
                purchase_line_id.icms_st_aliquota_deducao,
                'ipi_cst': purchase_line_id.ipi_cst,
                'pis_cst': purchase_line_id.pis_cst,
                'cofins_cst': purchase_line_id.cofins_cst,
            }
        else:
            vals = {
                'imported': True,
                'product_id': item.product_id.id,
                'uom_id': item.uom_id.id,
                'name': item.name if item.name else item.product_xprod,
                'cfop_id': cfop.id,
                'icms_csosn_simples': item.icms_cst if item.icms_cst and len(
                    item.icms_cst) == 3 else '',
                'icms_cst': item.icms_cst if item.icms_cst and len(
                    item.icms_cst) == 2 else '',
                'icms_aliquota_reducao_base': item.icms_aliquota_reducao_base,
                'icms_aliquota_credito': item.icms_aliquota_credito,
                'icms_st_aliquota_mva': item.icms_st_aliquota_mva,
                'icms_st_aliquota_reducao_base':
                item.icms_st_aliquota_reducao_base,
                'icms_st_aliquota_deducao': item.icms_st_aliquota_reducao_base,
                'issqn_aliquota': item.issqn_aliquota if item.issqn_aliquota
                else '',
                'issqn_base_calculo': item.issqn_base_calculo if
                item.issqn_base_calculo else '',
                'issqn_valor': item.issqn_valor if item.issqn_valor else '',
                'ipi_cst': item.ipi_cst,
                'pis_cst': item.pis_cst,
                'cofins_cst': item.cofins_cst,
            }

        if not tax_icms_id and item.icms_aliquota > 0:
            tax_icms_id, message = self._get_tax(
                'icms', item.icms_aliquota, company_id, tax_automation)
            message_log = message_log + message

        if not tax_icms_st_id and item.icms_st_aliquota > 0:
            tax_icms_st_id, message = self._get_tax(
                'icmsst', item.icms_st_aliquota, company_id, tax_automation)
            message_log = message_log + message

        if not tax_ipi_id and item.ipi_aliquota > 0:
            tax_ipi_id, message = self._get_tax(
                'ipi', item.ipi_aliquota, company_id, tax_automation)
            message_log = message_log + message

        if not tax_pis_id and item.pis_aliquota > 0:
            tax_pis_id, message = self._get_tax(
                'pis', item.pis_aliquota, company_id, tax_automation)
            message_log = message_log + message

        if not tax_cofins_id and item.cofins_aliquota > 0:
            tax_cofins_id, message = self._get_tax(
                'cofins', item.cofins_aliquota, company_id, tax_automation)
            message_log = message_log + message

        if not tax_issqn_id and item.issqn_aliquota > 0:
            tax_issqn_id, message = self._get_tax(
                'issqn', item.issqn_aliquota, company_id, tax_automation)
            message_log = message_log + message

        vals.update({
            'quantity': item.quantidade,
            'price_unit': item.preco_unitario,
            'price_subtotal': item.valor_bruto,
            'valor_frete': item.frete,
            'valor_seguro': item.seguro,
            'outras_despesas': item.outras_despesas,
            'fiscal_classification_id': ncm.id,
            'account_id': account_id.id,
            'tributos_estimados': item.tributos_estimados,
            'tax_icms_id': None if tax_icms_id is None else tax_icms_id.id,
            'icms_origem': item.origem,
            'icms_base_calculo': item.icms_base_calculo,
            'icms_valor': item.icms_valor,
            'icms_valor_credito': item.icms_valor_credito,
            'icms_st_base_calculo': item.icms_st_base_calculo,
            'icms_st_valor': item.icms_st_valor,
            'tax_icms_st_id': None if tax_icms_st_id is None else
            tax_icms_st_id.id,
            'tax_ipi_id': None if tax_ipi_id is None else tax_ipi_id.id,
            'ipi_base_calculo': item.ipi_aliquota,
            'ipi_reducao_bc': item.ipi_reducao_bc,
            'pis_valor': item.pis_valor,
            'pis_base_calculo': item.pis_base_calculo,
            'tax_pis_id': None if tax_pis_id is None else tax_pis_id.id,
            'cofins_base_calculo': item.cofins_base_calculo,
            'cofins_valor': item.cofins_valor,
            'tax_cofins_id': None if tax_cofins_id is None else
            tax_cofins_id.id,
            'tax_ii_id': None,
            'tax_issqn_id': None if tax_issqn_id is None else
            tax_issqn_id.id,
            'ii_base_calculo': item.ii_base_calculo,
            'ii_valor_despesas': item.ii_valor_despesas,
            'ii_valor_iof': item.ii_valor_iof,
            'ii_valor': item.ii_valor,
            'product_ean': item.product_ean,
            'product_cprod': item.product_cprod,
            'product_xprod': item.product_xprod,
        })

        return vals, message_log

    def _get_purchase_order_vals(self, po_number):
        purchase_order_id = self.env['purchase.order'].search([
            ('name', '=', po_number),
            ('state', '=', 'purchase')])

        if purchase_order_id.id:
            vals = {
                'purchase_id': purchase_order_id.id,
                'fiscal_position_id': purchase_order_id.fiscal_position_id.id,
                'payment_term_id': purchase_order_id.payment_term_id.id,
            }

            return vals

    def _get_tax(self, tax_domain, aliquota, company_id, tax_automation=False):
        tax = self.env['account.tax'].search([
            ('domain', '=', tax_domain),
            ('amount', '=', aliquota),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', company_id.id)], limit=1)

        if tax:
            return tax, ""
        elif tax_automation:
            return self._create_tax(tax_domain, aliquota, company_id)

        return None, ''

    def _create_tax(self, tax_domain, aliquota, company_id):
        vals = {
            'domain': tax_domain,
            'type_tax_use': 'purchase',
            'name': "%s (%s)" % (tax_domain, aliquota),
            'description': tax_domain,
            'amount': aliquota,
            'company_id': company_id.id,
        }
        if tax_domain in ('icms', 'pis', 'cofins'):
            vals.update(dict(amount_type='division', price_include=True))
        if tax_domain in ('icmsst',):
            vals.update(dict(amount_type='icmsst'))
        tax = self.env['account.tax'].create(vals)

        message = (u"<ul><li>Aliquota criada através da importação\
                   do xml da nf %s<br/></li></ul>" % self.numero)

        return tax, message

    def _create_supplierinfo(self, item, purchase_order_line,
                             automation=False):
        supplierinfo_id = self.env['product.supplierinfo'].search([
            ('name', '=', purchase_order_line.order_id.partner_id.id),
            ('product_code', '=', item.product_cprod)])

        if not supplierinfo_id:
            vals = {
                'name': purchase_order_line.order_id.partner_id.id,
                'product_name': item.product_xprod,
                'product_code': item.product_cprod,
                'product_tmpl_id': purchase_order_line.product_id.id,
            }

            self.env['product.supplierinfo'].create(vals)

            message = u"<ul><li>Produto do fornecedor criado através da\
                        importação do xml da nf %(nf)s. Produto\
                        do fornecedor %(codigo_produto_fornecedor)s\
                            - %(descricao_produto_fornecedor)s criado\
                        para o produto %(codigo_produto)s - \
                        %(descricao_produto)s<br/></li></ul>" % {
                'nf': self.numero,
                'codigo_produto_fornecedor':
                item.product_cprod,
                'descricao_produto_fornecedor':
                item.product_xprod,
                'codigo_produto':
                purchase_order_line.product_id.default_code,
                'descricao_produto':
                purchase_order_line.product_id.name,
            }

            return message

    def _get_purchase_line_id(
            self, item, purchase_order_id, supplierinfo_automation=False):
        purchase_line_ids = self.env['purchase.order.line'].search([
            ('order_id', '=', purchase_order_id)], order='sequence')

        if not purchase_line_ids:
            return False, "Item de ordem de compra não localizado"

        purchase_line_id = purchase_line_ids[int(
            item.item_pedido_compra) - 1]

        if hasattr(purchase_line_id.product_id, 'seller_id'):
            seller_id = purchase_line_id.product_id.seller_id

            if seller_id and seller_id.product_code == item.product_cprod:
                return purchase_line_id
            else:
                return purchase_line_ids.filtered(
                    lambda x: x.product_id.seller_id.product_code ==
                    item.product_cprod)

        message = self._create_supplierinfo(
            item, purchase_line_id, supplierinfo_automation)
        return purchase_line_id, message

    def _get_company_invoice(self, nfe, partner_automation):
        emit = nfe.NFe.infNFe.emit
        dest = nfe.NFe.infNFe.dest
        nfe_type = 'in' if nfe.NFe.infNFe.ide.tpNF.text == '0' else 'out'
        tipo_operacao = ''

        if hasattr(emit, 'CNPJ'):
            emit_cnpj_cpf = cnpj_cpf_format(str(emit.CNPJ.text).zfill(14))
        else:
            emit_cnpj_cpf = cnpj_cpf_format(str(emit.CPF.text).zfill(11))

        if hasattr(dest, 'CNPJ'):
            dest_cnpj_cpf = cnpj_cpf_format(str(dest.CNPJ.text).zfill(14))
        else:
            dest_cnpj_cpf = cnpj_cpf_format(str(dest.CPF.text).zfill(11))

        # !Importante
        # 1º pesquisa a empresa através do CNPJ, tanto emitente quanto dest.
        # 2º caso a empresa for destinatária usa o cnpj do emitente
        # para cadastrar parceiro senão usa o do destinatário
        # 3º o tipo de operação depende se a empresa emitiu ou não a nota
        # Se ela emitiu usa do xml o tipo, senão inverte o valor

        cnpj_cpf_partner = False
        destinatary = False
        company = self.env['res.company'].sudo().search(
            [('partner_id.cnpj_cpf', '=', dest_cnpj_cpf)])

        if not company:
            company = self.env['res.company'].sudo().search(
                [('partner_id.cnpj_cpf', '=', emit_cnpj_cpf)])
            if company:
                cnpj_cpf_partner = dest_cnpj_cpf
                tipo_operacao = 'entrada' if nfe_type == 'in' else 'saida'
            else:
                raise UserError(
                    "XML não destinado nem emitido por esta empresa.")
        else:
            destinatary = True
            cnpj_cpf_partner = emit_cnpj_cpf
            tipo_operacao = 'entrada' if nfe_type == 'out' else 'saida'

        emit_id = self.env['res.partner'].search([
            ('cnpj_cpf', '=', cnpj_cpf_partner)], limit=1)

        if not partner_automation and not emit_id:
            raise UserError(
                "Parceiro não encontrado, caso deseje cadastrar \
                um parceiro selecione a opção 'Cadastrar Parceiro'.")

        return dict(
            company_id=company.id,
            tipo_operacao=tipo_operacao,
            partner_id=emit_id.id,
            destinatary=destinatary,
        )


class InvoiceEletronicItem(models.Model):
    _inherit = 'invoice.eletronic.item'

    product_ean = fields.Char('EAN do Produto (XML)')
    product_cprod = fields.Char('Cód .Fornecedor (XML)')
    product_xprod = fields.Char('Nome do produto (XML)')
