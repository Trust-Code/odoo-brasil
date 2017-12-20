# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ambiente_nfse = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente_nfse",
        readonly=True)

    # Nota Campinas
    type_retention = fields.Selection([('A', u'ISS a recolher pelo prestador'),
                                       ('R', u'Retido na Fonte')],
                                      string='Tipo Recolhimento', default='A',)

    operation = fields.Selection([('A', u"Sem Dedução"),
                                  ('B', u"Com dedução/Materiais"),
                                  ('C', u"Imune/Isenta de ISSQN"),
                                  ('D', u"Devolução/Simples Remessa"),
                                  ('J', u"Intermediação")], string="Operação",)

    taxation = fields.Selection([('C', u"Isenta de ISS"),
                                 ('E', u"Não incidência no município"),
                                 ('F', u"Imune"),
                                 ('K', u"Exigibilidade Susp.Dec.J/Proc.A"),
                                 ('N', u"Não Tributável"),
                                 ('T', u"Tributável"),
                                 ('G', u"Tributável Fixo"),
                                 ('H', u"Tributável S.N."),
                                 ('M', u"Micro Empreendedor Individual(MEI)")],
                                string="Tributação",)

    def _return_pdf_invoice(self, doc):
        if self.service_document_id.code == '001':  # Paulistana
            return 'br_nfse.report_br_nfse_danfe'
        elif self.service_document_id.code == '002':  # Ginfes
            return 'br_nfse.report_br_nfse_danfe_ginfes'
        elif self.service_document_id.code == '008':  # Simpliss
            return 'br_nfse.report_br_nfse_danfe_simpliss'
        elif self.service_document_id.code == '010':
            return 'br_nfse.report_br_nfse_danfe_imperial'  # Imperial
        elif self.service_document_id.code == '009':  # Susesu
            return {
                "type": "ir.actions.act_url",
                "url": doc.url_danfe,
                "target": "_blank",
            }
        elif self.service_document_id.code == '011':
            return 'br_nfse.report_br_nfse_danfe_campinas'
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def _prepare_edoc_vals(self, inv, inv_lines):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv, inv_lines)

        res['ambiente_nfse'] = 'homologacao' \
            if inv.company_id.tipo_ambiente_nfse == '2' else 'producao'
        res['serie'] = inv.service_serie_id.id
        res['serie_documento'] = inv.service_document_id.id
        res['model'] = inv.service_document_id.code

        if res['model'] == '011':
            res['taxation'] = inv.taxation
            res['type_retention'] = inv.type_retention
            res['operation'] = inv.operation
        return res

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        res['codigo_servico_paulistana'] = \
            line.service_type_id.codigo_servico_paulistana
        res['codigo_tributacao_municipio'] = \
            line.service_type_id.codigo_tributacao_municipio
        return res
