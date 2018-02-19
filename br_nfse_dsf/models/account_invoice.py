# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    type_retention = fields.Selection([('A', u'ISS a recolher pelo prestador'),
                                       ('R', u'Retido na Fonte')],
                                      string='Tipo Recolhimento', default='A')

    operation = fields.Selection([('A', u"Sem Dedução"),
                                  ('B', u"Com dedução/Materiais"),
                                  ('C', u"Imune/Isenta de ISSQN"),
                                  ('D', u"Devolução/Simples Remessa"),
                                  ('J', u"Intermediação")], string="Operação")

    taxation = fields.Selection([('C', u"Isenta de ISS"),
                                 ('E', u"Não incidência no município"),
                                 ('F', u"Imune"),
                                 ('K', u"Exigibilidade Susp.Dec.J/Proc.A"),
                                 ('N', u"Não Tributável"),
                                 ('T', u"Tributável"),
                                 ('G', u"Tributável Fixo"),
                                 ('H', u"Tributável S.N."),
                                 ('M', u"Micro Empreendedor Individual(MEI)")],
                                string="Tributação")

    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position(self):
        if self.fiscal_position_id:
            self.type_retention = self.fiscal_position_id.type_retention
            self.operation = self.fiscal_position_id.operation
            self.taxation = self.fiscal_position_id.taxation

    def _return_pdf_invoice(self, doc):
        if self.service_document_id.code == '011':
            return 'br_nfse_dsf.report_br_nfse_danfe_dsf'
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def _prepare_edoc_vals(self, inv, inv_lines):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv, inv_lines)
        if self.service_document_id.code == '011':
            res['taxation'] = inv.taxation
            res['type_retention'] = inv.type_retention
            res['operation'] = inv.operation
        return res
