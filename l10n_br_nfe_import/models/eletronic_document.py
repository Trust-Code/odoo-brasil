import base64
import pytz
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


class EletronicDocument(models.Model):
    _inherit = 'eletronic.document'

    state = fields.Selection(selection_add=[('imported', 'Importado')])

    def get_ide(self, nfe, operacao):
        ''' Importa a seção <ide> do xml'''
        ide = nfe.NFe.infNFe.ide
        modelo = ide.mod
        serie = ide.serie
        num_controle = ide.cNF
        numero_nfe = ide.nNF
        data_emissao = parser.parse(str(ide.dhEmi))
        dt_entrada_saida = get(ide, 'dhSaiEnt')

        if dt_entrada_saida:
            dt_entrada_saida = parser.parse(str(dt_entrada_saida))
            dt_entrada_saida = dt_entrada_saida.astimezone(pytz.utc).replace(tzinfo=None)
        indicador_destinatario = ide.idDest
        ambiente = 'homologacao' if ide.tpAmb == 2\
            else 'producao'
        finalidade_emissao = str(ide.finNFe)

        return dict(
            tipo_operacao=operacao,
            model='nfce' if str(modelo) == '65' else 'nfe',
            serie_documento=serie,
            numero_controle=num_controle,
            numero=numero_nfe,
            data_emissao=data_emissao.astimezone(pytz.utc).replace(tzinfo=None),
            data_entrada_saida=dt_entrada_saida,
            ind_dest=str(indicador_destinatario),
            ambiente=ambiente,
            finalidade_emissao=finalidade_emissao,
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
            ('l10n_br_cnpj_cpf', '=', cnpj_cpf)], limit=1)
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
            valor_produtos=get(ICMSTot, 'vProd'),
            valor_frete=get(ICMSTot, 'vFrete'),
            valor_seguro=get(ICMSTot, 'vSeg'),
            valor_desconto=get(ICMSTot, 'vDesc'),
            valor_ii=get(ICMSTot, 'vII'),
            valor_ipi=get(ICMSTot, 'vIPI'),
            pis_valor=get(ICMSTot, 'vPIS'),
            cofins_valor=get(ICMSTot, 'vCOFINS'),
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
                    ('l10n_br_cnpj_cpf', '=', cnpj_cpf)], limit=1)

                if not transportadora_id:
                    state_obj = self.env['res.country.state']
                    state_id = state_obj.search([
                        ('code', '=', get(transp, 'transporta.UF')),
                        ('country_id.code', '=', 'BR')])

                    vals = {
                        'l10n_br_cnpj_cpf': cnpj_cpf,
                        'name': get(transp, 'transporta.xNome'),
                        'l10n_br_inscr_est': get(transp, 'transporta.IE', str),
                        'street': get(transp, 'transporta.xEnder'),
                        'city': get(transp, 'transporta.xMun'),
                        'state_id': state_id.id,
                        'l10n_br_legal_name': get(transp, 'transporta.xNome'),
                        'company_type': 'company',
                        'is_company': True,
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
                'especie': get(vol, 'esp'),
                'quantidade_volumes': get(vol, 'qVol'),
                'numeracao': get(vol, 'nVol'),
                'peso_liquido': get(vol, 'pesoL'),
                'peso_bruto': get(vol, 'pesoB'),
                'marca': get(vol, 'marca'),
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
                protNFe.cStat == 110 and company_id.l10n_br_cnpj_cpf in protNFe.chNFe:
            return dict(
                chave_nfe=protNFe.chNFe,
                data_autorizacao=parser.parse(
                    str(nfe.protNFe.infProt.dhRecbto)),
                mensagem_retorno=protNFe.xMotivo,
                protocolo_nfe=protNFe.nProt,
                codigo_retorno=protNFe.cStat,
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
            'indicador_total': indicador_total, 'unidade_medida': str(item.prod.uCom),
            'cfop': cfop, 'ncm': ncm, 'product_ean': item.prod.cEAN,
            'product_cprod': codigo, 'product_xprod': item.prod.xProd,
            'cest': cest, 'item_pedido_compra': nItemPed,
            'company_id': company_id.id,
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

        return self.env['eletronic.document.line'].create(
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
            'item_lista_servico': get(issqn, 'cListServ'),
            'iss_aliquota': get(issqn, 'vAliq'),
            'iss_base_calculo': get(issqn, 'vBC'),
            'iss_valor': get(issqn, 'vISSQN'),
            'iss_valor_retencao': get(issqn, 'vISSRet'),
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
        return {'document_line_ids': items}

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
        invoice_eletronic = self.env['eletronic.document'].create(invoice_dict)

        # if account_invoice_automation:
        #     invoice = invoice_eletronic.prepare_account_invoice_vals(
        #         company_id, tax_automation=tax_automation,
        #         supplierinfo_automation=supplierinfo_automation,
        #         fiscal_position_id=fiscal_position_id,
        #         payment_term_id=payment_term_id)
        #     invoice_eletronic.invoice_id = invoice.id

    def existing_invoice(self, nfe):
        if hasattr(nfe, 'protNFe'):
            protNFe = nfe.protNFe.infProt
        else:
            raise UserError('XML invalido!')

        chave_nfe = protNFe.chNFe
        invoice_eletronic = self.env['eletronic.document'].search([
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

        city_id = self.env['res.city'].search([
            ('l10n_br_ibge_code', '=', get(tag_nfe, ender_tag + '.cMun', str)[2:]),
            ('state_id', '=', state_id.id)])

        partner = {
            'name': get(tag_nfe, 'xFant') or get(tag_nfe, 'xNome'),
            'street': get(tag_nfe, ender_tag + '.xLgr'),
            'l10n_br_number': get(tag_nfe, ender_tag + '.nro', str),
            'l10n_br_district': get(tag_nfe, ender_tag + '.xBairro'),
            'city_id': city_id.id,
            'state_id': state_id.id,
            'zip': get(tag_nfe, ender_tag + '.CEP', str),
            'country_id': state_id.country_id.id,
            'phone': get(tag_nfe, ender_tag + '.fone'),
            'l10n_br_inscr_est': tag_nfe.IE.text if get(tag_nfe, 'IE', str) else None,
            'l10n_br_inscr_mun': tag_nfe.IM.text if get(tag_nfe, 'IM', str) else None,
            'l10n_br_cnpj_cpf': str(cnpj_cpf),
            'l10n_br_legal_name': get(tag_nfe, 'xNome'),
            'company_type': company_type,
            'is_company': is_company,
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
        ncm_id = self.env['account.ncm'].search([
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
            'type': 'product',
            'l10n_br_ncm_id': ncm_id.id,
            'standard_price': get(nfe_item, 'vUnCom'),
            'lst_price': 0.0,
            'l10n_br_cest': get(nfe_item, 'CEST', str),
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

    def prepare_account_invoice_line_vals(self, item):
        if item.product_id:
            product = item.product_id.with_context(force_company=self.company_id.id)
            if product.property_account_expense_id:
                account_id = product.property_account_expense_id
            else:
                account_id =\
                    product.categ_id.property_account_expense_categ_id
        else:
            account_id = self.env['ir.property'].with_context(
                force_company=self.company_id.id).get(
                    'property_account_expense_categ_id', 'product.category')

        vals = {
            'product_id': item.product_id.id,
            'product_uom_id': item.uom_id.id,
            'name': item.name if item.name else item.product_xprod,
            'quantity': item.quantidade,
            'price_unit': item.preco_unitario,
            'account_id': account_id.id,
        }
        return vals

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
            [('partner_id.l10n_br_cnpj_cpf', '=', dest_cnpj_cpf)])

        # company = self.env.company
        if not company:
            company = self.env['res.company'].sudo().search(
                [('partner_id.l10n_br_cnpj_cpf', '=', emit_cnpj_cpf)])
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
            ('l10n_br_cnpj_cpf', '=', cnpj_cpf_partner)], limit=1)

        if not partner_automation and not emit_id:
            raise UserError(
                "Parceiro não encontrado, caso deseje cadastrar " +
                "um parceiro selecione a opção 'Cadastrar Parceiro'.")

        return dict(
            company_id=company.id,
            tipo_operacao=tipo_operacao,
            partner_id=emit_id.id,
            destinatary=destinatary,
        )

    # ==================================================
    # Novos métodos para importação de XML
    def get_basic_info(self, nfe):
        nfe_type = get(nfe.NFe.infNFe.ide, 'tpNF', str)
        total = nfe.NFe.infNFe.total.ICMSTot.vNF
        products = len(nfe.NFe.infNFe.det)
        vals = self.inspect_partner_from_nfe(nfe)
        already_imported = self.existing_invoice(nfe)
        return dict(
            already_imported=already_imported,
            nfe_type=nfe_type,
            amount_total=total,
            total_products=products,
            **vals
        )

    def inspect_partner_from_nfe(self, nfe):
        '''Importação da sessão <emit> do xml'''
        nfe_type = nfe.NFe.infNFe.ide.tpNF
        tag_nfe = None
        if nfe_type == 1:
            tag_nfe = nfe.NFe.infNFe.emit
        else:
            tag_nfe = nfe.NFe.infNFe.dest

        if hasattr(tag_nfe, 'CNPJ'):
            cnpj_cpf = cnpj_cpf_format(str(tag_nfe.CNPJ.text).zfill(14))
        else:
            cnpj_cpf = cnpj_cpf_format(str(tag_nfe.CPF.text).zfill(11))

        partner_id = self.env['res.partner'].search([
            ('l10n_br_cnpj_cpf', '=', cnpj_cpf)], limit=1)

        partner_data = "%s - %s" % (cnpj_cpf, tag_nfe.xNome)
        return dict(partner_id=partner_id.id, partner_data=partner_data)
    
    
    def generate_eletronic_document(self, xml_nfe, create_partner):
        nfe = objectify.fromstring(xml_nfe)
        
        invoice_dict = {}
        if self.existing_invoice(nfe):
            raise UserError('Nota Fiscal já importada para o sistema!')

        partner_vals = self._get_company_invoice(nfe, create_partner)
        company_id = self.env['res.company'].browse(
            partner_vals['company_id'])
        invoice_dict.update(partner_vals)
        invoice_dict.update({
            'nfe_processada': base64.encodestring(xml_nfe),
            'nfe_processada_name': "NFe%08d.xml" % nfe.NFe.infNFe.ide.nNF
        })
        invoice_dict.update(self.get_protNFe(nfe, company_id))
        invoice_dict.update(self.get_main(nfe))
        partner = self.get_partner_nfe(
            nfe, partner_vals['destinatary'], create_partner)
        invoice_dict.update(
            self.get_ide(nfe, partner_vals['tipo_operacao']))
        invoice_dict.update(partner)
        invoice_dict.update(self.get_ICMSTot(nfe))
        invoice_dict.update(self.get_items(
            nfe, company_id, partner['partner_id'],
            invoice_dict['partner_id'],
            False))
        invoice_dict.update(self.get_infAdic(nfe))
        invoice_dict.update(self.get_cobr_fat(nfe))
        invoice_dict.update(self.get_transp(nfe))
        invoice_dict.update(
            {'reboque_ids': [(0, None, self.get_reboque(nfe))]})
        invoice_dict.update({'volume_ids': [(0, None, self.get_vol(nfe))]})
        invoice_dict.update(self.get_cobr_dup(nfe))
        invoice_dict.update(self.get_compra(nfe))
        invoice_dict.pop('destinatary', False)
        return self.env['eletronic.document'].create(invoice_dict)

    def check_inconsistency_and_redirect(self):
        to_check = []
        for line in self.document_line_ids:
            if not line.product_id or not line.uom_id:
                to_check.append((0, 0, {
                    'eletronic_line_id': line.id,
                    'uom_id': line.uom_id.id,
                    'product_id': line.product_id.id,
                }))

        if to_check:
            wizard = self.env['wizard.nfe.configuration'].create({
                'eletronic_doc_id': self.id,
                'partner_id': self.partner_id.id,
                'nfe_item_ids': to_check
            })
            return {
                "type": "ir.actions.act_window",
                "res_model": "wizard.nfe.configuration",
                'view_type': 'form',
                'views': [[False, 'form']],
                "name": "Configuracao",
                "res_id": wizard.id,
                'flags': {'mode': 'edit'}
            }
            

    def _prepare_account_invoice_vals(self):
        operation = 'in_invoice' \
            if self.tipo_operacao == 'entrada' else 'out_invoice'
        journal_id = self.env['account.move'].with_context(
            default_type=operation, default_company_id=self.company_id.id
        ).default_get(['journal_id'])['journal_id']
        partner = self.partner_id.with_context(force_company=self.company_id.id)
        account_id = partner.property_account_payable_id.id \
            if operation == 'in_invoice' else \
            partner.property_account_receivable_id.id

        vals = {
            'eletronic_doc_id': self.id,
            'company_id': self.company_id.id,
            'type': operation,
            'state': 'draft',
            'invoice_origin': self.pedido_compra,
            'ref': "%s/%s" % (self.numero, self.serie_documento),
            'invoice_date': self.data_emissao.date(),
            'date': self.data_emissao.date(),
            'partner_id': self.partner_id.id,
            'journal_id': journal_id,
            'amount_total': self.valor_final,
            'invoice_payment_term_id': self.env.ref('l10n_br_nfe_import.payment_term_for_import').id,
        }
        return vals

    def generate_account_move(self):
        next_action = self.check_inconsistency_and_redirect()
        if next_action:
            return next_action
        
        vals = self._prepare_account_invoice_vals()

        # purchase_order_vals = self._get_purchase_order_vals(self.pedido_compra)
        # purchase_order_id = None
        # if purchase_order_vals:
        #     vals.update(purchase_order_vals)
        #     purchase_order_id = vals['purchase_id']

        items = []
        for item in self.document_line_ids:
            invoice_item = self.prepare_account_invoice_line_vals(item)
            items.append((0, 0, invoice_item))

        vals['invoice_line_ids'] = items
        account_invoice = self.env['account.move'].create(vals)
        account_invoice.message_post(
            body="<ul><li>Fatura criada através da do xml da NF-e %s</li></ul>" % self.numero)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Fatura',
            'res_model': 'account.move',
            'res_id': account_invoice.id,
            'view_type': 'form',
            'views': [[False, 'form']],
            'flags': {'mode': 'readonly'}
        }


class EletronicDocumentLine(models.Model):
    _inherit = 'eletronic.document.line'

    product_ean = fields.Char('EAN do Produto (XML)')
    product_cprod = fields.Char('Cód .Fornecedor (XML)')
    product_xprod = fields.Char('Nome do produto (XML)')
