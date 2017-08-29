# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ambiente_nfse = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente_nfse",
        readonly=True)

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        res['codigo_servico_paulistana'] = \
            line.service_type_id.codigo_servico_paulistana
        return res

    def action_preview_danfse(self):
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])
        if not docs:
            raise UserError(u'Não existe um E-Doc relacionado à esta fatura')

        if self.invoice_model == '009':
            if docs[0].state != 'done':
                raise UserError('Nota Fiscal na fila de envio. Aguarde!')
            return {
                "type": "ir.actions.act_url",
                "url": docs[0].url_danfe,
                "target": "_blank",
            }

        report = ''
        if self.invoice_model == '001':
            report = 'br_nfse.main_template_br_nfse_danfe'
        elif self.invoice_model == '008':
            report = 'br_nfse.main_template_br_nfse_danfe_simpliss'

        action = self.env['report'].get_action(
            docs.ids, report)
        action['report_type'] = 'qweb-html'
        return action
