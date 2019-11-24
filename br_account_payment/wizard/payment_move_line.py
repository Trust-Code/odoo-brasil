# © 2019 Raphael Rodrigues, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PaymentAccountMoveLine(models.TransientModel):
    _name = 'payment.account.move.line'
    _description = 'Assistente Para Lançamento de Pagamentos'

    company_id = fields.Many2one(
        'res.company', related='journal_id.company_id',
        string='Company', readonly=True
    )
    move_line_id = fields.Many2one('account.move.line', readonly=True)
    partner_type = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Vendor')], readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    journal_id = fields.Many2one(
        'account.journal', string="Payment Journal", required=True,
        domain=[('type', 'in', ('bank', 'cash'))]
    )
    communication = fields.Char(string='Memo')
    amount = fields.Monetary(string='Payment Amount', required=True)
    payment_date = fields.Date(
        string='Payment Date', default=fields.Date.context_today, required=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id
    )

    @api.onchange('amount')
    def validate_amount_payment(self):
        """
        Method used to validate the payment amount to be recorded
        :return:
        """
        move_line_amount = self.move_line_id.debit or self.move_line_id.credit
        if self.amount > move_line_amount:
            raise ValidationError(_(
                'O valor do pagamento não pode ser maior '
                'que o valor da parcela.'))

    @api.constrains('payment_date')
    def validate_payment_date(self):
        """
        Method used to validate payment date
        :return:
        """
        move_line_date = self.move_line_id.date
        if self.payment_date < move_line_date:
            raise ValidationError(_('A data do pagamento não pode ser inferior'
                                    ' a data da parcela.'))

    def action_confirm_payment(self):
        pass
