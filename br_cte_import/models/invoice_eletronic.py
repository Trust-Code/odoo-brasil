import base64
import logging
from dateutil import parser
from datetime import datetime
from lxml import objectify

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# CAMPOS REMOVIDOS CTE
# finNFe (finalidade_emissao); indDest (identificador_destinatario)


def cnpj_cpf_format(cnpj_cpf):
    if len(cnpj_cpf) == 14:
        cnpj_cpf = (
            cnpj_cpf[0:2]
            + "."
            + cnpj_cpf[2:5]
            + "."
            + cnpj_cpf[5:8]
            + "/"
            + cnpj_cpf[8:12]
            + "-"
            + cnpj_cpf[12:14]
        )
    else:
        cnpj_cpf = (
            cnpj_cpf[0:3]
            + "."
            + cnpj_cpf[3:6]
            + "."
            + cnpj_cpf[6:9]
            + "-"
            + cnpj_cpf[9:11]
        )
    return cnpj_cpf


def convert(obj, conversion=None):
    if conversion:
        return conversion(obj.text)
    if isinstance(obj, objectify.StringElement):
        return str(obj)
    if isinstance(obj, objectify.IntElement):
        return int(obj)
    if isinstance(obj, objectify.FloatElement):
        return float(obj)
    raise "Tipo não implementado %s" % str(type(obj))


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


class InvoiceEletronic(models.Model):
    _inherit = "invoice.eletronic"

    model = fields.Selection(selection_add=[("57", "57 - CTe")])

    def import_cte(
        self,
        company_id,
        cte,
        cte_xml,
        partner_automation=False,
        account_invoice_automation=False,
        tax_automation=False,
        supplierinfo_automation=False,
        fiscal_position_id=False,
        payment_term_id=False,
        invoice_dict=None,
    ):
        invoice_dict = invoice_dict or {}
        if self.cte_existing_invoice(cte):
            raise UserError("Documento Eletrônico já importado!")

        partner_vals = self._cte_get_company_invoice(cte, partner_automation)
        company_id = self.env["res.company"].browse(
            partner_vals["company_id"]
        )
        invoice_dict.update(partner_vals)
        invoice_dict.update(
            {
                "nfe_processada": base64.encodestring(cte_xml),
                "nfe_processada_name": "CTe%08d.xml" % cte.CTe.infCte.ide.nCT,
            }
        )
        invoice_dict.update(self.get_protCTe(cte, company_id))
        invoice_dict.update(self.get_main(cte))
        partner = self.get_partner_cte(
            cte, partner_vals["destinatary"], partner_automation
        )
        invoice_dict.update(
            self.cte_get_ide(cte, partner_vals["tipo_operacao"])
        )
        invoice_dict.update(partner)
        invoice_dict.update(self.cte_get_items(cte))
        invoice_dict.update(self.cte_get_totals(cte))
        invoice_dict.pop("destinatary", False)
        invoice_eletronic = self.env["invoice.eletronic"].create(invoice_dict)

        if account_invoice_automation:
            invoice = invoice_eletronic.prepare_account_invoice_vals(
                company_id,
                tax_automation=tax_automation,
                supplierinfo_automation=supplierinfo_automation,
                fiscal_position_id=fiscal_position_id,
                payment_term_id=payment_term_id,
            )
            invoice_eletronic.invoice_id = invoice.id

    def cte_existing_invoice(self, nfe):
        if hasattr(nfe, "protCTe"):
            protCTe = nfe.protCTe.infProt
        else:
            raise UserError("XML invalido!")

        chave_nfe = protCTe.chCTe

        invoice_eletronic = self.env["invoice.eletronic"].search(
            [("chave_nfe", "=", chave_nfe)]
        )

        return invoice_eletronic

    def _cte_get_company_invoice(self, nfe, partner_automation):
        emit = nfe.CTe.infCte.emit
        tipo_operacao = "entrada"

        if hasattr(emit, "CNPJ"):
            cnpj_cpf_partner = cnpj_cpf_format(str(emit.CNPJ.text).zfill(14))
        else:
            cnpj_cpf_partner = cnpj_cpf_format(str(emit.CPF.text).zfill(11))

        destinatary = True
        company = self.env.user.company_id

        emit_id = self.env["res.partner"].search(
            [("cnpj_cpf", "=", cnpj_cpf_partner)], limit=1
        )

        if not partner_automation and not emit_id:
            raise UserError(
                "Parceiro não encontrado, caso deseje cadastrar \
                um parceiro selecione a opção 'Cadastrar Parceiro'."
            )

        return dict(
            company_id=company.id,
            tipo_operacao=tipo_operacao,
            partner_id=emit_id.id,
            destinatary=destinatary,
        )

    def get_protCTe(self, nfe, company_id):
        protCTe = nfe.protCTe.infProt

        if (
            protCTe.cStat in [100, 150]
            or protCTe.cStat == 110
            and company_id.cnpj_cpf in protCTe.chCTe
        ):
            return dict(
                chave_nfe=protCTe.chCTe,
                data_autorizacao=parser.parse(
                    str(nfe.protCTe.infProt.dhRecbto)
                ),
                mensagem_retorno=protCTe.xMotivo,
                protocolo_nfe=protCTe.nProt,
                codigo_retorno=protCTe.cStat,
                eletronic_event_ids=[
                    (
                        0,
                        None,
                        {
                            "code": protCTe.cStat,
                            "name": protCTe.xMotivo,
                        },
                    )
                ],
            )

    def get_partner_cte(self, cte, destinatary, partner_automation):
        """Importação da sessão <emit> do xml"""
        tag_cte = None
        if destinatary:
            tag_cte = cte.CTe.infCte.emit
        else:
            tag_cte = cte.CTe.infCte.rem

        if hasattr(tag_cte, "CNPJ"):
            cnpj_cpf = cnpj_cpf_format(str(tag_cte.CNPJ.text).zfill(14))
        else:
            cnpj_cpf = cnpj_cpf_format(str(tag_cte.CPF.text).zfill(11))

        partner_id = self.env["res.partner"].search(
            [("cnpj_cpf", "=", cnpj_cpf)], limit=1
        )
        if not partner_id and partner_automation:
            partner_id = self._create_partner(tag_cte, destinatary)
        elif not partner_id and not partner_automation:
            raise UserError(
                (
                    "Parceiro não cadastrado. Selecione a opção cadastrar "
                    + "parceiro, ou realize o cadastro manualmente."
                )
            )

        return dict(partner_id=partner_id.id)

    def cte_get_ide(self, cte, operacao):
        """Importa a seção <ide> do xml"""
        ide = cte.CTe.infCte.ide
        modelo = ide.mod
        serie = ide.serie
        num_controle = ide.cCT
        numero_cte = ide.nCT
        data_emissao = parser.parse(str(ide.dhEmi))
        data_fatura = get(ide, "dhSaiEnt")
        if data_fatura:
            data_fatura = parser.parse(str(data_fatura))
        ambiente = "homologacao" if ide.tpAmb == 2 else "producao"

        return dict(
            tipo_operacao=operacao,
            model=str(modelo),
            serie_documento=serie,
            numero_controle=num_controle,
            numero=numero_cte,
            data_emissao=data_emissao,
            data_fatura=data_fatura,
            ambiente=ambiente,
            code="AUTO",
            state="imported",
            name="Documento Eletrônico: n° " + str(numero_cte),
        )

    def cte_get_items(self, cte):
        product_delivery = self.env.ref(
            "br_cte_import.product_product_delivery"
        )

        infCte = cte.CTe.infCte

        price = infCte.vPrest.vRec
        cfop = infCte.ide.CFOP

        invoice_eletronic_Item = {
            "product_id": product_delivery.id,
            "name": product_delivery.name,
            "uom_id": product_delivery.uom_id.id,
            "quantidade": 1,
            "preco_unitario": price,
            "valor_bruto": price,
            "valor_liquido": price,
            "tipo_produto": product_delivery.fiscal_type,
            "cfop": cfop,
        }
        if hasattr(infCte.imp.ICMS, "ICMS00"):
            invoice_eletronic_Item.update(
                {
                    "icms_cst": get(infCte.imp, "ICMS.ICMS00.CST", str).zfill(
                        2
                    ),
                    "icms_base_calculo": get(infCte.imp, "ICMS.ICMS00.vBC"),
                    "icms_aliquota": get(infCte.imp, "ICMS.ICMS00.pICMS"),
                    "icms_valor": get(infCte.imp, "ICMS.ICMS00.vICMS"),
                }
            )
        return {"eletronic_item_ids": [(0, 0, invoice_eletronic_Item)]}

    def cte_get_totals(self, cte):
        infCte = cte.CTe.infCte
        return {
            'valor_servicos': infCte.vPrest.vRec,
            'valor_final': infCte.vPrest.vRec,
            'valor_bc_icms': get(infCte.imp, "ICMS.ICMS00.vBC"),
            "valor_icms": get(infCte.imp, "ICMS.ICMS00.vICMS"),
        }
