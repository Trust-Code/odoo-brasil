# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ambiente_nfse = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente_nfse",
        readonly=True)

    def _prepare_edoc_vals(self, inv, inv_lines):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv, inv_lines)

        res['ambiente_nfse'] = 'homologacao' \
            if inv.company_id.tipo_ambiente_nfse == '2' else 'producao'
        res['serie'] = inv.service_serie_id.id
        res['serie_documento'] = inv.service_document_id.id
        res['model'] = inv.service_document_id.code
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    state = fields.Selection(
        string="Status",
        selection=[
            ('pendente', 'Pendente'),
            ('transmitido', 'Transmitido'),
        ],
        default='pendente',
        help="""Define a situação eletrônica do item da fatura.
                Pendente: Ainda não foi transmitido eletronicamente.
                Transmitido: Já foi transmitido eletronicamente."""
    )

    numero_nfse = fields.Char(string="Número NFS-e",
                              help="""Número da NFS-e na qual o item foi
                              transmitido eletrônicamente.""")
