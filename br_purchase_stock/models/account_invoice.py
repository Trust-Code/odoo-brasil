# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        res['valor_seguro'] = line.valor_seguro
        res['outras_despesas'] = line.outras_despesas
        res['valor_frete'] = line.valor_frete
        res['ii_valor_despesas'] = line.valor_aduana
        return res

    total_despesas_aduana = fields.Float(
        string='Despesas Aduaneiras', digits=dp.get_precision('Account'),
        compute="_compute_amount")

    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'invoice_line_ids.price_total',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids
        self.total_despesas_aduana = sum(l.ii_valor_despesas for l in lines)
        self.amount_total = self.total_bruto - self.total_desconto + \
            self.total_tax + self.total_frete + self.total_seguro + \
            self.total_despesas
