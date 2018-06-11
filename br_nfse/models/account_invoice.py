# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('invoice_eletronic_ids.numero_nfse')
    def _compute_nfse_number(self):
        for inv in self:
            numeros = inv.invoice_eletronic_ids.mapped('numero_nfse')
            numeros = [n for n in numeros if n]
            inv.numero_nfse = ','.join(numeros)

    ambiente_nfse = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente_nfse",
        readonly=True)
    nfse_eletronic = fields.Boolean(
        related="service_document_id.nfse_eletronic", readonly=True)
    numero_nfse = fields.Char(
        'NFS-e', size=30, compute='_compute_nfse_number', store=True)

    def _prepare_edoc_vals(self, inv, inv_lines, serie_id):
        res = super(AccountInvoice, self)._prepare_edoc_vals(
            inv, inv_lines, serie_id)
        res['nfse_eletronic'] = inv.nfse_eletronic
        res['ambiente'] = inv.ambiente_nfse
        res['serie'] = serie_id.id
        res['serie_documento'] = serie_id.code
        res['model'] = serie_id.fiscal_document_id.code
        res['numero'] = serie_id.internal_sequence_id.next_by_id()
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
