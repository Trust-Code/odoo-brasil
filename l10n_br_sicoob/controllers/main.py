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
        journal_id = int(post['journal'])
        journal = request.env['account.journal'].sudo().browse(journal_id)
        codigo = post['code']
        company = request.env['res.company'].sudo().browse(1)
        return_url = '%s/sicoob/authorization?journal=%s' % (
            journal.sicoob_url_base, journal.id)

        url = 'https://sandbox.sicoob.com.br/token'
        header = {
            "Content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic %s" % company.sicoob_token_basic,
        }
        data = {
            'grant_type': 'authorization_code',
            'code': codigo,
            'redirect_uri': return_url,
        }

        response = requests.post(url, data, headers=header)
        journal.temp_access_token = response.json()['access_token']

        act_jour_id = request.env.ref('account.action_account_journal_form').id
        url = '/web#id=%s&view_type=form&model=account.journal&action=%s' % (
            journal_id, act_jour_id
        )
        return werkzeug.utils.redirect(url)
