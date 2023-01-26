from odoo import models, fields


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()

        if 'res_id' in res:
            invoice_ids = self.env['account.move'].browse(res.get('res_id'))
        else:
            invoice_ids = self.env['account.move'].search(res.get('domain'))
        fiscal_pos = self.fiscal_position_id

        for invoice_id in invoice_ids:
            for line in invoice_id.invoice_line_ids:
                tax_rules = fiscal_pos.get_tax_rules(
                    invoice_id.company_id, line.product_id, invoice_id.partner_id
                )
                line.l10n_br_tax_rule_ids = tax_rules

        return res