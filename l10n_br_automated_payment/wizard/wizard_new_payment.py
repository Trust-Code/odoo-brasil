# © 2020 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class WizardNewPaymentInvoice(models.TransientModel):
    _name = 'wizard.new.payment.invoice'
    _description = 'Criar nova transação para pagamento'

    @api.model
    def default_get(self, fields):
        res = super(WizardNewPaymentInvoice, self).default_get(fields)
        res_id = self._context.get('active_id')
        res_model = self._context.get('active_model')
        if res_id and res_model == 'account.move':
            record = self.env[res_model].browse(res_id)
            res.update({
                'move_id': record.id,
                'description': record.invoice_payment_ref,
                'amount': record.amount_residual,
                'currency_id': record.currency_id.id,
                'partner_id': record.partner_id.id,
            })
        return res

    payment_due = fields.Boolean(string="Pagamento Atrasado?")
    description = fields.Char(string="Descrição", readonly=1)
    partner_id = fields.Many2one('res.partner', readonly=1)
    date_change = fields.Date(string='Novo Vencimento')
    move_id = fields.Many2one('account.move')
    amount = fields.Monetary(string="Valor")
    currency_id = fields.Many2one('res.currency')

    def action_change_invoice_iugu(self):
        if self.move_id.invoice_payment_state == 'paid':
            raise UserError('A fatura já está paga!')
        if self.date_change:

            self.move_id.receivable_move_line_ids.write(
                {'date_maturity': self.date_change}
            )

            self.move_id.generate_payment_transactions()
