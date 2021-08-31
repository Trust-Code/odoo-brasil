from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    eletronic_doc_id = fields.Many2one('eletronic.document', string="Nota Fiscal")

    def _recompute_payment_terms_lines(self):
        return super(AccountMove, self.with_context(eletronic_doc_id=self.eletronic_doc_id))._recompute_payment_terms_lines()

    def action_invoice_open(self):
        super(AccountMove, self).action_invoice_open()
        for invoice in self:

            for item in invoice.invoice_line_ids:
                if not item.product_cprod:
                    continue

                seller_id = self.env['product.supplierinfo'].search([
                    ('product_code', '=', item.product_cprod),
                    ('name', '=', invoice.partner_id.id)])

                if not seller_id:
                    self._create_supplierinfo(item, invoice.partner_id)

    def _create_supplierinfo(self, account_invoice_line_id, partner_id):
        vals = {
            'name':  partner_id.id,
            'product_name': account_invoice_line_id.product_xprod,
            'product_code': account_invoice_line_id.product_cprod,
            'product_tmpl_id': account_invoice_line_id.product_id.id,
        }

        return self.env['product.supplierinfo'].create(vals)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    imported = fields.Boolean('Importado via NFe', readonly=True)
    product_ean = fields.Char('EAN - NFe')
    product_cprod = fields.Char('Código - NFe')
    product_xprod = fields.Char('Nome - NFe')
