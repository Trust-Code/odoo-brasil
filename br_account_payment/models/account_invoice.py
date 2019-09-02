# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


FIELD_STATE = {'draft': [('readonly', False)]}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', readonly=True,
        states=FIELD_STATE, string=u"Modo de pagamento")

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)

        for invoice_line in res:
            line = invoice_line[2]
            line['payment_mode_id'] = self.payment_mode_id.id
        return res

    @api.multi
    def register_payment(self, payment_line,
                         writeoff_acc_id=False, writeoff_journal_id=False):
        if self._context.get('move_line_to_reconcile'):
            line_to_reconcile = self._context.get('move_line_to_reconcile')
            return (line_to_reconcile + payment_line).reconcile(
                writeoff_acc_id, writeoff_journal_id)
        else:
            return super(AccountInvoice, self).register_payment(
                self, payment_line, writeoff_acc_id=writeoff_acc_id,
                writeoff_journal_id=writeoff_journal_id)
