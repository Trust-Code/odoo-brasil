# © 2019 Raphael Rodrigues, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PaymentAccountMoveLine(models.TransientModel):
    _name = 'payment.account.move.line'
    _description = 'Assistente Para Lançamento de Pagamentos'

    company_id = fields.Many2one(
        'res.company', related='journal_id.company_id',
        string='Exmpresa', readonly=True
    )
    move_line_id = fields.Many2one(
        'account.move.line', readonly=True, string='Conta à Pagar/Receber')
    invoice_id = fields.Many2one(
        'account.invoice', readonly=True, string='Fatura')
    partner_type = fields.Selection(
        [('customer', 'Cliente'), ('supplier', 'Fornecedor')], readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Cliente/Fornecedor', readonly=True
    )
    journal_id = fields.Many2one(
        'account.journal', string="Diário", required=True,
        domain=[('type', 'in', ('bank', 'cash'))]
    )
    communication = fields.Char(string='Anotações')
    payment_date = fields.Date(
        string='Data do Pagamento',
        default=fields.Date.context_today, required=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moeda', required=True,
        default=lambda self: self.env.user.company_id.currency_id
    )
    amount_residual = fields.Monetary(
        string='Saldo', readonly=True,
        related='move_line_id.amount_residual'
    )
    amount = fields.Monetary(
        string='Valor do Pagamento', required=True,
    )

    @api.model
    def default_get(self, fields):
        rec = super(PaymentAccountMoveLine, self).default_get(fields)
        move_line_id = rec.get('move_line_id', False)
        amount = 0
        if not move_line_id:
            raise UserError(
                _("Não foi selecionada nenhuma linha de cobrança."))
        move_line = self.env['account.move.line'].browse(move_line_id)
        if move_line[0].amount_residual:
            amount = move_line[0].amount_residual if \
                rec['partner_type'] == 'customer' else \
                move_line[0].amount_residual * -1
        if move_line[0].invoice_id:
            invoice = move_line[0].invoice_id
            rec.update({'invoice_id': invoice.id})
        rec.update({
            'amount': amount,
        })

        return rec

    def _get_payment_vals(self):
        """
        Method responsible for generating payment record amounts
        """
        payment_type = 'inbound' if self.move_line_id.debit else 'outbound'
        payment_methods = \
            payment_type == 'inbound' and \
            self.journal_id.inbound_payment_method_ids or \
            self.journal_id.outbound_payment_method_ids
        payment_method_id = payment_methods and payment_methods[0] or False
        vals = {
            'partner_id': self.partner_id.id,
            'move_line_id': self.move_line_id.id,
            'journal_id': self.journal_id.id,
            'communication': self.communication,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'payment_type': payment_type,
            'payment_method_id': payment_method_id.id,
            'currency_id': self.currency_id.id,
        }
        return vals

    def action_confirm_payment(self):
        """
        Method responsible for creating the payment
        """
        payment = self.env['account.payment']
        vals = self._get_payment_vals()
        pay = payment.with_context(
            force_counterpart_account=self.move_line_id.account_id.id).\
            create(vals)
        pay.post()
        move_line = self.env['account.move.line'].browse(vals['move_line_id'])
        lines_to_reconcile = (pay.move_line_ids + move_line).filtered(
            lambda l: l.account_id == move_line.account_id)
        lines_to_reconcile.reconcile()
