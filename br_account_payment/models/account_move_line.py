# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line', 'br.localization.filtering']

    l10n_br_payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string=u"Modo de pagamento",
        oldname='payment_mode_id')
    l10n_br_order_line_id = fields.Many2one(
        'payment.order.line', string='Linha de Pagamento',
        oldname='order_line_id')

    @api.multi
    @api.depends('debit', 'credit', 'user_type_id', 'amount_residual')
    def _compute_payment_value(self):
        for item in self.filtered(lambda x: x.l10n_br_localization):
            item.l10n_br_payment_value = item.debit \
                if item.user_type_id.type == 'receivable' else item.credit * -1
    l10n_br_payment_value = fields.Monetary(
        string="Valor", compute=_compute_payment_value, store=True,
        currency_field='company_currency_id',
        oldname='payment_value')

    @api.multi
    def action_register_payment(self):
        dummy, act_id = self.env['ir.model.data'].get_object_reference(
            'account', 'action_account_invoice_payment')
        receivable = (self.user_type_id.type == 'receivable')
        vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
        vals['context'] = {
            'default_amount': self.debit or self.credit,
            'default_partner_type': 'customer' if receivable else 'supplier',
            'default_partner_id': self.partner_id.id,
            'default_communication': self.name,
            'default_payment_type': 'inbound' if receivable else 'outbound',
            'default_move_line_id': self.id,
        }
        if self.invoice_id:
            vals['context']['default_invoice_ids'] = [self.invoice_id.id]
        return vals
