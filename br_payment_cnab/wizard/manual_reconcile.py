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

        if line_ids.filtered(lambda x: x.state not in ('processed', 'sent')):
            raise UserError(
                'Apenas itens enviados podem ser baixados manualmente')

        if self.confirmation == 'processed':
            line_ids.mark_order_line_processed('AA', 'Processado manualmente')
        elif self.confirmation == 'rejected':
            line_ids.mark_order_line_processed(
                True, 'ZZ', 'Rejeitado manualmente')
        elif self.confirmation == 'paid':
            line_ids.mark_order_line_paid('00', 'Confirmação manual')
        else:
            raise UserError('Confirmação inválida!')
