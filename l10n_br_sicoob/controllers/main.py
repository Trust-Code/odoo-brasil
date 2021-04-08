# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import werkzeug
import requests
from odoo import http
from odoo.http import request


class SicoobController(http.Controller):

    @http.route(
        '/sicoob/authorization', type='http', auth="none",
        methods=['GET', 'POST'], csrf=False)
    def sicoob_authorization(self, **post):
        journal = request.env['account.journal'].sudo().search([
            ('bank_statements_source', '=', 'sicoob_sync')
        ], limit=1)
        codigo = post['code']
        return_url = '%s/sicoob/authorization' % journal.l10n_br_sicoob_url_base

        if journal.l10n_br_sicoob_enviroment == 'producao':
            url = 'https://api.sisbr.com.br/auth/token'
        else:
            url = 'https://sandbox.sicoob.com.br/token'
        header = {
            "Content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic %s" % journal.l10n_br_sicoob_token_basic,
        }
        data = {
            'grant_type': 'authorization_code',
            'code': codigo,
            'redirect_uri': return_url,
        }

        response = requests.post(url, data, headers=header)
        journal.l10n_br_sicoob_access_token = response.json()['access_token']

        act_jour_id = request.env.ref('account.action_account_journal_form').id
        url = '/web#id=%s&view_type=form&model=account.journal&action=%s' % (
            journal.id, act_jour_id
        )
        return werkzeug.utils.redirect(url)
