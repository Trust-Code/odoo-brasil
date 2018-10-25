# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.exceptions import UserError


class l10nBrPaymentManualReconcile(models.TransientModel):
    _name = 'l10n_br_payment.manual.reconcile'

    name = fields.Char(string="Nome")
    confirmation = fields.Selection([
        ('processed', 'Processado'),
        ('paid', 'Pago'),
        ('rejected', 'Rejeitado')], string="Confirmação do Pagamento")

    def action_confirm_payments(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        line_ids = self.env['payment.order.line'].browse(active_ids)

        if line_ids.filtered(lambda x: x.state != 'sent'):
            raise UserError(
                'Apenas itens enviados podem ser baixados manualmente')

        if self.confirmation == 'processed':
            line_ids.write({'state': 'processed'})
        elif self.confirmation == 'rejected':
            line_ids.write({'state': 'rejected'})
        elif self.confirmation == 'paid':
            line_ids.mark_order_line_paid()
        else:
            raise UserError('Confirmação inválida!')
