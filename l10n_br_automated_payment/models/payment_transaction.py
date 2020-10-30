# © 2019 Danimar Ribeiro
# Part of OdooNext. See LICENSE file for full copyright and licensing details.

import iugu
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    transaction_url = fields.Char(string="Url de Pagamento", size=256) 
    origin_move_line_id = fields.Many2one('account.move.line')
    date_maturity = fields.Date(string="Data de Vencimento")

    def cron_verify_transaction(self):
        documents = self.search([('state', 'in', ['draft', 'pending']), ], limit=50)
        for doc in documents:
            try:
                doc.action_verify_transaction()
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                _logger.exception("Payment Transaction ID {}: {}.".format(
                    doc.id, str(e)), exc_info=True)

    def action_verify_transaction(self):
        if self.acquirer_id.provider != 'iugu':
            return
        if not self.acquirer_reference:
            raise UserError('Esta transação não foi enviada a nenhum gateway de pagamento')
        token = self.env.company.iugu_api_token
        iugu.config(token=token)
        iugu_invoice_api = iugu.Invoice()

        data = iugu_invoice_api.search(self.acquirer_reference)
        if "errors" in data:
            raise UserError(data['errors'])
        if data.get('status', '') == 'paid' and self.state not in ('done', 'authorized'):
            self._set_transaction_done()
            self._post_process_after_done()
            if self.origin_move_line_id:
                self.origin_move_line_id._create_bank_tax_move(data)
        else:
            self.iugu_status = data['status']

    def cancel_transaction_in_iugu(self):
        if not self.acquirer_reference:
            raise UserError('Esta parcela não foi enviada ao IUGU')
        token = self.env.company.iugu_api_token
        iugu.config(token=token)
        iugu_invoice_api = iugu.Invoice()
        iugu_invoice_api.cancel(self.acquirer_reference)

    def action_cancel_transaction(self):
        self._set_transaction_cancel()
        if self.acquirer_id.provider == 'iugu':
            self.cancel_transaction_in_iugu()
