import logging
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)


class IuguController(http.Controller):
    _notify_url = '/iugu/notificacao/'

    @http.route(
        '/iugu/notificacao/', type='http', auth="none",
        methods=['GET', 'POST'], csrf=False)
    def iugu_form_feedback(self, **post):
        request.env['payment.transaction'].sudo().form_feedback(post, 'iugu')
        return "<status>OK</status>"

    @http.route(
        '/iugu/checkout/redirect', type='http',
        auth='none', methods=['GET', 'POST'])
    def iugu_checkout_redirect(self, **post):
        post = post
        if 'secure_url' in post:
            return redirect(post['secure_url'])
