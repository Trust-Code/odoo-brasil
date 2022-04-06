# © 2019 Danimar Ribeiro
# Part of OdooNext. See LICENSE file for full copyright and licensing details.

import base64
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
    email_sent = fields.Boolean(string="E-mail enviado")

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
                self.origin_move_line_id._create_bank_tax_move(
                    (data.get('taxes_paid_cents') or 0) / 100)
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

    def _find_attachment_ids_email(self):
        return []

    def send_email_bank_slip(self):
        mail = self.env.user.company_id.l10n_br_bank_slip_email_template
        if not mail:
            raise UserError(_('Modelo de email padrão não configurado'))
        atts = self._find_attachment_ids_email()

        # if not atts:
        #     return

        _logger.info('Sending e-mail for bank_slip %s (number: %s)' % (
            self.id, self.invoice_ids[0].name))

        values = mail.generate_email(
            [self.invoice_ids[0].id],
            ['subject', 'body_html', 'email_from', 'email_to', 'partner_to',
             'email_cc', 'reply_to', 'mail_server_id']
        )[self.invoice_ids[0].id]
        subject = values.pop('subject')
        values.pop('body')
        values.pop('attachment_ids')
        values.pop('res_id')
        values.pop('model')
        # Hack - Those attachments are being encoded twice,
        # so lets decode to message_post encode again
        new_items = []
        for item in values.get('attachments', []):
            new_items.append((item[0], base64.b64decode(item[1])))
        values['attachments'] = new_items
        self.invoice_ids[0].message_post(
            body=values['body_html'], subject=subject,
            message_type='email', subtype_xmlid='mail.mt_comment',
            email_layout_xmlid='mail.mail_notification_paynow',
            attachment_ids=atts + mail.attachment_ids.ids, **values)

    def send_email_bank_slip_queue(self):
        bank_slip_queue = self.search(
            [('email_sent', '=', False),
             ('state', 'in', ['draft', 'pending'])], limit=5)

        bank_slip_queue = bank_slip_queue.filtered(
                lambda x: x.invoice_ids[0].l10n_br_edoc_policy  == 'after_payment')
        for bank_slip in bank_slip_queue:
            bank_slip.send_email_bank_slip()
            bank_slip.email_sent = True
