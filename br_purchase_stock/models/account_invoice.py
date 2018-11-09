# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'br.localization.filtering']

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        if not self.l10n_br_localization:
            return res
        res['l10n_br_valor_seguro'] = line.l10n_br_valor_seguro
        res['l10n_br_outras_despesas'] = line.l10n_br_outras_despesas
        res['l10n_br_valor_frete'] = line.l10n_br_valor_frete
        res['ii_valor_despesas'] = line.valor_aduana
        return res

    l10n_br_total_despesas_aduana = fields.Float(
        string='Despesas Aduaneiras', digits=dp.get_precision('Account'),
        compute="_compute_amount", oldname='total_despesas_aduana')

    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'invoice_line_ids.price_total',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        if self.l10n_br_localization:
            lines = self.invoice_line_ids
            self.l10n_br_total_despesas_aduana = sum(
                l.l10n_br_ii_valor_despesas for l in lines)
            self.amount_total = (
                self.l10n_br_total_bruto - self.l10n_br_total_desconto +
                self.l10n_br_total_tax + self.l10n_br_total_frete +
                self.l10n_br_total_seguro + self.l10n_br_total_despesas
            )
