# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import pprint
import logging
from odoo import http, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)

INVOICE_CREATED = 'invoice.created'
INVOICE_CHANGED = 'invoice.status_changed'
INVOICE_DUE = 'invoice.due'


class IuguController(http.Controller):

    @http.route(
        '/iugu/webhook', type='http', auth="none",
        methods=['GET', 'POST'], csrf=False)
    def iugu_webhook(self, **post):
        _logger.info('iugu post-data: %s' % pprint.pformat(post))
        iugu_id = post['data[id]']
        event = post['event']

        if event == INVOICE_CHANGED:
            move_line = request.env['account.move.line'].with_user(SUPERUSER_ID).search(
                [('iugu_id', '=', iugu_id)])
            move_line.action_verify_iugu_payment()
        if event == INVOICE_DUE:
            move_line = request.env['account.move.line'].with_user(SUPERUSER_ID).search(
                [('iugu_id', '=', iugu_id)])
            move_line.action_notify_due_payment()
        return "ok"
